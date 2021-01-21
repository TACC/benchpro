# System Imports
import configparser as cp
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
import exception
import logger

glob = None

# Read benchmark report file input dict
#def get_bench_report(result_path):
#
#    # Confirm file exists
#    bench_report = os.path.join(result_path, glob.stg['bench_report_file'])
#    if not os.path.isfile(bench_report):
#        exception.print_warning(glob.log, "File '" + glob.stg['bench_report_file'] + "' not found in " + glob.lib.rel_path(result_path) + ". Skipping.")
#        return False
#
#    report_parser    = cp.ConfigParser()
#    report_parser.optionxform=str
#    report_parser.read(bench_report)
#
#    print()
#
#    # Confirm jobid is readable in report file
#    try:
#        jobid = report_parser.get('bench', 'jobid')
#    except:
#        print(e)
#        exception.print_warning(glob.log, "Failed to read key 'jobid' in " + glob.lib.rel_path(bench_report) + ". Skipping.")
#        return False
#
#    # Return dict of report file sections
#    return {section: dict(report_parser.items(section)) for section in report_parser.sections()}

# Move benchmark directory from pending to captured/failed, once processed
def move_to_archive(result_path, dest):
    if not os.path.isdir(result_path):
        exception.error_and_quit(glob.log, "result directory '" + glob.lib.rel_path(result_path) + "' not found.")

    # Move to archive
    try:
        su.move(result_path, dest)
    # If folder exists, rename and try again
    except:
        exception.print_warning(glob.log, "Result directory already exists in archive. Appending suffix .dup")        
        # Rename result dir
        su.move(result_path, result_path + ".dup")
        # Try again
        move_to_archive(result_path + ".dup", dest)

# Create .capture-complete file in result dir
def capture_complete(result_path):
    glob.log.debug("Successfully captured result in " + result_path)
    print("Successfully captured result in " + glob.lib.rel_path(result_path))
    move_to_archive(result_path, glob.stg['captured_path'])

# Create .capture-failed file in result dir
def capture_failed(result_path):
    glob.log.debug("Failed to capture result in " + result_path)
    print("Failed to capture result in " + glob.lib.rel_path(result_path))
    move_to_archive(result_path, glob.stg['failed_path'])

