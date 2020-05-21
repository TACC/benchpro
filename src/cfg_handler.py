# System Imports
import configparser as cp
import os
import sys

import src.exception as exception
import src.global_settings as gs

logger = ''

# Check cfg file exists


def check_file(cfg_type, cfg_name, logger):
    # Format cfg filename
    suffix = ''
    subdir = ''

    cfg_path = gs.cwd + gs.sl
    # First check in user's $PWD
    if os.path.isfile(cfg_path + cfg_name):
        return cfg_path + cfg_name

    # Then check in project base_dir
    cfg_path = gs.base_dir + gs.sl
    if os.path.isfile(cfg_path + cfg_name):
        return cfg_path + cfg_name

    # Then reformat to expected naming convention and look in .config/
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

    cfg_path = gs.base_dir + gs.sl + gs.configs_dir + gs.sl + subdir + gs.sl

    if not os.path.isfile(cfg_path + cfg_name):
        exception.error_and_quit(
            logger, "Input file \"" + cfg_name + "\" not found.")

    return cfg_path + cfg_name

# Read cfg file into dict


def read_cfg_file(cfg_file, logger):
    cfg_parser = cp.RawConfigParser()
    cfg_parser.read(cfg_file)

    cfg_dict = {'metadata': {'cfg_file': cfg_file}}
    for section in cfg_parser.sections():
        cfg_dict[section] = {}
        for value in cfg_parser.options(section):
            cfg_dict[section][value] = cfg_parser.get(section, value)

    return cfg_dict

# Convert module name to directory name


def get_label(compiler):
    label = compiler
    if compiler.count(gs.sl) > 0:
        comp_ver = compiler.split(gs.sl)
        label = comp_ver[0] + comp_ver[1].split(".")[0]
    return label

# Parse the contents of build cfg file, add metadata and check for issues


