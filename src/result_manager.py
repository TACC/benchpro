# System Imports
import configparser as cp
import copy
import csv
import glob as gb
import os
import shutil as su
import subprocess
import sys
import time
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    pass

# Local Imports
import src.logger as logger

glob = None

# Move benchmark directory from complete to captured/failed, once processed
def move_to_archive(result_path, dest):
    if not os.path.isdir(result_path):
        glob.lib.msg.error("result directory '" + glob.lib.rel_path(result_path) + "' not found.")

    # Move to archive
    try:
        su.move(result_path, dest)
    # If folder exists, rename and try again
    except:
        glob.lib.msg.warning("Result directory already exists in archive. Appending suffix .dup")        
        # Rename result dir
        su.move(result_path, result_path + ".dup")
        # Try again
        move_to_archive(result_path + ".dup", dest)

# Create .capture-complete file in result dir
def capture_complete(result_path):
    glob.lib.msg.low("Successfully captured result in " + glob.lib.rel_path(result_path))
    move_to_archive(result_path, glob.stg['captured_path'])

# Create .capture-failed file in result dir
def capture_failed(result_path):
    glob.lib.msg.high("Failed to capture result in " + glob.lib.rel_path(result_path))
    # Move failed result to subdir if 'move_failed_result' is set
    if glob.stg['move_failed_result']:
        move_to_archive(result_path, glob.stg['failed_path'])

def capture_skipped(result_path):
    glob.lib.msg.low("Skipping this dryrun result in " + glob.lib.rel_path(result_path))
    if glob.stg['move_failed_result']:
        move_to_archive(result_path, glob.stg['failed_path'])

