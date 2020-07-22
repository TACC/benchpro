# System Imports
import configparser as cp
import glob as gb
import os
import re
import subprocess
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception
import src.input_handler as input_handler

glob = common = None

# Search for unique cfg file in cfg dir
def search_cfg_str(cfg_name, search_path):

    if os.path.isdir(search_path):

        glob.log.debug("Looking for " + cfg_name + " in " + common.rel_path(search_path) + "...")
        matches = gb.glob(search_path + glob.stg['sl'] + "*" + cfg_name + "*")

        if len(matches) == 1:
            glob.log.debug("Found")
            return matches[0]

        elif len(matches) > 1:
            print("Multiple input config files matching '" + cfg_name + "' found in " + common.rel_path(search_path) + ":")
            for match in matches:
                print("  " + match.split('/')[-1])
            
            exception.error_and_quit(glob.log, "please provide unique input config label.")

    return None

# Check cfg file exists
def check_file(cfg_type, cfg_name):
    suffix = None
    subdir = None

    # 1: check if provided cfg_name is a file
    if os.path.isfile(cfg_name):
        glob.log.debug("Found")
        return cfg_name

    # 2: check for file in user's CWD
    search_path = glob.cwd + glob.stg['sl']
    glob.log.debug("Looking for " + cfg_name + " in " + search_path + "...")
    if os.path.isfile(search_path + cfg_name):
        glob.log.debug("Found")
        return search_path + cfg_name

    # 3: check in project basedir
    search_path = glob.basedir + glob.stg['sl']
    glob.log.debug("Looking for " + cfg_name + " in " + common.rel_path(search_path) + "...")
    if os.path.isfile(search_path + cfg_name):
        glob.log.debug("Found")
        return search_path + cfg_name

    # 4 Search cfg dir
    search_path = glob.stg['config_path'] + glob.stg['sl'] 
    glob.log.debug("Looking for " + cfg_name + " in " + common.rel_path(search_path) + "...")
    if os.path.isfile(search_path + cfg_name):
        glob.log.debug("Found")
        return search_path + cfg_name

    # 5: Search 'type' subdir
    search_path = search_path + cfg_type + glob.stg['sl']
    cfg_file = search_cfg_str(cfg_name, search_path)
    if cfg_file:
        return cfg_file

    # 6. Seach system subdir 
    search_path = search_path + glob.system + glob.stg['sl']
    cfg_file = search_cfg_str(cfg_name, search_path)
    if cfg_file:
        return cfg_file

    # Not found
    handler = input_handler.init(glob)
    handler.show_available()

    exception.error_and_quit(glob.log, "input cfg file for '" + common.rel_path(cfg_name) + "' not found.")

# Parse cfg file into dict
def read_cfg_file(cfg_file):
    cfg_parser = cp.ConfigParser()
    cfg_parser.optionxform=str
    cfg_parser.read(cfg_file)

    # Add file name & label to dict
    cfg_label = cfg_file.split(glob.stg['sl'])[-1][:-10]
    
    cfg_dict = {}
    cfg_dict['metadata'] ={}

    cfg_dict['metadata']['cfg_label'] = cfg_label
    cfg_dict['metadata']['cfg_file']  = cfg_file

    for section in cfg_parser.sections():
        cfg_dict[section] = {}
        for value in cfg_parser.options(section):
            cfg_dict[section][value] = cfg_parser.get(section, value)

    # Overload cfg params with cmd line args
    common.overload_params(cfg_dict)

    return cfg_dict

# Error if section heading missing in cfg file
def check_dict_section(cfg_file, cfg_dict, section):
    if not section in cfg_dict:
        exception.error_and_quit(glob.log, "["+section+"] section heading required in " + common.rel_path(cfg_file) + ". Consult the documentation.")

# Error if value missing in cfg file
def check_dict_key(cfg_file, cfg_dict, section, key):
    # If key not found 
    if not key in cfg_dict[section]:
        exception.error_and_quit(glob.log, "'" + key + "' value must be present in section [" + section + "] in " + common.rel_path(cfg_file) + ". Consult the documentation.")
    # If key not set
    if not cfg_dict[section][key]:
        exception.error_and_quit(glob.log, "'" + key + "' value must be non-null in section [" + section + "] in " + common.rel_path(cfg_file) + ". Consult the documentation.")

