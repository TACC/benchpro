
# System Imports
import configparser as cp
import os
import sys


sl                  = "/"
configs_dir         = "cfgs"


# Check cfg file exists
def check_cmd_cfgs(cfg, logger):

    if not ".cfg" in cfg:
        cfg += ".cfg"

    if not os.path.isfile(cfg):
        cfg = "." + sl + configs_dir + sl + cfg
        if not os.path.isfile(cfg):
            logger.debug("ERROR: Input file \"" + cfg + "\" not found.")
            logger.debug("Exitting")

    return cfg

# Read cfg file into dict
def read_cfg_file(cfg, logger):

    cfg_parser = cp.RawConfigParser()
    cfg_parser.read(check_cmd_cfgs(cfg, logger))

    cfg_dict = {'metadata': {'cfg_file' : cfg}}
    for section in cfg_parser.sections():
        cfg_dict[section] = {}
        for value in cfg_parser.options(section):
            cfg_dict[section][value] = cfg_parser.get(section, value)

    return cfg_dict

def check_code_cfg(cfg_dict, use_default_paths, logger):

    if not use_default_paths and not cfg_dict['general']['build_prefix']:
        logger.debug("ERROR: use_default_paths=False in settings.cfg but build_prefix not set in "+ cfg_dict['metadata']['cfg_file'])
        logger.debug("Exitting")
        sys.exit(1)

    if use_default_paths and cfg_dict['general']['build_prefix']:
        logger.debug("ERROR: use_default_paths=True in settings.cfg but build_prefix is set in"+ cfg_dict['metadata']['cfg_file'])
        logger.debug("Exitting")
        sys.exit(1)

    return cfg_dict

def check_sched_cfg(cfg_dict, use_default_paths, logger):
    return cfg_dict

