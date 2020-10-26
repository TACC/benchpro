# System Imports
import configparser as cp
import os
import psycopg2
from psycopg2 import sql
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.logger as logger

glob = common = None

# Create .capture-complete file in result dir
def capture_complete(path):
    glob.log.debug("Successfully captured result in " + path)
    print("Successfully captured result in " + common.rel_path(path))
    with open(os.path.join(path, ".capture-complete"), 'w'): pass

# Create .capture-failed file in result dir
def capture_failed(path):
    glob.log.debug("Failed to capture result in " + path)
    print("Failed to capture result in " + common.rel_path(path))
    with open(os.path.join(path, ".capture-failed"), 'w'): pass

# Function to test if benchmark produced valid result
def validate_result(result_path):
    # Get validation requirement from bench cfg file
    cfg_file = os.path.join(result_path, "bench_files", "bench.cfg")

    cfg_handler.ingest_cfg('bench', cfg_file, glob)
    glob.log.debug("Got result validation requirements from file: "+cfg_file)

    # Benchmark output file containing result, override default in glob_obj.cfg if 'output_file' set in bench.cfg 
    output_file = glob.code['config']['output_file']
    if 'output_file' in glob.code['result']:
        if glob.code['result']['output_file']:
            output_file = glob.code['result']['output_file']

    output_path = common.find_exact(output_file, result_path)
    # Test for benchmark output file
    if not output_path:
        exception.print_warning(glob.log, "Result file " + output_file + " not found in " + common.rel_path(result_path) + ". It seems the benchmark failed to run.\nWas dry_run=True?")
        return False, None

    glob.log.debug("Looking for valid result in "+output_path)

    # Run expr collection
    if glob.code['result']['method'] == 'expr':

        # replace <file> filename placeholder with value in glob_obj.cfg
        glob.code['result']['expr'] = glob.code['result']['expr'].replace("{output_file}", output_path)

        # Run validation expression on output file
        try:
            glob.log.debug("Running: '" + glob.code['result']['expr'] + "'")
            cmd = subprocess.run(glob.code['result']['expr'], shell=True,
                                         check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.log.debug("Pulled result from " + output_path + ":  " + result_str + " " + glob.code['result']['unit'])

        except subprocess.CalledProcessError as e:
            exception.print_warning(glob.log, "Using '" + glob.code['result']['expr'] + "' on file " + common.rel_path(output_path) + " failed to find a valid a result. Skipping." )
            return False, None

    # Run scipt collection
    elif glob.code['result']['method'] == 'script':
        result_script = glob.stg['script_path'] + glob.stg['sl'] + glob.stg['result_scripts_dir'] + glob.stg['sl'] + glob.code['result']['script']
        if not os.path.exists(result_script):
            exception.print_warning(glob.log, "Result collection script not found at "+ common.rel_path(result_script))
            return False, None

        # Run validation script on output file
        try:
            glob.log.debug("Running: '" + result_script + " " + output_path + "'")
            cmd = subprocess.run(result_script + " " + output_path, shell=True,
                                check=True, capture_output=True, universal_newlines=True)
            result_str = cmd.stdout.strip()
            glob.log.debug("Pulled result from " + output_path + ":  " + result_str + " " + glob.code['result']['unit'])

        except subprocess.CalledProcessError as e:
            exception.print_warning(glob.log, "Running script '" + common.rel_path(result_script) + "' on file " + common.rel_path(output_path) + " failed to find a valid a result." )
            return False, None
            
     # Cast to float
    try:
        result = float(result_str)
    except:
        exception.print_warning(glob.log, "result extracted from " + output_file + " is not a float: '" + result_str + "'")
        return False, None

    # Check float non-zero
    if not result:
        exception.print_warning(glob.log, "result extracted from " + output_file + " is '0.0'.")
        return False, None

    glob.log.debug("Successfully found result '" + str(result) + " " + glob.code['result']['unit'] + " for result " + common.rel_path(result_path))

    # Return valid result and unit
    return result, glob.code['result']['unit']

# Get list of fields in results table
def get_table_fields():

    try:
        conn = psycopg2.connect(
            dbname =    glob.stg['db_name'],
            user =      glob.stg['db_user'],
            host =      glob.stg['db_host'],
            password =  glob.stg['db_passwd']
        )
    except Exception as err:
        print ("psycopg2 connect() ERROR:", err)
        sys.exit(1)

    cur = conn.cursor()
    query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name='" + glob.stg['table_name'] + "';"

    try:
        sql_object = sql.SQL(query).format(sql.Identifier( glob.stg['table_name'] ))
        cur.execute( sql_object )
        col_names = ( cur.fetchall() )

        # iterate list of tuples and grab first element
        columns = []
        for tup in col_names:
            columns += [ tup[0] ]

        cur.close()

    except Exception as err:
        print ("Failed to collect db information", err)

    # remove id field
    columns.remove('id')
    return columns

# Get required key from report, if not found try get it from the [bench] section, otherwise error
def get_required_key(report_parser, section, key):
    try:
        return report_parser.get(section, key)
    except:
        pass
    try:
        return report_parser.get('bench', key)
    except:    
        exception.error_and_quit(glob.log, "missing required report field '"+key+"'")

# Get optional key from report or return ""
def get_optional_key(report_parser, section, key):
    try:
        return report_parser.get(section, key)
    except:
        return ""
        
# Generate dict for postgresql 
def get_insert_dict(result_dir, result, unit):
    
    # Bench report
    bench_report = glob.stg['bench_path'] + glob.stg['sl'] + result_dir + glob.stg['sl'] + glob.stg['bench_report_file']
    if not os.path.exists(bench_report):
        exception.print_warning(glob.log, common.rel_path(bench_report) + " not found.")
        return False

    report_parser    = cp.ConfigParser()
    report_parser.optionxform=str
    report_parser.read(bench_report)

    # Get JOBID in order to get NODELIST from sacct
    try:
        jobid = report_parser.get('bench', 'jobid')
    except:
        print(e)
        exception.print_warning(glob.log, "Failed to read key 'jobid' in " + common.rel_path(bench_report) + ". Skipping.")
        return False
  
    elapsed_time = None
    end_time = None
    submit_time = get_required_key(report_parser, 'bench', 'start_time')
    # Handle local exec
    if jobid == "local":
        elapsed_time = 0
        end_time = submit_time
        jobid = "0"

    else:
        elapsed_time = common.get_elapsed_time(jobid)
        end_time = common.get_end_time(jobid)

    nodelist = common.get_nodelist(jobid)

    insert_dict = {}
   
    insert_dict['username']         = glob.user
    insert_dict['system']           = get_required_key(report_parser, 'build', 'system')
    insert_dict['submit_time']      = submit_time
    insert_dict['elapsed_time']     = elapsed_time
    insert_dict['end_time']         = end_time
    insert_dict['description']      = get_optional_key(report_parser, 'bench', 'description')
    insert_dict['jobid']            = jobid
    insert_dict['nodelist']         = ", ".join(nodelist)
    insert_dict['nodes']            = get_required_key(report_parser, 'bench', 'nodes')
    insert_dict['ranks']            = get_required_key(report_parser, 'bench', 'ranks')
    insert_dict['threads']          = get_required_key(report_parser, 'bench', 'threads')
    insert_dict['code']             = get_required_key(report_parser, 'build', 'code')
    insert_dict['version']          = get_optional_key(report_parser, 'build', 'version')
    insert_dict['compiler']         = get_optional_key(report_parser, 'build', 'compiler')
    insert_dict['mpi']              = get_optional_key(report_parser, 'build', 'mpi')
    insert_dict['modules']          = get_optional_key(report_parser, 'build', 'modules')
    insert_dict['dataset']          = get_required_key(report_parser, 'bench', 'dataset')
    insert_dict['result']           = str(result)
    insert_dict['result_unit']      = unit
    insert_dict['resource_path']    = os.path.join(glob.user, insert_dict['system'], insert_dict['jobid'])
    
    # Confirm model fields have all been filled
    model_fields = get_table_fields()
    insert_fields = insert_dict.keys()

    for key in insert_fields:
        # Remove key from model list
        if key in model_fields:
            model_fields.remove(key)
        # Error if trying to insert field not in model
        else:
            exception.error_and_quit(glob.log, "Trying to insert into field '" + key + "' not present in results table '" + glob.stg['table_name'] + "'")

    # If missing model fields in INSERT dict
    if len(model_fields) > 0:
        exception.error_and_quit(glob.log, "The benchmark result is missing fields present in the results table:" + str(model_fields))

    return insert_dict

# Insert result into postgres db
def insert_db(insert_dict):

    # Connect to db
    try:
        conn = psycopg2.connect(
            dbname =    glob.stg['db_name'],
            user =      glob.stg['db_user'],
            host =      glob.stg['db_host'],
            password =  glob.stg['db_passwd']
        )
        cur = conn.cursor()
    except psycopg2.Error as e:
        print(e)
        exception.error_and_quit(glob.log, "Unable to connect to database")

    keys = ', '.join(insert_dict.keys())
    vals = ", ".join(["'" + str(v) + "'" for v in insert_dict.values()])

    # Perform INSERT
    try:
        cur.execute("INSERT INTO " + glob.stg['table_name'] + " (" + keys + ") VALUES (" + vals + ");")
        conn.commit()
    except psycopg2.Error as e:
        print(e)
        return False

    cur.close()
    conn.close()

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
            exception.error_and_quit(glob.log, "Keys 'ssh_user' and 'ssh_key' required in glob_obj.cfg if using SCP file transmission.")

        server_path = glob.stg['scp_path'] + glob.stg['sl'] + dest_dir

        # Create directory on remote server
        if make_remote_dir(server_path):
            # SCP source dir to dest_dir
            if scp_files(glob.stg['bench_path'] + glob.stg['sl'] + result_dir + glob.stg['sl'] + "hw_report", server_path):
                return True

        # Use network FS
    elif glob.stg['file_copy_handler'] == "fs":
        if not glob.stg['dest_dir']:
            exception.error_and_quit(glob.log, "Key 'dest_dir' required in glob_obj.cfg if using FS file transmission.")

        print("FS copy")

        # Transmission method neither 'scp' or 'fs'
    else:
        return False

# Look for results and send them to db
def capture_result(glob_obj):
    global glob, common
    glob = glob_obj

    common = common_funcs.init(glob)
    # Start logger
    glob.log = logger.start_logging("CAPTURE", glob.stg['results_log_file'] + "_" + glob.time_str + ".log", glob)

    # Get list of completed benchmarks
    results = common.get_pending_results()

    # No outstanding results
    if not results:
        print("No new results found in " + common.rel_path(glob.stg['bench_path']))

    else:
        captured = 0
        if len(results) == 1: print("Starting capture for ", len(results), " new result.")
        else: print("Starting capture for ", len(results), " new results.")
        print()

        for result_dir in results:

            result_path = glob.stg['bench_path'] + glob.stg['sl'] + result_dir
            result, unit = validate_result(result_path)

            # If unable to get valid result, skipping this result
            if not result:
                capture_failed(result_path)
                print()
                continue

            print("Result:", result, unit)

            # Get insert_dict
            insert_dict = get_insert_dict(result_dir, result, unit)
            # If insert_dict failed
            if not insert_dict:
                capture_failed(result_path)
                print()
                continue

            dest_dir = insert_db(insert_dict)

            # If insert failed
            if not dest_dir:
                capture_failed(result_path)
                print()
                continue

            # send files to db server
            sent = send_files(result_dir, dest_dir)

            # If files copied successfully
            if not sent:
                exception.print_warning(glob.log, "Failed to copy provenance data to database server.")
                print()

            # Touch .capture-complete file
            capture_complete(glob.stg['bench_path'] + glob.stg['sl'] + result_dir)
            captured += 1
            print()

        print("Done. ", captured, " results sucessfully captured")

# Test if search field is valid in results/models.py
def test_search_field(model_fields, field):

    if field in model_fields:
        return True

    else:
        print("ERROR: '" + field + "' is not a valid search field.")
        print("Available fields:")
        for f in model_fields:
            print("  "+f)
        sys.exit(2)

# Parse comma-delmited list of search criteria, test keys and return SQL WHERE statement
def parse_input_str(args):
    input_list= args.split(':')

    # Get fields from DB
    model_fields = get_table_fields()

    select_str = ""
    for option in input_list:
        search = option.split('=')
        # Test search key is in db
        if test_search_field(model_fields, search[0]):
            if select_str: select_str += " AND "
            else: select_str += " " 
            select_str = select_str + search[0] + "='" + search[1] + "'"

    return select_str

# Run SELECT on db with user search criteria
def run_query(query_str):

    # Connect to db
    try:
        conn = psycopg2.connect(
            dbname =    glob.stg['db_name'],
            user =      glob.stg['db_user'],
            host =      glob.stg['db_host'],
            password =  glob.stg['db_passwd']
        )
        cur = conn.cursor()
    except psycopg2.Error as e:
        print(e)
        exception.error_and_quit(glob.log, "Unable to connect to database")

    if query_str == "all":
        query_str = ""
    else:
        query_str = "WHERE" + query_str

    # Perform INSERT
    try:
        cur.execute("SELECT * FROM " + glob.stg['table_name'] + " " + query_str + ";")
        rows = cur.fetchall()
    except psycopg2.Error as e:
        print(e)
        return False

    cur.close()
    conn.close()

    return rows

# Query db for results
def query_db(glob_obj):
    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    query_results = None
    search_str="all"
    # No search filter 
    if glob.args.queryDB == "all":
        query_results = run_query(glob.args.queryDB)
    # Search filter
    else:
        search_str = parse_input_str(glob.args.queryDB)
        query_results = run_query(search_str)

    # If query produced results
    if query_results:
        print()
        print("Using search '" + search_str + " ' " + str(len(query_results)) + " results were found:")
        print()
        print("|"+ "USER".center(12) +"|"+ "SYSTEM".center(12) +"|"+ "JOBID".center(12) +"|"+ "CODE".center(20) +"|"+ "DATASET".center(20) +"|"+ "RESULT".center(20) +"|")
        print("|"+ "-"*12 +"+"+ "-"*12 +"+"+ "-"*12 +"+"+ "-"*20 +"+"+ "-"*20 +"+"+ "-"*20 +"|")
        for result in query_results:
            print("|"+ result[1].center(12) +"|"+ result[2].center(12) +"|"+ str(result[4]).center(12) +"|"+ (result[8]+"-"+result[9]).center(20) +"|"+ result[13].center(20) +"|"+ (str(result[14])+" "+result[15]).center(20) +"|")

    else:
        print("No results found matching search criteria.")
    
# List local results
def list_results(glob_obj):
    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    # Running results
    if glob.args.listResults == 'running' or glob.args.listResults == 'all':
        result_list = common.get_running_results()
        if result_list:
            print("Found", len(result_list), "running benchmarks:")
            for result in result_list:
                print("  " + result)
        else:
            print("No running benchmarks found.")
        print()

    # Completed results
    if glob.args.listResults == 'pending' or glob.args.listResults == 'all':
        result_list = common.get_pending_results()
        if result_list:
            print("Found", len(result_list), "pending benchmark results:")
            for result in result_list:
                print("  " + result)
        else:
            print("No pending benchmark results found.")
        print()

    # Captured results
    if glob.args.listResults == 'captured' or glob.args.listResults == 'all':
        result_list = common.get_captured_results()
        if result_list:
            print("Found", len(result_list), "captured benchmark results:")
            for result in result_list:
                print("  " + result)
        else:
            print("No captured benchmark results found.")
        print()

    # Failed results
    if glob.args.listResults == 'failed' or glob.args.listResults == 'all':
        result_list = common.get_failed_results()
        if result_list:
            print("Found", len(result_list), "failed benchmark results:")
            for result in result_list:
                print("  " + result)
        else:
            print("No failed benchmark results found.")
        print()

    if not glob.args.listResults in ['running', 'pending', 'captured', 'failed', 'all']:
        print("Invalid input, provide 'running', 'pending', 'captured', 'failed' or 'all'.")


# Get list of results matching search str
def get_matching_results(result_str):

    matching_results = []
    for result in common.get_subdirs(glob.stg['bench_path']):
        if result_str in result:
            matching_results.append(result)

    if not matching_results:
        print("No results found matching selection '" + result_str + "'")
        sys.exit(1)

    elif len(matching_results) > 1:
        print("Multiple results found matching '" + result_str + "'")
        for result in sorted(matching_results):
            print("  " + result)
        sys.exit(1)

    else:
        return matching_results

# Show info for local result
def query_result(glob_obj):
    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    glob.log = logger.start_logging("CAPTURE", glob.stg['results_log_file'] + "_" + glob.time_str + ".log", glob)

    result_path = os.path.join(glob.stg['bench_path'], get_matching_results(glob.args.queryResult)[0])
    bench_report = os.path.join(result_path, "bench_report.txt")

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
    if common.check_job_complete(jobid):
        result, unit = validate_result(result_path)
        if result:
            print("Result: " + str(result) + " " + unit)
    else: 
        print("Job " + jobid + " still running.")


def print_results(result_list):
    for result in result_list:
        print("  " + result)

def delete_results(result_list):
    print()
    print("\033[91;1mDeleting in", glob.stg['timeout'], "seconds...\033[0m")
    time.sleep(glob.stg['timeout'])
    print("No going back now...")
    for result in result_list:
        su.rmtree(glob.stg['bench_path'] + glob.stg['sl'] + result)
    print("Done.")

# Remove local result
def remove_result(glob_obj):
    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    # Check all results for failed status and remove
    if glob.args.removeResult == 'failed':
        result_list = common.get_failed_results()
        if result_list:
            print("Found", len(result_list), "failed results:")
            print_results(result_list)
            delete_results(result_list)
        else:
            print("No failed results found.")

    # Check all results for captured status and remove
    elif glob.args.removeResult == 'captured':
        result_list = common.get_submitted_results()
        if result_list:
            print("Found", len(result_list), "captured results:")
            print_results(result_list)
            delete_results(result_list)
        else:
            print("No captured results found.")

    # Remove all results in ./results dir
    elif glob.args.removeResult == 'all':
        result_list = common.get_subdirs(glob.stg['bench_path'])    
        if result_list:
            print("Found", len(result_list), " results:")
            print_results(result_list)
            delete_results(result_list)
        else:
            print("No results found.")

    # Remove unique result matching input str
    else:
        results = get_matching_results(glob.args.removeResult)
        print("Found matching results: ")
        for res in results:
            print("  " + res)
        delete_results(results)

