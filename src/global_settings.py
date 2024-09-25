# System Imports
import configparser
from datetime import datetime
import getpass
import inspect
import itertools
import os
from pathlib import Path
import socket
import sys
import time

# Local Imports
import src.lib              as lib
import src.validator        as validator

# Global constants
class setup(object):

    # Text formatting
    warning                     = '\033[1;33mWARNING \033[0m'
    error                       = '\033[0;31mERROR \033[0m'
    success                     = '\033[0;32mSUCCESS \033[0m'
    note                        = '\033[0;34mNOTE \033[0m'
    bold                        = '\033[1m'
    end                         = '\033[0m'

    white                       = '\033[1m'
    grey                        = '\033[1m' #'\033[1;30m'

    # Get dev_mode from environ
    dev_mode                    = True
    dev_str                     = "[DEV]"
    if os.environ.get("BP_DEV") == "0":
        dev_mode                = False
        dev_str                 = "[PRODUCTION]"

    ev                          = {}

    # User info
    session                     = {}
    # suites.ini dict
    suite                       = {}

    # List of paths to add to PATH
    paths                       = []

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

    valid_keys                  = []

    # Contents of user's user.ini
    defs_overload_list          = []
    defs_overload_dict          = {}
    required_overload_keys      = ['allocation']

    # Lists of application/result base dirs
    bp_apps                     = []
    bp_results                  = []

    # Files to cleanup on fail
    cleanup                     = []
    # Command line history
    cmd                         = None

    # Context variables
    user                        = getpass.getuser()
    home                        = os.path.expandvars("$HOME")
    hostname                    = str(socket.gethostname())

    # If FQDN - take first 2 fields
    if ("." in hostname):
        hostname                = '.'.join(map(str, hostname.split('.')[0:2]))

    # Check CWD doesn't throw errors
    try:
        cwd                     = os.getcwd()
    except BaseException:
        print("It seems your current working directory doesn't exist. Quitting.")
        sys.exit(1)

    # Ingest EVs
    for key, val in os.environ.items():
        if ("BP_" in key or "BPS_" in key) and (key != "BP_DEV"):
            ev[key]  = val

    # Resolve relative paths and EVs in $BP_HOME/user.ini
    def resolve(self, value: str) -> str:

        value = os.path.expandvars(str(value))
        # Check for unresolved EV
        if "$" in value:
            print(
                "Unable to resolve environment variable in '" +
                value +
                "''. Exiting.")
            sys.exit(1)

        # Convert relative paths: ./[path] -> $BP_HOME/[path]
        if len(value) > 2:
            if value[0:2] == "./":
                return [os.path.join(self.ev['BP_HOME'], value[2:]),
                        os.path.join(self.ev['BPS_INC'], value[2:])]
        return value


    # Process each key-value in .ini, check for null values
    def process(self, key: str, value: str):
        # List of optional keys exempted from NULL check
        optional = ['collection_path', 'ssh_user', 'ssh_key', 'scp_path']

        # Throw exception if required value is NULL

        #print("key", key, "value", value)

        if key and key not in optional and not value:
            print("Missing value for key '" +
                  key +
                  "' in $BP_HOME/user.ini, check the documentation.")
            sys.exit(1)

        # Cast to dtype
        return self.lib.destring(value)


    # Read ini file and return configparser obj
    def read_ini(self, ini_file:str, required: bool):

        if not os.path.isfile(ini_file):
            # Required
            if required:
                print("Unable to read file " + ini_file)
                sys.exit(1)
            # Not required
            else:
                return

        ini_parser = configparser.RawConfigParser(allow_no_value=True)
        ini_parser.optionxform=str

        # This reading method allows for [sections] be present or not
        with open(ini_file) as fp:
            ini_parser.read_file(itertools.chain(['[user]'], fp), source=ini_file)

        return ini_parser

    # Read in user.ini file
    def read_settings(self, settings_file: str, overload: bool):

        settings_parser = self.read_ini(settings_file, not overload)

        # If missing user.ini file, run validator
        if not settings_parser:
            return
            print("FATAL: failed to read settings file " + settings_file)
            sys.exit(1)

        # Read contents of ini into dict
        for section in settings_parser:
            if not section == "DEFAULT":

                for key in settings_parser[section]:
                    # Convert values to correct datatype
                    value = self.process(key, settings_parser[section][key])
                    # Auto-resolve all val in [path]
                    if section == "paths":
                        value = self.resolve(value)
                    # Add to overload dict (user settings)
                    if overload:
                        # Process before casting to str, 0 -> False
                        self.defs_overload_list += [key+"="+str(value)]
                        self.defs_overload_dict[key] = value

                    # Add to stg dict (site settings)
                    else:
                        self.stg[key] = value

    # Default settings from site package
    def read_default_settings(self):
        self.read_settings(os.path.join(self.ev['BPS_INC'], "defaults.ini"), False)

    # Use defined settings - overwrite the defaults
    def read_user_settings(self):

        settings_file = os.path.join(self.ev['BP_HOME'], "user.ini")

        # Run validator if user user.ini file is missing
        if not os.path.isfile(settings_file):
            self.args.validate = True
            return

        self.read_settings(settings_file, True)

        # Create overload dict from user.ini & --overload
        self.lib.overload.init_overload_dict()


    def join(self, path1, path2):
        return os.path.join(path1, path2)

    def join_paths(self, path1, path2):
        if isinstance(path1, list):
            out = []
            for path in path1:
                out.append(self.join(path, path2))

        elif isinstance(path2, list):
            out = []
            for path in path2:
                out.append(self.join(path1, path))

        else:
            return self.join(path1, path2)

    # Add user and site /bin paths to PATH
    def add_to_path(self):
        for path in self.paths:
            os.environ['PATH'] = os.environ['PATH'] + ":" + path

    def derived_variables(self):


