# System Imports
import configparser as cp
import os
import re
import subprocess
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception

logger = gs = common = None

# Check cfg file exists
def check_file(cfg_type, cfg_name):
	suffix = ''
	subdir = ''

	# 1: check if provided cfg_name is a file
	if os.path.isfile(cfg_name):
		logger.debug("Found")
		return cfg_name

	# 2: check for file in user's CWD
	search_path = gs.cwd + gs.sl
	logger.debug("Looking for " + cfg_name + " in CWD: " + search_path + "...")
	if os.path.isfile(search_path + cfg_name):
		logger.debug("Found")
		return search_path + cfg_name

	# 3: check in project base_dir
	search_path = gs.base_dir + gs.sl
	logger.debug("Looking for " + cfg_name + " in $TOPDIR: " + search_path + "...")
	if os.path.isfile(search_path + cfg_name):
		logger.debug("Found")
		return search_path + cfg_name

	# 4: reformat naming and look in ./config dir
	if cfg_type == 'build':
		subdir = gs.build_cfg_dir
		if not "_build" in cfg_name:
			suffix += "_build"

	elif cfg_type == 'bench':
		subdir = gs.bench_cfg_dir
		if not "_bench" in cfg_name:
			suffix += "_bench"

	elif cfg_type == 'sched':
		subdir = gs.sched_cfg_dir

	if not ".cfg" in cfg_name:
		suffix += ".cfg"

	cfg_full_name = cfg_name + suffix
	search_path = gs.config_path + gs.sl + subdir + gs.sl

	logger.debug("Looking for " + cfg_full_name + " in " + search_path + "...")

	if os.path.isfile(search_path + cfg_full_name):
		logger.debug("Found")
		return search_path + cfg_full_name
	
	# 5: Search keyword in ./config/build
	logger.debug("Searching for *" + cfg_name + "* in " + search_path + "...")
	search_result = common.find_partial(cfg_name, search_path)
	if os.path.isfile(search_result):
		logger.debug("Found")
		return  search_result

	print("Available applications:")
	for cfg in os.listdir(search_path):
		print("  "+cfg)
	exception.error_and_quit(logger, "input cfg file for '" + common.rel_path(cfg_name) + "' not found.")

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

# Gets full module name of default module, eg: 'intel' -> 'intel/18.0.2'
def get_full_module_name(module, cmd_prefix):
	cmd = subprocess.run(cmd_prefix + "ml -t -d av  2>&1 | grep '^" + module +"'", shell=True,
							check=True, capture_output=True, universal_newlines=True)
	return cmd.stdout.strip()

# Check if module is available on the system
def check_module_exists(module, module_use):

	cmd_prefix = ""
	if module_use:
		cmd_prefix = "ml use " + module_use + "; "

	try:
		cmd = subprocess.run(cmd_prefix + "module spider " + module, shell=True,
								check=True, capture_output=True, universal_newlines=True)

	except subprocess.CalledProcessError as e:
		exception.error_and_quit(logger, "module '" + module + "' not available on this system")

	return get_full_module_name(module, cmd_prefix)


# Error if section heading missing in cfg file
def check_dict_section(cfg_file, cfg_dict, section):
	if not section in cfg_dict:
		exception.error_and_quit(logger, "["+section+"] section heading required in " + common.rel_path(cfg_file) + ". Consult the documentation.")

# Error if value missing in cfg file
def check_dict_key(cfg_file, cfg_dict, section, key):
	# If key not found 
	if not key in cfg_dict[section]:
		exception.error_and_quit(logger, "'" + key + "' value must be present in section [" + section + "] in " + common.rel_path(cfg_file) + ". Consult the documentation.")
	# If key not set
	if not cfg_dict[section][key]:
		exception.error_and_quit(logger, "'" + key + "' value must be non-null in section [" + section + "] in " + common.rel_path(cfg_file) + ". Consult the documentation.")