# Check build config file and add required fields
def process_build_cfg(cfg_dict):

    # Check for missing essential parameters 
    check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'general')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'code')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'version')

    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'compiler')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'mpi')

    # Instantiate missing optional parameters
    if not 'system'           in cfg_dict['general'].keys():  cfg_dict['general']['system']         = ""
    if not 'build_prefix'     in cfg_dict['general'].keys():  cfg_dict['general']['build_prefix']   = ""
    if not 'template'         in cfg_dict['general'].keys():  cfg_dict['general']['template']       = ""
    if not 'module_use'       in cfg_dict['general'].keys():  cfg_dict['general']['module_use']     = ""

    if not 'exe'              in cfg_dict['build'].keys():    cfg_dict['build']['exe']              = ""
    if not 'arch'             in cfg_dict['build'].keys():    cfg_dict['build']['arch']             = ""
    if not 'opt_flags'        in cfg_dict['build'].keys():    cfg_dict['build']['opt_flags']        = ""  
    if not 'build_label'      in cfg_dict['build'].keys():    cfg_dict['build']['build_label']      = ""
    if not 'bin_dir'          in cfg_dict['build'].keys():    cfg_dict['build']['bin_dir']          = ""
    if not 'collect_hw_stats' in cfg_dict['build'].keys():    cfg_dict['build']['collect_hw_stats'] = False

    # Extract compiler type from label by splitting by / and removing ints
    cfg_dict['build']['compiler_type'] = re.sub("\d", "", cfg_dict['modules']['compiler'].split('/')[0])

    # Insert 1 node for build job
    cfg_dict['build']['nodes'] = "1"
    # Path to application's data directory
    cfg_dict['build']['benchmark_repo'] = glob.stg['benchmark_repo']

    # Get system from env if not defined
    if not cfg_dict['general']['system']:
        exception.print_warning(glob.log, "'system' not defined in " + common.rel_path(cfg_dict['metadata']['cfg_file']))
        exception.print_warning(glob.log, "getting system label from $TACC_SYSTEM: " + str(os.getenv('TACC_SYSTEM')))
        cfg_dict['general']['system'] = str(os.getenv('TACC_SYSTEM'))
        if not cfg_dict['general']['system']:
            exception.error_and_quit(glob.log, "$TACC_SYSTEM not set, unable to continue. Please define 'system' in " + common.rel_path(cfg_dict['metadata']['cfg_file']))

    # Check requested modules exist, and if so, result full module names
    common.check_module_exists(cfg_dict['modules'], cfg_dict['general']['module_use'])

    # Parse system info config file 
    system_file = check_file('system', glob.stg['config_path'] + glob.stg['sl'] + glob.stg['system_cfg_file'])
    system_dict = read_cfg_file(system_file)

    # Parse architecture defaults config file 
    arch_file = check_file('arch', glob.stg['config_path'] + glob.stg['sl'] + glob.stg['arch_cfg_file'])
    arch_dict = read_cfg_file(arch_file)

    # Get core count for system
    try:
        cfg_dict['build']['cores'] = system_dict[cfg_dict['general']['system']]['cores']
        glob.log.debug("Core count for " + cfg_dict['general']['system'] + " = " + cfg_dict['build']['cores'])

    except:
        exception.error_and_quit(glob.log, "system profile '" + cfg_dict['general']['system'] + "' missing in " + common.rel_path(system_file))

    # If arch requested = 'system', get default arch for this system
    if cfg_dict['build']['arch'] == 'default' or not cfg_dict['build']['arch']:
        cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
        glob.log.debug("Requested build arch='default'. Using system default for " + cfg_dict['general']['system'] + " = " + cfg_dict['build']['arch'])

    # If using custom opt_flags, must provide build_label
    if cfg_dict['build']['opt_flags'] and not cfg_dict['build']['build_label']:
        exception.error_and_quit(glob.log, "if building with custom optimization flags, please define a 'build_label in [build] section of " + common.rel_path(cfg_dict['metadata']['cfg_file']))

    # Set default build label
    if not cfg_dict['build']['build_label']:
        cfg_dict['build']['build_label'] = 'default'

    # Generate default build path if one is not defined
    if not cfg_dict['general']['build_prefix']:
        cfg_dict['general']['working_path'] = glob.stg['build_path'] + glob.stg['sl'] + cfg_dict['general']['system'] + glob.stg['sl'] + cfg_dict['build']['arch'] + glob.stg['sl'] + \
                                              common.get_module_label(cfg_dict['modules']['compiler']) + glob.stg['sl'] + common.get_module_label(cfg_dict['modules']['mpi']) + glob.stg['sl'] + \
                                              cfg_dict['general']['code'] + glob.stg['sl'] + cfg_dict['general']['version'] + glob.stg['sl'] + cfg_dict['build']['build_label']

    # Translate 'build_prefix' to 'working_path' for better readability
    else:
        cfg_dict['general']['working_path'] = cfg_dict['general']['build_prefix']
    
    # Get build and install subdirs
    cfg_dict['general']['build_path']   = cfg_dict['general']['working_path'] + glob.stg['sl'] + glob.stg['build_subdir']
    cfg_dict['general']['install_path'] = cfg_dict['general']['working_path'] + glob.stg['sl'] + glob.stg['install_subdir']

