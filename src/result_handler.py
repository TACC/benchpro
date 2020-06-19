# System Imports
import configparser as cp
import psycopg2
import subprocess
import sys

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception

logger = gs = ''

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
	if bench_cfg['validation']['method'] == 'regex':

		# replace <output> filename placeholder with value in settings.cfg
		bench_cfg['validation']['expression'] = bench_cfg['validation']['expression'].replace("<output>", result_path + gs.sl + gs.output_file)

		try:
			# Run expression on output file
			cmd = subprocess.run(bench_cfg['validation']['expression'], shell=True,
										 check=True, capture_output=True, universal_newlines=True)
			result_str = cmd.stdout.strip("\n")
			logger.debug("Pulled result from " + gs.output_file + ":  " + result_str + " " + bench_cfg['validation']['unit'])

		except subprocess.CalledProcessError as e:
				exception.error_and_quit(logger, "Using '" + bench_cfg['validation']['expression'] + "' on file " + output_file + " failed to produce a result." )
 
 	# Cast to float
	try:
		result = float(result_str)
	except:
		exception.error_and_quit(logger, "Result '" + result_str + "' extracted from " + output_file + " is not a float.")
		
	return result, bench_cfg['validation']['unit']

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
		insert_dict['system']		= report_parser.get('report', 'system')
		insert_dict['code']			= report_parser.get('report', 'code')
		insert_dict['version']		= report_parser.get('report', 'version')
		insert_dict['dataset']		= report_parser.get('report', 'dataset')
		insert_dict['submit_date']	= report_parser.get('report', 'submit_date')
		insert_dict['job_id']		= report_parser.get('report', 'job_id')
		insert_dict['node_list']	= report_parser.get('report', 'node_list')
	except:
 		exception.error_and_quit(logger, "Unable to read build_report.txt file in " + common.rel_path(code_path))

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

	keys = ["username", "system", "submit_time", "jobid", "nodes", "ranks", "threads", "code", "version", "compiler", "mpi", "modules", "dataset", "result", "result_unit"]
	vals = [gs.user,	insert_dict['system'], "2020-06-19 11:08:16.518177", insert_dict['job_id'], 6, 8, 1, insert_dict['code'], insert_dict['version'], "mpi", "impi", "", insert_dict['dataset'], insert_dict['result'], insert_dict['unit']]

	key_str = ", ".join(keys)
	val_str = ", ".join(["'" + str(v) + "'" for v in vals])

	# Perform INSERT
	try:
		cur.execute("INSERT INTO results_result (" + key_str + ") VALUES (" + val_str + ");")
		conn.commit()
	except psycopg2.Error as e:
		print(e)

	cur.close()
	conn.close()

# Look for results and send them to db
def capture_result(args, settings):
	global logger, gs
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
			# Get dict and insert into db
			insert_db(get_insert_dict(result_dir, result, unit))


