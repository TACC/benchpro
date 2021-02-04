# System Imports
import configparser as cp
import glob as gb
import os
import re
import subprocess
import sys

# Local Imports
import exception

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Search for unique cfg file in cfg dir
    def search_cfg_str(self, cfg_name, search_path):

        if os.path.isdir(search_path):
            self.glob.log.debug("Looking for " + cfg_name + " in " + self.glob.lib.rel_path(search_path) + "...")
            matches = gb.glob(os.path.join(search_path, "*" + cfg_name + "*"))
            matches.sort()
            # Unique match
            if len(matches) == 1:
                self.glob.log.debug("Found")
                return matches[0]

            # Muliple matches
            elif len(matches) > 1:
                default = [i for i in matches if "default" in i]
                # Check for default
                if len(default) == 1:
                    return default[0]

                # Error
                else:
                    print("Multiple input config files matching '" + cfg_name + "' found in " + self.glob.lib.rel_path(search_path) + ":")
                    for match in matches:
                        print("  " + match.split('/')[-1])
            
                    exception.error_and_quit(self.glob.log, "please provide a unique input config.")

        return None

    # Search path of cfg files for unique match of search list
    def search_cfg_with_list(self, search_list, search_path):

        if os.path.isdir(search_path):
            self.glob.log.debug("Looking for config file in " + self.glob.lib.rel_path(search_path) + "...")
            cfg_list = gb.glob(os.path.join(search_path, "*"))

            # For every cfg file in directory
            for cfg in cfg_list:
                # Ignore directories
                if all(search in cfg for search in search_list):
                    # If all search list elems found, return matching cfg file
                    return cfg      
        return None

    # Check cfg file exists
    def check_file(self, cfg_type, cfg_name):
        suffix = None
        subdir = None

        # If search input is a string, assume user input and search for cfg in various locations
        if isinstance(cfg_name, str):

            self.glob.log.debug("Checking if " + cfg_name + " is a full path...")
            # 1: check if rovided cfg_name is a path
            if cfg_name[0] == "/":
                self.glob.log.debug("Found")
                return cfg_name

            # 2: check for file in user's CWD
            search_path = self.glob.cwd + self.glob.stg['sl']
            self.glob.log.debug("Looking for " + cfg_name + " in " + search_path + "...")
            if os.path.isfile(search_path + cfg_name):
                self.glob.log.debug("Found")
                return search_path + cfg_name

            # 3: check user's HOME
            search_path = os.getenv("HOME") + self.glob.stg['sl']
            self.glob.log.debug("Looking for " + cfg_name + " in " + search_path + "...")
            if os.path.isfile(search_path + cfg_name):
                self.glob.log.debug("Found")
                return search_path + cfg_name


            # 4: check in project basedir
            search_path = self.glob.basedir + self.glob.stg['sl']
            self.glob.log.debug("Looking for " + cfg_name + " in " + self.glob.lib.rel_path(search_path) + "...")
            if os.path.isfile(search_path + cfg_name):
                self.glob.log.debug("Found")
                return search_path + cfg_name
    
            # If not found, cast to list for further searching 
            cfg_name = [cfg_name]

        # Use search list to look in expected places

        # 5: Search cfg dir
        search_path = self.glob.stg['config_path'] + self.glob.stg['sl'] 
        cfg_file = self.search_cfg_with_list(cfg_name, search_path)
        if cfg_file:
            return cfg_file

        # 6: Search 'type' subdir
        search_path = search_path + cfg_type + self.glob.stg['sl']
        cfg_file = self.search_cfg_with_list(cfg_name, search_path)
        if cfg_file:
            return cfg_file

        # 7: Seach system subdir 
        search_path = search_path + self.glob.sys_env + self.glob.stg['sl']
        cfg_file = self.search_cfg_with_list(cfg_name, search_path)
        if cfg_file:
            return cfg_file

        # Not found
        if cfg_type:
            self.glob.lib.misc.print_avail_type(cfg_type, os.path.join(self.glob.stg['config_path'], cfg_type))

            exception.error_and_quit(self.glob.log, "config file containing '" + ", ".join(cfg_name) + "' not found.")

        else:
            exception.error_and_quit(self.glob.log, "input file containing '" + ", ".join(cfg_name) + "' not found.")
       

    # Find matching config file given search criteria
    def find_cfg(self, search_dict, avail_cfgs):
    
        matching_cfgs = []

        # Iter over all avail cfg files
        for cfg in avail_cfgs:

            # Iter over all search terms
            match = True
            for key in search_dict.keys():

                # For each section of cfg    
                for sec in cfg.keys():
                    # If key is in cfg section
                    if key in cfg[sec].keys():
                        # If value set in cfg 
                        if cfg[sec][key]:
                            # If not equal to search, not a match
                            if not search_dict[key] == cfg[sec][key]:
                                match = False
                        # Overload key with search term
                        else:
                            cfg[sec][key] = search_dict[key]

            # If match, add to list
            if match:
                matching_cfgs.append(cfg)

  


        if not matching_cfgs:
            exception.error_and_quit(self.glob.log, "no matching config file found matching search criteria '" + ", ".join([key + " = " + search_dict[key] for key in search_dict.keys()]) + "'")

        elif len(matching_cfgs) == 1:
            return matching_cfgs[0]

        else:
            exception.error_and_quit(self.glob.log, "multiple config files found matching search criteria '" + ", ".join([key + " = " + search_dict[key] for key in search_dict.keys()]) + "':")
            for cfg in matching_cfgs:
                print("    " + self.glob.lib.rel_path(cfg))

    # Parse cfg file into dict
    def read_file(self, cfg_file):
        cfg_parser = cp.ConfigParser()
        cfg_parser.optionxform=str
        cfg_parser.read(cfg_file)
    
        # Add file name & label to dict
        cfg_dict = {}
        cfg_dict['metadata'] ={}

        cfg_dict['metadata']['cfg_label'] = ".".join(cfg_file.split(self.glob.stg['sl'])[-1].split(".")[:-1])
        cfg_dict['metadata']['cfg_file']  = cfg_file

        # Read sections into dict 
        for section in cfg_parser.sections():
            cfg_dict[section] = dict(cfg_parser.items(section))

        return cfg_dict

    # Error if section heading missing in cfg file
    def check_dict_section(self, cfg_file, cfg_dict, section):
        if not section in cfg_dict:
            exception.error_and_quit(self.glob.log, "["+section+"] section heading required in " + self.glob.lib.rel_path(cfg_file) + \
                                    ". Consult the documentation.")

    # Error if value missing in cfg file
    def check_dict_key(self, cfg_file, cfg_dict, section, key):
        # If key not found 
        if not key in cfg_dict[section]:
            exception.error_and_quit(self.glob.log, "'" + key + "' value must be present in section [" + section + \
                                    "] in " + self.glob.lib.rel_path(cfg_file) + ". Consult the documentation.")
        # If key not set
        if not cfg_dict[section][key]:
            exception.error_and_quit(self.glob.log, "'" + key + "' value must be non-null in section [" + section + \
                                    "] in " + self.glob.lib.rel_path(cfg_file) + ". Consult the documentation.")

    # Convert strings to correct dtype if detected
    def get_val_types(self, cfg_dict):
        for sect in cfg_dict:
            for key in cfg_dict[sect]:

                # If cfg value is string, try cast it to other types
                if isinstance(cfg_dict[sect][key], str):
                    if cfg_dict[sect][key] in  ["True", "true"]:
                        cfg_dict[sect][key] = True
                    # Test if False
                    elif cfg_dict[sect][key] in ["False", "false"]:
                        cfg_dict[sect][key] = False
                    # Test if int
                    elif cfg_dict[sect][key].isdigit():
                        cfg_dict[sect][key] =  int(cfg_dict[sect][key])

    # Check build config file and add required fields
    def process_build_cfg(self, cfg_dict):

        # Check for missing essential parameters 
        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'general')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'code')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'version')

        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'compiler')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'mpi')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'config')

        # Instantiate missing optional parameters
        if not 'system'           in cfg_dict['general'].keys():  cfg_dict['general']['system']         = self.glob.sys_env
        if not 'build_prefix'     in cfg_dict['general'].keys():  cfg_dict['general']['build_prefix']   = ""
        if not 'template'         in cfg_dict['general'].keys():  cfg_dict['general']['template']       = ""
        if not 'module_use'       in cfg_dict['general'].keys():  cfg_dict['general']['module_use']     = ""
        if not 'sched_cfg'        in cfg_dict['general'].keys():  cfg_dict['general']['sched_cfg']      = ""

        if not 'exe'              in cfg_dict['config'].keys():    cfg_dict['config']['exe']              = ""
        if not 'arch'             in cfg_dict['config'].keys():    cfg_dict['config']['arch']             = ""
        if not 'opt_flags'        in cfg_dict['config'].keys():    cfg_dict['config']['opt_flags']        = ""  
        if not 'build_label'      in cfg_dict['config'].keys():    cfg_dict['config']['build_label']      = ""
        if not 'bin_dir'          in cfg_dict['config'].keys():    cfg_dict['config']['bin_dir']          = ""
        if not 'collect_hw_stats' in cfg_dict['config'].keys():    cfg_dict['config']['collect_hw_stats'] = False

        # Convert dtypes
        self.get_val_types(cfg_dict)

        # Extract compiler type from label by splitting by / and removing ints
        cfg_dict['config']['compiler_type'] = re.sub("\d", "", cfg_dict['modules']['compiler'].split('/')[0])

        # Path to application's data directory
        cfg_dict['config']['benchmark_repo'] = self.glob.stg['benchmark_repo']

        self.glob.lib.overload_params(cfg_dict)

        # Get system from env if not defined
        if not cfg_dict['general']['system']:
            self.glob.log.debug("WARNING: 'system' not defined in " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
            self.glob.log.debug("WARNING: getting system label from $TACC_SYSTEM: " + self.glob.sys_env)
            cfg_dict['general']['system'] = self.glob.sys_env
            if not cfg_dict['general']['system']:
                exception.error_and_quit(self.glob.log, "$TACC_SYSTEM not set, unable to continue. Please define 'system' in " + \
                                        self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))

        # Set system variables from system.cfg
        self.glob.system = self.glob.lib.get_system_vars(cfg_dict['general']['system'])

        # Check that system settings were successfully parserd from file
        if not self.glob.system:
            exception.error_and_quit(self.glob.log, "Failed to read system profile '"+ cfg_dict['requirements']['system'] +"' in " + \
                                        self.glob.lib.rel_path(os.path.join(self.glob.stg['config_basedir'], self.glob.stg['system_cfg_file'])) + \
                                        "\nPlease add this system profile.")

        # Check requested modules exist, and if so, result full module names
        if self.glob.stg['check_modules']:
            self.glob.lib.check_module_exists(cfg_dict['modules'], cfg_dict['general']['module_use'])

        # Parse architecture defaults config file 
        arch_file = self.check_file('arch', self.glob.stg['config_path'] + self.glob.stg['sl'] + self.glob.stg['arch_cfg_file'])
        arch_dict = self.read_file(arch_file)

        # Get core count for system
        try:
            cfg_dict['config']['cores'] = self.glob.system['cores_per_node']
            self.glob.log.debug("Core count for " + cfg_dict['general']['system'] + " = " + cfg_dict['config']['cores'])

        except:
            exception.error_and_quit(self.glob.log, "system profile '" + cfg_dict['general']['system'] + \
                                    "' missing in " + self.glob.lib.rel_path(system_file))

        # If arch requested = 'system', get default arch for this system
        if cfg_dict['config']['arch'] == 'system' or not cfg_dict['config']['arch']:
            cfg_dict['config']['arch'] = self.glob.system['default_arch']
            self.glob.log.debug("Requested build arch='default'. Using system default for " + cfg_dict['general']['system'] + \
                            " = " + cfg_dict['config']['arch'])

        # If using custom opt_flags, must provide build_label
        if cfg_dict['config']['opt_flags'] and not cfg_dict['config']['build_label']:
            exception.error_and_quit(self.glob.log, "if building with custom optimization flags, please define a " + \
                                    "'build_label in [build] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))

        # Get default optimization flags based on system arch
        if not cfg_dict['config']['opt_flags']:
            try:
                cfg_dict['config']['opt_flags'] = arch_dict[cfg_dict['config']['arch']][cfg_dict['config']['compiler_type']]
            except:
                exception.print_warning(self.glob.log, "Unable to determine default optimization flags for '" + \
                                        cfg_dict['config']['compiler_type'] + "' compiler " + \
                                        "on arch '" + cfg_dict['config']['arch'] + "'")

        # Set default build label
        if not cfg_dict['config']['build_label']:
            cfg_dict['config']['build_label'] = 'default'

        # Generate default build path if one is not defined
        if not cfg_dict['general']['build_prefix']:
            cfg_dict['metadata']['working_path'] = os.path.join(self.glob.stg['build_path'], \
                                                                cfg_dict['general']['system'], \
                                                                cfg_dict['config']['arch'],\
                                                                self.glob.lib.get_module_label(cfg_dict['modules']['compiler']), \
                                                                self.glob.lib.get_module_label(cfg_dict['modules']['mpi']), \
                                                                cfg_dict['general']['code'], str(cfg_dict['general']['version']), \
                                                                cfg_dict['config']['build_label'])

        # Translate 'build_prefix' to 'working_path' for better readability
        else:
            cfg_dict['metadata']['working_path'] = cfg_dict['general']['build_prefix']

        # Get build and install subdirs
        cfg_dict['metadata']['build_path']   = os.path.join(cfg_dict['metadata']['working_path'], self.glob.stg['build_subdir'])
        cfg_dict['metadata']['install_path'] = os.path.join(cfg_dict['metadata']['working_path'], self.glob.stg['install_subdir'])

        # Overload params from cmdline
        self.glob.lib.overload_params(cfg_dict)

        # Set sched nodes to 1 for build jobs
        cfg_dict['config']['nodes'] = 1

    # Check bench config file and add required fields
    def process_bench_cfg(self, cfg_dict):

        # Check for missing essential parameters
        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'runtime')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'runtime', 'nodes')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'runtime', 'threads')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'config')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'config', 'dataset')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'result')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'method')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'unit')

        # Instantiate missing optional parameters

        if not 'code'               in cfg_dict['requirements'].keys():  cfg_dict['requirements']['code']    = ""
        if not 'version'            in cfg_dict['requirements'].keys():  cfg_dict['requirements']['version'] = ""
        if not 'build_label'        in cfg_dict['requirements'].keys():  cfg_dict['requirements']['label']   = ""
        if not 'system'             in cfg_dict['requirements'].keys():  cfg_dict['requirements']['system']  = ""

        if not 'ranks_per_node'     in cfg_dict['runtime'].keys():  cfg_dict['runtime']['ranks_per_node']    = 0
        if not 'max_running_jobs'   in cfg_dict['runtime'].keys():  cfg_dict['runtime']['max_running_jobs']  = 10
        if not 'hostfile'           in cfg_dict['runtime'].keys():  cfg_dict['runtime']['hostfile']          = ""
        if not 'hostlist'           in cfg_dict['runtime'].keys():  cfg_dict['runtime']['hostlist']          = ""

        if not 'exe'                in cfg_dict['config'].keys():    cfg_dict['config']['exe']               = ""
        if not 'bench_label'        in cfg_dict['config'].keys():    cfg_dict['config']['label']             = ""
        if not 'template'           in cfg_dict['config'].keys():    cfg_dict['config']['template']          = ""
        if not 'collect_hw_stats'   in cfg_dict['config'].keys():    cfg_dict['config']['collect_hw_stats']  = False
        if not 'gpus'               in cfg_dict['config'].keys():    cfg_dict['config']['gpus']              = 0

        if not 'description'        in cfg_dict['result'].keys():   cfg_dict['result']['description']        = ""
        if not 'output_file'        in cfg_dict['result'].keys():   cfg_dict['result']['output_file']        = ""

        # Convert cfg keys to correct datatype
        self.get_val_types(cfg_dict)

        # Overload params from cmdline
        self.glob.lib.overload_params(cfg_dict)

        # If system not specified for bench requirements, add current system
        if not cfg_dict['requirements']['system']:
            cfg_dict['requirements']['system'] = self.glob.sys_env
    
        # Set system variables from system.cfg
        self.glob.system = self.glob.lib.get_system_vars(cfg_dict['requirements']['system'])
    
        # Check that system settings were successfully parserd from file
        if not self.glob.system:
            exception.error_and_quit(self.glob.log, "Failed to read system profile '"+ cfg_dict['requirements']['system'] +"' in " + \
                                        self.glob.lib.rel_path(os.path.join(self.glob.stg['config_basedir'], self.glob.stg['system_cfg_file'])) + \
                                        "\nPlease add this system profile.")

        # Set default 1 rank per core, if not defined
        if not cfg_dict['runtime']['ranks_per_node']:
            cfg_dict['runtime']['ranks_per_node'] = self.glob.system['cores_per_node']

        # Expression method
        if cfg_dict['result']['method'] == "expr":
            if not 'expr' in cfg_dict['result']:
                exception.error_and_quit(self.glob.log, "if using 'expr' result validation method, 'expr'" + \
                                " key is required in [result] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
        # Script method
        elif cfg_dict['result']['method'] == "script":
            if not 'script' in cfg_dict['result']:
                exception.error_and_quit(self.glob.log, "if using 'script' result validation method, 'script'" + \
                                " key is required in [result] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
        # 'method' not == 'expr' or 'script'
        else:
            exception.error_and_quit(self.glob.log, "'method' key in [result] section of " + \
                                cfg_dict['metadata']['cfg_file'] + "must be either expr or script." )

        # If benchmark uses GPUs, delimit any lists
        if cfg_dict['config']['gpus']:
            cfg_dict['config']['gpus']          = str(cfg_dict['config']['gpus']).split(",")

        # Handle comma-delimited lists
        cfg_dict['runtime']['nodes']            = str(cfg_dict['runtime']['nodes']).split(",")
        cfg_dict['runtime']['threads']          = str(cfg_dict['runtime']['threads']).split(",")
        cfg_dict['runtime']['ranks_per_node']   = str(cfg_dict['runtime']['ranks_per_node']).split(",")

        # num threads must equal num ranks
        if not len(cfg_dict['runtime']['threads']) == len(cfg_dict['runtime']['ranks_per_node']):
            if len(cfg_dict['runtime']['threads']) == 1:
                cfg_dict['runtime']['threads'] = [cfg_dict['runtime']['threads'][0]] * len(cfg_dict['runtime']['ranks_per_node'])
            elif len(cfg_dict['runtime']['ranks_per_node']) == 1:
                cfg_dict['runtime']['ranks_per_node'] = [cfg_dict['runtime']['ranks_per_node'][0]] * len(cfg_dict['runtime']['threads'])
            else:
                exception.error_and_quit(self.glob.log, "input mismatch: 'threads' and 'ranks_per_node' lists must be of equal length in " + \
                                    self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
    
        # Require label if code not set
        if not cfg_dict['requirements']['code'] and not cfg_dict['config']['label']:
            exception.error_and_quit(self.glob.log, "if 'code' is not set, provide 'label' in " + \
                                    self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
    
        #Check bench_mode in set correctly
        if self.glob.stg['bench_mode'] not in  ["sched", "local"]:
            exception.error_and_quit(self.glob.log, "Unsupported benchmark execution mode found: '"+glob.stg['bench_mode']+ \
                                    "' in settings.ini, please specify 'sched' or 'local'.")
    
        # Check for hostfile/hostlist if exec_mode is local (mpirun)
        if self.glob.stg['bench_mode'] == "local":
            # Both hostfile and hostlist is set?
            if cfg_dict['runtime']['hostfile'] and cfg_dict['runtime']['hostlist']:
                exception.error_and_quit(self.glob.log, "both 'hostlist' and 'hostfile' set in " + \
                                        self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']) + ", please provide only one.")
    
            # Define --hostfile args
            if cfg_dict['runtime']['hostfile']:
                hostfile = self.check_file("", cfg_dict['runtime']['hostfile'])
                cfg_dict['runtime']['host_str'] = "-hostfile " + hostfile
    
            # Define -host args
            elif cfg_dict['runtime']['hostlist']:
                cfg_dict['runtime']['host_str'] = "-host " + cfg_dict['runtime']['hostlist'].strip(" ")
    
            # Error if neither is set
            else:
                exception.error_and_quit(self.glob.log, "if using 'bench_mode=local' in settings.ini, " + \
                                        "provide either a 'hostfile' or 'hostlist' under [runtime] in " + \
                                        self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
    
        # Deal with empty values
        if not cfg_dict['runtime']['max_running_jobs']:
            cfg_dict['runtime']['max_running_jobs'] = 10
    
    # Check sched config file and add required fields
    def process_sched_cfg(self, cfg_dict):
    
        # Check for missing essential parameters
        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'type')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'queue')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'account')
    
        # Instantiate missing optional parameters
        if not 'reservation' in    cfg_dict['sched'].keys():   cfg_dict['sched']['reservation']   = ""
    
        self.glob.lib.overload_params(cfg_dict)
    
        # Fill missing parameters
        if not cfg_dict['sched']['runtime']:
            cfg_dict['sched']['runtime'] = '02:00:00'
            self.glob.log.debug("Set runtime = " + cfg_dict['sched']['runtime'])
        if not cfg_dict['sched']['threads']:
            cfg_dict['sched']['threads'] = 1
            self.glob.log.debug("Set threads = " + cfg_dict['sched']['threads'])
    
    # Read input param config and test 
    def ingest(self, cfg_type, search_dict):


        # Check input file exists
        #cfg_file = self.check_file(cfg_type, cfg_search)
    
        # Parse input fo;e
        #cfg_dict = self.read_file(cfg_file)
    
        # Process and store build cfg 
        if cfg_type == 'build':

            cfg_dict = self.find_cfg(search_dict, self.glob.build_cfgs)
            self.glob.log.debug("Starting build cfg processing.")
            self.process_build_cfg(cfg_dict)
            self.glob.code = cfg_dict
    
        # Process and store bench cfg 
        elif cfg_type == 'bench':
            cfg_dict = self.find_cfg(search_dict, self.glob.bench_cfgs)
            self.glob.log.debug("Starting bench cfg processing.")
            self.process_bench_cfg(cfg_dict)
            self.glob.code = cfg_dict
    
        # Process and store sched cfg 
        elif cfg_type == 'sched':

            cfg_file = self.check_file(cfg_type, search_dict)
            cfg_dict = self.read_file(cfg_file)
            self.glob.log.debug("Starting sched cfg processing.")
            self.process_sched_cfg(cfg_dict)
            self.glob.sched = cfg_dict
    
        # Process and store compiler cfg 
        elif cfg_type == 'compiler':
            cfg_file = self.check_file(cfg_type, search_dict)
            cfg_dict = self.read_file(cfg_file)
            self.glob.compiler = cfg_dict
    
    
