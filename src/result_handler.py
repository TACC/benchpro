# System Imports
import configparser as cp
import os
import psycopg2
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception

logger = gs = common = None

# Create .capture-complete file in result dir
def capture_complete(path):
	logger.debug("Successfully captured result in " + path)
	print("Successfully captured result in " + common.rel_path(path))
	with open(path + gs.sl + ".capture-complete", 'w'): pass

# Create .capture-failed file in result dir
def capture_failed(path):
	logger.debug("Failed to capture result in " + path)
	print("Failed to capture result in " + common.rel_path(path))
	with open(path + gs.sl + ".capture-failed", 'w'): pass

# Function to test if benchmark produced valid result
def validate_result(result_path):
	# Get validation requirement from bench cfg file
	cfg_file = result_path + gs.sl + "bench_files" + gs.sl + "bench.cfg"

	bench_cfg = cfg_handler.get_cfg('bench', cfg_file, gs, logger)
	logger.debug("Got result validation requirements from file: "+cfg_file)

	# Benchmark output file containing result, override default in settings.cfg if 'output_file' set in bench.cfg 
	output_file = gs.output_file
	if 'output_file' in bench_cfg['result']:
		if bench_cfg['result']['output_file']:
			output_file = bench_cfg['result']['output_file']

	output_path = common.find_exact(output_file, result_path)[0]
	# Test for benchmark output file
	if not output_path:
		exception.print_warning(logger, "Result file " + output_file + " not found in " + common.rel_path(result_path) + ". It seems the benchmark failed to run. Was dry_run=True in settings.cfg?")
		return False, None

	logger.debug("Looking for valid result in "+output_path)

	# Run regex collection
	if bench_cfg['result']['method'] == 'regex':

		# replace <file> filename placeholder with value in settings.cfg
		bench_cfg['result']['expr'] = bench_cfg['result']['expr'].replace("<file>", output_path)

		# Run validation expression on output file
		try:
			logger.debug("Running: '" + bench_cfg['result']['expr'] + "'")
			cmd = subprocess.run(bench_cfg['result']['expr'], shell=True,
										 check=True, capture_output=True, universal_newlines=True)
			result_str = cmd.stdout.strip("")
			logger.debug("Pulled result from " + output_path + ":  " + result_str + " " + bench_cfg['result']['unit'])

		except subprocess.CalledProcessError as e:
			exception.print_warning(logger, "Using '" + bench_cfg['result']['expr'] + "' on file " + common.rel_path(output_path) + " failed to find a valid a result. Skipping." )
			return False, None

	# Run scipt collection
	elif bench_cfg['result']['method'] == 'script':
		result_script = gs.script_path + gs.sl + gs.result_scripts_dir + gs.sl + bench_cfg['result']['script']
		if not os.path.exists(result_script):
			exception.print_warning(logger, "Result collection script not found at "+ common.rel_path(result_script))
			return False, None

		# Run validation script on output file
		try:
			logger.debug("Running: '" + result_script + " " + output_path + "'")
			cmd = subprocess.run(result_script + " " + output_path, shell=True,
								check=True, capture_output=True, universal_newlines=True)
			result_str = cmd.stdout.strip("")
			logger.debug("Pulled result from " + output_path + ":  " + result_str + " " + bench_cfg['result']['unit'])

		except subprocess.CalledProcessError as e:
			exception.print_warning(logger, "Running script '" + common.rel_path(result_script) + "' on file " + common.rel_path(output_path) + " failed to find a valid a result." )
			return False, None
			
 	# Cast to float
	try:
		result = float(result_str)
	except:
		exception.print_warning(logger, "Result '" + result_str + "' extracted from " + output_file + " is not a float.")
		return False, None

	# Check float non-zero
	if not result:
		exception.print_warning(logger, "Result extracted from " + output_file + " is '0.0'.")
		return False, None

	logger.debug("Successfully found result '" + str(result) + " " + bench_cfg['result']['unit'] + " for result " + common.rel_path(result_path))

	# Return valid result and unit
	return result, bench_cfg['result']['unit']


