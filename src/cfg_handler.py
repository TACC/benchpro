# System Imports
import configparser as cp
import os
import sys

import src.exception as exception

logger = gs = ''

# Check cfg file exists
def check_file(cfg_type, cfg_name):
	suffix = ''
	subdir = ''

	# First: check for file in user's CWD
	cfg_path = gs.cwd + gs.sl
	logger.debug("Looking for " + cfg_name + " in " + cfg_path + "...")
	if os.path.isfile(cfg_path + cfg_name):
		logger.debug("Found")
		return cfg_path + cfg_name

	# Second: check in project base_dir
	cfg_path = gs.base_dir + gs.sl
	logger.debug("Looking for " + cfg_name + " in " + cfg_path + "...")
	if os.path.isfile(cfg_path + cfg_name):
		logger.debug("Found")
		return cfg_path + cfg_name

	# Third: reformat naming and look in ./config dir
	if cfg_type == 'build':
		subdir = gs.build_cfg_dir
		if not "_build" in cfg_name:
			suffix += "_build"

	elif cfg_type == 'run':
		subdir = gs.run_cfg_dir
		if not "_run" in cfg_name:
			suffix += "_run"

	elif cfg_type == 'sched':
		subdir = gs.sched_cfg_dir

	if not ".cfg" in cfg_name:
		suffix += ".cfg"

	cfg_name += suffix
	cfg_path = gs.config_path + gs.sl + subdir + gs.sl

	logger.debug("Looking for " + cfg_name + " in " + cfg_path + "...")

	if not os.path.isfile(cfg_path + cfg_name):
		exception.error_and_quit(logger, "Input file '" + cfg_name + "' not found.")

	logger.debug("Found")
	return cfg_path + cfg_name

# Parse cfg file into dict
def read_cfg_file(cfg_file):
	cfg_parser = cp.ConfigParser()
	cfg_parser.optionxform=str
	cfg_parser.read(cfg_file)
	# Add file name to dict
	cfg_dict = {'metadata': {'cfg_file': cfg_file}}
	for section in cfg_parser.sections():
		cfg_dict[section] = {}
		for value in cfg_parser.options(section):
			cfg_dict[section][value] = cfg_parser.get(section, value)

	return cfg_dict

# Convert module name to usable directory name, Eg: intel/18.0.2 -> intel18
def get_label(module):
	label = module
	if module.count(gs.sl) > 0:
		comp_ver = module.split(gs.sl)
		label = comp_ver[0] + comp_ver[1].split(".")[0]
		logger.debug("Converted " + module + " to " + label)
	return label

# Check build config file and add required fields
def process_build_cfg(cfg_dict):

	# Check for missing essential parameters in general section
	if not cfg_dict['general']['code'] or not cfg_dict['general']['version']:
		print("Missing required parameters in "+cfg_dict['metadata']['cfg_file'])
		print("----------------------------")
		print("Code".ljust(10),	  ":", cfg_dict['general']['code'])
		print("Version".ljust(10),   ":", cfg_dict['general']['version'])
		print("----------------------------")
		exception.error_and_quit(logger, "Cannot continue due to missing inputs.")

	# Insert 1 node for build job
	cfg_dict['build']['nodes'] = "1"

	# Get system from env if not defined
	if not cfg_dict['general']['system']:
		exception.print_warning(logger, "system not defined in '" + cfg_dict['metadata']['cfg_file'] + \
								"', getting system label from $TACC_SYSTEM: " + str(os.getenv('TACC_SYSTEM')))
		cfg_dict['general']['system'] = str(os.getenv('TACC_SYSTEM'))

	# Check for compiler and MPI
	if not cfg_dict['modules']['compiler'] or not cfg_dict['modules']['mpi']:
		exception.error_and_quit(logger, "compiler and/or MPI module not provided.")

	# Parse system info config file 
	system_file = check_file('system', gs.config_dir + gs.sl + gs.system_cfg_file)
	system_dict = read_cfg_file(system_file)

	# Parse architecture defaults config file 
	arch_file = check_file('arch', gs.config_dir + gs.sl + gs.arch_cfg_file)
	arch_dict = read_cfg_file(arch_file)

	# Extract compiler type
	cfg_dict['build']['compiler_type'] = cfg_dict['modules']['compiler'].split('/')[0]

	# Get core count for system
	try:
		cfg_dict['build']['cores'] = system_dict[cfg_dict['general']['system']]['cores']
		logger.debug("Core count for " + cfg_dict['general']['system'] + " = " + cfg_dict['build']['cores'])

	except:
		exception.error_and_quit(logger, "System profile '" + cfg_dict['general']['system'] + "' missing in " + config_dir + gs.sl + gs.system_cfg_file)

	# If arch requested = 'system', get default arch for this system
	if cfg_dict['build']['arch'] == 'system':
		cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
		logger.debug("Requested build arch='system'. Using system default for " + cfg_dict['general']['system'] + " = " + cfg_dict['build']['arch'])

	# If using custom opt flags
	if cfg_dict['build']['opt_flags']:
		# If arch is defined
		if cfg_dict['build']['arch']:
			# If label is not provided
			if not cfg_dict['build']['build_label']:
				cfg_dict['build']['build_label'] = cfg_dict['build']['arch'] + "-modified"

			# Add custom opts to arch opts
			try:
				cfg_dict['build']['opt_flags'] = "'" + cfg_dict['build']['opt_flags'].replace('"', '').replace( \
					'\'', '') + " " + arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']].replace('\'', '') + "'"
			except:
				exception.error_and_quit(logger, "No default optimization flags for " + \
										 cfg_dict['build']['arch'] + " found in " + gs.arch_cfg_file)

			exception.print_warning(logger, "an archicture '" + cfg_dict['build']['arch'] + "' and custom optimization flags '" + \
									cfg_dict['build']['opt_flags'] + "' have both been defined.")
			exception.print_warning(logger, "setting compile flags to: " + cfg_dict['build']['opt_flags'])
		# If arch not defined
		else:
			if not cfg_dict['build']['build_label']:
				exception.error_and_quit(logger, "When using custom optimization flags 'opt_flags' in " + \
										 cfg_dict['metadata']['cfg_file'] + ", you need to provide a build label 'build_label'.")
	# If not using custom opt flags
	else:
		# If arch not defined, use system default arch
		if not cfg_dict['build']['arch']:
			cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
			exception.print_warning(logger, "no architecture defined in " + cfg_dict['metadata']['cfg_file'])
			exception.print_warning(logger, "using default system arch for " + cfg_dict['general']['system'] + ": " + cfg_dict['build']['arch'])

		# Use arch as build label
		cfg_dict['build']['build_label'] = cfg_dict['build']['arch']

		print(cfg_dict['build']['arch'])
		print(cfg_dict['build']['compiler_type'])

		# Get optimization flags for arch
		try:
			cfg_dict['build']['opt_flags'] = arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']]
		except:
			exception.error_and_quit(logger, "No default optimization flags for " + cfg_dict['build']['arch'] + " found in " + gs.arch_cfg_file)

	# Generate default build path if on is not defined
	if not cfg_dict['general']['build_prefix']:
		cfg_dict['general']['working_path'] = gs.build_path + gs.sl + cfg_dict['general']['system'] + gs.sl + get_label(cfg_dict['modules']['compiler']) + gs.sl + get_label( \
						cfg_dict['modules']['mpi']) + gs.sl + cfg_dict['general']['code'] + gs.sl + cfg_dict['build']['build_label'] + gs.sl + cfg_dict['general']['version']
	# Translate 'build_prefix' to 'working_path' for better readability
	else:
		cfg_dict['general']['working_path'] = cfg_dict['general']['build_prefix']
	
	# Get build and install subdirs
	cfg_dict['general']['build_path']   = cfg_dict['general']['working_path'] + gs.sl + "build"
	cfg_dict['general']['install_path'] = cfg_dict['general']['working_path'] + gs.sl + "install"

