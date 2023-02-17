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

    white                       = '\033[1m'
    grey                        = '\033[1m' #'\033[1;30m'

    # Get dev_mode from environ
    dev_mode                    = True
    dev_str                     = "[DEV]"
    if os.environ.get("BP_DEV") == "0":
        dev_mode                = False
        dev_str                 = "[PRODUCTION]"

    # Create log obj
    log                         = None

    ev                          = {}

    # User info
    session                     = {}
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
    installed_apps_list         = []
    # List of staging command to add to script
    stage_ops                   = []

    # List of paths to add to PATH
    paths                       = []

    # Quit after validator
    quit_after_val              = False


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
    overloaded_dict             = {} 
    valid_keys                  = []

    # Contents of user's settings.ini
    defs_overload_list          = []
    defs_overload_dict          = {}
    required_overload_keys      = ['slurm_account']

    # Lists of application/result base dirs
    bp_apps                     = []
    bp_results                  = []

    # Suppress build manager output
    quiet_build                 = False
    # Files to cleanup on fail
    cleanup                     = []
    # Command line history
    cmd                         = None

    # Context variables
    user                        = os.path.expandvars("$USER")
    home                        = os.path.expandvars("$HOME")
    hostname                    = str(socket.gethostname())

    # If FQDN - take first 2 fields
    if ("." in hostname):
        hostname                = '.'.join(map(str, hostname.split('.')[0:2]))

    # Check CWD doesn't throw errors
    try:
        cwd                     = os.getcwd()
    except BaseException:
        print("It seems your current working directory doesn't exist. Aborting.")
        sys.exit(1)

    # Version info is populated by lib.files.init
    version_client              = None
    version_client_date         = None
    version_site                = os.getenv('BPS_VERSION')
    version_site_full           = os.getenv('BPS_VERSION_STR') + " " + dev_str
#    version_site_date           = os.getenv("BP_BUILD_DATE")

    # Ingest EVs
    for key, val in os.environ.items():
        if ("BP_" in key or "BPS_" in key) and (key != "BP_DEV"):
            ev[key]  = val

    # Resolve relative paths and EVs in $BP_HOME/settings.ini
    def resolve(self, val):

        val = os.path.expandvars(str(val))
        # Check for unresolved EV
        if "$" in val:
            print(
                "Unable to resolve environment variable in '" +
                val +
                "''. Exiting.")
            sys.exit(1)

        # Convert relative paths: ./[path] -> $BP_HOME/[path]
        if len(val) > 2:
            if val[0:2] == "./":
                return [os.path.join(self.ev['BP_HOME'], val[2:]),
                        os.path.join(self.ev['BPS_INC'], val[2:])]
        return val

    # Process each key-value in .ini, check for null values
    def process(self, key, value):
        # List of optional keys exempted from NULL check
        optional = ['collection_path', 'ssh_user', 'ssh_key', 'scp_path']

        # Throw exception if required value is NULL

        #print("key", key, "value", value)

        if key and key not in optional and not value:
            print("Missing value for key '" +
                  key +
                  "' in $BP_HOME/settings.ini, check the documentation.")
            sys.exit(1)

        # Cast to dtype
        return self.lib.destr(value)

    # Read ini file and return configparser obj
    def read_ini(self, ini_file, required):

        if not os.path.isfile(ini_file):
            # Required
            if required:
                print("Unable to read file " + ini_file)
                sys.exit(1)
            # Not required
            else:
                return

        ini_parser = configparser.RawConfigParser(allow_no_value=True)
        
        # This reading method allows for [sections] be present or not
        with open(ini_file) as fp:
            ini_parser.read_file(itertools.chain(['[user]'], fp), source=ini_file)            

        return ini_parser

    # Read in settings.ini file
    def read_settings(self, settings_file, overload):

        settings_parser = self.read_ini(settings_file, not overload)

        # If missing settings.ini file, run validator 
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

        settings_file = os.path.join(self.ev['BP_HOME'], "settings.ini")

        # Run validator if user settings.ini file is missing
        if not os.path.isfile(settings_file):
            self.args.validate = True
            self.quit_after_val = True
            return 

        self.read_settings(os.path.join(self.ev['BP_HOME'], "settings.ini"), True)

        # Create overload dict from settings.ini & --overload
        self.lib.overload.init_overload_dict()
        self.lib.overload.check_for_required_overloads()


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

        # Add to PATH
        self.paths += [self.stg['user_bin_path']]
        self.paths += [self.stg['site_bin_path']]
        self.add_to_path()
        self.paths += [os.path.join(self.ev['BPS_HOME'], "python", "bin")]

        # Check if BP_DEBUG is set
        if "BP_DEBUG" in os.environ:
            self.stg['debug'] = self.process(None, os.environ.get('BP_DEBUG'))
            print("BP_DEBUG=" + str(self.stg['debug']) + " (from env)")

        # Derived variables
        self.stg['user_mod_path']       = os.path.join(
                                            self.ev['BP_HOME'], self.stg['module_dir'])
        self.stg['site_mod_path']       = os.path.join(
                                            self.ev['BPS_HOME'], self.stg['module_dir'])
        self.stg['pending_path']        = os.path.join(
                                            self.ev['BP_RESULTS'], self.stg['pending_subdir'])
        self.stg['captured_path']       = os.path.join(
                                            self.ev['BP_RESULTS'], self.stg['captured_subdir'])
        self.stg['failed_path']         = os.path.join(
                                            self.ev['BP_RESULTS'], self.stg['failed_subdir'])

        self.stg['script_path']         =os.path.join(
                                            self.ev['BP_HOME'], self.stg['module_dir'])

        # Add some useful key-values
        self.stg['date_str'] = datetime.now().strftime("%Y.%m.%d")
        self.stg['time_str'] = datetime.now().strftime("%Y-%m-%dT%H-%M")

        try:
            self.session['columns'], self.session['rows'] = os.get_terminal_size()
        except:
            self.session['columns'], self.session['rows'] = 640, 480

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
                self.overload_dict['slurm_account'], self.overload_dict['gid'] = [gid[1:] for gid in gid_table if gid[0] == self.stg['working_group']][0]
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

        # Init function library
        self.lib = lib.init(self)

        # Parse $BPS_HOME/package/defaults.ini
        self.read_default_settings()

        # Init valid key list
        self.lib.overload.set_valid_keys()

        # Overwrite defaults with user settings in $BP_HOME/settings.ini
        self.read_user_settings()

        # Derive variables
        self.derived_variables()

        # Parse $BP_HOME/suites.ini
        self.read_suites()

        # Get system label
        self.get_system_label()

        # Run Overloads
        self.lib.overload.replace(None)

        # Add user's app path
        self.bp_apps    += [self.ev['BP_APPS']]
        self.bp_results += [self.ev['BP_RESULTS']]

        # Check group stuff
        self.check_group()

        # Update EV dict from overloads
        self.lib.overload.replace(self.ev)

        # Set module path 
        self.stg['module_path']      = os.path.join(
                                          self.bp_apps[-1], self.stg['module_dir'])


        #print("stg")
        #print(self.stg)

        # Read version info 
        #self.lib.files.get_client_version()
