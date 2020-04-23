
# System Imports
import configparser as cp
import os
import sys

sl                  = "/"

configs_dir         = "config"
code_cfg_dir        = "codes"
sched_cfg_dir       = "sched"

system_cfg_file     = "system.cfg"

# Check cfg file exists
def check_file(cfg_type, cfg_name, exception_logger):

    if not ".cfg" in cfg_name:
        cfg_name += ".cfg"

    subdir = ''
    if   cfg_type == 'code' : subdir = code_cfg_dir
    elif cfg_type == 'sched': subdir = sched_cfg_dir

    cfg_path = "./"

    print(cfg_path+cfg_name)
    if not os.path.isfile(cfg_path+cfg_name):
        cfg_path += configs_dir + sl

    print(cfg_path+cfg_name)
    if not os.path.isfile(cfg_path+cfg_name):
        cfg_path += subdir + sl

    print(cfg_path+cfg_name)
    if not os.path.isfile(cfg_path+cfg_name):
        exception_logger.debug("ERROR: Input file \"" + cfg_name + "\" not found.")
        exception_logger.debug("Exitting")
        sys.exit(1)

    return cfg_path+cfg_name

# Read cfg file into dict
def read_cfg_file(cfg_file, exception_logger):

    cfg_parser = cp.RawConfigParser()
    cfg_parser.read(cfg_file)

    cfg_dict = {'metadata': {'cfg_file' : cfg_file}}
    for section in cfg_parser.sections():
        cfg_dict[section] = {}
        for value in cfg_parser.options(section):
            cfg_dict[section][value] = cfg_parser.get(section, value)

    return cfg_dict

# Check the contents of code input cfg file for issues
def check_code_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger):

    # Check for missing essential parameters in general section
    if not cfg_dict['general']['code'] or not cfg_dict['general']['version'] or not cfg_dict['general']['system']:
        exception_logger.debug("ERROR: Missing parameter detected in "+ cfg_dict['metadata']['cfg_file'])
        exception_logger.debug("ERROR: Please ensure at least 'code', 'version' and 'system' are defined in the [general] section.")
        exception_logger.debug("Exitting")

        sys.exit(1)

    # Check for conflicting parameter combinations
    if not use_default_paths and not cfg_dict['general']['build_prefix']:
        exception_logger.debug("ERROR: use_default_paths=False in settings.cfg but build_prefix not set in "+ cfg_dict['metadata']['cfg_file'])
        exception_logger.debug("Exitting")
        sys.exit(1)

    if use_default_paths and cfg_dict['general']['build_prefix']:
        exception_logger.debug("ERROR: use_default_paths=True in settings.cfg but build_prefix is set in"+ cfg_dict['metadata']['cfg_file'])
        exception_logger.debug("Exitting")
        sys.exit(1)

    # Fill missing parameters
    system_file = check_file('system', configs_dir+sl+system_cfg_file, exception_logger)
    system_dict = read_cfg_file(system_file, exception_logger)

    try:
        cfg_dict['build']['cores'] = system_dict[cfg_dict['general']['system']]['cores']

        if not cfg_dict['build']['arch']:
            cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
            build_logger.debug("WARNING: no architecture defined in "+cfg_dict['metadata']['cfg_file'])
            build_logger.debug("WARNING: using default system arch for "+cfg_dict['general']['system']+": "+cfg_dict['build']['arch'])

    except:
        exception_logger.debug("ERROR: System profile '"+cfg_dict['general']['system']+"' missing in "+configs_dir+sl+system_cfg_file)
        exception_logger.debug("Exitting")
        sys.exit(1)

    return cfg_dict

# Check the contents of schede input cfg file for issues
def check_sched_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger):

    # Check for missing essential parameters in general section
    if not cfg_dict['scheduler']['type'] or not cfg_dict['scheduler']['queue'] or not cfg_dict['scheduler']['account']:
        exception_logger.debug("ERROR: Missing parameter detected in "+ cfg_dict['metadata']['cfg_file'])
        exception_logger.debug("Please ensure at least 'type', 'queue' and 'account' are defined in the [scheduler] section.")
        sys.exit(1)

    # Fill missing parameters
    if not cfg_dict['scheduler']['job_label']:
        cfg_dict['scheduler']['job_label'] = 'builder'
    if not cfg_dict['scheduler']['runtime']:
        cfg_dict['scheduler']['runtime'] = '02:00:00'
    if not cfg_dict['scheduler']['job_label']:
        cfg_dict['scheduler']['threads'] = 4

    return cfg_dict

def get_cfg(cfg_type, cfg_name, use_default_paths, build_logger, exception_logger):

    cfg_file = check_file(cfg_type, cfg_name, exception_logger)
    cfg_dict = read_cfg_file(cfg_file, exception_logger)

    if cfg_type == 'code':    check_code_cfg_contents (cfg_dict, use_default_paths, build_logger, exception_logger)
    elif cfg_type == 'sched': check_sched_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger)

    return cfg_dict
