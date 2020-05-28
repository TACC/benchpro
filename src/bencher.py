# System Imports
import argparse
import configparser as cp
import os
import sys
import time
from datetime import datetime

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.splash as splash
import src.template_handler as template_handler

logger = gs = ''

# Check input
def run_bench(args, settings):

	global logger, gs
	gs = settings
	common = common_funcs.init(gs)

	# Start logger
	logger = common.start_logging("RUN", gs.base_dir + gs.sl + gs.run_log_file + "_" + gs.time_str + ".log")

	code_path = common.check_if_installed(args.run)

	# Get app info from build report
	report_parser	 = cp.RawConfigParser()
	report_parser.read(gs.build_path + gs.sl + code_path + gs.sl + gs.build_report_file)
	system 	= report_parser.get('report', 'system')
	code 	= report_parser.get('report', 'code')
	version = report_parser.get('report', 'version')

	logger.debug("Application details:")
	logger.debug("System  = "+system)
	logger.debug("Code	  = "+code)
	logger.debug("Version = "+version)

	# Print warning when using default benchmark inputs
	if not args.params:
		args.params = code
		print("WARNING: No input parameters (--params) given, using defaults for debugging.")
		logger.debug("WARNING: No input parameters (--params) given, using defaults for debugging.")

	run_cfg = cfg_handler.get_cfg('run',  		args.params, gs, logger)
	sched_cfg = cfg_handler.get_cfg('sched', 	args.sched,  gs, logger)

	session = code + "-" + gs.time_str

	# Path to benchmark session directory
	run_cfg['bench']['base_path'] = gs.build_path + gs.sl + code_path + gs.sl + session
	# Path to application's data directory
	run_cfg['bench']['benchmark_repo'] = gs.benchmark_repo + gs.sl + code
	# Directory to add to MODULEPATH
	run_cfg['bench']['base_mod'] = gs.module_path
	# Directory to application installation
	run_cfg['bench']['app_mod'] = code_path


	# Template files
	sched_template = gs.template_path + gs.sl + gs.sched_tmpl_dir + gs.sl + sched_cfg['scheduler']['type'] + ".template"
	run_template   = gs.template_path + gs.sl + gs.run_tmpl_dir + gs.sl + code + "-" + version + ".run"

	script_file = "tmp." + code + "-run." + sched_cfg['scheduler']['type']

	tmp = run_cfg['sched']['nodes']
	loop = 1

	# for each nodes in list
	for node in tmp:
		logger.debug("Building script for " + node + " nodes")

		print()
		print("Building script " + str(loop)  + " of " + str(len(tmp)) + ": " + str(node) + " nodes.")

		# Update node var
		run_cfg['sched']['nodes'] = node

		# Get working_path
		subdir = "nodes_" + node.zfill(3)
		run_cfg['bench']['working_path'] = run_cfg['bench']['base_path'] + gs.sl + subdir

		# Get total ranks from nodes * ranks_per_node
		run_cfg['sched']['ranks'] = int(node) * int(run_cfg['sched']['ranks_per_node'])

		# Generate benchmark template
		template_handler.generate_template([run_cfg['sched'], run_cfg['bench'], sched_cfg['scheduler']],
									   [sched_template, run_template],
									   script_file, gs, logger)

		if run_cfg['bench']['collect_hw']:
			with open(script_file, 'a') as f:	
				f.write(gs.src_path + gs.sl + "collect_hw_info.sh " + gs.utils_path + " " + run_cfg['bench']['working_path'] + gs.sl + "hw_report")

		# Create benchmark directory
		common.create_install_dir(run_cfg['bench']['working_path'], logger)
		# Copy temp job script
		common.install(run_cfg['bench']['working_path'], script_file, logger)
		# Delete tmp job script
		exception.remove_tmp_files(logger)
		# Submit job
		job_id = common.submit_job(run_cfg['bench']['working_path'] + gs.sl + script_file[4:], logger)

		loop += 1

