# System Imports
import subprocess

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

def capture_result(args, settings):
	global logger, gs
	gs = settings

	common = common_funcs.init(gs)
	# Start logger
	logger = common.start_logging("CAPTURE", gs.base_dir + gs.sl + gs.bench_log_file + "_" + gs.time_str + ".log")

	results = common.get_subdirs(gs.bench_path)

	for result_dir in results:
		result, unit = validate_result(gs.bench_path + gs.sl + result_dir)
		print(result, unit)