def process_build_cfg(cfg_dict, logger):

    # Insert 1 node for build
    cfg_dict['build']['ranks'] = "1"

    # Get system from env if not defined
    if not cfg_dict['general']['system']:
        logger.debug("WARNING: system not defined in '" +
                     cfg_dict['metadata']['cfg_file'] + "', getting system label from $TACC_SYSTEM: " + str(os.getenv('TACC_SYSTEM')))
        cfg_dict['general']['system'] = str(os.getenv('TACC_SYSTEM'))
        print(cfg_dict['general']['system'])

    # Check for missing essential parameters in general section
    if not cfg_dict['general']['code'] or not cfg_dict['general']['version']:
        exception.error_and_quit(logger, "Missing parameter detected in " +
                                 cfg_dict['metadata']['cfg_file'] + "\n Please ensure at least 'code', 'version' and 'system' are defined in the [general] section.")

    # Check for conflicting parameter combinations
    if not gs.use_default_paths and not cfg_dict['general']['build_prefix']:
        exception.error_and_quit(
            logger, "use_default_paths=False in settings.cfg but build_prefix not set in " + cfg_dict['metadata']['cfg_file'])

    if gs.use_default_paths and cfg_dict['general']['build_prefix']:
        exception.error_and_quit(
            logger, "use_default_paths=True in settings.cfg but build_prefix is set in" + cfg_dict['metadata']['cfg_file'])

    system_file = check_file('system', gs.configs_dir +
                             gs.sl + gs.system_cfg_file, logger)
    system_dict = read_cfg_file(system_file, logger)

    arch_file = check_file('arch', gs.configs_dir +
                           gs.sl + gs.arch_cfg_file, logger)
    arch_dict = read_cfg_file(arch_file, logger)

    # Extract compiler type
    cfg_dict['build']['compiler_type'] = cfg_dict['modules']['compiler'].split(
        '/')[0]

    # Get core count for given system
    try:
        cfg_dict['build']['cores'] = system_dict[cfg_dict['general']
                                                 ['system']]['cores']
    except:
        exception.error_and_quit(logger, "System profile '" +
                                 cfg_dict['general']['system'] + "' missing in " + configs_dir + gs.sl + gs.system_cfg_file)

    # If system default arch provided, get system default
    if cfg_dict['build']['arch'] == 'system':
        cfg_dict['build']['arch'] = system_dict[cfg_dict['general']
                                                ['system']]['default_arch']

    # If using custom opt flags
    if cfg_dict['build']['opt_flags']:
        # If arch is defined
        if cfg_dict['build']['arch']:
            # If label is not provided
            if not cfg_dict['build']['opt_label']:
                cfg_dict['build']['opt_label'] = cfg_dict['build']['arch'] + "-modified"

            # Add custom opts to arch opts
            try:
                cfg_dict['build']['opt_flags'] = "'" + cfg_dict['build']['opt_flags'].replace('"', '').replace(
                    '\'', '') + " " + arch_dict[cfg_dict['build']['arch']][cfg_dict['build']['compiler_type']].replace('\'', '') + "'"
            except:
                exception.error_and_quit(logger, "No default optimization flags for " +
                                         cfg_dict['build']['arch'] + " found in " + arch_cfg_file)

            logger.debug("WARNING: An archicture '" + cfg_dict['build']['arch'] +
                         "' and custom optimization flags '" + cfg_dict['build']['opt_flags'] + "' have both been defined.")
            logger.debug("WARNING: Setting compile flags to: " +
                         cfg_dict['build']['opt_flags'])
        # If arch not defined
        else:
            if not cfg_dict['build']['opt_label']:
                exception.error_and_quit(logger, "When using custom optimization flags 'opt_flags' in " +
                                         cfg_dict['metadata']['cfg_file'] + ", you need to provide a build label 'opt_label'.")
    # If not using custom opt flags
    else:
        # If arch not defined, use system default arch
        if not cfg_dict['build']['arch']:
            cfg_dict['build']['arch'] = system_dict[cfg_dict['general']
                                                    ['system']]['default_arch']
            logger.debug("WARNING: no architecture defined in " +
                         cfg_dict['metadata']['cfg_file'])
            logger.debug("WARNING: using default system arch for " +
                         cfg_dict['general']['system'] + ": " + cfg_dict['build']['arch'])

        # Use arch as build label
        cfg_dict['build']['opt_label'] = cfg_dict['build']['arch']

        # Get optimization flags for arch
        try:
            cfg_dict['build']['opt_flags'] = arch_dict[cfg_dict['build']
                                                       ['arch']][cfg_dict['build']['compiler_type']]
        except:
            exception.error_and_quit(logger, "No default optimization flags for " +
                                     cfg_dict['build']['arch'] + " found in " + arch_cfg_file)

    # Generate default build path if on is not defined
    if not cfg_dict['general']['build_prefix']:
        cfg_dict['general']['build_prefix'] = gs.base_dir + gs.sl + "build" + gs.sl + cfg_dict['general']['system'] + gs.sl + get_label(cfg_dict['modules']['compiler']) + gs.sl + get_label(
            cfg_dict['modules']['mpi']) + gs.sl + cfg_dict['general']['code'] + gs.sl + cfg_dict['build']['opt_label'] + gs.sl + cfg_dict['general']['version']

    return cfg_dict

# Parse the contents of run cfg file, add metadata and check for issues


def process_run_cfg(cfg_dict, logger):
    print()

# Parse the contents of sched cfg file, add metadata and check for issues


def process_sched_cfg(cfg_dict, logger):

    # Check for missing essential parameters in general section
    if not cfg_dict['scheduler']['type'] or not cfg_dict['scheduler']['queue'] or not cfg_dict['scheduler']['account']:
        exception.error_and_quit(logger, "Missing parameter detected in " +
                                 cfg_dict['metadata']['cfg_file'] + "\n Please ensure at least 'type', 'queue' and 'account' are defined in the [scheduler] section.")

    # Fill missing parameters
    if not cfg_dict['scheduler']['job_label']:
        cfg_dict['scheduler']['job_label'] = 'builder'
    if not cfg_dict['scheduler']['runtime']:
        cfg_dict['scheduler']['runtime'] = '02:00:00'
    if not cfg_dict['scheduler']['job_label']:
        cfg_dict['scheduler']['threads'] = 4

    return cfg_dict


def get_cfg(cfg_type, cfg_name,  log_to_use):

    global logger
    logger = log_to_use

    cfg_file = check_file(cfg_type, cfg_name, logger)
    cfg_dict = read_cfg_file(cfg_file, logger)

    # Start the appropriate processing function for cfg type
    if cfg_type == 'build':
        process_build_cfg(cfg_dict, logger)
    elif cfg_type == 'run':
        process_run_cfg(cfg_dict, logger)
    elif cfg_type == 'sched':
        process_sched_cfg(cfg_dict, logger)

    return cfg_dict
