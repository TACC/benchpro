# System Imports
import configparser as cp
import glob as gb
import os
import pwd
import re
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.exception as exception

# Contains several useful functions, mostly used by bencher and builder
class init(object):
    def __init__(self, glob):
            self.glob = glob

    # Get relative paths for full paths before printing to stdout
    def rel_path(self, path):
        # if empty str
        if not path:
            return None
        # if absolute
        if path[0] == self.glob.stg['sl']:
            return self.glob.stg['topdir_env_var'] + path.replace(self.glob.basedir, "")
        # if not
        else:
            return path

    # Find file in directory
    def find_exact(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name
    
        # Search recursively for file
        files = gb.glob(path+'/**/'+file_name, recursive = True)

        if files:
            return files[0]
        else:
            return None

    # Find *file* in directory
    def find_partial(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name
        # Search provided path for file
        for root, dirs, files in os.walk(path):
            match = next((s for s in files if file_name in s), None)
            if match:
                return os.path.join(root, match)
        # File not found
        return None

    # Get owner of file
    def file_owner(self, file_name):
        return pwd.getpwuid(os.stat(file_name).st_uid).pw_name

    # Get list of default modules
    def get_default_modules(self, cmd_prefix):
        
        try:
            cmd = subprocess.run(cmd_prefix +"ml -t -d av  2>&1", shell=True,
                                check=True, capture_output=True, universal_newlines=True)
        except:
            exception.error_and_quit(self.glob.log, "unable to execute 'ml -t -d av'")
        # Return list of default modules
        return cmd.stdout.split("\n")

    # Gets full module name of default module, eg: 'intel' -> 'intel/18.0.2'
    def get_full_module_name(self, module, default_modules):

        if not '/' in module:
            # Get default module version from 
            for line in default_modules:
                if module+"/" in line:
                    return line
            else:
                exception.error_and_quit(self.glob.log, "failed to process module '" + module + "'")

        else:
            return module

    # Check if module is available on the system
    def check_module_exists(self, module_dict, module_use):

        # Preload custom module path if needed
        cmd_prefix = ""
        if module_use:
            cmd_prefix = "ml use " + module_use + "; "

        # Get list of default system modules
        default_modules = self.get_default_modules(cmd_prefix)

        # Confirm defined modules exist on this system and extract full module name if necessary
        for module in module_dict:
            try:
                cmd = subprocess.run(cmd_prefix + "module spider " + module_dict[module], shell=True,
                                    check=True, capture_output=True, universal_newlines=True)

            except subprocess.CalledProcessError as e:
                exception.error_and_quit(self.glob.log, module + " module '" + module_dict[module] + "' not available on this system")

            # Update module with full label
            module_dict[module] = self.get_full_module_name(module_dict[module], default_modules)

    # Convert module name to usable directory name, Eg: intel/18.0.2 -> intel18
    def get_module_label(self, module):
        label = module
        if module.count(self.glob.stg['sl']) > 0:
            comp_ver = module.split(self.glob.stg['sl'])
            label = comp_ver[0] + comp_ver[1].split(".")[0]
        return label

    # Confirm application exe is available
    def check_exe(self, exe, code_path):
        exe_search = self.find_exact(exe, code_path)
        if exe_search:
            print("Application executable found at:")
            print(">  " + self.rel_path(exe_search))
            print()
        else:
            exception.error_and_quit(self.glob.log, "failed to locate application executable '" + exe + "'in " + self.rel_path(code_path))

    # Get a list of sub-directories, called by 'search_tree'
    def get_subdirs(self, base):
        return [name for name in os.listdir(base)
            if os.path.isdir(os.path.join(base, name))]

    # Recursive function to scan app directory, called by 'get_installed'
    def search_tree(self, installed_list, app_dir, start_depth, current_depth, max_depth):
        for d in self.get_subdirs(app_dir):
            if d != self.glob.stg['module_basedir']:
                new_dir = app_dir + self.glob.stg['sl'] + d
                # Once tree hits max search depth, append path to list
                if current_depth == max_depth:
                    installed_list.append(self.glob.stg['sl'].join(new_dir.split(self.glob.stg['sl'])[start_depth + 1:]))
                # Else continue to search tree 
                else:
                    self.search_tree(installed_list, new_dir, start_depth,current_depth + 1, max_depth)

    # Get list of installed apps
    def get_installed(self):
        app_dir = self.glob.stg['build_path']
        start = app_dir.count(self.glob.stg['sl'])
        # Send empty list to search function 
        installed_list = []
        self.search_tree(installed_list, app_dir, start, start, start + self.glob.stg['tree_depth'])
        installed_list.sort()
        return installed_list

    # Check if a string returns a unique installed application
    def check_if_installed(self, requested_code):
        installed_list = self.get_installed()
        matched_codes = []
        for code_string in installed_list:
            if requested_code in code_string:
                matched_codes.append(code_string)
        # No matches
        if len(matched_codes) == 0:
            print("No installed applications match your selection '" + requested_code + "'")
            print()
            print("Currently installed applications:")
            for code in installed_list:
                print(" " + code)
            sys.exit(2)
        # Unique match
        elif len(matched_codes) == 1:
            return matched_codes[0]
        # More than 1 match
        else:
            for code in matched_codes:
                # Exact match to 1 of multiple results
                if requested_code == code:
                    return code
            
        print("Multiple installed applications match your selection '" + requested_code + "':")
        for code in matched_codes:
            print("  ->" + code)
        print("Please be more specific.")
        sys.exit(1)

    # Check that job ID is not running
    def check_job_complete(self, jobid):
        # If job not available in squeue anymore
        try:
            cmd = subprocess.run("sacct -j " + jobid + " --format State", shell=True, \
                            check=True, capture_output=True, universal_newlines=True)
        # Assuming complete
        except:
            return True

        state = cmd.stdout.split("\n")[2]

        # Job COMPLETE
        if ("COMPLETED" in state) or ("CANCELLED" in state) or ("ERROR" in state):
            return True

        # Job RUNNING or PENDING
        return False

    # Get all results in ./results
    def get_all_results(self):
        results = self.get_subdirs(self.glob.stg['bench_path'])
        results.sort()
        return results

    # Test list of result dirs for file presence
    def filter_results_by_file(self, results_dir_list, check_file, criteria):
        filtered_results = []
        result_path = self.glob.stg['bench_path'] + self.glob.stg['sl']
        # Check list for 'check_file'
        for result_dir in results_dir_list:
            if os.path.isfile(result_path + self.glob.stg['sl'] + result_dir + self.glob.stg['sl'] + check_file) == criteria:
                filtered_results.append(result_dir)
        # Return list of dirs that pass the test
        return filtered_results

    # Return list of result dirs whose job RUNNING state meets criteria
    def filter_results_by_complete_jobid(self, criteria):

        not_failed = self.filter_results_by_file(self.get_all_results(), ".capture-failed", False)
        not_failed_and_not_captured = self.filter_results_by_file(not_failed, ".capture-complete", False)
        filtered_results = []

        # Check that job is complete
        for result in not_failed_and_not_captured:
            jobid = None

            try:
            # Get jobID from bench_report.txt
                with open(self.glob.stg['bench_path'] + self.glob.stg['sl'] + result + self.glob.stg['sl'] + self.glob.stg['bench_report_file'], 'r') as inFile:
                    for line in inFile:
                        if "jobid" in line:
                            jobid = line.split("=")[1].strip()
            except:
                pass

            # Check job is completed
            if self.check_job_complete(jobid) == criteria:
                filtered_results.append(result)

        filtered_results.sort()
        return filtered_results

    # Get result dirs that have '.capture-failed' file inside
    def get_failed_results(self):
        return self.filter_results_by_file(self.get_all_results(), ".capture-failed", True)

    # Get result dirs that have '.capture-complete' file inside
    def get_captured_results(self):
        return self.filter_results_by_file(self.get_all_results(), ".capture-complete", True)

    # Check if there are don't have '.capture-failed' or '.capture-complete' and JOBID != RUNNING 
    def get_pending_results(self):
        return self.filter_results_by_complete_jobid(True)

    # Check if there are benchmark jobs running
    def get_running_results(self):
        return self.filter_results_by_complete_jobid(False)

    # Get list of uncaptured results and print note to user
    def print_new_results(self):
        # Uncaptured results + job complete
        pending_results = self.get_pending_results()
        if pending_results:
            print("NOTE: There are " + str(len(pending_results)) + " uncaptured results found in " + self.rel_path(self.glob.stg['bench_path']))
            print("Run 'benchtool --capture' to send to database.")
            print()

    # Log cfg contents
    def send_inputs_to_log(self, label, cfg_list):
        self.glob.log.debug(label + " started with the following inputs:")
        self.glob.log.debug("======================================")
        for cfg in cfg_list:
            for seg in cfg:
                self.glob.log.debug("[" + seg + "]")
                for line in cfg[seg]:
                    self.glob.log.debug("  " + str(line) + "=" + str(cfg[seg][line]))
        self.glob.log.debug("======================================")

    # Check for unpopulated <<<keys>>> in template file
    def test_template(self, template_obj):

        key = "<<<.*>>>"
        unfilled_keys = [re.search(key, line) for line in template_obj]
        unfilled_keys = [match.group(0) for match in unfilled_keys if match]
    
        if len(unfilled_keys) > 0:
            # Conitue regardless
            if not self.glob.stg['exit_on_missing']:
                exception.print_warning(self.glob.log, "WARNING: Missing parameters were found in template file:" + ", ".join(unfilled_keys))
                exception.print_warning(self.glob.log, "exit_on_missing=False in settings.cfg so continuing anyway...")
            # Error and exit
            else:
                exception.error_and_quit(self.glob.log, "Missing parameters were found after populating the template file and exit_on_missing=True in settings.cfg: " + ' '.join(unfilled_keys))
        else:
            self.glob.log.debug("All build parameters were filled, continuing")

    # Create directories if needed
    def create_dir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                exception.error_and_quit(
                    self.glob.log, "Failed to create directory " + path)

    # Copy tmp files to directory
    def install(self, path, obj, new_obj_name):
        # Get file name
        if not new_obj_name:
            new_obj_name = obj
            if self.glob.stg['sl'] in obj:
                new_obj_name = obj.split(self.glob.stg['sl'])[-1]
            # Strip tmp prefix from file for new filename
            if 'tmp.' in obj:
                new_obj_name = obj[4:]
    
        try:
            su.copyfile(obj, path + self.glob.stg['sl'] + new_obj_name)
            self.glob.log.debug("Copied file " + obj + " into " + path)
        except IOError as e:
            print(e)
            exception.error_and_quit(
                self.glob.log, "Failed to move " + obj + " to " + path + self.glob.stg['sl'] + new_obj_name)

    # Get Job IDs of RUNNING AND PENDNIG jobs
    def get_active_jobids(self):
        # Get list of jobs from sacct
        running_jobs_list = []
        job_list = None
        try:
            cmd = subprocess.run("sacct -u mcawood", shell=True, \
                                check=True, capture_output=True, universal_newlines=True)
            job_list = cmd.stdout.split("\n")

        except:
            pass

        # Add RUNNING job IDs to list
        for job in job_list:
            if "RUNNING" in job or "PENDING" in job:
                running_jobs_list.append(int(job.split(" ")[0]))

        running_jobs_list.sort()

        return running_jobs_list

    # If build job is running, add dependency str
    def get_build_job_dependency(self, jobid):
        if not self.check_job_complete(jobid):
            self.glob.dep_list.append(jobid)

    # Set job dependency if max_running_jobs is reached
    def get_dep_str(self):
        if not self.glob.dep_list:
            return ""
        else:
            return "--dependency=afterany:" + ":".join(self.glob.dep_list) + " "

    # Submit script to scheduler
    def submit_job(self, dep, job_path, script_file):
        script_path= job_path + self.glob.stg['sl'] + script_file
        # If dry_run, quit
        if self.glob.stg['dry_run']:
            print("This was a dryrun, job script created at " + self.rel_path(script_path))
            self.glob.log.debug("This was a dryrun, job script created at " + script_path)
            # Return jobid and host placeholder 
            return "dryrun"

        else:
            print("Job script:")
            print(">  " + self.rel_path(script_path))
            print()
            print("Submitting to scheduler...")
            self.glob.log.debug("Submitting " + script_path + " to scheduler...")

            try:
                cmd = subprocess.run("sbatch " + dep + script_path, shell=True, \
                                     check=True, capture_output=True, universal_newlines=True)
    
                self.glob.log.debug(cmd.stdout)
                self.glob.log.debug(cmd.stderr)

                jobid = None
                i = 0
                jobid_line = "Submitted batch job"

                # Find job ID
                for line in cmd.stdout.splitlines():
                    if jobid_line in line:
                        jobid = line.split(" ")[-1]

                time.sleep(5)

                cmd = subprocess.run("squeue -a --job " + jobid, shell=True, \
                                     check=True, capture_output=True, universal_newlines=True)

                print(cmd.stdout)

                print()
                print("Job " + jobid + " output log:")
                print(">  "+ self.rel_path(job_path + self.glob.stg['sl'] + jobid + ".out"))
                print("Job " + jobid + " error log:")
                print(">  "+ self.rel_path(job_path + self.glob.stg['sl'] + jobid + ".err"))
                print()

                self.glob.log.debug(cmd.stdout)
                self.glob.log.debug(cmd.stderr)
                # Return job info
                return jobid

            except subprocess.CalledProcessError as e:
                print(e)
                exception.error_and_quit(self.glob.log, "failed to submit job to scheduler")

    # Get node suffixes from brackets: "[094-096]" => ['094', '095', '096']
    def get_node_suffixes(self, suffix_str):
        suffix_list = []
        for suf in suffix_str.split(','):
            if '-' in suf:
                start, end = suf.split('-')
                tmp = range(int(start), int(end)+1)
                tmp = [str(t).zfill(3) for t in tmp]
                suffix_list.extend(tmp)
            else:
                suffix_list.append(suf)
        return suffix_list

    # Parse SLURM nodelist to list: "c478-[094,102],c479-[032,094]" => ['c478-094', 'c478-102', 'c479-032', 'c479-094'] 
    def parse_nodelist(self, slurm_nodes):
        node_list = []
        while slurm_nodes:
            prefix_len = 4
            # Expand brackets first
            if '[' in slurm_nodes:
                # Get position of first '[' and ']'
                start = slurm_nodes.index('[')+1
                end = slurm_nodes.index(']')
                # Get node prefix for brackets, eg 'c478-'
                prefix = slurm_nodes[start-6:start-1]
                # Expand brackets 
                suffix = self.get_node_suffixes(slurm_nodes[start:end])
                node_list.extend([prefix + s for s in suffix])
                # Remove parsed nodes
                slurm_nodes = slurm_nodes[:start-6] + slurm_nodes[end+2:]
            # Extract remaining nodes
            else:
                additions = slurm_nodes.split(',')
                node_list.extend([s.strip() for s in additions])
                slurm_nodes = None

        node_list.sort()

        return node_list

    # Get NODELIST from sacct  using JOBID
    def get_nodelist(self, jobid):

        try:
            cmd = subprocess.run("sacct -X -P -j  " + jobid + " --format NodeList", shell=True, \
                                    check=True, capture_output=True, universal_newlines=True)

        except:
            return ""

        # Parse SLURM NODELIST into list
        return self.parse_nodelist(cmd.stdout.split("\n")[1])

    def overload(self, overload_key, param_dict):
        # If found matching key
            if overload_key in param_dict:
                old = param_dict[overload_key]
                datatype = type(param_dict[overload_key])

                try:
                    # Convert datatypes
                    if datatype is str: 
                        param_dict[overload_key] = str(self.glob.overload_dict[overload_key])
                    elif datatype is int:
                        param_dict[overload_key] = int(self.glob.overload_dict[overload_key])
                    elif datatype is bool:
                        param_dict[overload_key] = self.glob.overload_dict[overload_key] == 'True'

                except:
                    exception.error_and_quit(self.glob.log, "datatype mismatch for '" + overload_key +"', expected=" + datatype + ", provided=" + type(overload_key))

                print("Overloading " + overload_key + ": '" + str(old) + "' -> '" + str(param_dict[overload_key]) + "'" )
                # Remove key from overload dict
                self.glob.overload_dict.pop(overload_key)

    # Replace cfg params with cmd line inputs 
    def overload_params(self, search_dict):
        for overload_key in list(self.glob.overload_dict):
            # If dealing with code/sched/compiler cfg, descend another level
            if list(search_dict)[0] == "metadata":
                for section_dict in search_dict:
                    self.overload(overload_key, search_dict[section_dict])
            else:
                self.overload(overload_key, search_dict)

    # Print warning if cmd line params dict not empty
    def check_for_unused_overloads(self):
        if len(self.glob.overload_dict):
            print("The following --overload params are invalid:")
            for key in self.glob.overload_dict:
                print("  " + key + "=" + self.glob.overload_dict[key])
            exception.error_and_quit(self.glob.log, "Invalid input arguments.")

    # Write module to file
    def write_list_to_file(self, list_obj, output_file):
        with open(output_file, "w") as f:
            for line in list_obj:
                f.write(line)

