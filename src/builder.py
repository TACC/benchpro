# System Imports
import datetime
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

gs = common = logger = None

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

# Generate build report after job is submitted
def generate_build_report(build_cfg, sched_output):
	report_file = build_cfg['general']['working_path'] + gs.sl + gs.build_report_file

	print("Build report:")

	with open(report_file, 'a') as out:
		out.write("[build]\n")
		out.write("code         = "+ build_cfg['general']['code']             + "\n")
		out.write("version      = "+ build_cfg['general']['version']          + "\n")
		out.write("system       = "+ build_cfg['general']['system']           + "\n")
		out.write("compiler     = "+ build_cfg['modules']['compiler']		  + "\n")
		out.write("mpi          = "+ build_cfg['modules']['mpi']              + "\n")
		if build_cfg['general']['module_use']:
			out.write("module_use   = "+ build_cfg['general']['module_use']       + "\n")
		out.write("modules      = "+ ", ".join(build_cfg['modules'].values()) + "\n")
		out.write("optimization = "+ build_cfg['build']['opt_flags']          + "\n")	
		out.write("exe          = "+ build_cfg['build']['check_exe']          + "\n")
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
	common.print_new_results()

	# Parse config input files

	build_cfg 		= cfg_handler.get_cfg(gs.build_cfg_dir,		args.build, 			gs, logger)
	sched_cfg 		= cfg_handler.get_cfg(gs.sched_cfg_dir,		args.sched,				gs, logger)
	compiler_cfg 	= cfg_handler.get_cfg('compiler', 	gs.compile_cfg_file,	gs, logger)

	print()
	print("Using application config file:") 
	print(">  " + common.rel_path(build_cfg['metadata']['cfg_file']))
	print()
	print("Using scheduler config file:")
	print(">  " + common.rel_path(sched_cfg['metadata']['cfg_file']))
	print()

	# Print inputs to log
	common.send_inputs_to_log('Builder', [build_cfg, sched_cfg, compiler_cfg], logger)

	# Get compiler cmds for gcc/intel, otherwise compiler type is unknown
	known_compiler_type = True
	try:
		compiler_cfg['common'].update(compiler_cfg[build_cfg['build']['compiler_type']])
	except:
		known_compiler_type = False

	# Check if build dir already exists
	check_for_previous_install(build_cfg['general']['working_path'])

	# Name of tmp build script
	script_file = "tmp." + build_cfg['general']['code'] + "-build." + sched_cfg['sched']['type']

	# Input template files
	sched_template = common.find_exact(sched_cfg['sched']['type'] + ".template", gs.template_path)[0]

	# Set build template to default, if set in build.cfg: overload
	build_template = ""
	if build_cfg['general']['template']:
		print("overwrite template")
		build_template = build_cfg['general']['template']

	else:
		build_template = build_cfg['general']['code'] + "-" + build_cfg['general']['version'] + ".build"

	build_template_search = common.find_partial(build_template, gs.template_path + gs.sl + gs.build_tmpl_dir)

	if not build_template_search:
		exception.error_and_quit(logger, "failed to locate build template '" + build_template + "' in " + common.rel_path(gs.template_path + gs.sl + gs.build_tmpl_dir))	
	else:
		build_template = build_template_search

	# Get compiler template if compiler type is known (therefore can fill compiler cmds)
	compiler_template = None
	if known_compiler_type:
		compiler_template 	= common.find_exact(gs.compile_tmpl_file, gs.template_path)[0]

	# Get ranks from threads (?)
	sched_cfg['sched']['ranks'] = sched_cfg['sched']['threads']  
	# Get job label
	sched_cfg['sched']['job_label'] = build_cfg['general']['code'] + "_build"

	# Generate build script
	template_handler.generate_template([build_cfg['general'], build_cfg['modules'], build_cfg['build'], sched_cfg['sched'], compiler_cfg['common']],
 									   [sched_template, compiler_template, build_template],
									   script_file, gs, logger)



	# Add sanity check
	if build_cfg['build']['check_exe']:
		with open(script_file, 'a') as f:
			f.write("ldd " + build_cfg['general']['install_path'] + gs.sl +  build_cfg['build']['bin_dir'] + gs.sl + build_cfg['build']['check_exe'] + "\n")

	# Add hardware collection script to job script
	if build_cfg['build']['collect_hw_stats']:
		if common.file_owner(gs.utils_path + gs.sl + "lshw") == "root":
			with open(script_file, 'a') as f:
				f.write(gs.src_path + gs.sl + "collect_hw_info.sh " + gs.utils_path + " " + build_cfg['general']['working_path'] + gs.sl + "hw_report" + "\n")
		else:
			exception.print_warning(logger, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")



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
	sched_output = common.submit_job(build_cfg['general']['working_path'], script_file[4:], logger)

	# Generate build report
	generate_build_report(build_cfg, sched_output)