# Function to test if benchmark produced valid result
def validate_result(result_path):
    # Get dict of report file contents
    glob.report_dict = glob.lib.report.read(result_path)
    if not glob.report_dict:
        print("Unable to read benchmark report file in " + glob.lib.rel_path(result_path))
        return False, None

    # Get output file path
    glob.output_path = glob.lib.find_exact(glob.report_dict['result']['output_file'], result_path)

    # Test for benchmark output file
    if not glob.output_path:
        exception.print_warning(glob.log, "Result file " + glob.report_dict['result']['output_file'] + " not found in " + \
                                glob.lib.rel_path(result_path) + ". It seems the benchmark failed to run.\nWas dry_run=True?")
        return False, None

    glob.log.debug("Looking for valid result in " + glob.output_path)

    # Run expr collection
    if glob.report_dict['result']['method'] == 'expr':

        # replace <file> filename placeholder with value in glob_obj.cfg
        glob.report_dict['result']['expr'] = glob.report_dict['result']['expr'].replace("{output_file}", glob.output_path)

        # Run validation expression on output file
        try:
            glob.log.debug("Running: '" + glob.report_dict['result']['expr'] + "'")
            cmd = subprocess.run(glob.report_dict['result']['expr'], shell=True,
                                         check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.log.debug("Pulled result from " + glob.output_path + ":  " + result_str + \
                            " " + glob.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            exception.print_warning(glob.log, "Using '" + glob.report_dict['result']['expr'] + "' on file " + \
                                    glob.lib.rel_path(glob.output_path) + \
                                    " failed to find a valid a result. Skipping." )
            return False, None

    # Run scipt collection
    elif glob.report_dict['result']['method'] == 'script':
        result_script = os.path.join(glob.stg['script_path'], glob.stg['result_scripts_dir'], glob.report_dict['result']['script'])
        if not os.path.exists(result_script):
            exception.print_warning(glob.log, "Result collection script not found in "+ glob.lib.rel_path(result_script))
            return False, None

        # Run validation script on output file
        try:
            glob.log.debug("Running: '" + result_script + " " + glob.output_path + "'")
            cmd = subprocess.run(result_script + " " + glob.output_path, shell=True,
                                check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.log.debug("Pulled result from " + glob.output_path + ":  " + result_str + " " + \
                            glob.report_dict['result']['unit'])

        except subprocess.CalledProcessError as e:
            exception.print_warning(glob.log, "Running script '" + glob.lib.rel_path(result_script) + "' on file " + \
                                            glob.lib.rel_path(glob.output_path) + \
                                            " failed to find a valid a result." )
            return False, None
            
     # Cast to float
    try:
        result = float(result_str)
    except:
        exception.print_warning(glob.log, "result extracted from " + glob.lib.rel_path(glob.output_path) + " is not a float: '" + \
                                result_str + "'")
        return False, None

    # Check float non-zero
    if not result:
        exception.print_warning(glob.log, "result extracted from " + glob.lib.rel_path(glob.output_path) + " is '0.0'.")
        return False, None

    glob.log.debug("Successfully found result '" + str(result) + " " + glob.report_dict['result']['unit'] + " for result " + \
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
        exception.error_and_quit(glob.log, "missing required report field '"+key+"'")

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
        jobid = glob.report_dict['bench']['jobid']
    except:
        print(e)
        exception.print_warning(glob.log, "Failed to read key 'jobid' in " + glob.lib.rel_path(bench_report) + ". Skipping.")
        return False
  
    elapsed_time = None
    end_time = None
    submit_time = get_required_key('bench', 'start_time')
    # Handle local exec
    if jobid == "local":
        jobid = "0"

    # Get elapsed and end time from output file
    elapsed_time = get_elapsed_time()
    end_time = get_end_time()

    nodelist = glob.lib.sched.get_nodelist(jobid)

    insert_dict = {}
   
    insert_dict['username']         = glob.user
    insert_dict['system']           = get_required_key('build', 'system')
    insert_dict['submit_time']      = submit_time
    insert_dict['elapsed_time']     = elapsed_time
    insert_dict['end_time']         = end_time
    insert_dict['capture_time']     = datetime.now()
    insert_dict['description']      = get_optional_key('bench', 'description')
    insert_dict['jobid']            = jobid
    insert_dict['job_status']       = glob.lib.sched.get_job_status(jobid)
    insert_dict['nodelist']         = ", ".join(nodelist)
    insert_dict['nodes']            = get_required_key('bench', 'nodes')
    insert_dict['ranks']            = get_required_key('bench', 'ranks')
    insert_dict['threads']          = get_required_key('bench', 'threads')
    insert_dict['dataset']          = get_required_key('bench', 'dataset')
    insert_dict['result']           = str(result)
    insert_dict['result_unit']      = unit
    insert_dict['resource_path']    = os.path.join(glob.user, insert_dict['system'], insert_dict['jobid'])
    insert_dict['app_id']           = get_required_key('build', 'app_id')


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
            exception.error_and_quit(glob.log, "Trying to insert into field '" + key + \
                                        "' not present in results table '" + glob.stg['result_table'] + "'")

    return insert_dict


    return insert_dict['resource_path']

# Return valid SSH key path of error
def get_ssh_key():
    key_path = os.path.join(glob.stg['ssh_key_dir'], glob.stg['ssh_key'])
    if os.path.isfile(key_path):
        return key_path
    else:
        exception.error_and_quit(glob.log, "Could not locate SSH key '" + glob.stg['ssh_key'] + "' in " + glob.stg['ssh_key_dir'])

# Create directory on remote server
def make_remote_dir(dest_dir):
    # Check that SSH key exists
    key = get_ssh_key()
    try:
        expr = "ssh -i " + key +" " + glob.stg['ssh_user'] + "@" + glob.stg['db_host'] + " -t mkdir -p " + dest_dir
        glob.log.debug("Running: '" + expr + "'")
        # ssh -i [key] [user]@[db_host] -t mkdir -p [dest_dir]
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

        glob.log.debug("Directory " + dest_dir  + " created on " + glob.stg['db_host'])

    except subprocess.CalledProcessError as e:
        print(e)
        glob.log.debug("Failed to create directory " + dest_dir + " on " + glob.stg['db_host'])
        return False

    return True

# SCP files to remote server
def scp_files(src_dir, dest_dir):

    # Check that SSH key exists 
    key = get_ssh_key()

    try:
        expr = "scp -i " + key + " -r " + src_dir + " " + glob.stg['ssh_user'] + "@" + glob.stg['db_host'] + ":" + dest_dir + "/"
        glob.log.debug("Running: '" + expr + "'")
        # scp -i [key] -r [src_dir] [user]@[server]:[dest_dir]
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)

        glob.log.debug("Copied " + src_dir + " to " + glob.stg['db_host'] + ":" + dest_dir)

    except subprocess.CalledProcessError as e:
        print(e)
        glob.log.debug("Failed to copy " + src_dir + " to " + glob.stg['db_host'] + "+" + dest_dir)
        return False    

    return True

# Send benchmark provenance files to db server
def send_files(result_dir, dest_dir):

    # Use SCP
    if glob.stg['file_copy_handler'] == "scp":
        if not glob.user or not glob.stg['ssh_key']:
            exception.error_and_quit(glob.log, \
                        "Keys 'ssh_user' and 'ssh_key' required in glob_obj.cfg if using SCP file transmission.")

        server_path = os.path.join(glob.stg['scp_path'],dest_dir)

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
            exception.error_and_quit(glob.log, "Failed to create remote directory on database server.")

        # Use network FS
    elif glob.stg['file_copy_handler'] == "fs":
        if not glob.stg['dest_dir']:
            exception.error_and_quit(glob.log, "Key 'dest_dir' required in glob_obj.cfg if using FS file transmission.")

        print("FS copy")

        # Transmission method neither 'scp' or 'fs'
    else:
       exception.error_and_quit(glob.log, "unknown 'file_copy_handler' option in settings.cfg. Accepts 'scp' or 'fs'.") 
       
# Look for results and send them to db
def capture_result(glob_obj):
    global glob
    glob = glob_obj

    # Start logger
    glob.log = logger.start_logging("CAPTURE", glob.stg['results_log_file'] + "_" + glob.time_str + ".log", glob)

    # Get list of results in ./results/pending with a COMPLETE job state
    results = glob.lib.get_completed_results(glob.lib.get_pending_results(), True)

    # No outstanding results
    if not results:
        print("No new results found in " + glob.lib.rel_path(glob.stg['pending_path']))

    else:
        captured = 0
        if len(results) == 1: print("Starting capture for ", len(results), " new result.")
        else: print("Starting capture for ", len(results), " new results.")
        print()

        for result_dir in results:


            # Capture application profile for this result to db if not already present
            glob.lib.db.capture_application(os.path.join(glob.stg['pending_path'], result_dir))

            glob.result_path = os.path.join(glob.stg['pending_path'], result_dir)
            result, unit = validate_result(glob.result_path)

            # If unable to get valid result, skipping this result
            if not result:
                capture_failed(glob.result_path)
                print()
                continue

            print("Result:", result, unit)

            # 1. Get insert_dict
            insert_dict = get_insert_dict(glob.result_path, result, unit)

            # If insert_dict failed
            if not insert_dict:
                capture_failed(glob.result_path)
                print()
                continue

            # 2. Insert dict into db
            print("Inserting into database...")
            glob.lib.db.capture_result(insert_dict)

            # 3. Send files to db server
            print("Sending provenance data...")
            send_files(glob.result_path, insert_dict['resource_path'])

            # 4. Touch .capture-complete file
            capture_complete(glob.result_path)
            captured += 1
            print()

        print("Done. ", captured, " results sucessfully captured")

# Test if search field is valid in results/models.py
def test_search_field(field):

    if field in glob.model_fields:
        return True

    else:
        print("ERROR: '" + field + "' is not a valid search field.")
        print("Available fields:")
        for f in glob.model_fields:
            print("  "+f)
        sys.exit(1)

# Parse comma-delmited list of search criteria, test keys and return SQL WHERE statement
def parse_input_str(args):

    # No filter
    if args == "all":
        return ";"
    
    input_list= args.split(':')

    select_str = ""
    for option in input_list:
        search = option.split('=')
        if not len(search) == 2:
            print("ERROR: invalid query key-value pair: " + option)   
            sys.exit(1)
    
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
    search_str = "SELECT * FROM " + glob.stg['result_table'] + " " + parse_input_str(glob.args.queryDB)

    query_results = glob.lib.db.exec_query(search_str)

    col_width = [12, 12, 12, 12, 32, 18]
    # If query produced results
    if query_results:
        print()
        print("Using search " + search_str + " " + str(len(query_results)) + " results were found:")
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
            print(  "|"+ result[1].center(col_width[0]) +\
                    "|"+ result[2].center(col_width[1]) +\
                    "|"+ str(result[4]).center(col_width[2]) +\
                    "|"+ str(result[18]).center(col_width[3]) +\
                    "|"+ str(result[8]).center(col_width[4]) +\
                    "|"+ (str(result[9])+" "+str(result[10])).center(col_width[5]) +"|")

    else:
        print("No results found matching search criteria: '" + search_str + "'")

    # Export to csv
    if glob.args.export:
        csvFile = os.path.join(glob.basedir, "dbquery_"+ glob.time_str + ".csv")
        print()
        print("Exporting to csv file: " + glob.lib.rel_path(csvFile))

        with open(csvFile, 'w') as outFile:
            wr = csv.writer(outFile, quoting=csv.QUOTE_ALL)
            wr.writerow(glob.model_fields)
            wr.writerows(query_results)
        
        print("Done.")

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
        running = glob.lib.get_completed_results(pending_list, False)
        if running:
            print("Found", len(running), "running benchmarks:")
            for result in running:
                print("  " + result)
        else:
            print("No running benchmarks found.")
        print()

    # Completed results
    if glob.args.listResults == 'pending' or glob.args.listResults == 'all':
        # Get list of pending results
        pending = glob.lib.get_completed_results(pending_list, True)
        if pending:
            print("Found", len(pending_list), "pending benchmark results:")
            for result in pending_list:
                print("  " + result)
        else:
            print("No pending benchmark results found.")
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

    if not glob.args.listResults in ['running', 'pending', 'captured', 'failed', 'all']:
        print("Invalid input, provide 'running', 'pending', 'captured', 'failed' or 'all'.")

# Get list of result dirs matching search str
def get_matching_results(result_path, result_str):

    matching_results = gb.glob(os.path.join(result_path, "*"+result_str+"*"))
    return matching_results

# Show info for local result
def query_result(glob_obj, result_label):
    global glob
    glob = glob_obj

    # Start logger
    glob.log = logger.start_logging("CAPTURE", glob.stg['results_log_file'] + "_" + glob.time_str + ".log", glob)

    # Search ./results/pending ./results/captured and ./results/failed
    matching_dirs = get_matching_results(glob.stg['pending_path'],  result_label) + \
                    get_matching_results(glob.stg['captured_path'], result_label) + \
                    get_matching_results(glob.stg['failed_path'],   result_label)

    # No result found
    if not matching_dirs:
        print("No matching result found matching '" + result_label + "'.")
        sys.exit(1)

    # Multiple results
    elif len(matching_dirs) > 1:
        print("Multiple results found matching '" + result_label + "'")
        for result in sorted(matching_dirs):
            print("  " + glob.lib.rel_path(result))
        sys.exit(1)

    result_path = os.path.join(glob.stg['pending_path'], matching_dirs[0])
    bench_report = os.path.join(result_path, "bench_report.txt")

    if not os.path.isfile(bench_report):
        print("Missing report file " + glob.lib.rel_path(bench_report))
        print("It seems something went wrong with --bench")
        sys.exit(1)

    jobid = ""
    print("Benchmark report:")
    print("----------------------------------------")    
    with open(bench_report, 'r') as report:
        content = report.read()
        print(content)
        for line in content.split("\n"):
            if line[0:5] == "jobid":
                jobid = line.split('=')[1].strip()

    print("----------------------------------------")

    # If job complete extract result
    if jobid == "dry_run":
        print("Dry_run - skipping result check.")
    
    elif glob.lib.sched.check_job_complete(jobid):
        result, unit = validate_result(result_path)
        if result:
            print("Result: " + str(result) + " " + unit)
    else: 
        print("Job " + jobid + " still running.")

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
    pending  = glob.lib.get_pending_results()
    captured = glob.lib.get_captured_results()
    failed   = glob.lib.get_failed_results()

    # Check all results for failed status and remove
    if glob.args.removeResult == 'failed':
        if failed:
            print("Found", len(failed), "failed results:")
            print_results(failed)
            delete_results([os.path.join(glob.stg['failed_path'], x) for x in failed])
        else:
            print("No failed results found.")

    # Check all results for captured status and remove
    elif glob.args.removeResult == 'captured':
        if captured:
            print("Found", len(captured), "captured results:")
            print_results(captured)
            delete_results([os.path.join(glob.stg['captured_path'], x) for x in captured])
        else:
            print("No captured results found.")

    # Remove all results in ./results dir
    elif glob.args.removeResult == 'all':
        all_results = pending_list + captured_list + failed_list
        if all_results:
            print("Found", len(all_results), " results:")
            print_results(all_results)
            delete_results([os.path.join(glob.stg['pending_path'], x) for x in pending] +\
                            [os.path.join(glob.stg['captured_path'], x) for x in captured] +\
                            [os.path.join(glob.stg['failed_path'], x) for x in failed])
        else:
            print("No results found.")

    # Remove unique result matching input str
    else:
        results = get_matching_results(glob.stg['pending_path'], glob.args.removeResult) +\
                  get_matching_results(glob.stg['captured_path'], glob.args.removeResult) +\
                  get_matching_results(glob.stg['failed_path'], glob.args.removeResult)
        if results:
            print("Found " + len(results) + " matching results: ")
            for res in results:
                print("  " + res.split(glob.stg['sl'])[-1])
            delete_results(results)
        else:
            print("No results found matching '" + glob.args.removeResult + "'")


# Print app info from table
def print_app_from_table(glob_obj):

    global glob
    glob = glob_obj
    # Get app from table
    app = glob.lib.db.get_app_from_table(glob.args.db_app)

    if not app:
        print("No application found matching app_id='" + glob.args.db_app + "'")

    app = app[0][1:]

    labels = ["Code", "Version", "System", "Compiler", "MPI", "Module list", "Optimization Flags", "Executable", "Install prefix", "Build date", "Job ID", "App_ID"]

    print("----Application Report----")
    for i in range(12):
        print(labels[i].ljust(20) + " = " + str(app[i]))

    print("-------------------------")