# Generate dict for postgresql 
def get_insert_dict(result_dir, result, unit):
	
	# Bench report
	bench_report = gs.bench_path + gs.sl + result_dir + gs.sl + gs.bench_report_file
	if not os.path.exists(bench_report):
		exception.print_warning(logger, common.rel_path(bench_report) + " not found.")
		return False

	report_parser    = cp.ConfigParser()
	report_parser.optionxform=str
	report_parser.read(bench_report)

	insert_dict = {}

	try:
		insert_dict['username'] 		= gs.user
		insert_dict['system']			= report_parser.get('build', 'system')
		insert_dict['submit_time']		= report_parser.get('bench', 'bench_date')
		insert_dict['jobid']    		= report_parser.get('bench', 'job_id')
		insert_dict['nodes']			= report_parser.get('bench', 'nodes')
		insert_dict['ranks']			= report_parser.get('bench', 'ranks')
		insert_dict['threads']			= report_parser.get('bench', 'threads')
		insert_dict['code']				= report_parser.get('build', 'code')
		insert_dict['version']			= report_parser.get('build', 'version')
		insert_dict['compiler']			= report_parser.get('build', 'compiler')
		insert_dict['mpi']				= report_parser.get('build', 'mpi')
		insert_dict['modules']			= report_parser.get('build', 'modules')
		insert_dict['dataset']			= report_parser.get('bench', 'dataset')
		insert_dict['result'] 			= str(result)
		insert_dict['result_unit'] 		= unit
		insert_dict['resource_path'] 	= gs.user + gs.sl + insert_dict['system'] + gs.sl + insert_dict['jobid']
	
	except Exception as e:
		print(e)
		exception.print_warning(logger, "Failed to read a key in " + common.rel_path(bench_report) + ". Skipping.")
		return False

	return insert_dict

# Insert result into postgres db
def insert_db(insert_dict):

	# Connect to db
	try:
		conn = psycopg2.connect(dbname=gs.db_name, user=gs.db_user, host=gs.db_host, password=gs.db_passwd)
		cur = conn.cursor()
	except psycopg2.Error as e:
		print(e)
		exception.error_and_quit(logger, "Unable to connect to database")

	keys = ', '.join(insert_dict.keys())
	vals = ", ".join(["'" + str(v) + "'" for v in insert_dict.values()])

	# Perform INSERT
	try:
		cur.execute("INSERT INTO results_result (" + keys + ") VALUES (" + vals + ");")
		conn.commit()
	except psycopg2.Error as e:
		print(e)
		return False

	cur.close()
	conn.close()

	return insert_dict['resource_path']

# Create directory on remote server
def make_remote_dir(dest_dir):

	try:
		logger.debug("Running: '" + "ssh -i " + gs.key +" " + gs.user + "@" + gs.db_host + " -t mkdir -p " + dest_dir + "'")
		# ssh -i [key] [user]@[db_host] -t mkdir -p [dest_dir]
		cmd = subprocess.run("ssh -i " + gs.key +" " + gs.user + "@" + gs.db_host + " -t mkdir -p " + dest_dir, shell=True,
							check=True, capture_output=True, universal_newlines=True)

		logger.debug("Directory " + dest_dir  + " created on " + gs.db_host)

	except subprocess.CalledProcessError as e:
		print(e)
		logger.debug("Failed to create directory " + dest_dir + " on " + gs.db_host)
		return False

	return True

# SCP files to remote server
def scp_files(src_dir, dest_dir):

	# Check that SSH key exists 
	if not os.path.exists(gs.key):
		exception.error_and_quit(logger, "Could not locate SSH key '" + gs.key + "'")	

	try:
		logger.debug("Running: '" + "scp -i " + gs.key + " -r " + src_dir + " " + gs.user + "@" + gs.db_host + ":" + dest_dir + "/" + "'")
		# scp -i [key] -r [src_dir] [user]@[server]:[dest_dir]
		cmd = subprocess.run("scp -i " + gs.key + " -r " + src_dir + " " + gs.user + "@" + gs.db_host + ":" + dest_dir + "/", shell=True,
							check=True, capture_output=True, universal_newlines=True)

		logger.debug("Copied " + src_dir + " to " + gs.db_host + ":" + dest_dir)

	except subprocess.CalledProcessError as e:
		print(e)
		logger.debug("Failed to copy " + src_dir + " to " + gs.db_host + "+" + dest_dir)
		return False	

	return True