# Check build config file and add required fields
def process_build_cfg(cfg_dict):

	# Check for missing essential parameters 
	check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'general')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'code')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'version')

	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'compiler')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'mpi')

	# Instantiate missing optional parameters
	if not 'system' in 				cfg_dict['general'].keys():	cfg_dict['general']['system']			= "" 
	if not 'build_prefix' in 		cfg_dict['general'].keys():	cfg_dict['general']['build_prefix']		= ""
	if not 'build_template' in		cfg_dict['general'].keys():	cfg_dict['general']['build_template']	= ""
	if not 'module_template' in		cfg_dict['general'].keys(): cfg_dict['general']['module_template']	= ""
	if not 'module_use' in			cfg_dict['general'].keys(): cfg_dict['general']['module_use']		= ""

	if not 'arch' in 				cfg_dict['build'].keys():	cfg_dict['build']['arch'] 				= ""
	if not 'opt_flags' in 			cfg_dict['build'].keys():	cfg_dict['build']['opt_flags'] 			= ""	
	if not 'build_label' in 		cfg_dict['build'].keys():	cfg_dict['build']['build_label'] 		= ""
	if not 'bin_dir' in 			cfg_dict['build'].keys():	cfg_dict['build']['bin_dir'] 			= ""

	if not 'collect_hw_stats' in 	cfg_dict['run'].keys():		cfg_dict['run']['collect_hw_stats']		= False

	# Extract compiler type from label by splitting by / and removing ints
	cfg_dict['build']['compiler_type'] = re.sub("\d", "", cfg_dict['modules']['compiler'].split('/')[0])

	# Insert 1 node for build job
	cfg_dict['build']['nodes'] = "1"
	# Path to application's data directory
	cfg_dict['build']['benchmark_repo'] = gs.benchmark_repo

	# Get system from env if not defined
	if not cfg_dict['general']['system']:
		exception.print_warning(logger, "'system' not defined in " + common.rel_path(cfg_dict['metadata']['cfg_file']))
		exception.print_warning(logger, "getting system label from $TACC_SYSTEM: " + str(os.getenv('TACC_SYSTEM')))
		print()
		cfg_dict['general']['system'] = str(os.getenv('TACC_SYSTEM'))
		if not cfg_dict['general']['system']:
			exception.error_and_quit(logger, "$TACC_SYSTEM not set, unable to continue. Please define 'system' in " + common.rel_path(cfg_dict['metadata']['cfg_file']))

	# Check requested modules exist, and if so, result full module names
	for mod in cfg_dict['modules']:
		cfg_dict['modules'][mod] = check_module_exists(cfg_dict['modules'][mod], cfg_dict['general']['module_use'])

	# Parse system info config file 
	system_file = check_file('system', gs.config_path + gs.sl + gs.system_cfg_file)
	system_dict = read_cfg_file(system_file)

	# Parse architecture defaults config file 
	arch_file = check_file('arch', gs.config_path + gs.sl + gs.arch_cfg_file)
	arch_dict = read_cfg_file(arch_file)

	# Get core count for system
	try:
		cfg_dict['build']['cores'] = system_dict[cfg_dict['general']['system']]['cores']
		logger.debug("Core count for " + cfg_dict['general']['system'] + " = " + cfg_dict['build']['cores'])

	except:
		exception.error_and_quit(logger, "System profile '" + cfg_dict['general']['system'] + "' missing in " + common.rel_path(system_file))

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
										 common.rel_path(cfg_dict['metadata']['cfg_file']) + ", you need to provide a build label 'build_label'.")
	# If not using custom opt flags
	else:
		# If arch not defined, use system default arch
		if not cfg_dict['build']['arch']:
			cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
			exception.print_warning(logger, "'arch' not defined in " + common.rel_path(cfg_dict['metadata']['cfg_file']))
			exception.print_warning(logger, "using default system arch for " + cfg_dict['general']['system'] + ": " + cfg_dict['build']['arch'])

		# Use arch as build label
		cfg_dict['build']['build_label'] = cfg_dict['build']['arch']

		# Get optimization flags for arch
		try:
			cfg_dict['build']['opt_flags'] = arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']]
		except:
			exception.print_warning(logger, "No default optimization flags for " + cfg_dict['build']['arch'] + " found in " + gs.arch_cfg_file + " for compiler type '" + cfg_dict['build']['compiler_type'] + "'")
			cfg_dict['build']['opt_flags'] = ""

	# Generate default build path if one is not defined
	if not cfg_dict['general']['build_prefix']:
		cfg_dict['general']['working_path'] = gs.build_path + gs.sl + cfg_dict['general']['system'] + gs.sl + common.get_label(cfg_dict['modules']['compiler']) + gs.sl + \
			common.get_label(cfg_dict['modules']['mpi']) + gs.sl + cfg_dict['general']['code'] + gs.sl + cfg_dict['build']['build_label'] + gs.sl + cfg_dict['general']['version']
	# Translate 'build_prefix' to 'working_path' for better readability
	else:
		cfg_dict['general']['working_path'] = cfg_dict['general']['build_prefix']
	
	# Get build and install subdirs
	cfg_dict['general']['build_path']   = cfg_dict['general']['working_path'] + gs.sl + gs.build_subdir
	cfg_dict['general']['install_path'] = cfg_dict['general']['working_path'] + gs.sl + gs.install_subdir

