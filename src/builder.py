# System Imports
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.module_handler as module_handler
import src.template_handler as template_handler

gs = common = logger = ''

# Check if an existing installation exists
def check_for_previous_install(path):
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
		exception.error_and_quit(logger, "module '" + module + "' not available on this system")

# Log cfg contents
def send_inputs_to_log(cfg):
	logger.debug("Builder started with the following inputs:")
	for seg in cfg:
		logger.debug("[" + seg + "]")
		for line in cfg[seg]:
			logger.debug("  " + str(line) + "=" + str(cfg[seg][line]))

# Generate build report after job is submitted
def generate_build_report(build_cfg, sched_output):
	report_file = build_cfg['general']['working_path'] + gs.sl + gs.build_report_file

	print("Build report:")

	with open(report_file, 'a') as out:
		out.write("[build]\n")
		out.write("code         = "+ build_cfg['general']['code']             + "\n")
		out.write("version      = "+ build_cfg['general']['version']          + "\n")
		out.write("system       = "+ build_cfg['general']['system']           + "\n")
		out.write("compiler     = "+ build_cfg['modules']['compiler']         + "\n")
		out.write("mpi          = "+ build_cfg['modules']['mpi']              + "\n")
		out.write("modules      = "+ ", ".join(build_cfg['modules'].values()) + "\n")
		out.write("optimization = "+ build_cfg['build']['opt_flags']          + "\n")	
		out.write("build_prefix = "+ build_cfg['general']['working_path']     + "\n")
		out.write("build_date   = "+ str(datetime.datetime.now())             + "\n")
		out.write("job_id       = "+ sched_output[0]                          + "\n")
		out.write("nodelist     = "+ sched_output[1]                          + "\n")

	print(">  " + common.rel_path(report_file))

# Main methond for generating and submitting build script
def build_code(args, settings):

	# Get global settings obj
	global gs, common, logger
	gs = settings

	# Instantiate common_funcs
	common = common_funcs.init(gs)

	# Init loggers
	logger = common.start_logging("BUILD", gs.base_dir + gs.sl + gs.build_log_file + "_" + gs.time_str + ".log")

	# Check for new results
	common.print_results()

	# Parse config input files
	build_cfg =	 cfg_handler.get_cfg('build',	args.install,		gs, logger)
	sched_cfg =	cfg_handler.get_cfg('sched',	args.sched,		  gs, logger)
	compiler_cfg = cfg_handler.get_cfg('compiler', gs.compile_cfg_file, gs, logger)

	print()
	print("Using application config file:") 
	print(">  " + common.rel_path(build_cfg['metadata']['cfg_file']))
	print()
	print("Using scheduler config file:")
	print(">  " + common.rel_path(sched_cfg['metadata']['cfg_file']))
	print()

	# Print inputs to log
	send_inputs_to_log(build_cfg)
	send_inputs_to_log(sched_cfg)
	send_inputs_to_log(compiler_cfg)

	# Get compiler cmds for gcc/intel
	compiler_cfg['common'].update(compiler_cfg[build_cfg['build']['compiler_type']])

	# Input Checks
	for mod in build_cfg['modules']: 
		check_module_exists(build_cfg['modules'][mod])

	# Check if build dir already exists
	check_for_previous_install(build_cfg['general']['working_path'])

	# Name of tmp build script
	script_file = "tmp." + build_cfg['general']['code'] + "-build." + sched_cfg['scheduler']['type']

	# Input template files
	sched_template		= gs.template_path + gs.sl + gs.sched_tmpl_dir + gs.sl + sched_cfg['scheduler']['type'] + ".template"
	build_template		= gs.template_path + gs.sl + gs.build_tmpl_dir + gs.sl + build_cfg['general']['code'] + "-" + build_cfg['general']['version'] + ".build"
	compiler_template 	= gs.template_path + gs.sl + gs.compile_tmpl_file

	# Get ranks from threads (?)
	sched_cfg['scheduler']['ranks'] = sched_cfg['scheduler']['threads']  
	# Get job label
	sched_cfg['scheduler']['job_label'] = build_cfg['general']['code']+ "-build"

	# Generate build script
	template_handler.generate_template([build_cfg['general'], build_cfg['modules'], build_cfg['build'], build_cfg['run'], sched_cfg['scheduler'], compiler_cfg['common']],
 									   [sched_template, compiler_template, build_template],
									   script_file, gs, logger)


	# Generate module in temp location
	mod_path, mod_file = module_handler.make_mod(build_cfg['general'], build_cfg['build'], build_cfg['modules'], gs, logger)

	# Make build path and move tmp build script file
	common.create_dir(build_cfg['general']['working_path'], logger)
	common.install(build_cfg['general']['working_path'], script_file, "", logger)
	print()
	print("Build script location:")
	print(">  " + common.rel_path(build_cfg['general']['working_path']))
	print()

	# Make module path and move tmp module file
	common.create_dir(mod_path, logger)
	common.install(mod_path, mod_file, "", logger)

	print("Module file location:")
	print(">  " + common.rel_path(mod_path))
	print()

	# Copy code and sched cfg & template files to build dir
	provenance_path = build_cfg['general']['working_path'] + gs.sl + "build_files"
	common.create_dir(provenance_path, logger)

	common.install(provenance_path, build_cfg['metadata']['cfg_file'], "build.cfg", logger)
	common.install(provenance_path, build_template, "build.template", logger)

	common.install(provenance_path, sched_cfg['metadata']['cfg_file'], "", logger)
	common.install(provenance_path, sched_template, "", logger)

	# Clean up tmp files
	exception.remove_tmp_files(logger)

	# Submit build script to scheduler
	sched_output = common.submit_job(build_cfg['general']['working_path'] + gs.sl + script_file[4:], logger)

	# Generate build report
	generate_build_report(build_cfg, sched_output)
