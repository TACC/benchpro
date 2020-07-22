# System Imports
import configparser 
from datetime import datetime
import os
import socket
import sys

# Global constants
class settings(object):

    # Context variables
    user                = str(os.getlogin())
    hostname            = str(socket.gethostname())
    if ("." in hostname):
        hostname        = '.'.join(map(str, hostname.split('.')[0:2]))

    # Chicken & egg situation with 'sl' here - hardcoded 
    basedir             = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
    time_str            = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    cwd                 = os.getcwd()

    #----------------------------settings.cfg--------------------------------

    # Check for empty params and datatypes in settings.cfg
    def process(key, value):
        optional = ['user',
                    'key',
                    'django_static_dir',
                    'server_dir']

        if key not in optional and not value:
            print("Missing value for key '" + key + "' in settings.cfg, check the documentation.")
            sys.exit(2)

        # Test if True
        elif value == "True":
            return True

        # Test if False
        elif value == "False":
            return False

        # Test if int
        elif value.isdigit():
            return int(value)
        
        else: 
            return value

    # Global settings dict
    stg = {}

    # Parse settings.cfg
    settings_cfg    = "settings.cfg"
    settings_parser = configparser.RawConfigParser(allow_no_value=True)
    settings_parser.read(basedir + "/" + settings_cfg)

    for section in settings_parser:
        if not section == "DEFAULT":
            for key in settings_parser[section]:
                stg[key] = process(key, settings_parser[section][key])

    # Derived variable
    stg['top_env']             = stg['topdir_env_var'] + stg['sl']
    stg['module_basedir']      = "modulefiles"
    stg['log_path']            = basedir + stg['sl'] + stg['log_dir']
    stg['build_path']          = basedir + stg['sl'] + stg['build_basedir']
    stg['bench_path']          = basedir + stg['sl'] + stg['bench_basedir']
    stg['config_path']         = basedir + stg['sl'] + stg['config_basedir']
    stg['template_path']       = basedir + stg['sl'] + stg['template_basedir']
    stg['script_path']         = basedir + stg['sl'] + stg['script_basedir']
    stg['result_script_path']  = stg['script_path']  + stg['sl'] + stg['result_scripts_dir']
    stg['system_scripts_path'] = stg['script_path']  + stg['sl'] + stg['result_scripts_dir']
    stg['module_path']         = stg['build_path']   + stg['sl'] + stg['module_basedir']
    stg['src_path']            = basedir + stg['sl'] + "src"
    stg['utils_path']          = basedir + stg['sl'] + stg['system_utils_dir']

    # Get system label
    system = str(os.getenv(stg['system_env'].strip('$')))
    if not system:
        print("ERROR: " + stg['system_env'] + " not set.")
        exit(2)

    #----------------------------settings.cfg--------------------------------

    def __init__(self):

        # Create logging obj
        log = None
    
        # Session variable dicts
        code     = {}
        sched    = {}
        compiler = {}