# Send benchmark provenance files to db server
def send_files(result_dir, dest_dir):

	# Use SCP
	if gs.file_copy_handler == "scp":
		if not gs.user or not gs.key:
			exception.error_and_quit(logger, "Keys 'user' and 'key' required in settings.cfg if using SCP file transmission.")

		server_path = gs.django_static_dir + gs.sl + dest_dir

		# Create directory on remote server
		if make_remote_dir(server_path):
			# SCP source dir to dest_dir
			if scp_files(gs.bench_path + gs.sl + result_dir + gs.sl + "hw_report", server_path):
				return True

		# Use network FS
	elif gs.file_copy_handler == "fs":
		if not gs.dest_dir:
			exception.error_and_quit(logger, "Key 'dest_dir' required in settings.cfg if using FS file transmission.")

		print("FS copy")

		# Transmission method neither 'scp' or 'fs'
	else:
		return False

# Look for results and send them to db
def capture_result(args, settings):
	global logger, gs, common
	gs = settings

	common = common_funcs.init(gs)
	# Start logger
	logger = common.start_logging("CAPTURE", gs.base_dir + gs.sl + gs.results_log_file + "_" + gs.time_str + ".log")

	# Get list of completed benchmarks
	results = common.check_for_complete_results()

	# No outstanding results
	if not results:
		print("No new results found in " + common.rel_path(gs.bench_path))

	else:
		captured = 0
		if len(results) == 1: print("Starting capture for ", len(results), " new result.")
		else: print("Starting capture for ", len(results), " new results.")
		print()

		for result_dir in results:

			result_path = gs.bench_path + gs.sl + result_dir
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
				exception.print_warning(logger, "Failed to copy provenance data to database server.")
				print()

			# Touch .capture-complete file
			capture_complete(gs.bench_path + gs.sl + result_dir)
			captured += 1
			print()

		print("Done. ", captured, " results sucessfully captured")


# Test if search field is valid in results/models.py
def test_search_field(field):
	model_fields = ['username',
					'system',
					'submit_time',
					'jobid',
					'nodes',
					'ranks',
					'threads',
					'code',
					'version',
					'compiler',
					'mpi',
					'modules',
					'dataset',
					'result',
					'result_unit',
					'resource_path'
					]
	if field in model_fields:
		return True

	else:
		print("WARNING: '" + field + "' is not a valid search field.")
		print("Available fields:")
		for f in model_fields:
			print("  "+f)
		return False

# Parse comma-delmited list of search criteria, test keys and return SQL WHERE statement
def parse_input_str(args):
	input_list= args.split(',')

	select_str = ""
	for option in input_list:
		search = option.split('=')
		# Test search key is in db
		if test_search_field(search[0]):
			if select_str: select_str += " AND "
			else: select_str += " " 
			select_str = select_str + search[0] + "='" + search[1] + "'"

	return select_str

# Run SELECT on db with user search criteria
def run_query(query_str):

	# Connect to db
	try:
		conn = psycopg2.connect(dbname=gs.db_name, user=gs.db_user, host=gs.db_host, password=gs.db_passwd)
		cur = conn.cursor()
	except psycopg2.Error as e:
		print(e)
		exception.error_and_quit(logger, "Unable to connect to database")

	if query_str == "all":
		query_str = ""
	else:
		query_str = "WHERE" + query_str

	# Perform INSERT
	try:
		cur.execute("SELECT * FROM results_result " + query_str + ";")
		rows = cur.fetchall()
	except psycopg2.Error as e:
		print(e)
		return False

	cur.close()
	conn.close()

	return rows

# Query db for results
def query_db(args, settings):
	global gs, common
	gs = settings
	common = common_funcs.init(gs)

	query_results = None
	search_str="all"
	# No search filter 
	if args == "all":
		query_results = run_query(args)
	# Search filter
	else:
		search_str = parse_input_str(args)
		query_results = run_query(search_str)

	# If query produced results
	if query_results:
		print()
		print("Using search \"" + search_str + " \" " + str(len(query_results)) + " results were found:")
		print()
		print("|"+ "USER".center(12) +"|"+ "SYSTEM".center(12) +"|"+ "JOBID".center(12) +"|"+ "CODE".center(20) +"|"+ "DATASET".center(20) +"|"+ "RESULT".center(20) +"|")
		print("|"+ "-"*12 +"+"+ "-"*12 +"+"+ "-"*12 +"+"+ "-"*20 +"+"+ "-"*20 +"+"+ "-"*20 +"|")
		for result in query_results:
			print("|"+ result[1].center(12) +"|"+ result[2].center(12) +"|"+ str(result[4]).center(12) +"|"+ (result[8]+"-"+result[9]).center(20) +"|"+ result[13].center(20) +"|"+ (str(result[14])+" "+result[15]).center(20) +"|")

	else:
		print("No results found matching search criteria.")
	