# Function to test if benchmark produced valid result
def validate_result(result_path):

    # Get dict of report file contents
    glob.report_dict = glob.lib.report.read(result_path)
    if not glob.report_dict:
        glob.lib.msg.low("Unable to read benchmark report file in " + glob.lib.rel_path(result_path))
        return "failed", None

    # Get output file path
    glob.output_path = glob.lib.files.find_exact(glob.report_dict['result']['output_file'], result_path)

    # Deal with dry_run 
    if glob.report_dict['bench']['task_id'] == "dry_run":
        return "skipped", None

    # Test for benchmark output file
    if not glob.output_path:
        glob.lib.msg.warning("Result file " + glob.report_dict['result']['output_file'] + " not found in " + \
                                glob.lib.rel_path(result_path) + ". It seems the benchmark failed to run.\nWas dry_run=True?")
        return "failed", None

    glob.lib.msg.log("Looking for valid result in " + glob.output_path)

    # Run expr collection
    if glob.report_dict['result']['method'] == 'expr':

        # replace <file> filename placeholder with value in glob_obj.cfg
        glob.report_dict['result']['expr'] = glob.report_dict['result']['expr'].replace("[output_file]", glob.output_path)

        # Run validation expression on output file
        try:
            glob.lib.msg.log("Running: '" + glob.report_dict['result']['expr'] + "'")
            cmd = subprocess.run(glob.report_dict['result']['expr'], shell=True,
                                         check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.lib.msg.log("Pulled result from " + glob.output_path + ":  " + result_str + \
                            " " + glob.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            glob.lib.msg.warning("Using '" + glob.report_dict['result']['expr'] + "' on file " + \
                                    glob.lib.rel_path(glob.output_path) + \
                                    " failed to find a valid a result. Skipping." )
            return "failed", None

    # Run scipt collection
    elif glob.report_dict['result']['method'] == 'script':
        result_script = os.path.join(glob.stg['script_path'], glob.stg['result_scripts_dir'], glob.report_dict['result']['script'])
        if not os.path.exists(result_script):
            glob.lib.msg.warning("Result collection script not found in "+ glob.lib.rel_path(result_script))
            return "failed", None

        # Run validation script on output file
        try:
            glob.lib.msg.log("Running: '" + result_script + " " + glob.output_path + "'")
            cmd = subprocess.run(result_script + " " + glob.output_path, shell=True,
                                check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.lib.msg.log("Pulled result from " + glob.output_path + ":  " + result_str + " " + \
                            glob.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            print(e)
            glob.lib.msg.warning("Running script '" + glob.lib.rel_path(result_script) + "' on file " + \
                                            glob.lib.rel_path(glob.output_path) + \
                                            " failed to find a valid a result." )
            return "failed", None
            
     # Cast to float
    try:
        result = float(result_str)
    except:
        glob.lib.msg.warning("result extracted from " + glob.lib.rel_path(glob.output_path) + " is not a float: '" + \
                                result_str + "'")
        return "failed", None

    # Check float non-zero
    if not result:
        glob.lib.msg.warning("result extracted from " + glob.lib.rel_path(glob.output_path) + " is '0.0'.")
        return "failed", None

    glob.lib.msg.log("Successfully found result '" + str(result) + " " + glob.report_dict['result']['unit'] + " for result " + \
                    glob.lib.rel_path(result_path))

    # Return valid result and unit
    return result, glob.report_dict['result']['unit']

# Get required key from report, if not found try get it from the [bench] section, otherwise error
def get_required_key(section, key):
    try:
        return glob.report_dict[section][key]
    except:
        pass
    try:
        return glob.report_dict['bench'][key]
    except:    
        glob.lib.msg.error("missing required report field '"+key+"'")

# Get optional key from report or return ""
def get_optional_key(section, key):
    try:
        return glob.report_dict[section][key]
    except:
        return ""

# Get timestamp from output file
def get_timestamp(line_id):
    output_file = os.path.join(glob.result_path, glob.report_dict['bench']['stdout'])

    # Search for tiem line and return in
    with open(output_file, 'r') as f:
        for line in f.readlines():
            if line.startswith(line_id):
                return line

    # Time line not found 
    return None

# Return start time from job output file
def get_start_time():
    start = get_timestamp("START")
    if start:
        return start.split(" ")[1]
    return None

# Return end time from job output file
def get_end_time():
    end = get_timestamp("END")
    if end:
        return get_timestamp("END").split(" ")[1]
    return None

# Get difference of end and start times from job output file
def get_elapsed_time():
    start_sec = get_timestamp("START")
    end_sec   = get_timestamp("END")

    if start_sec and end_sec: 
        return int(end_sec.split(" ")[2]) - int(start_sec.split(" ")[2])
    return None

# Generate dict for postgresql 
def get_insert_dict(result_path, result, unit):
    
    # Get JOBID in order to get NODELIST from sacct
    try:
        task_id = glob.report_dict['bench']['task_id']
    except:
        glob.lib.msg.low(e)
        glob.lib.msg.warning("Failed to read key 'task_id' in " + glob.lib.rel_path(bench_report) + ". Skipping.")
        return False
  
    elapsed_time = None
    end_time = None
    submit_time = get_required_key('bench', 'start_time')
    # Handle local exec
    if task_id == "local":
        task_id = "0"

    # Get elapsed and end time from output file
    elapsed_time = get_elapsed_time()
    end_time = get_end_time()

    nodelist = glob.lib.sched.get_nodelist(task_id)

    insert_dict = {}
   
    insert_dict['username']         = glob.user
    insert_dict['system']           = get_required_key('build', 'system')
    insert_dict['submit_time']      = submit_time
    insert_dict['elapsed_time']     = elapsed_time
    insert_dict['end_time']         = end_time
    insert_dict['capture_time']     = datetime.now()
    insert_dict['description']      = get_optional_key('bench', 'description')
    insert_dict['exec_mode']       = get_required_key('bench', 'exec_mode')
    insert_dict['task_id']          = task_id
    insert_dict['job_status']       = glob.lib.sched.get_job_status(task_id)
    insert_dict['nodelist']         = ", ".join(nodelist)
    insert_dict['nodes']            = get_required_key('bench', 'nodes')
    insert_dict['ranks']            = get_required_key('bench', 'ranks')
    insert_dict['threads']          = get_required_key('bench', 'threads')
    insert_dict['gpus']             = get_required_key('config', 'gpus')
    insert_dict['dataset']          = get_required_key('bench', 'dataset')
    insert_dict['result']           = str(result)
    insert_dict['result_unit']      = unit
    insert_dict['resource_path']    = os.path.join(glob.user, insert_dict['system'], insert_dict['task_id'])
    insert_dict['app_id']           = get_optional_key('build', 'app_id')


    # Remove None values
    insert_fields = list(insert_dict.keys())

    for key in insert_fields:
        if insert_dict[key] is None:
            insert_dict.pop(key)

    model_fields = glob.lib.db.get_table_fields(glob.stg['result_table'])
    insert_fields = insert_dict.keys()

    for key in insert_fields:

        # Remove key from model list
        if key in model_fields:
            model_fields.remove(key)
        # Error if trying to insert field not in model
        else:
            glob.lib.msg.error("Trying to insert into field '" + key + \
                                        "' not present in results table '" + glob.stg['result_table'] + "'")

    return insert_dict

# Create directory on remote server
def make_remote_dir(dest_dir):
    # Check that SSH key exists
    try:
        expr = "ssh -i " + glob.stg['ssh_key_path'] +" " + glob.stg['ssh_user'] + "@" + glob.stg['db_host'] + " -t mkdir -p " + dest_dir
        glob.lib.msg.log("Running: '" + expr + "'")
        # ssh -i [key] [user]@[db_host] -t mkdir -p [dest_dir]
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

        glob.lib.msg.log("Directory " + dest_dir  + " created on " + glob.stg['db_host'])

    except subprocess.CalledProcessError as e:
        glob.lib.msg.low(e)
        glob.lib.msg.log("Failed to create directory " + dest_dir + " on " + glob.stg['db_host'])
        return False

    return True

# SCP files to remote server
def scp_files(src_dir, dest_dir):

    # Check that SSH key exists 
    try:
        expr = "scp -i " + glob.stg['ssh_key_path'] + " -r " + src_dir + " " + glob.stg['ssh_user'] + "@" + glob.stg['db_host'] + ":" + dest_dir + "/"
        glob.lib.msg.log("Running: '" + expr + "'")
        # scp -i [key] -r [src_dir] [user]@[server]:[dest_dir]
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

        glob.lib.msg.log("Copied " + src_dir + " to " + glob.stg['db_host'] + ":" + dest_dir)

    except subprocess.CalledProcessError as e:
        glob.lib.msg.low(e)
        glob.lib.msg.log("Failed to copy " + src_dir + " to " + glob.stg['db_host'] + "+" + dest_dir)
        return False    

    return True

# Send benchmark provenance files to db server
def send_files(result_dir, dest_dir):

    # Use SCP
    if glob.stg['file_copy_handler'] == "scp":
        if not glob.user or not glob.stg['ssh_key']:
            glob.lib.msg.error("Keys 'ssh_user' and 'ssh_key' required in glob_obj.cfg if using SCP file transmission.")

        server_path = os.path.join(glob.stg['scp_path'],dest_dir)

        # Check SSH key 
        if not glob.lib.files.find_exact(glob.stg['ssh_key_path'], ""):
            glob.lib.msg.error("Unable to access ssh key " + glob.stg('ssh_key'))

        # Create directory on remote server
        if make_remote_dir(server_path):

            # Copy main output file
            scp_files(glob.output_path, server_path)

            # Copy matching files to server
            search_substrings = ["*.err", "*.out", "*.sched", "*.txt", "*.log"]
            for substring in search_substrings:
                matching_files = gb.glob(os.path.join(glob.result_path, substring))
                for match in matching_files:
                    scp_files(match, server_path)

            # SCP bench_files to server
            if os.path.isdir(os.path.join(glob.result_path, "bench_files")):
                scp_files(os.path.join(glob.result_path, "bench_files"), server_path)

            # SCP hw_utils to server
            if os.path.isdir(os.path.join(glob.result_path, "hw_report")):
                scp_files(os.path.join(glob.result_path, "hw_report"), server_path)


        else:
            glob.lib.msg.error("Failed to create remote directory on database server.")

        # Use local blackhole
    elif glob.stg['file_copy_handler'] == "cp":
        if not glob.stg['collection_path']:
            glob.lib.msg.error("Key 'collection_path' required in $BP_HOME/settings.ini if using 'cp' file transmission mode.")

        # Check write permissions
        if not glob.lib.files.write_permission(glob.stg['collection_path']): 
            glob.lib.msg.error("Unable to write result data to " + glob.stg['collection_path'])
        
        # File destination
        copy_path = os.path.join(glob.stg['collection_path'], dest_dir)
        glob.lib.files.create_dir(copy_path) 
        
        # Copy files to local directory
        glob.lib.files.copy(copy_path, glob.output_path, "", False)

        # Copy matching files to server
        search_substrings = ["*.err", "*.out", "*.sched", "*.job", "*.txt", "*.log"]
        for substring in search_substrings:
            matching_files = gb.glob(os.path.join(glob.result_path, substring))
            for match in matching_files:
                glob.lib.files.copy(copy_path, os.path.join(glob.result_path, match), "", False)

        # SCP bench_files to server
        if os.path.isdir(os.path.join(glob.result_path, "bench_files")):
            glob.lib.files.copy(copy_path, os.path.join(glob.result_path, "bench_files"), "", False)

        # SCP hw_utils to server
        if os.path.isdir(os.path.join(glob.result_path, "hw_report")):
            glob.lib.files.copy(copy_path, os.path.join(glob.result_path, "hw_report"), "", False)

    # Transmission method neither 'scp' or 'cp'
    else:
       glob.lib.msg.error("unknown 'file_copy_handler' option in settings.cfg. Accepts 'scp' or 'cp'.") 
       
# Look for results and send them to db
def capture_result(glob_obj):
    global glob
    glob = glob_obj

    # Start logger
    logger.start_logging("CAPTURE", glob.stg['results_log_file'] + "_" + glob.stg['time_str'] + ".log", glob)

    # Get list of results in $BP_RESULTS/complete with a COMPLETE job state
    results = glob.lib.get_completed_results(glob.lib.get_pending_results(), True)

    # No outstanding results
    if not results:
        glob.lib.msg.high("No new results found in " + glob.lib.rel_path(glob.stg['pending_path']))

    else:
        glob.lib.msg.log("Capturing " + str(len(results)) + " results")
        captured = 0
        if len(results) == 1: glob.lib.msg.heading("Starting capture for " + str(len(results)) + " new result.")
        else: glob.lib.msg.heading("Starting capture for " + str(len(results)) + " new results.")

        for result_dir in results:
            # Capture application profile for this result to db if not already present
            glob.lib.msg.log("Capturing " + result_dir)
            glob.lib.db.capture_application(os.path.join(glob.stg['pending_path'], result_dir))

            glob.result_path = os.path.join(glob.stg['pending_path'], result_dir)
            result, unit = validate_result(glob.result_path)

            # If unable to get valid result, skipping this result
            if result == "failed":
                capture_failed(glob.result_path)
                continue
            
            if result == "skipped":
                capture_skipped(glob.result_path)
                continue

            glob.lib.msg.low("Result: " + str(result) + " " + unit)

            # 1. Get insert_dict
            insert_dict = get_insert_dict(glob.result_path, result, unit)

            # If insert_dict failed
            if not insert_dict:
                capture_failed(glob.result_path)
                continue

            # 2. Insert result into db
            glob.lib.msg.low("Inserting into database...")
            glob.lib.db.capture_result(insert_dict)

            # 3. Copy files to collection dir
            glob.lib.msg.low("Sending provenance data...")
            send_files(glob.result_path, insert_dict['resource_path'])

            # 4. Touch .capture-complete file
            capture_complete(glob.result_path)
            captured += 1

        glob.lib.msg.high(["", "Done. " + str(captured) + " results sucessfully captured"])

# Test if search field is valid in results/models.py
def test_search_field(field):

    if field in glob.model_fields:
        return True

    else:
        glob.lib.msg.error(["'" + field + "' is not a valid search field.", 
                            "Available fields:"] +
                            glob.model_fields)

# Parse comma-delmited list of search criteria, test keys and return SQL WHERE statement
def parse_input_str(args):

    # No filter
    if not args or args == "all":
        return ";"
   
    select_str = ""
    for option in args.split(","):
        search = option.split('=')
        if not len(search) == 2:
            glob.lib.msg.error("Invalid query key-value pair: " + option)   
    
        # Test search key is in db
        if test_search_field(search[0]):
            if select_str: select_str += " AND "
            else: select_str += " " 

            # Handle time related query fields
            if search[0] in ['submit_time']:
                select_str += "DATE(" + search[0] + ") = '" + search[1] + "'"
            else:
                select_str += search[0] + "='" + search[1] + "'"

    return "WHERE " + select_str + ";"

# Query db for results
def query_db(glob_obj):
    global glob
    glob = glob_obj

    glob.model_fields = glob.lib.db.get_table_fields(glob.stg['result_table'])

    # Get sql query statement 
    search_str = "SELECT * FROM " + glob.stg['result_table'] + " " + parse_input_str(glob.args.dbResult)

    query_results = glob.lib.db.exec_query(search_str)

    col_width = [12, 12, 12, 12, 32, 18]
    # If query produced results
    if query_results:
        print()
        print("Running query:")
        print(search_str)
        print(str(len(query_results)) + " results were found:")
        print()
        print("|"+  "USER".center(col_width[0]) +"|"+\
                    "SYSTEM".center(col_width[1]) +"|"+ \
                    "JOBID".center(col_width[2]) +"|"+ \
                    "APPID".center(col_width[3]) +"|"+ \
                    "DATASET".center(col_width[4]) +"|"+ \
                    "RESULT".center(col_width[5]) +"|")

        print("|"+  "-"*col_width[0] +"+" +\
                    "-"*col_width[1] +"+"+ \
                    "-"*col_width[2] +"+"+ \
                    "-"*col_width[3] +"+"+ \
                    "-"*col_width[4] +"+"+ \
                    "-"*col_width[5] +"|")

        for result in query_results:
            print(  "|"+ result[0].center(col_width[0]) +\
                    "|"+ result[1].center(col_width[1]) +\
                    "|"+ str(result[3]).center(col_width[2]) +\
                    "|"+ str(result[17]).center(col_width[3]) +\
                    "|"+ str(result[7]).center(col_width[4]) +\
                    "|"+ (str(result[8])+" "+str(result[9])).center(col_width[5]) +"|")

        # Export to csv
        if glob.args.export:
            csvFile = os.path.join(glob.bp_home, "dbquery_"+ glob.stg['time_str'] + ".csv")
            print()
            print("Exporting to csv file: " + glob.lib.rel_path(csvFile))

            with open(csvFile, 'w') as outFile:
                wr = csv.writer(outFile, quoting=csv.QUOTE_ALL)
                wr.writerow(glob.model_fields)
                wr.writerows(query_results)

            print("Done.")

    else:
        print("No results found matching search criteria: '" + search_str + "'")

# List local results
def list_results(glob_obj):
    global glob
    glob = glob_obj

    # Get list of all results
    pending_list  = glob.lib.get_pending_results()
    captured_list = glob.lib.get_captured_results()
    failed_list   = glob.lib.get_failed_results()

    # Running results
    if glob.args.listResults == 'running' or glob.args.listResults == 'all':
        # Get list of running results
        running = glob.lib.get_completed_results(copy.deepcopy(pending_list), False)
        if running:
            print("Found", len(running), "running benchmarks:")
            for result in running:
                print("  " + result)
        else:
            print("No running benchmarks found.")
        print()

    # Completed results
    if glob.args.listResults == 'complete' or glob.args.listResults == 'all':
        # Get list of complete results
        pending_list = glob.lib.get_completed_results(pending_list, True)
        if pending_list:
            print("Found", len(pending_list), "complete benchmark results:")
            for result in pending_list:
                print("  " + result)
        else:
            print("No complete benchmark results found.")
        print()

    # Captured results
    if glob.args.listResults == 'captured' or glob.args.listResults == 'all':
        if captured_list:
            print("Found", len(captured_list), "captured benchmark results:")
            for result in captured_list:
                print("  " + result)
        else:
            print("No captured benchmark results found.")
        print()

    # Failed results
    if glob.args.listResults == 'failed' or glob.args.listResults == 'all':
        # Get list of results which failed to capture
        if failed_list:
            print("Found", len(failed_list), "failed benchmark results:")
            for result in failed_list:
                print("  " + result)
        else:
            print("No failed benchmark results found.")
        print()

    if not glob.args.listResults in ['running', 'complete', 'captured', 'failed', 'all']:
        print("Invalid input, provide 'running', 'complete', 'captured', 'failed' or 'all'.")

# Get list of result dirs matching search str
def get_matching_results(result_path, result_str):
    matching_results = gb.glob(os.path.join(result_path, "*"+result_str+"*"))
    return matching_results

# Show info for local result
def query_result(glob_obj, result_label):
    global glob
    glob = glob_obj

    # Search ./results/complete ./results/captured and ./results/failed
    matching_dirs = get_matching_results(glob.stg['pending_path'],  result_label) + \
                    get_matching_results(glob.stg['captured_path'], result_label) + \
                    get_matching_results(glob.stg['failed_path'],   result_label)

    # No result found
    if not matching_dirs:
        glob.lib.msg.error("No matching result found matching '" + result_label + "'.")

    # Multiple results
    elif len(matching_dirs) > 1:
        glob.lib.msg.error(["Multiple results found matching '" + result_label + "'"] + \
                            sorted(["    " + x.split(glob.stg['sl'])[-1] for x in matching_dirs])+ \
                            [""])

    result_path = os.path.join(glob.stg['pending_path'], matching_dirs[0])
    bench_report = os.path.join(result_path, "bench_report.txt")

    if not os.path.isfile(bench_report):
        glob.lib.msg.error(["Missing report file " + glob.lib.rel_path(bench_report),
                            "It seems something went wrong with --bench"])

    task_id = ""
    print("Report for benchmark: " + result_label)
    print("----------------------------------------")   

    # Read report and print it
    report_dict = glob.lib.report.read(bench_report)

    for section in report_dict:
        print("[" + section + "]")
        for key in report_dict[section]:
            print(key.ljust(20) + report_dict[section][key])

    print("----------------------------------------")

    # Handle dryrun
    if report_dict['bench']['task_id'] == "dry_run":
        print("Dry_run - skipping result check.")
    else:
        # Local exec mode
        if report_dict['bench']['exec_mode'] == "local":
            # Check PID is not running        
            complete = not glob.lib.proc.pid_running(report_dict['bench']['task_id'])

        # Sched exec mode
        if report_dict['bench']['exec_mode'] == "sched":
            # Check jobid is not running
            complete = glob.lib.sched.check_job_complete(report_dict['bench']['task_id'])

        # If task complete, extract result
        if complete:
            result, unit = validate_result(result_path)
            if not result == "failed":
                print("Result: " + str(result) + " " + str(unit))

        else: 
            print("Job " + task_id + " still running.")

# Print list of result directories
def print_results(result_list):
    for result in result_list:
        print("  " + result)

# Delete list of result directories
def delete_results(result_list):
    print()
    print("\033[91;1mDeleting in", glob.stg['timeout'], "seconds...\033[0m")
    time.sleep(glob.stg['timeout'])
    print("No going back now...")
    for result in result_list:
        su.rmtree(result)
    print("Done.")

# Remove local result
def remove_result(glob_obj):
    global glob
    glob = glob_obj

    # Get list of all results
    pending_list  = glob.lib.get_pending_results()
    captured_list = glob.lib.get_captured_results()
    failed_list   = glob.lib.get_failed_results()

    # Check all results for failed status and remove
    if glob.args.delResult[0] == 'failed':
        if failed_list:
            print("Found", len(failed_list), "failed results:")
            print_results(failed_list)
            delete_results([os.path.join(glob.stg['failed_path'], x) for x in failed_list])
        else:
            print("No failed results found.")

    # Check all results for captured status and remove
    elif glob.args.delResult[0] == 'captured':
        if captured_list:
            print("Found", len(captured_list), "captured results:")
            print_results(captured_list)
            delete_results([os.path.join(glob.stg['captured_path'], x) for x in captured_list])
        else:
            print("No captured results found.")

    # Remove all results in ./results dir
    elif glob.args.delResult[0] == 'all':

        all_results = pending_list + captured_list + failed_list

        if all_results:
            print("Found", len(all_results), " results:")
            print_results(all_results)
            delete_results([os.path.join(glob.stg['pending_path'], x) for x in pending_list] +\
                            [os.path.join(glob.stg['captured_path'], x) for x in captured_list] +\
                            [os.path.join(glob.stg['failed_path'], x) for x in failed_list])
        else:
            print("No results found.")

    # Remove unique result matching input str
    else:
        results = get_matching_results(glob.stg['pending_path'], glob.args.delResult[0]) +\
                  get_matching_results(glob.stg['captured_path'], glob.args.delResult[0]) +\
                  get_matching_results(glob.stg['failed_path'], glob.args.delResult[0])
        if results:
            print("Found " + str(len(results)) + " matching results: ")
            for res in results:
                print("  " + res.split(glob.stg['sl'])[-1])
            delete_results(results)
        else:
            print("No results found matching '" + glob.args.delResult[0] + "'")


# Print app info from table
def print_app_from_table(glob_obj):

    global glob
    glob = glob_obj
    # Get app from table

    query = glob.args.dbApp

    # Print all applications in table 
    if query == "all":
        all_apps = glob.lib.db.get_app_from_table("*")    
        print(all_apps)


    else:

        app = glob.lib.db.get_app_from_table(glob.args.dbApp)


        if not app:
            print("No application found matching app_id='" + glob.args.dbApp + "'")
            sys.exit(0)

        app = app[0][0:]

        labels = [  "Code", 
                    "Version", 
                    "System", 
                    "Compiler", 
                    "MPI", 
                    "Module list", 
                    "Optimization Flags", 
                    "Executable", 
                    "Install prefix", 
                    "Build date", 
                    "Job ID", 
                    "App_ID"]

        print("----Application Report----")
        for i in range(12):
            print(labels[i].ljust(20) + " = " + str(app[i]))

        print("-------------------------")


