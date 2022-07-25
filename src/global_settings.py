# System Imports
import configparser
from datetime import datetime
import inspect
import itertools
import os
from pathlib import Path
import socket
import sys

# Local Imports
import src.lib as lib

# Global constants
class setup(object):

    # Text formatting
    warning                     = '\033[1;33mWARNING \033[0m'
    error                       = '\033[0;31mERROR \033[0m'
    success                     = '\033[0;32mSUCCESS \033[0m'
    note                        = '\033[0;34mNOTE \033[0m'
    bold                        = '\033[1m'
    end                         = '\033[0m'

    white                       = '\033[1;30m'
    grey                        = '\033[1m'

    # Get dev_mode from environ
    dev_mode                    = True
    dev_str                     = "[DEV]"
    if os.environ.get("BP_DEV") == "0":
        dev_mode                = False
        dev_str                 = "[PRODUCTION]"

    # Create log obj
    log                         = None

    ev                          = {}
    # defaults.ini dict
    stg                         = {}
    # Cfg file dict
    config                      = {}
    config['general']           = {}
    config['config']            = {}
    config['modules']           = {}
    config['requirements']      = {}
    config['runtime']           = {}
    config['result']            = {}
    config['files']             = {}
    # Scheduler dict
    sched                       = {}
    sched['sched']              = {}
    # Compiler dict
    compiler                    = {}
    # suites.ini dict
    suite                       = {}
    # System dict
    system                      = {}
    # Module dict
    modules                     = {}
    # populated with metadata about installed apps
    installed_apps              = []
    # List of staging command to add to script
    stage_ops                   = []
    # Contents of user's settings.ini
    user_settings               = []
    # Report obj
    build_report                = None
    # List of dependant 'any' jobs
    any_dep_list                = []
    # List of dependant 'ok' jobs
    ok_dep_list                 = []
    # Process ID of previous task
    prev_pid                    = 0
    # Lists of avail config files
    build_cfgs                  = []
    bench_cfgs                  = []
    # dict for storing overload key-values
    overload_dict               = {}
    overloaded                  = [] 
    # List populated with appliction info
    installed_app_list          = []
    installed_app_paths         = []
    # Suppress build manager output
    quiet_build                 = False
    # Files to cleanup on fail
    cleanup                     = []
    # Command line history
    cmd                         = None

    # Context variables
    user                        = str(os.getlogin())
    home                        = os.path.expandvars("$HOME")
    hostname                    = str(socket.gethostname())
    # If FQDN - take first 2 fields
    if ("." in hostname):
        hostname                = '.'.join(map(str, hostname.split('.')[0:2]))

    # Check CWD doesn't throw errors
    try:
        cwd                     = os.getcwd()
    except BaseException:
        print("It seems your current working directory doesn't exist. Exitting.")
        sys.exit(1)

    # Version info is populated by lib.files.init
    version_client              = None
    version_client_date         = None
    version_site                = os.getenv('BPS_VERSION')
    version_site_full           = version_site + "-" + os.getenv('BP_BUILD_ID') + " " + dev_str
    version_site_date           = os.getenv("BP_BUILD_DATE")

    # Ingest EVs
    for key, val in os.environ.items():
        if "BP_" in key:
            ev[key]  = val

    # Resolve relative paths and EVs in $BP_HOME/settings.ini
    def resolve(self, ev):
        path = os.path.expandvars(ev)
        # Check for unresolved EV
        if "$" in path:
            print(
                "Unable to resolve environment variable in '" +
                path +
                "''. Exiting.")
            sys.exit(1)

        # Convert relative paths: ./[path] -> $BP_HOME/[path]
        if len(path) > 2:
            if path[0:2] == "./":
                return os.path.join(self.ev['BP_HOME'], path[2:])
        return path

    # Process each key-value in .ini, check for null values
    def process(self, key, value):
        # List of optional keys exempted from NULL check
        optional = ['collection_path', 'ssh_user', 'ssh_key', 'scp_path']

        # Throw exception if required value is NULL
        if key not in optional and not value:
            print("Missing value for key '" +
                  key +
                  "' in $BP_HOME/settings.ini, check the documentation.")
            sys.exit(1)

        # True
        elif value in ["1", "T", "t", "True", "true"]:
            return True
        # False
        elif value in ["0", "F", "f", "False", "false"]:
            return False
        # Int
        elif value.isdigit():
            return int(value)
        # String
        else:
            return value

    # Read ini file and return configparser obj
    def read_ini(self, ini_file):

        ini_parser = configparser.RawConfigParser(allow_no_value=True)
        
        # This reading method allows for [sections] be present or not
        with open(ini_file) as fp:
            ini_parser.read_file(itertools.chain(['[DEFAULT]'], fp), source=ini_file)            

        return ini_parser

    # Read in settings.ini file
    def read_settings(self, settings_file, overload):

        if not os.path.isfile(settings_file) and not overload:
            print("Unable to read file " + settings_file)
            sys.exit(1)

        # Read contents of ini into dict
        settings_parser = self.read_ini(settings_file)

        for section in settings_parser:
            if not section == "DEFAULT":
                for key in settings_parser[section]:
                    # Convert values to correct datatype
                    value = self.process(key, settings_parser[section][key])
                    # Add to overload dict (user settings)
                    if overload:
                        self.user_settings += [value]
                    # Add to stg dict (site settings)
                    else:
                        self.stg[key] = value

    # Default settings from site package
    def read_default_settings(self):
        self.read_settings(os.path.join(self.ev['BPS_INC'], "defaults.ini"), False)

    # Use defined settings - overwrite the defaults
    def read_user_settings(self):
        self.read_settings(os.path.join(self.ev['BP_HOME'], "settings.ini"), True)
        self.lib.overload.setup_dict()

    def derived_variables(self):

        self.stg['log_path']            = self.resolve(self.stg['log_dir'])
        self.stg['config_path']         = self.resolve(self.stg['config_dir'])
        self.stg['template_path']       = self.resolve(self.stg['template_dir'])
        self.stg['local_repo']          = self.resolve(self.stg['local_repo_env'])
        self.stg['collection_path']     = self.resolve(self.stg['collection_path'])
        self.stg['resource_path']       = self.resolve(self.stg['resource_dir'])

        # Derived variables
        self.stg['module_dir']          = "modulefiles"
        self.stg['user_mod_path']       = os.path.join(
                                        self.ev['BP_HOME'], self.stg['module_dir'])
        self.stg['build_dir']           = os.path.basename(self.ev['BP_APPS'])
        self.stg['pending_path']        = os.path.join(
                                        self.ev['BP_RESULTS'], self.stg['pending_subdir'])
        self.stg['captured_path']       = os.path.join(
                                        self.ev['BP_RESULTS'], self.stg['captured_subdir'])
        self.stg['failed_path']         = os.path.join(
                                        self.ev['BP_RESULTS'], self.stg['failed_subdir'])
        self.stg['module_path']         = os.path.join(
                                        self.ev['BP_APPS'], self.stg['module_dir'])
        self.stg['utils_path']          = os.path.join(
                                        self.stg['resource_path'], self.stg['hw_utils_subdir'])
        self.stg['script_path']         = os.path.join(
                                        self.stg['resource_path'], self.stg['script_subdir'])
        self.stg['rules_path']          = os.path.join(
                                        self.stg['config_path'], self.stg['rules_dir'])

        # Add some useful key-values
        self.stg['date_str'] = datetime.now().strftime("%Y.%m.%d")
        self.stg['time_str'] = datetime.now().strftime("%Y-%m-%dT%H-%M")


    # Read suites.ini
    def read_suites(self):

        suite_parser = self.read_ini(os.path.join(self.ev['BP_HOME'], "suites.ini"))

        # Read suites into own dict
        self.suite = dict(suite_parser.items('suites'))

    # Get system EV
    def get_system_label(self):

        # Get system label
        self.system['system'] = self.resolve(self.stg['system_env'])

        # Check its set
        if not self.system['system']:
            print("ERROR: " + self.stg['system_env'] + " not set.")
            exit(1)

    # Initialize the global dicts, settings and libraries
    def __init__(self, args):

        self.args = args

        # Init function library
        self.lib = lib.init(self)

        # Parse $BPS_SITE/package/defaults.ini
        self.read_default_settings()

        # Overwrite defaults with user settings in $BP_HOME/settings.ini
        self.read_user_settings()

        # Derive variables
        self.derived_variables()

        # Parse $BP_HOME/suites.ini
        self.read_suites()

        # Get system label
        self.get_system_label()

        # Read version info 
        self.lib.files.get_client_version()
