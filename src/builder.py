# System Imports
import configparser as cp
import glob
import os
import pprint as pp
import re
import shutil as su
import socket
import subprocess
import sys
import time
from datetime import datetime

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.module_handler as module_handler
import src.template_handler as template_handler

gs	 = ''

# Check if an existing installation exists
def check_for_previous_install(path, logger):
	if os.path.exists(path):
		if gs.overwrite:
			logger.debug("WARNING: It seems this app is already installed. Deleting old build in " +
						 path + " because 'overwrite=True' in settings.cfg")

			print()
			print("WARNING: Application directory already exists and 'overwrite=True' in settings.cfg, continuing in 5 seconds...")
			print()

			time.sleep(gs.timeout)
			print("No going back now...")

			su.rmtree(path)
		else:
			exception.error_and_quit(logger, "It seems this app is already installed in " + path +
									 ". The install directory already exists and 'overwrite=False' in settings.cfg")

# Check if module is available on the system
def check_module_exists(module):
	try:
		cmd = subprocess.run("module spider " + module, shell=True,
							 check=True, capture_output=True, universal_newlines=True)

	except subprocess.CalledProcessError as e:
		exception.error_and_quit(
			logger, "module " + module + " not available on this system")

# Log cfg contents
def send_inputs_to_log(cfg, logger):
	logger.debug("Builder started with the following inputs:")
	for seg in cfg:
		logger.debug("[" + seg + "]")
		for line in cfg[seg]:
			logger.debug("  " + str(line) + "=" + str(cfg[seg][line]))

# Generate build report after job is submitted
def generate_build_report(code_cfg, sched_output, logger):
	report_file = code_cfg['general']['working_path'] + gs.sl + gs.build_report_file

	print("Writing build report to " + report_file)

	with open(report_file, 'a') as out:
		out.write("[report]\n")
		out.write("code         = "+ code_cfg['general']['code'] + "\n")
		out.write("version      = "+ code_cfg['general']['version'] + "\n")
		out.write("system       = "+ code_cfg['general']['system'] + "\n")
		out.write("modules      = "+ ", ".join(code_cfg['modules'].values()) + "\n")
		out.write("optimization = "+ code_cfg['build']['opt_flags'] + "\n")	
		out.write("build_prefix = "+ code_cfg['general']['working_path'] + "\n")
		out.write("build_date   = "+ gs.time_str + "\n")
		out.write("job_id       = "+ sched_output[0] + "\n")
		out.write("Build_host   = "+ sched_output[1])

# Main methond for generating and submitting build script
def build_code(args, settings):

	# Get global settings obj
	global gs
	gs = settings

	# Instantiate common_funcs
	common = common_funcs.init(gs)

	# Init loggers
	logger = common.start_logging("BUILD", gs.base_dir + gs.sl + gs.build_log_file + "_" + gs.time_str + ".log")

	# Parse config input files
	code_cfg =	 cfg_handler.get_cfg('build',	args.install,		gs, logger)
	sched_cfg =	cfg_handler.get_cfg('sched',	args.sched,		  gs, logger)
	compiler_cfg = cfg_handler.get_cfg('compiler', gs.compile_cfg_file, gs, logger)

	print('{:25}'.format('Using application config'), ":", code_cfg['metadata']['cfg_file'])
	print('{:25}'.format('Using scheduler config'), ":",   sched_cfg['metadata']['cfg_file'])

	# Print inputs to log
	send_inputs_to_log(code_cfg, logger)
	send_inputs_to_log(sched_cfg, logger)
	send_inputs_to_log(compiler_cfg, logger)

	# Get compiler cmds for gcc/intel
	compiler_cfg['common'].update(compiler_cfg[code_cfg['build']['compiler_type']])

	# Input Checks
	for mod in code_cfg['modules']: 
		check_module_exists(code_cfg['modules'][mod])

	# Check if build dir already exists
	check_for_previous_install(code_cfg['general']['working_path'], logger)

	# Name of tmp build script
	script_file = "tmp." + code_cfg['general']['code'] + "-build." + sched_cfg['scheduler']['type']

	# Input template files
	sched_template		= gs.template_path + gs.sl + gs.sched_tmpl_dir + gs.sl + sched_cfg['scheduler']['type'] + ".template"
	build_template		= gs.template_path + gs.sl + gs.build_tmpl_dir + gs.sl + code_cfg['general']['code'] + "-" + code_cfg['general']['version'] + ".build"
	compiler_template 	= gs.template_path + gs.sl + gs.compile_tmpl_file

	# Get ranks from threads (?)
	sched_cfg['scheduler']['ranks'] = sched_cfg['scheduler']['threads']  

	# Generate build script
	template_handler.generate_template([code_cfg['general'], code_cfg['modules'], code_cfg['build'], code_cfg['run'], sched_cfg['scheduler'], compiler_cfg['common']],
 									   [sched_template, compiler_template, build_template],
									   script_file, gs, logger)


	# Generate module in temp location
	mod_path, mod_file = module_handler.make_mod(code_cfg['general'], code_cfg['build'], code_cfg['modules'], gs, logger)

	# Make build path and move tmp file
	common.create_install_dir(code_cfg['general']['working_path'], logger)
	common.install(code_cfg['general']['working_path'], script_file, logger)
	print('{:25}'.format('Build script location'), ":", code_cfg['general']['working_path'])

	# Make module path and move tmp file
	common.create_install_dir(mod_path, logger)
	common.install(mod_path, mod_file, logger)
	print('{:25}'.format('Module file location'), ":", mod_path)

	# Copy code and sched cfg & template files to build dir
	provenance_path = code_cfg['general']['working_path'] + gs.sl + "build_files"
	common.create_install_dir(provenance_path, logger)
	common.install(provenance_path, code_cfg['metadata']['cfg_file'], logger)
	common.install(provenance_path, sched_cfg['metadata']['cfg_file'], logger)
	common.install(provenance_path, sched_template, logger)
	common.install(provenance_path, build_template, logger)

	# Clean up tmp files
	exception.remove_tmp_files(logger)

	# Submit build script to scheduler
	sched_output = common.submit_job(code_cfg['general']['working_path'] + gs.sl + script_file[4:], logger)

	# Generate build report
	generate_build_report(code_cfg, sched_output, logger)