# Check bench config file and add required fields
def process_bench_cfg(cfg_dict):

    # Check for missing essential parameters
    check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'nodes')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'threads')

    check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench', 'exe')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'bench', 'dataset')

    check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'result')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'method')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'unit')

    # Instantiate missing optional parameters
    if not 'ranks_per_node'     in cfg_dict['sched'].keys():  cfg_dict['sched']['ranks_per_node']    = 0
    if not 'max_running_jobs'   in cfg_dict['sched'].keys():  cfg_dict['sched']['max_running_jobs']  = 10
    if not 'template'           in cfg_dict['bench'].keys():  cfg_dict['bench']['template']          = ""
    if not 'collect_hw_stats'   in cfg_dict['bench'].keys():  cfg_dict['bench']['collect_hw_stats']  = False
    if not 'description'        in cfg_dict['result'].keys():  cfg_dict['result']['description']     = ""

    # Handle comma-delimited lists
    cfg_dict['sched']['nodes'] = cfg_dict['sched']['nodes'].split(",")

    # Get system default ranks per core, if not defined
    if not cfg_dict['sched']['ranks_per_node']:
        system_file = check_file('system', glob.stg['config_path'] + glob.stg['sl'] + glob.stg['system_cfg_file'])    
        system_dict = read_cfg_file(system_file)
        try:
            cfg_dict['sched']['ranks_per_node'] = system_dict[str(os.getenv('TACC_SYSTEM'))]['cores']
        except:
            exception.error_and_quit(glob.log, "unable to read TACC_SYSTEM variable to determine default cores per node, please define in [sched] section of" + common.rel_path(cfg_dict['metadata']['cfg_file']))

    # Check result validation inputs
    
    # Expression method
    if cfg_dict['result']['method'] == "regex":
        if not 'expr' in cfg_dict['result']:
            exception.error_and_quit(glob.log, "if using 'regex' result validation method, 'expr' key is required in [result] section of " + common.rel_path(cfg_dict['metadata']['cfg_file']))
    # Script method
    elif cfg_dict['result']['method'] == "script":
        if not 'script' in cfg_dict['result']:
            exception.error_and_quit(glob.log, "if using 'script' result validation method, 'script' key is required in [result] section of " + common.rel_path(cfg_dict['metadata']['cfg_file']))
    # 'method' not == 'regex' or 'script'
    else:
        exception.error_and_quit(glob.log, "'method' key in [result] section of " + cfg_dict['metadata']['cfg_file'] + "must be either regex or script." )
    # Add output filename from settings.cfg
    cfg_dict['bench']['output_file'] = glob.stg['output_file']

# Check sched config file and add required fields
def process_sched_cfg(cfg_dict):

    # Check for missing essential parameters
    check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'type')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'queue')
    check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'account')

    # Instantiate missing optional parameters
    if not 'reservation' in    cfg_dict['sched'].keys():   cfg_dict['sched']['reservation']   = ""

    # Fill missing parameters
    if not cfg_dict['sched']['runtime']:
        cfg_dict['sched']['runtime'] = '02:00:00'
        glob.log.debug("Set runtime = " + cfg_dict['sched']['runtime'])
    if not cfg_dict['sched']['threads']:
        cfg_dict['sched']['threads'] = 4
        glob.log.debug("Set threads = " + cfg_dict['sched']['threads'])

# Read input param config and test 
def ingest_cfg(cfg_type, cfg_name, glob_obj):

    global glob, common 
    glob = glob_obj
    common = common_funcs.init(glob)

    # Check input file exists
    cfg_file = check_file(cfg_type, cfg_name)
    # Parse input fo;e
    cfg_dict = read_cfg_file(cfg_file)

    # Process and store build cfg 
    if cfg_type == 'build':
        glob.log.debug("Starting build cfg processing.")
        process_build_cfg(cfg_dict)
        glob.code = cfg_dict

    # Process and store bench cfg 
    elif cfg_type == 'bench':
        glob.log.debug("Starting bench cfg processing.")
        process_bench_cfg(cfg_dict)
        glob.code = cfg_dict

    # Process and store sched cfg 
    elif cfg_type == 'sched':
        glob.log.debug("Starting sched cfg processing.")
        process_sched_cfg(cfg_dict)
        glob.sched = cfg_dict

    # Process and store compiler cfg 
    elif cfg_type == 'compiler':
        glob.compiler = cfg_dict


