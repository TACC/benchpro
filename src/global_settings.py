# System Imports
import configparser
from datetime import datetime
import os
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

    # Get dev_mode from environ
    dev_mode                    = False
    if "BP_DEV" in os.environ:
        dev_mode                = True

    # Create log obj
    log                         = None

    # settings.ini dict
    stg                         = {}
    # Cfg file dict
    config                      = {}
    config['general']           = {}
    config['config']            = {}
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

    # List of staging command to add to script
    stage_ops                   = []
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
    # Suppress build manager output
    quiet_build                 = False
    # Files to cleanup on fail
    cleanup                     = []
    # Command line history
    cmd                         = ""

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

    # Get versions
    version_site                = os.getenv('BP_VERSION')
    version_site_full           = version_site + "-" + os.getenv('BP_BUILD_ID')

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

        # Convert relative paths: ./[path] -> [bp_home]/[path]
        if len(path) > 2:
            if path[0:2] == "./":
                return os.path.join(self.bp_home, path[2:])
        return path

    # Process each key-value in $BP_HOME/settings.ini, check for null values
    def process(self, key, value):
        # List of optional keys exempted from NULL check
        optional = ['scp_path',
                    'ssh_user',
                    'ssh_key',
                    'collection_path']

        # Throw exception if required value is NULL
        if key not in optional and not value:
            print("Missing value for key '" +
                  key +
                  "' in $BP_HOME/settings.ini, check the documentation.")
            sys.exit(1)

        # True
        elif value in ["True", "true"]:
            return True
        # False
        elif value in ["False", "false"]:
            return False
        # Int
        elif value.isdigit():
            return int(value)
        # String
        else:
            return value

    # Read ini file and return configparser obj
    def read_ini(self, ini_file):

        # Check user files are present
        if not os.path.isfile(ini_file):
            print(ini_file +
                  " file not found, did you install required user files?")
            print("If not, do so now with:")
            print("git clone https://github.com/TACC/benchpro.git $HOME/benchpro")
            print("Quitting for now...")
            sys.exit(1)

        ini_parser = configparser.RawConfigParser(allow_no_value=True)
        ini_parser.read(ini_file)

        return ini_parser

    # Read in settings.ini file
    def read_settings(self):

        # Run ConfigParser on settings.ini
        settings_parser = self.read_ini(
            os.path.join(self.bp_home, "settings.ini"))

        # Read contents of settings.ini into dict
        for section in settings_parser:
            if not section == "DEFAULT":
                for key in settings_parser[section]:
                    # Convert values to correct datatype
                    self.stg[key] = self.process(
                        key, settings_parser[section][key])

        # Preserve enviroment variable labels
        self.stg['project_env']         = self.stg['home_path']
        self.stg['app_env']             = self.stg['build_path']
        self.stg['result_env']          = self.stg['bench_path']

        # Resolve paths
        self.stg['home_path']           = self.resolve(self.stg['home_path'])
        self.stg['build_path']          = self.resolve(self.stg['build_path'])
        self.stg['bench_path']          = self.resolve(self.stg['bench_path'])
        self.stg['log_path']            = self.resolve(self.stg['log_dir'])
        self.stg['config_path']         = self.resolve(self.stg['config_dir'])
        self.stg['template_path']       = self.resolve(self.stg['template_dir'])
        self.stg['ssh_key_path']        = self.resolve(self.stg['ssh_key'])
        self.stg['local_repo']          = self.resolve(self.stg['local_repo_env'])
        self.stg['collection_path']     = self.resolve(self.stg['collection_path'])
        self.stg['resource_path']       = self.resolve(self.stg['resource_dir'])

        # Derived variables
        self.stg['module_dir']          = "modulefiles"
        self.stg['build_dir']           = os.path.basename(self.stg['build_path'])
        self.stg['pending_path']        = os.path.join(
                                        self.stg['bench_path'], self.stg['pending_subdir'])
        self.stg['captured_path']       = os.path.join(
                                        self.stg['bench_path'], self.stg['captured_subdir'])
        self.stg['failed_path']         = os.path.join(
                                        self.stg['bench_path'], self.stg['failed_subdir'])
        self.stg['module_path']         = os.path.join(
                                        self.stg['build_path'], self.stg['module_dir'])
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

        suite_parser = self.read_ini(os.path.join(self.bp_home, "suites.ini"))

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
    def __init__(self):

        # EV for project dir
        self.bp_home = "BP_HOME"

        # Check that EV is loaded
        if self.bp_home not in os.environ:
            print(
                "$" +
                self.bp_home +
                " not set. Load BenchPRO module. Aborting!")
            sys.exit(1)

        # Resolve EV
        self.bp_home = self.resolve("$" + self.bp_home)

        # Parse $BP_HOME/settings.ini file
        self.read_settings()

        # Parse $BP_HOME/suites.ini
        self.read_suites()

        # Get system label
        self.get_system_label()

        # Init function library
        self.lib = lib.init(self)
