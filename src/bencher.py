# System Imports
import configparser as cp

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.template_handler as template_handler

logger = gs = ''

# Check input
def run_bench(args, settings):

	global logger, gs
	gs = settings
	common = common_funcs.init(gs)

	# Start logger
	logger = common.start_logging("RUN", gs.base_dir + gs.sl + gs.bench_log_file + "_" + gs.time_str + ".log")

	code_path = common.check_if_installed(args.bench)

	# Get app info from build report
	report_parser	 = cp.ConfigParser()
	report_parser.optionxform=str
	report_parser.read(gs.build_path + gs.sl + code_path + gs.sl + gs.build_report_file)

	try:
		system 	= report_parser.get('report', 'system')
		code 	= report_parser.get('report', 'code')
		version = report_parser.get('report', 'version')
	except:
		exception.error_and_quit(logger, "Unable to read build_report.txt file in "+code_path)

	logger.debug("Application details:")
	logger.debug("System  = "+system)
	logger.debug("Code	  = "+code)
	logger.debug("Version = "+version)

	# Print warning when using default benchmark inputs
	if not args.params:
		args.params = code
		print("WARNING: No input parameters (--params) given, using defaults for debugging.")
		logger.debug("WARNING: No input parameters (--params) given, using defaults for debugging.")

	bench_cfg = cfg_handler.get_cfg('bench', args.params, gs, logger)
	sched_cfg = cfg_handler.get_cfg('sched', args.sched,  gs, logger)

	session =  "bench-" + gs.time_str


	# Add variables from build report to bench cfg dict
	bench_cfg['bench']['version'] = version
	bench_cfg['bench']['code'] = code
	bench_cfg['bench']['system'] = system

	# Path to benchmark session directory
	bench_cfg['bench']['base_path'] = gs.bench_path + gs.sl + system + "_" + code + "_" + gs.time_str
	# Path to application's data directory
	bench_cfg['bench']['benchmark_repo'] = gs.benchmark_repo
	# Directory to add to MODULEPATH
	bench_cfg['bench']['base_mod'] = gs.module_path
	# Directory to application installation
	bench_cfg['bench']['app_mod'] = code_path


	# Template files
	sched_template = gs.template_path + gs.sl + gs.sched_tmpl_dir + gs.sl + sched_cfg['scheduler']['type'] + ".template"
	bench_template   = gs.template_path + gs.sl + gs.bench_tmpl_dir + gs.sl + code + "-" + version + ".bench"

	script_file = "tmp." + code + "-bench." + sched_cfg['scheduler']['type']

	tmp = bench_cfg['sched']['nodes']
	loop = 1

	# for each nodes in list
	for node in tmp:
		logger.debug("Write script for " + node + " nodes")

		print()
		print("Building script " + str(loop)  + " of " + str(len(tmp)) + ": " + str(node) + " nodes.")

		# Update node var
		bench_cfg['sched']['nodes'] = node

		# Get working_path
		subdir = node.zfill(3) + "nodes"
		bench_cfg['bench']['working_path'] = bench_cfg['bench']['base_path'] + "_" + subdir
		print("Benchmark working directory:")
		print(">  " + common.rel_path(bench_cfg['bench']['working_path']))
		print()

		# Get total ranks from nodes * ranks_per_node
		bench_cfg['sched']['ranks'] = int(node) * int(bench_cfg['sched']['ranks_per_node'])

		# Generate benchmark template
		template_handler.generate_template([bench_cfg['sched'], bench_cfg['bench'], sched_cfg['scheduler']],
									   [sched_template, bench_template],
									   script_file, gs, logger)

		if bench_cfg['bench']['collect_hw']:
			with open(script_file, 'a') as f:	
				f.write(gs.src_path + gs.sl + "collect_hw_info.sh " + gs.utils_path + " " + bench_cfg['bench']['working_path'] + gs.sl + "hw_report")


		# Make bench path and move tmp bench script file
		common.create_dir(bench_cfg['bench']['working_path'], logger)
		common.install(bench_cfg['bench']['working_path'], script_file, "", logger)

		# Copy bench cfg & template files to bench dir
		provenance_path = bench_cfg['bench']['working_path'] + gs.sl + "bench_files"
		common.create_dir(provenance_path, logger)

		common.install(provenance_path, bench_cfg['metadata']['cfg_file'], "bench.cfg", logger)
		common.install(provenance_path, bench_template, "bench.template", logger)

		common.install(provenance_path, sched_cfg['metadata']['cfg_file'], "", logger)
		common.install(provenance_path, sched_template, "", logger)

		# Delete tmp job script
		exception.remove_tmp_files(logger)
		# Submit job
		job_id = common.submit_job(bench_cfg['bench']['working_path'] + gs.sl + script_file[4:], logger)

		loop += 1

