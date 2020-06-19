# System Imports
import configparser as cp
import psycopg2
import subprocess
import sys

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

	# Benchmark output file containing result 
	output_file = result_path + gs.sl + gs.output_file
	logger.debug("Looking for valid result in "+cfg_file)

	# Run validation
	if bench_cfg['result']['method'] == 'regex':

		# replace <output> filename placeholder with value in settings.cfg
		bench_cfg['result']['expression'] = bench_cfg['result']['expression'].replace("<output>", result_path + gs.sl + gs.output_file)

		try:
			# Run expression on output file
			cmd = subprocess.run(bench_cfg['result']['expression'], shell=True,
										 check=True, capture_output=True, universal_newlines=True)
			result_str = cmd.stdout.strip("\n")
			logger.debug("Pulled result from " + gs.output_file + ":  " + result_str + " " + bench_cfg['result']['unit'])

		except subprocess.CalledProcessError as e:
				exception.print_warning(logger, "Using '" + bench_cfg['result']['expression'] + "' on file " + output_file + " failed to find a valid a result. Skipping." )
				capture_failed(result_path)
				return False, False

 	# Cast to float
	try:
		result = float(result_str)
	except:
		exception.print_warning(logger, "Result '" + result_str + "' extracted from " + output_file + " is not a float. Skipping.")
		capture_failed(result_path)
		return False, False

	return result, bench_cfg['result']['unit']

# Generate dict for postgresql 
def get_insert_dict(result_dir, result, unit):
	
	# Bench report
	bench_report = gs.bench_path + gs.sl + result_dir + gs.sl + gs.bench_report_file

	report_parser    = cp.ConfigParser()
	report_parser.optionxform=str
	report_parser.read(bench_report)

	insert_dict = {}
	insert_dict['result'] = result
	insert_dict['unit'] = unit

	try:
		insert_dict['code']			   = report_parser.get('build', 'code')
		insert_dict['version']		   = report_parser.get('build', 'version')
		insert_dict['system']          = report_parser.get('build', 'system')
		insert_dict['compiler']        = report_parser.get('build', 'compiler')
		insert_dict['mpi']             = report_parser.get('build', 'mpi')
		insert_dict['modules']         = report_parser.get('build', 'modules')
		insert_dict['optimization']    = report_parser.get('build', 'optimization')
		insert_dict['build_prefix']    = report_parser.get('build', 'build_prefix')
		insert_dict['build_date']      = report_parser.get('build', 'build_date')
		insert_dict['build_job_id']    = report_parser.get('build', 'job_id')
		insert_dict['build_node_list'] = report_parser.get('build', 'nodelist')

		insert_dict['nodes']           = report_parser.get('bench', 'nodes')
		insert_dict['ranks']           = report_parser.get('bench', 'ranks')
		insert_dict['threads']         = report_parser.get('bench', 'threads')
		insert_dict['dataset']         = report_parser.get('bench', 'dataset')
		insert_dict['bench_date']      = report_parser.get('bench', 'bench_date')
		insert_dict['bench_job_id']	   = report_parser.get('bench', 'job_id')
		insert_dict['nodelist']	       = report_parser.get('bench', 'nodelist')
	except:
 		exception.error_and_quit(logger, "Unable to read bench_report.txt file in " + common.rel_path(bench_report))

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

	keys = ["username", "system",              "submit_time",             "jobid",              "nodes", "ranks", "threads", "code", "version", "compiler", "mpi", "modules", "dataset", "result", "result_unit"]
	vals = [gs.user,	insert_dict['system'], insert_dict['bench_date'], insert_dict['bench_job_id'], insert_dict['nodes'], insert_dict['ranks'], insert_dict['threads'], insert_dict['code'], insert_dict['version'], insert_dict['compiler'], insert_dict['mpi'], insert_dict['modules'], insert_dict['dataset'], insert_dict['result'], insert_dict['unit']]

	key_str = ", ".join(keys)
	val_str = ", ".join(["'" + str(v) + "'" for v in vals])

	# Perform INSERT
	try:
		cur.execute("INSERT INTO results_result (" + key_str + ") VALUES (" + val_str + ");")
		conn.commit()
	except psycopg2.Error as e:
		print(e)
		return False

	cur.close()
	conn.close()

	return True

# Look for results and send them to db
def capture_result(args, settings):
	global logger, gs, common
	gs = settings

	common = common_funcs.init(gs)
	# Start logger
	logger = common.start_logging("CAPTURE", gs.base_dir + gs.sl + gs.results_log_file + "_" + gs.time_str + ".log")

	results = common.check_for_new_results()
	
	# No outstanding results
	if not results:
		print("No new results found in " + common.rel_path(gs.bench_path))
	else:
		for result_dir in results:
			result, unit = validate_result(gs.bench_path + gs.sl + result_dir)

			# If unable to get valid result, skipping this result
			if not result:
				print("Skipping this result")
				continue
			# Get dict and insert into db
			inserted = insert_db(get_insert_dict(result_dir, result, unit))

			# If result inserted into db, touch .capture-complete file
			if inserted:
				capture_complete(gs.bench_path + gs.sl + result_dir)