# List local results
def list_results(args, settings):
	global gs, common
	gs = settings
	common = common_funcs.init(gs)

	# Running results
	if args == 'running' or args == 'all':
		result_list = common.check_for_running_results()
		if result_list:
			print("Found", len(result_list), "running benchmarks:")
			for result in result_list:
				print("  " + result)
		else:
			print("No running benchmarks found.")
		print()

	# Completed results
	if args == 'complete' or args == 'all':
		result_list = common.check_for_complete_results()
		if result_list:
			print("Found", len(result_list), "completed benchmark results:")
			for result in result_list:
				print("  " + result)
		else:
			print("No completed benchmark results found.")
		print()

	# Captured results
	if args == 'captured' or args == 'all':
		result_list = common.check_for_submitted_results()
		if result_list:
			print("Found", len(result_list), "captured benchmark results:")
			for result in result_list:
				print("  " + result)
		else:
			print("No captured benchmark results found.")
		print()

	# Failed results
	if args == 'failed' or args == 'all':
		result_list = common.check_for_failed_results()
		if result_list:
			print("Found", len(result_list), "failed benchmark results:")
			for result in result_list:
				print("  " + result)
		else:
			print("No failed benchmark results found.")
		print()

	if not args in ['running', 'complete', 'captured', 'failed', 'all']:
		print("Invalid input, provide 'running', 'complete', 'captured', 'failed' or 'all'.")


# Get list of results matching search str
def get_matching_results(result_str):

	matching_results = []
	for result in common.get_subdirs(gs.bench_path):
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
def query_result(args, settings):
	global gs, common, logger
	gs = settings
	common = common_funcs.init(gs)

	logger = common.start_logging("CAPTURE", gs.base_dir + gs.sl + gs.results_log_file + "_" + gs.time_str + ".log")

	result_path = gs.bench_path + gs.sl + get_matching_results(args)[0]
	bench_report = result_path + gs.sl + "bench_report.txt"
	print("Benchmark report:")
	print("----------------------------------------")	
	with open(bench_report, 'r') as report:
		print(report.read())
	print("----------------------------------------")

	result, unit = validate_result(result_path)
	if result:
		print("Result: " + str(result) + " " + unit)


def print_results(result_list):
	for result in result_list:
		print("  " + result)

def delete_results(result_list):
	print("")
	print('\033[1m' + "Deleting in", gs.timeout, "seconds...")
	time.sleep(gs.timeout)
	print('\033[0m' + "No going back now...")
	for result in result_list:
		su.rmtree(gs.bench_path + gs.sl + result)
	print("Done.")

# Remove local result
def remove_result(args, settings):
	global gs, common
	gs = settings
	common = common_funcs.init(gs)

	# Check all results for failed status and remove
	if args == 'failed':
		result_list = common.check_for_failed_results()
		if result_list:
			print("Found", len(result_list), "failed results:")
			print_results(result_list)
			delete_results(result_list)
		else:
			print("No failed results found.")

	# Check all results for captured status and remove
	elif args == 'captured':
		result_list = common.check_for_submitted_results()
		if result_list:
			print("Found", len(result_list), "captured results:")
			print_results(result_list)
			delete_results(result_list)
		else:
			print("No captured results found.")

	# Remove all results in ./results dir
	elif args == 'all':
		result_list = common.get_subdirs(gs.bench_path)	
		if result_list:
			print("Found", len(result_list), " results:")
			print_results(result_list)
			delete_results(result_list)
		else:
			print("No results found.")

	# Remove unique result matching input str
	else:
		results = get_matching_results(args)
		print("Found matching results: ")
		for res in results:
			print("  " + res)
		delete_results(results)

