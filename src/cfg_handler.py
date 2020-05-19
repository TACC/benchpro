# System Imports
import configparser as cp
import os
import sys

import src.exception as exception

sl                  = "/"
base_dir            = sl.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1])
configs_dir         = "config"
code_cfg_dir        = "codes"
sched_cfg_dir       = "sched"
system_cfg_file     = "system.cfg"
arch_cfg_file       = "architecture_defaults.cfg"

# Check cfg file exists
def check_file(cfg_type, cfg_name, exception_logger):
    if not ".cfg" in cfg_name:
        cfg_name += ".cfg"

    subdir = ''
    if   cfg_type == 'code' : subdir = code_cfg_dir
    elif cfg_type == 'sched': subdir = sched_cfg_dir

    cfg_path = base_dir + sl

    if not os.path.isfile(cfg_path+cfg_name):
        cfg_path += configs_dir + sl

    if not os.path.isfile(cfg_path+cfg_name):
        cfg_path += subdir + sl

    if not os.path.isfile(cfg_path+cfg_name):
        exception.error_and_quit(exception_logger, "Input file \""+cfg_name+"\" not found.")

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

# Convert module name to directory name
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]
    return label

# Check the contents of code input cfg file for issues
def check_code_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger):
    # Check for missing essential parameters in general section
    if not cfg_dict['general']['code'] or not cfg_dict['general']['version'] or not cfg_dict['general']['system']:
        exception.error_and_quit(exception_logger, "Missing parameter detected in "+ cfg_dict['metadata']['cfg_file'] + "\n Please ensure at least 'code', 'version' and 'system' are defined in the [general] section.")

    # Check for conflicting parameter combinations
    if not use_default_paths and not cfg_dict['general']['build_prefix']:
        exception.error_and_quit(exception_logger, "use_default_paths=False in settings.cfg but build_prefix not set in "+ cfg_dict['metadata']['cfg_file'])

    if use_default_paths and cfg_dict['general']['build_prefix']:
        exception.error_and_quit(exception_logger, "use_default_paths=True in settings.cfg but build_prefix is set in"+ cfg_dict['metadata']['cfg_file'])

    system_file = check_file('system', configs_dir+sl+system_cfg_file, exception_logger)
    system_dict = read_cfg_file(system_file, exception_logger)

    arch_file = check_file('arch', configs_dir+sl+arch_cfg_file, exception_logger)
    arch_dict = read_cfg_file(arch_file, exception_logger)


    # Extract compiler type
    cfg_dict['build']['compiler_type']   = cfg_dict['modules']['compiler'].split('/')[0]

    # Get core count for given system
    try:
        cfg_dict['build']['cores'] = system_dict[cfg_dict['general']['system']]['cores']
    except:
        exception.error_and_quit(exception_logger, "System profile '"+cfg_dict['general']['system']+"' missing in "+configs_dir+sl+system_cfg_file)

    # If system default arch provided, get system default
    if cfg_dict['build']['arch'] == 'system':
        cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']


    # If using custom opt flags
    if cfg_dict['build']['opt_flags']:
        # If arch is defined
        if cfg_dict['build']['arch']:
            # If label is not provided
            if not cfg_dict['build']['opt_label']:
                cfg_dict['build']['opt_label'] = cfg_dict['build']['arch'] + "-modified"             

            # Add custom opts to arch opts
            try:
                cfg_dict['build']['opt_flags'] = "'" + cfg_dict['build']['opt_flags'].replace('"', '').replace('\'', '') + " " + arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']].replace('\'', '') + "'"
            except:
                exception.error_and_quit(exception_logger, "No default optimization flags for "+cfg_dict['build']['arch']+" found in "+arch_cfg_file)

            build_logger.debug("WARNING: An archicture '"+cfg_dict['build']['arch']+"' and custom optimization flags '"+cfg_dict['build']['opt_flags']+"' have both been defined.")
            build_logger.debug("WARNING: Setting compile flags to: "+cfg_dict['build']['opt_flags'])
        # If arch not defined
        else:
            if not cfg_dict['build']['opt_label']:
                exception.error_and_quit(exception_logger, "When using custom optimization flags 'opt_flags' in "+cfg_dict['metadata']['cfg_file']+", you need to provide a build label 'opt_label'.")
    # If not using custom opt flags
    else:
        # If arch not defined, use system default arch
        if not cfg_dict['build']['arch']:
            cfg_dict['build']['arch'] = system_dict[cfg_dict['general']['system']]['default_arch']
            build_logger.debug("WARNING: no architecture defined in "+cfg_dict['metadata']['cfg_file'])
            build_logger.debug("WARNING: using default system arch for "+cfg_dict['general']['system']+": "+cfg_dict['build']['arch'])

        # Use arch as build label
        cfg_dict['build']['opt_label'] = cfg_dict['build']['arch']

        # Get optimization flags for arch
        try:
            cfg_dict['build']['opt_flags'] = arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']]
        except:
            exception.error_and_quit(exception_logger, "No default optimization flags for "+cfg_dict['build']['arch']+" found in "+arch_cfg_file)

    
    # Generate default build path if on is not defined
    if not cfg_dict['general']['build_prefix']:
        cfg_dict['general']['build_prefix'] = base_dir + sl + "build" + sl + cfg_dict['general']['system'] + sl + get_label(cfg_dict['modules']['compiler']) + sl + get_label(cfg_dict['modules']['mpi']) + sl  + cfg_dict['general']['code'] + sl + cfg_dict['build']['opt_label'] + sl + cfg_dict['general']['version']

    return cfg_dict

# Check the contents of schede input cfg file for issues
def check_sched_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger):
    # Check for missing essential parameters in general section
    if not cfg_dict['scheduler']['type'] or not cfg_dict['scheduler']['queue'] or not cfg_dict['scheduler']['account']:
        exception.error_and_quit(exception_logger, "Missing parameter detected in "+ cfg_dict['metadata']['cfg_file']+ "\n Please ensure at least 'type', 'queue' and 'account' are defined in the [scheduler] section.")

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

    if cfg_type == 'code':    
        check_code_cfg_contents (cfg_dict, use_default_paths, build_logger, exception_logger)
    elif cfg_type == 'sched': 
        check_sched_cfg_contents(cfg_dict, use_default_paths, build_logger, exception_logger)

    return cfg_dict