# Check bench config file and add required fields
def process_bench_cfg(cfg_dict):

	# Check for missing essential parameters
	check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'nodes')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'ranks_per_node')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'threads')

	check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench', 'exe')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench', 'dataset')

	check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'result')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'method')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'unit')

	# Instantiate missing optional parameters
	if not 'template' in 	cfg_dict['bench'].keys():	cfg_dict['bench']['template']	= ""
	if not 'collect_hw' in 	cfg_dict['bench'].keys():	cfg_dict['bench']['collect_hw']	= ""

	# Handle comma-delimited lists
	cfg_dict['sched']['nodes'] = cfg_dict['sched']['nodes'].split(",")

	# Check result validation inputs
	
	# Expression method
	if cfg_dict['result']['method'] == "regex":
		if not 'expr' in cfg_dict['result']:
			exception.error_and_quit(logger, "if using 'regex' result validation method, 'expr' key is required in [result] section of " + common.rel_path(cfg_dict['metadata']['cfg_file']))
	# Script method
	elif cfg_dict['result']['method'] == "script":
		if not 'script' in cfg_dict['result']:
			exception.error_and_quit(logger, "if using 'script' result validation method, 'script' key is required in [result] section of " + common.rel_path(cfg_dict['metadata']['cfg_file']))
	# 'method' not == 'regex' or 'script'
	else:
		exception.error_and_quit(logger, "'method' key in [result] section of " + cfg_dict['metadata']['cfg_file'] + "must be either regex or script." )
	# Add output filename from settings.cfg
	cfg_dict['bench']['output_file'] = gs.output_file

	# Default hardware collection to False if not set
	if not 'collect_hw' in cfg_dict['bench']:
		cfg_dict['bench']['collect_hw'] = False

# Check sched config file and add required fields
def process_sched_cfg(cfg_dict):

	# Check for missing essential parameters
	check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'type')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'queue')
	check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'account')

	# Fill missing parameters
	if not cfg_dict['sched']['runtime']:
		cfg_dict['sched']['runtime'] = '02:00:00'
		logger.debug("Set runtime = " + cfg_dict['sched']['runtime'])
	if not cfg_dict['sched']['threads']:
		cfg_dict['sched']['threads'] = 4
		logger.debug("Set threads = " + cfg_dict['sched']['threads'])

# Read input param config and test 
def get_cfg(cfg_type, cfg_name, settings,  log_to_use):

	global logger, gs, common 
	logger = log_to_use
	gs = settings
	common = common_funcs.init(gs)

	# Check input file exists
	cfg_file = check_file(cfg_type, cfg_name)
	# Parse input fo;e
	cfg_dict = read_cfg_file(cfg_file)

	# Start processing function for cfg type
	if cfg_type == 'build':
		logger.debug("Starting build cfg processing.")
		process_build_cfg(cfg_dict)
	elif cfg_type == 'bench':
		logger.debug("Starting bench cfg processing.")
		process_bench_cfg(cfg_dict)
	elif cfg_type == 'sched':
		logger.debug("Starting sched cfg processing.")
		process_sched_cfg(cfg_dict)

	return cfg_dict
