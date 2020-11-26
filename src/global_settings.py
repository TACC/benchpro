# System Imports
import configparser 
from datetime import datetime
import os
import socket
import sys

# Global constants
class settings(object):

    # Coloured text
    warning     = '\033[1;33mWARNING: \033[0m'
    error       = '\033[0;31mERROR: \033[0m'
    success     = '\033[0;32mSUCCESS: \033[0m'
    note        = '\033[0;34mNOTE: \033[0m'

    # Create logging obj
    log = None

    # Global variable dicts
    stg      = {}
    code     = {}
    sched    = {}
    compiler = {}
    suite    = {}

    dep_list = {}
    overload_dict = {}
    quiet_build =  False 
    prev_pid = 0


    # Context variables
    user                = str(os.getlogin())
    hostname            = str(socket.gethostname())
    if ("." in hostname):
        hostname        = '.'.join(map(str, hostname.split('.')[0:2]))

    # Chicken & egg situation with 'sl' here - hardcoded 
    basedir             = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
    time_str            = datetime.now().strftime("%Y-%m-%dT%H-%M")
    cwd                 = os.getcwd()

    # Resolve relative paths in settings.ini
    def resolve_path(self, path):
        if len(path) > 2:
            if path[0:2] == "./":
                return os.path.join(self.basedir, path[2:])
        return path

    # Check for empty params and datatypes in settings.ini
    def process(self, key, value):
        optional = ['user',
                    'key',
                    'scp_path',
                    'blackhole_path']
        if key not in optional and not value:
            print("Missing value for key '" + key + "' in settings.ini, check the documentation.")
            sys.exit(1)
        # Test if True
        elif value in  ["True", "true"]:
            return True
        # Test if False
        elif value in ["False", "false"]:
            return False
        # Test if int
        elif value.isdigit():
            return int(value)
        else: 
            return value

    # Read in settings.ini file
    def read_settings(self):
        settings_ini    = os.path.join(self.basedir, "settings.ini")
        settings_parser = configparser.RawConfigParser(allow_no_value=True)
        settings_parser.read(settings_ini)

        #----------------------------settings.ini--------------------------------

        # Read contents of settings.ini into dict
        for section in settings_parser:
            if not section == "DEFAULT":
                for key in settings_parser[section]:
                    # Convert values to correct datatype
                    self.stg[key] = self.process(key, settings_parser[section][key])

        # Read suites into own dict
        self.suite = dict(settings_parser.items('suites'))

        self.stg['script_basedir']   = self.resolve_path(self.stg['script_basedir'])
        self.stg['ssh_key_dir']      = self.resolve_path(self.stg['ssh_key_dir'])
        self.stg['config_basedir']   = self.resolve_path(self.stg['config_basedir'])
        self.stg['template_basedir'] = self.resolve_path(self.stg['template_basedir'])
        self.stg['build_basedir']    = self.resolve_path(self.stg['build_basedir'])
        self.stg['bench_basedir']    = self.resolve_path(self.stg['bench_basedir'])

        # Derived variables
        self.stg['top_env']             = self.stg['topdir_env_var'] + self.stg['sl']
        self.stg['module_basedir']      = "modulefiles"
        self.stg['log_path']            = os.path.join(self.basedir, self.stg['log_dir'])
        self.stg['build_path']          = os.path.join(self.basedir, self.stg['build_basedir'])
        self.stg['bench_path']          = os.path.join(self.basedir, self.stg['bench_basedir'])
        self.stg['current_path']        = os.path.join(self.stg['bench_path'], self.stg['current_subdir'])
        self.stg['archive_path']        = os.path.join(self.stg['bench_path'], self.stg['archive_subdir'])
        self.stg['config_path']         = os.path.join(self.basedir, self.stg['config_basedir'])
        self.stg['template_path']       = os.path.join(self.basedir, self.stg['template_basedir'])
        self.stg['script_path']         = os.path.join(self.basedir, self.stg['script_basedir'])
        self.stg['result_script_path']  = os.path.join(self.stg['script_path'], self.stg['result_scripts_dir'])
        self.stg['system_scripts_path'] = os.path.join(self.stg['script_path'], self.stg['result_scripts_dir'])
        self.stg['module_path']         = os.path.join(self.stg['build_path'], self.stg['module_basedir'])
        self.stg['src_path']            = os.path.join(self.basedir, "src")
        self.stg['utils_path']          = os.path.join(self.basedir, self.stg['system_utils_dir'])


    def __init__(self):

        # Parse settings.ini
        self.read_settings() 

        # Get system label
        self.sys_env = str(os.getenv(self.stg['system_env'].strip('$')))
        if not self.sys_env:
            print("ERROR: " + self.stg['system_env'] + " not set.")
            exit(2)

        #----------------------------settings.ini--------------------------------

