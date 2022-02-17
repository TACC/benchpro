# System Imports
import configparser 
from datetime import datetime
import os
import socket
import sys

# Local Imports
import src.lib as lib

# Global constants
class settings(object):

    # Text formatting
    warning     = '\033[1;33mWARNING \033[0m'
    error       = '\033[0;31mERROR \033[0m'
    success     = '\033[0;32mSUCCESS \033[0m'
    note        = '\033[0;34mNOTE \033[0m'
    bold        = '\033[1m'
    end         = '\033[0m'

    # Create logging obj
    log = None
    op = ""
    # ===Global variable dicts===

    # stg = settings.ini
    stg         = {}
    # Cfg file key-values
    config      = {}
    config['general'] = {}
    config['config'] = {}
    config['requirements'] = {}
    config['runtime'] = {}
    config['result'] = {}
    # Scheduler key-values
    sched       = {}
    sched['sched'] = {}
    # Compiler key-values
    compiler    = {}
    # Elems of [suite] from settings.ini
    suite       = {}
    # System key-values
    system      = {}
    # List of staging command to add to script
    stage_ops   = []

    # Report obj
    build_report= None

    # list of depency jobs
    any_dep_list = []
    ok_dep_list = []
    prev_pid = 0

    # Cfg lists
    build_cfgs = []
    bench_cfgs = [] 

    overload_dict = {}
    quiet_build =  False 

    # Files to cleanup on fail
    cleanup = []

    # Command history line
    cmd = ""

    # Context variables
    user                = str(os.getlogin())
    hostname            = str(socket.gethostname())
    home                = os.path.expandvars("$HOME")

    if ("." in hostname):
        hostname        = '.'.join(map(str, hostname.split('.')[0:2]))

    # Set basic vars
    time_str            = datetime.now().strftime("%Y-%m-%dT%H-%M")
    try:
        cwd                 = os.getcwd()
    except:
        print("It seems your current working directory doesn't exist. Exitting.")
        sys.exit(1)

    # Resolve relative paths and envvars in settings.ini
    def resolve_path(self, path):
        path = os.path.expandvars(path)
        # Check for unresolved envvar
        if "$" in path:
            print("Unable to resolve environment variable in '" + path + "''. Exiting.")
            sys.exit(1)
    
        # Convert relative paths
        if len(path) > 2:
            if path[0:2] == "./":
                return os.path.join(self.bt_home, path[2:])
                
        return path

    # Check for empty params and datatypes in settings.ini
    def process(self, key, value):
        optional = ['user',
                    'key',
                    'scp_path',
                    'ssh_user',
                    'ssh_key',
                    'collection_path']
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
    def read_settings(self, bt_home):

        self.bt_home = self.resolve_path(bt_home)

        settings_ini    = os.path.join(self.bt_home, "settings.ini")
        settings_parser = configparser.RawConfigParser(allow_no_value=True)
        settings_parser.read(settings_ini)

        # Check user files are present
        if not os.path.isfile(settings_ini):
            print("$BP_HOME/settings.ini file not found, did you install required user files?")
            print("If not, do so now with:")
            print("git clone https://github.com/TACC/benchpro.git $HOME/benchpro")
            print("Quitting for now...")
            sys.exit(1)
    
        # Read contents of settings.ini into dict
        for section in settings_parser:
            if not section == "DEFAULT":
                for key in settings_parser[section]:
                    # Convert values to correct datatype
                    self.stg[key] = self.process(key, settings_parser[section][key])

        # Read suites into own dict
        self.suite = dict(settings_parser.items('suites'))

        # Preserve enviroment variable labels
        self.stg['project_env']         = self.stg['home_path'] 
        self.stg['app_env']             = self.stg['build_path'] 
        self.stg['result_env']          = self.stg['bench_path'] 

        # Resolve paths
        self.stg['home_path']            = self.resolve_path(self.stg['home_path'])
        self.stg['build_path']           = self.resolve_path(self.stg['build_path'])
        self.stg['bench_path']           = self.resolve_path(self.stg['bench_path'])

        self.stg['ssh_key_path']        = self.resolve_path(self.stg['ssh_key'])
        self.stg['config_path']         = self.resolve_path(self.stg['config_dir'])
        self.stg['template_path']       = self.resolve_path(self.stg['template_dir'])
        self.stg['resource_path']       = self.resolve_path(self.stg['resource_dir'])
        self.stg['local_repo']          = self.resolve_path(self.stg['local_repo_env'])
        self.stg['collection_path']     = self.resolve_path(self.stg['collection_path'])

        # Derived variables
        self.stg['module_dir']          = "modulefiles"
        self.stg['build_dir']           = os.path.basename(self.stg['build_path']) 
        self.stg['log_path']            = os.path.join(self.bt_home, self.stg['log_dir'])
        self.stg['pending_path']       = os.path.join(self.stg['bench_path'], self.stg['pending_subdir'])
        self.stg['captured_path']       = os.path.join(self.stg['bench_path'], self.stg['captured_subdir'])
        self.stg['failed_path']         = os.path.join(self.stg['bench_path'], self.stg['failed_subdir'])
        self.stg['module_path']         = os.path.join(self.stg['build_path'], self.stg['module_dir'])
        self.stg['utils_path']          = os.path.join(self.stg['resource_path'], self.stg['hw_utils_subdir'])
        self.stg['script_path']         = os.path.join(self.stg['resource_path'], self.stg['script_subdir'])
        self.stg['rules_path']          = os.path.join(self.stg['config_path'], self.stg['rules_dir'])

    # Initialize the global object, settings and libraries
    def __init__(self, bt_home):

        # Parse settings.ini
        self.read_settings(bt_home) 

        # Get system label
        self.system['system'] = self.resolve_path(self.stg['system_env'])

        # Check its set
        if not self.system['system']:
            print("ERROR: " + self.stg['system_env'] + " not set.")
            exit(1)

        # Init function library
        self.lib = lib.init(self)