#        self.stg['user_stats_path']     = os.path.join(
#                                            self.ev['BP_HOME'],
#                                            self.stg['resource_subdir'],
#                                            self.stg['script_subdir'],
#                                            self.stg['stats_subdir']
#                                            )

        self.stg['site_stats_path']     = os.path.join(
                                            self.ev['BPS_INC'],
                                            self.stg['resource_subdir'],
                                            self.stg['script_subdir'],
                                            self.stg['stats_subdir']
                                            )

        self.stg['user_results_path']   = os.path.join(
                                            self.ev['BP_HOME'],
                                            self.stg['resource_subdir'],
                                            self.stg['script_subdir'],
                                            self.stg['results_subdir']
                                            )

        self.stg['site_results_path']   = os.path.join(
                                            self.ev['BPS_INC'],
                                            self.stg['resource_subdir'],
                                            self.stg['script_subdir'],
                                            self.stg['results_subdir']
                                            )


        # Add to PATH
        #self.paths += [self.stg['user_bin_path']]
#        self.paths += [self.stg['site_stats_path']]
#        self.add_to_path()
        self.paths += [os.path.join(self.ev['BPS_HOME'], "python", "bin")]

        # Derived variables
        self.stg['user_mod_path']       = os.path.join(
                                            self.ev['BP_HOME'], 
                                            self.stg['module_dir']
                                            )
        self.stg['site_mod_path']       = os.path.join(
                                            self.ev['BPS_HOME'], 
                                            self.stg['module_dir']
                                            )
        self.stg['pending_path']        = os.path.join(
                                            self.ev['BP_RESULTS'], 
                                            self.stg['pending_subdir']
                                            )
        self.stg['captured_path']       = os.path.join(
                                            self.ev['BP_RESULTS'], 
                                            self.stg['captured_subdir']
                                            )
        self.stg['failed_path']         = os.path.join(
                                            self.ev['BP_RESULTS'], 
                                            self.stg['failed_subdir']
                                            )
