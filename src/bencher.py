# System Imports
import configparser as cp
import datetime
import os
import shutil as su

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.template_handler as template_handler

logger = gs = common = None

# Generate bench report after job is submitted
def generate_bench_report(build_report, bench_cfg, sched_output):
	bench_report = bench_cfg['bench']['working_path'] + gs.sl + gs.bench_report_file
	logger.debug("Benchmark report file:" + bench_report)
		
	# Copy 'build_report' to 'bench_report'
	su.copyfile(build_report, bench_report)

	print("Bench report:")
	with open(bench_report, 'a') as out:
		out.write("[bench]\n")
		out.write("bench_path  = "+ bench_cfg['bench']['working_path']   + "\n")
		out.write("nodes       = "+ bench_cfg['sched']['nodes']          + "\n")
		out.write("ranks       = "+ bench_cfg['sched']['ranks_per_node'] + "\n")
		out.write("threads     = "+ bench_cfg['sched']['threads']        + "\n")
		out.write("dataset     = "+ bench_cfg['bench']['dataset']        + "\n")
		out.write("bench_date  = "+ str(datetime.datetime.now())         + "\n")
		out.write("job_script  = "+ bench_cfg['bench']['job_script']     + "\n")
		out.write("job_id      = "+ sched_output[0]                      + "\n")
		out.write("nodelist    = "+ sched_output[1]                      + "\n")
		if not sched_output[0] == "dry_run":
			out.write("stdout      = "+ sched_output[0]+".out"           + "\n")
			out.write("stderr      = "+ sched_output[0]+".err"           + "\n")
			out.write("result_file = "+ bench_cfg['bench']['output_file']+ "\n")

	print(">  " + common.rel_path(bench_report))

# Confirm application exe is available
def check_exe(exe, code_path):
	exe_search = common.find_exact(exe, code_path)[0]
	if exe_search:
		print("Application executable found at:")
		print(">  " + common.rel_path(exe_search))
		print()
	else:
		exception.error_and_quit(logger, "failed to locate application executable '" + exe + "'in " + common.rel_path(code_path))	

# Check input
def run_bench(args, settings):

	global logger, gs, common
	gs = settings
	common = common_funcs.init(gs)

	# Start logger
	logger = common.start_logging("RUN", gs.base_dir + gs.sl + gs.bench_log_file + "_" + gs.time_str + ".log")

	# Check for new results
	common.print_new_results()

	# Get app info from build report
	code_dir = common.check_if_installed(args.bench)
	code_path = gs.build_path + gs.sl + code_dir
	build_report = code_path + gs.sl + gs.build_report_file
	report_parser	 = cp.ConfigParser()
	report_parser.optionxform=str
	report_parser.read(build_report)

	# Get code labee from build_report, for finding default params (if needed)
	try:
		job_id 	= report_parser.get('build', 'job_id')
	except:
		exception.error_and_quit(logger, "Unable to read build_report.txt file in " + common.rel_path(code_path))

	# Check build job is complete
	if not common.check_job_complete(job_id):
		exception.error_and_quit(logger, "Job ID " + job_id + "is RUNNING. It appears '" + args.bench + "' is still compiling.")

	# Get code label from build_report to find appropriate bench cfg file
	code = report_parser.get('build', 'code')

	# Print warning when using default benchmark inputs
	if not args.params:
		args.params = code
		print("WARNING: No input parameters (--params) given, using defaults for debugging.")
		logger.debug("WARNING: No input parameters (--params) given, using defaults for debugging.")

	# Get bench config dicts
	bench_cfg = cfg_handler.get_cfg(gs.bench_cfg_dir, args.params, gs, logger)
	sched_cfg = cfg_handler.get_cfg(gs.sched_cfg_dir, args.sched,  gs, logger)

	# Check application exe
	check_exe(bench_cfg['bench']['exe'], code_path)

	# Add variables from build report to bench cfg dict
	bench_cfg['bench']['code'] 		= report_parser.get('build', 'code')
	bench_cfg['bench']['version'] 	= report_parser.get('build', 'version')
	bench_cfg['bench']['system'] 	= report_parser.get('build', 'system')

	# Get job label
	sched_cfg['sched']['job_label'] = code+"_bench"

	# Path to benchmark session directory
	bench_cfg['bench']['base_path'] = gs.bench_path + gs.sl + bench_cfg['bench']['system'] + "_" + bench_cfg['bench']['code'] + "_" + gs.time_str
	# Path to application's data directory
	bench_cfg['bench']['benchmark_repo'] = gs.benchmark_repo
	# Directory to add to MODULEPATH
	bench_cfg['bench']['base_mod'] = gs.module_path
	# Directory to application installation
	bench_cfg['bench']['app_mod'] = code_dir

	# Print inputs to log
	common.send_inputs_to_log('Bencher', [bench_cfg, sched_cfg], logger)

	# Template files
	sched_template = common.find_exact(sched_cfg['sched']['type'] + ".template", gs.template_path + gs.sl + gs.sched_tmpl_dir)[0]

	# Set bench template to default, if set in bench.cfg: overload
	bench_template = ""
	if bench_cfg['bench']['template']:
		bench_template = bench_cfg['bench']['template']
	else:
		bench_template = bench_cfg['bench']['code'] + "-" + bench_cfg['bench']['version'] + ".bench"
	
	bench_template_search = common.find_partial(bench_template, gs.template_path + gs.sl + gs.bench_tmpl_dir)
	
	if not bench_template_search:
		exception.error_and_quit(logger, "failed to locate bench template '" + bench_template + "' in " + common.rel_path(gs.template_path + gs.sl + gs.bench_tmpl_dir))
	else:
		bench_template = bench_template_search

	bench_cfg['bench']['job_script'] = bench_cfg['bench']['code'] + "-bench." + sched_cfg['sched']['type']
	script_file = "tmp." + bench_cfg['bench']['job_script']

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
		template_handler.generate_template([bench_cfg['sched'], bench_cfg['bench'], sched_cfg['sched']],
									   [sched_template, bench_template],
									   script_file, gs, logger)

		# Add hardware collection script to job script
		if bench_cfg['bench']['collect_hw_stats']:
			if common.file_owner(gs.utils_path + gs.sl + "lshw") == "root":
				with open(script_file, 'a') as f:	
					f.write(gs.src_path + gs.sl + "collect_hw_info.sh " + gs.utils_path + " " + bench_cfg['bench']['working_path'] + gs.sl + "hw_report")
			else:
				exception.print_warning(logger, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")


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
		sched_output = common.submit_job(bench_cfg['bench']['working_path'], bench_cfg['bench']['job_script'], logger)

		# Generate bench report
		generate_bench_report(build_report, bench_cfg, sched_output)

		loop += 1

