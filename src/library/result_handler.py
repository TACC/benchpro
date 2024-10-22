# System Imports
import configparser as cp
import copy
import csv
from datetime import datetime
import glob as gb
import os
import shutil as su
import subprocess
import sys
import time
from typing import List

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    pass

# Local Imports
import src.logger          as logger
from src.modules import Result


class init(object):

    def __init__(self, glob):
        self.glob = glob
        Result.glob = self.glob

    # Get contents of output file from result dir
    def set_vars(self, result_path:str) -> dict:

        self.result_path = result_path

        # Get dict of report file contents
        self.report_dict = self.glob.lib.report.read(result_path)
        if not self.report_dict:
            self.glob.lib.msg.low("Unable to read benchmark report file in " + self.glob.lib.rel_path(result_path))
            return False

        # Deal with dry_run
        if "dry" in self.report_dict['bench']['task_id']:
            self.glob.lib.msg.log("Skipping dry_run in " + result_path)
            return False

        # Get output file path
        self.output_path = self.glob.lib.files.find_exact(self.report_dict['result']['output_file'], result_path)
        # Test for benchmark output file
        if not self.output_path:
            self.glob.lib.msg.log("Result file " + self.report_dict['result']['output_file'] + " not found in " + \
                                    self.glob.lib.rel_path(result_path) + ". It seems the benchmark failed to run.\nWas dry_run=True?")
            return False

        return True
        

    def with_expr(self):

        # replace <file> filename placeholder with value in .cfg
        self.report_dict['result']['expr'] = self.report_dict['result']['expr'].replace("[output_file]", self.output_path)

        # Run extraction expression on output file
        try:
            self.glob.lib.msg.log("Running: '" + self.report_dict['result']['expr'] + "'")
            cmd = subprocess.run(self.report_dict['result']['expr'], shell=True,
                                         check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            self.glob.lib.msg.log("Pulled result from " + self.output_path + ":  " + result_str + \
                            " " + self.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.warn("Using '" + self.report_dict['result']['expr'] + "' on file " + \
                                    self.glob.lib.rel_path(self.output_path) + \
                                    " failed to find a valid a result. Skipping." )
            return None

        return result_str

    def with_script(self):

        # Check user's directory first
        result_script = os.path.join(self.glob.stg['user_results_path'],  self.report_dict['result']['script'])
        if not os.path.exists(result_script):

            # Check site's bin dir
            result_script = os.path.join(self.glob.stg['site_results_path'],  self.report_dict['result']['script'])
            if not os.path.exists(result_script):
                self.glob.lib.msg.warn("Result collection script '" + \
                                        self.report_dict['result']['script'] + \
                                        "' not found in " + \
                                        self.glob.lib.rel_path(self.glob.stg['user_results_path']))
                return None

        # Run validation script on output file
        try:
            self.glob.lib.msg.log("Running: '" + result_script + " " + self.output_path + "'")
            cmd = subprocess.run(result_script + " " + self.output_path, shell=True,
                                check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            self.glob.lib.msg.log("Pulled result from " + self.output_path + ":  " + result_str + " " + \
                            self.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.log("Running script '" + self.glob.lib.rel_path(result_script) + "' on file " + \
                                                self.glob.lib.rel_path(self.output_path) + \
                                            " failed to find a valid result." )
            return None

        return result_str

    def search(self) -> str:

        self.glob.lib.msg.log("Looking for valid result in " + self.output_path)

        # Run expr collection
        if self.report_dict['result']['method'] == 'expr':
            return self.with_expr()
            
    
        elif self.report_dict['result']['method'] == 'script':
            return self.with_script()


        self.glob.lib.msg.warn("Unrecognized result extraction method '" + \
                                self.report_dict['result']['method'] + \
                                "' found in " + self.result_path)
        return None

    def validate(self, result_str: str) -> float:

         # Cast to float
        try:
            result = round(float(result_str), 2)
        except:
            self.glob.lib.msg.log("result extracted from " + self.glob.lib.rel_path(self.output_path) + " is not a float: '" + \
                                    result_str + "'")

            self.glob.lib.msg.print_file_tail(os.path.join(self.report_dict['bench']['path'], self.report_dict['bench']['stderr']))
            return None

        # Check float non-zero
        if not result:
            self.glob.lib.msg.warn("result extracted from " + self.glob.lib.rel_path(self.output_path) + " is '0.0'.")
            return None

        return result


    # Retrieve result value from output file
    def extract(self, result_path: str) -> float:

        # Setup collection variables
        if not self.set_vars(result_path):
            return 0.

        # Extract result from file
        result = self.search()
        if not result:
            return 0.

        # Validate result 
        valid_result = self.validate(result)
        if not valid_result:
            return 0.

        self.glob.lib.msg.log("Successfully found result '" + result + " " + self.report_dict['result']['unit'] + " for result " + \
                        self.glob.lib.rel_path(result_path))

        # Return valid result
        return valid_result


    # Get result from benchmark dir
    def retrieve(self, result_path: str) -> float:
        # Get cached result
        cached_result = self.glob.lib.files.decache_result(result_path)
        if cached_result:
            return cached_result

        else:
            # Get result from file
            return self.extract(result_path)


    # Create directory on remote server
    def make_remote_dir(self, dest_dir: str):
        # Check that SSH key exists
        try:
            expr = "ssh -i " + self.glob.stg['ssh_key_path'] +" " + self.glob.stg['ssh_user'] + "@" + self.glob.stg['db_host'] + " -t mkdir -p " + dest_dir
            self.glob.lib.msg.log("Running: '" + expr + "'")
            # ssh -i [key] [user]@[db_host] -t mkdir -p [dest_dir]
            cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

            self.glob.lib.msg.log("Directory " + dest_dir  + " created on " + self.glob.stg['db_host'])

        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.low(e)
            self.glob.lib.msg.log("Failed to create directory " + dest_dir + " on " + self.glob.stg['db_host'])
            return False

        return True


    # SCP files to remote server
    def scp_files(self, src_dir: str, dest_dir: str) -> bool:

        # Check that SSH key exists 
        try:
            expr = "scp -i " + self.glob.stg['ssh_key_path'] + " -r " + src_dir + " " + self.glob.stg['ssh_user'] + "@" + self.glob.stg['db_host'] + ":" + dest_dir + "/"
            self.glob.lib.msg.log("Running: '" + expr + "'")
            # scp -i [key] -r [src_dir] [user]@[server]:[dest_dir]
            cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

            self.glob.lib.msg.log("Copied " + src_dir + " to " + self.glob.stg['db_host'] + ":" + dest_dir)

        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.low(e)
            self.glob.lib.msg.log("Failed to copy " + src_dir + " to " + self.glob.stg['db_host'] + "+" + dest_dir)
            return False    

        return True


    # Send benchmark provenance files to db server
    def send_files(self, result_dir: str, dest_dir: str):

        # Use SCP
        if self.glob.stg['file_copy_handler'] == "scp":
            if not self.glob.user or not self.glob.stg['ssh_key']:
                self.glob.lib.msg.error("Keys 'ssh_user' and 'ssh_key' required in glob_obj.cfg if using SCP file transmission.")

            server_path = os.path.join(self.glob.stg['scp_path'],dest_dir)

            # Check SSH key 
            if not self.glob.lib.files.find_exact(self.glob.stg['ssh_key_path'], ""):
                self.glob.lib.msg.error("Unable to access ssh key " + self.glob.stg('ssh_key'))

            # Create directory on remote server
            if self.make_remote_dir(server_path):

                # Copy main output file
                self.scp_files(self.output_path, server_path)

                # Copy matching files to server
                search_substrings = ["*.err", "*.out", "*.sched", "*.txt", "*.log"]
                for substring in search_substrings:
                    matching_files = gb.glob(os.path.join(self.result_path, substring))
                    for match in matching_files:
                        self.scp_files(match, server_path)

                # SCP bench_files to server
                if os.path.isdir(os.path.join(self.result_path, "bench_files")):
                    self.scp_files(os.path.join(self.result_path, "bench_files"), server_path)

                # SCP hw_utils to server
                if os.path.isdir(os.path.join(self.result_path, "hw_report")):
                    self.scp_files(os.path.join(self.result_path, "hw_report"), server_path)


            else:
                self.glob.lib.msg.error("Failed to create remote directory on database server.")

            # Use local blackhole
        elif self.glob.stg['file_copy_handler'] == "cp":
            if not self.glob.ev['BPS_COLLECT']:
                self.glob.lib.msg.error("Key 'collection_path' required in $BP_HOME/user.ini if using 'cp' file transmission mode.")

            # Check write permissions
            if not self.glob.lib.files.write_permission(glob.ev['BPS_COLLECT']): 
                self.glob.lib.msg.error("Unable to write result data to " + self.glob.ev['BPS_COLLECT'])
        
            # File destination
            copy_path = os.path.join(glob.ev['BPS_COLLECT'], dest_dir)
            self.glob.lib.files.create_dir(copy_path) 
    
            # Copy files to local directory
            self.glob.lib.files.copy(copy_path, self.output_path, "", False)
    
            # Copy matching files to server
            search_substrings = ["*.err", "*.out", "*.sched", "*.job", "*.txt", "*.log"]
            for substring in search_substrings:
                matching_files = gb.glob(os.path.join(self.result_path, substring))
                for match in matching_files:
                    self.glob.lib.files.copy(copy_path, os.path.join(self.result_path, match), "", False)

            # SCP bench_files to server
            if os.path.isdir(os.path.join(self.result_path, "bench_files")):
                self.glob.lib.files.copy(copy_path, os.path.join(self.result_path, "bench_files"), "", False)

            # SCP hw_utils to server
            if os.path.isdir(os.path.join(self.result_path, "hw_report")):
                self.glob.lib.files.copy(copy_path, os.path.join(self.result_path, "hw_report"), "", False)

        # Transmission method neither 'scp' or 'cp'
        else:
           self.glob.lib.msg.error("unknown 'file_copy_handler' option in settings.cfg. Accepts 'scp' or 'cp'.") 


    def construct_list(self, top_path: str) -> List[Result]:
        result_list = []
        for result_dir in self.glob.lib.files.get_subdirs(top_path):
            # Read report
            report = Result(os.path.join(top_path, result_dir))
            if report.success:
                result_list.append(report)
            else:
                result_list.append(report)
                #print("Incompatible report format.")
        return result_list


    def get_pending(self) -> List[Result]:
        return self.construct_list(self.glob.stg['pending_path'])


    def get_captured(self) -> List[Result]:
        return self.construct_list(self.glob.stg['captured_path'])


    def get_failed(self) -> List[Result]:
        return self.construct_list(self.glob.stg['failed_path'])


    def get_completed(self) -> List[Result]:
        pending_results = self.get_pending()
        complete_results = []

        for result in pending_results:
            result.process()
            if result.success and result.complete and not result.dry_run:
                complete_results.append(result)
        
        return complete_results


    def collect_reports(self, result_type: str = None) -> List[Result]:

        # Assign default Args value if not provided
        result_type = result_type or "all"

        # Check for valid input
        if result_type not in ["pending", "complete", "captured", "failed", "all"]:
            self.glob.lib.msg.error("Accepted inputs: all, pending, complete, captured, failed")

        report_list = []

        if result_type == "complete":
            report_list.extend(self.get_completed())
        if result_type in ["all", "pending"]:
            report_list.extend(self.get_pending())
        if result_type in ["all", "captured"]:
            report_list.extend(self.get_captured())
        if result_type in ["all", "failed"]:
            report_list.extend(self.get_failed())
        return report_list


    # Find list of result dirs matching search str
    def find(self, search_str: str = None) -> Result:

        # Convert str input to search dict
        search_str = search_str or self.glob.args.queryResult
        search_dict = self.glob.lib.parse_input_str(search_str, "result_id")

        # Get all result reports
        report_list = self.glob.lib.result.collect_reports()

        # Iterate over result reports
        for report in list(report_list):

            # Iterate over search criteria
            for key in search_dict:
                match = False
                # Key match in [bench] section
                if report.bench:
                    if key in report.bench:
                        # Value match
                        if search_dict[key] == report.bench[key]:
                            match = True
                # Key match in [build] section
                if report.build:
                    if key in report.build:
                        # Value match
                        if search_dict[key] == report.build[key]:
                            match = True

                if not match:   
                    report_list.remove(report)
                    break

        # No result found
        if not report_list:
            self.glob.lib.msg.error("No matching result found matching '" + search_str + "'.")

        # Multiple results
        elif len(report_list) > 1:
            self.glob.lib.msg.print_result_table(report_list)
            self.glob.lib.msg.error(["Multiple results found matching '" + search_str + "'"])

        # Take first match
        match = report_list[0]
        # Process result
        match.process()

        return match


    # Show info for local result
    def query(self, search_str: str = None) -> None:

        search_str = search_str or self.glob.args.queryResult
        # Look for result matching search str
        match = self.glob.lib.result.find(search_str)

        for section in match.report:
            print("------------ " + section.upper() + " -------------")
            for key in match.report[section]:
                print(key.ljust(20, ".") + " " +  match.report[section][key])

        print("----------------------------------------")

        # Handle dryrun
        if match.dry_run:
            print("Dry_run - skipping result check.")
            return 

        # If task complete, print result
        if match.complete and match.value:
            print("Result: " + str(match.value) + " " + str(match.unit))
        # Task still running
        elif match.status == "RUNNING":
            print("Job " + str(match.task_id) + " is still running.")
        # Task still pending
        elif match.status == "PENDING":
            print("Job " + str(match.task_id) + " is still queued.")
        # Failed
        else:
            self.glob.lib.msg.print_file_tail(os.path.join(match.path, match.bench['stderr']))


    # Print list of result directories
    def print_results(self, result_list):
        for result in result_list:
            print("  " + result)


    # Remove local result
    def remove(self, input_str: str = None) -> None:

        input_str = input_str or self.glob.args.delResult[0]
        remove_list = []
    

        # If removing by type
        if input_str in ['failed', 'captured', 'all']:
            # Get matching results
            remove_list = self.collect_reports(input_str)
        # Remove by search criteria
        else:
            remove_list = [self.find(input_str)]

        # No matching results
        if not remove_list:
            self.glob.lib.msg.exit("No results found.")

        # Print result to remove
        self.glob.lib.msg.print_result_table(remove_list)
         # Prompt user
        self.glob.lib.msg.prompt()

        # Delete results in list
        for idx, result in enumerate(remove_list):
            self.glob.lib.msg.high("Deleting " + str(idx+1) + " of " + str(len(remove_list)))
            self.glob.lib.files.delete_dir(result.path)
        self.glob.lib.msg.high("Done.")

    def dry_run(self, jobid: str) -> bool:
        if "dry" in jobid:
            return True
        return False


    def task_id(self, task: str) -> int:
        try:
            return int(task)
        except:
            return 0


    def app_id(self, build: dict) -> str:
        if "app_id" in build:
            return build['app_id']
        else:
            return "NA"


    def status(self, report: Result) -> str:
        # Check for cache first
        cached_status = self.glob.lib.files.decache_status(report.path)
        if cached_status:
            return cached_status

        # Dry run
        if "dry" in report.bench['task_id']:
            return report.bench['task_id']

        # Query scheduler
        if report.bench['exec_mode'] == "sched":

            return self.glob.lib.sched.task_status(str(report.task_id))
        # Query OS PID
        elif report.bench['exec_mode'] == "local":
            return self.glob.lib.proc.task_status(str(report.task_id))


    def complete(self, report: Result) -> bool:
        if report.status in ["COMPLETED", "CANCELLED", "ERROR", "FAILED", "TIMEOUT", "UNKNOWN"]:
            return True
        return False        