#        self.stg['script_path']         =os.path.join(
#                                            self.ev['BP_HOME'], 
#                                            self.stg['module_dir']
#                                            )

        # Add some useful key-values
        self.stg['date_str'] = datetime.now().strftime("%Y.%m.%d")
        self.stg['time_str'] = datetime.now().strftime("%Y-%m-%dT%H-%M")

        try:
            self.session['columns'], self.session['rows'] = os.get_terminal_size()
        except:
            self.session['columns'], self.session['rows'] = 640, 480

        # Get text wrap chars
        self.stg['width'] = min(self.stg['width'], self.session['columns'])

        self.stg['exec_mode'] = None
        self.stg['op_mode'] = None
        if self.args.build:
            self.stg['exec_mode'] = self.stg['build_mode']
            self.stg['op_mode'] = 'build'
        elif self.args.bench:
            self.stg['exec_mode'] = self.stg['bench_mode']
            self.stg['op_mode'] = 'bench'
        
        if self.stg['disable_sched']:
            self.stg['exec_mode'] = 'local'



    # Read suites.ini
    def read_suites(self):

        suite_parser = self.read_ini(os.path.join(self.ev['BP_HOME'], "suites.ini"), False)
        if suite_parser:
            # Read suites into own dict
            self.suite = dict(suite_parser.items('suites'))

    # Get system EV
    def get_system_label(self):

        # Get system label
        self.system['system'] = self.resolve(self.stg['system_env'])

        # Check its set
        if not self.system['system']:
            print("FATAL: " + self.stg['system_env'] + " not set.")
            sys.exit(1)

    def check_group(self):

        if self.stg['shared_apps']:
            if self.stg['working_group'] == "None":
                print("FATAL: working_group not set.")
                print("bps shared_apps=False")
                print("OR")
                print("bps working_group=[group]")
                print("Find your working_group with bp --notices")
                sys.exit(1)

            # working_group not in lookup table
            gid_file = self.lib.files.read(os.path.join(self.ev['BPS_INC'], "resources/groups.txt"))
            gid_table = [line.split() for line in gid_file]

            try:
                self.overload_dict['allocation'], self.overload_dict['gid'] = [gid[1:] for gid in gid_table if gid[0] == self.stg['working_group']][0]
            except:
                print("FATAL: unrecongized working_group '" + self.stg['working_group'] + "', your options:")
                [print(gid[0]) for gid in gid_table]
                print()
                print("bps working_group=[your_group]")
                print()
                sys.exit(1)

            # Test group dir
            group_apps  = os.path.join(self.stg['group_app_prefix'], self.stg['working_group']) 

            if not os.path.isdir(group_apps):
                print("FATAL: your shared application directory '"+group_apps+"' doesn't exist.")
                print("You can disable shared applications with:")
                print("bps shared_apps=0")
                sys.exit(1)

            # Add shared app path to bp_apps
            self.bp_apps += [group_apps]
            #self.bp_results +=


    # Initialize the global dicts, settings and libraries
    def __init__(self, args):

        self.args = args

        # defaults.ini dict
        self.stg                         = {}

        # Mutable dict definitions
        # Create log obj
        self.log                         = None
        self.timing1                     = 0.
        self.timing2                     = 0.

        self.config                      = {}
        self.config['general']           = {}
        self.config['config']            = {}
        self.config['modules']           = {}
        self.config['requirements']      = {}
        self.config['runtime']           = {}
        self.config['result']            = {}
        self.config['files']             = {}

        # Scheduler dict
        self.sched                       = {}
        self.sched['sched']              = {}
        # Compiler dict
        self.compiler                    = {}
        self.mpi                         = {}
        self.mod_name_map                = {}
        self.mod_name_map['nvidia']      = 'nvhpc'


        # System dict
        self.system                      = {}
        # Module dict
        self.modules                     = {}
        # populated with metadata about installed apps
        self.installed_apps_list         = []
        self.bench_results_list          = []

        # dict for storing overload key-values
        self.overload_dict               = {}
        self.overloaded_dict             = {}

        # List of staging command to add to script
        self.stage_ops                   = []

        # Init function library
        self.lib = lib.init(self)


        # Parse $BPS_HOME/package/defaults.ini
        self.read_default_settings()

        # Init valid key list
        self.lib.overload.set_valid_keys()

        # Overwrite defaults with user settings in $BP_HOME/user.ini
        self.read_user_settings()

        # Run purge with args.purge=True
        self.lib.files.purge()

        # Parse $BP_HOME/suites.ini
        self.read_suites()

        # Get system label
        self.get_system_label()

        # Run Overloads
        self.lib.overload.replace(None)

        # Check group stuff
        self.check_group()

        # Update EV dict from overloads
        self.lib.overload.replace(self.ev)

        # Derive variables
        self.derived_variables()

        # Start validator
        validator.start(self)

        # Check version compatiblity 
        self.lib.version.check()


        # Check all required overload variables are set
        self.lib.overload.check_for_required_overloads()


        # Add user's app path
        self.bp_apps    += [self.ev['BP_APPS']]
        self.bp_results += [self.ev['BP_RESULTS']]

        # Set module path
        self.stg['module_path']      = os.path.join(
                                          self.bp_apps[-1], self.stg['module_dir'])


        #print("stg")
        #print(self.stg)

        # Read version info
        #self.lib.files.get_client_version()