# Check run config file and add required fields
def process_run_cfg(cfg_dict):

    # Check for missing essential parameters in general section
	if not cfg_dict['sched']['nodes'] or not cfg_dict['sched']['ranks_per_node'] or not cfg_dict['sched']['threads'] or not cfg_dict['bench']['exe']:
		print("Missing required parameters in "+cfg_dict['metadata']['cfg_file'])
		print("----------------------------")
		print("Nodes".ljust(16),   			":", cfg_dict['sched']['nodes'])
		print("Ranks_per_node".ljust(16),	":", cfg_dict['sched']['ranks_per_node'])
		print("Threads".ljust(16),   		":", cfg_dict['sched']['threads'])
		print("Exe".ljust(16),   			":", cfg_dict['bench']['exe'])
		print("----------------------------")
		exception.error_and_quit(logger, "Cannot continue due to missing inputs.")

	# Handle comma-delimited lists
	cfg_dict['sched']['nodes'] = cfg_dict['sched']['nodes'].split(",")

# Check sched config file and add required fields
def process_sched_cfg(cfg_dict):

	# Check for missing essential parameters in general section
	if not cfg_dict['scheduler']['type'] or not cfg_dict['scheduler']['queue'] or not cfg_dict['scheduler']['account']:

		print("Missing required parameters in "+cfg_dict['metadata']['cfg_file'])
		print("----------------------------")
		print("Type".ljust(16),		":", cfg_dict['schededuler']['type'])
		print("Queue".ljust(16),   	":", cfg_dict['schededuler']['queue'])
		print("Account".ljust(16),	":", cfg_dict['schededuler']['account'])
		print("----------------------------")
		exception.error_and_quit(logger, "Cannot continue due to missing inputs.")

	# Fill missing parameters
	if not cfg_dict['scheduler']['job_label']:
		cfg_dict['scheduler']['job_label'] = 'builder'
		logger.debug("Set job_label = " + cfg_dict['scheduler']['job_label'])
	if not cfg_dict['scheduler']['runtime']:
		cfg_dict['scheduler']['runtime'] = '02:00:00'
		logger.debug("Set runtime = " + cfg_dict['scheduler']['runtime'])
	if not cfg_dict['scheduler']['job_label']:
		cfg_dict['scheduler']['threads'] = 4
		logger.debug("Set threads = " + cfg_dict['scheduler']['threads'])

# Read input param config and test 
def get_cfg(cfg_type, cfg_name, settings,  log_to_use):

	global logger, gs 
	logger = log_to_use
	gs = settings

	# Check input file exists
	cfg_file = check_file(cfg_type, cfg_name)
	# Parse input fo;e
	cfg_dict = read_cfg_file(cfg_file)

	# Start processing function for cfg type
	if cfg_type == 'build':
		logger.debug("Starting build cfg processing.")
		process_build_cfg(cfg_dict)
	elif cfg_type == 'run':
		logger.debug("Starting run cfg processing.")
		process_run_cfg(cfg_dict)
	elif cfg_type == 'sched':
		logger.debug("Starting sched cfg processing.")
		process_sched_cfg(cfg_dict)

	return cfg_dict
