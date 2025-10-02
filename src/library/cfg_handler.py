# System Imports
import copy
import glob as gb
import os
import re
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Search path of cfg files for unique match of search list
    def search_cfg_with_list(self, search_list, search_path):

        if os.path.isdir(search_path):
            self.glob.lib.msg.log("Looking for config file in " + self.glob.lib.rel_path(search_path) + "...")
            cfg_list = gb.glob(os.path.join(search_path, "*"))

            # For every cfg file in directory
            for cfg in cfg_list:
                # Ignore directories
                if all(search in cfg for search in search_list):
                    # If all search list elems found, return matching cfg file
                    return cfg      
        return None

    # Find matching config file given search criteria
    def search_cfg_with_dict(self, search_dict, avail_cfgs_list, blanks_are_wild):

        matching_cfgs = []
        # Iter over all avail cfg files

        for avail_cfgs in avail_cfgs_list:
            for cfg in avail_cfgs:
                # Iter over all search terms
                match = True
                found = False

                for key in search_dict.keys():
                    # For each section of cfg
                    for sec in cfg.keys():
                        # If key is in cfg section and we can match to blank values
                        if key in cfg[sec].keys():
                            found = True
                            # 1: both set but not equal = NO MATCH
                            if search_dict[key] and cfg[sec][key] and not search_dict[key] == cfg[sec][key]:
                                match = False
                            # 2: if search dict contains value missing in cfg
                            elif search_dict[key] and not cfg[sec][key]:
                                # allow blank wildcards
                                if blanks_are_wild:
                                    cfg[sec][key] = search_dict[key]
                                else:
                                    match = False

                            # 3: if cfg contains value missing in search dict and wildcards not allowed
                            elif cfg[sec][key] and not search_dict[key] and not blanks_are_wild:
                                match = False

                # If match, add to list
                if match and found:
                    matching_cfgs.append(cfg)

            # Match found in this direct
            if len(matching_cfgs) == 1:
                return matching_cfgs[0]

            # Multiple cfgs found
            elif len(matching_cfgs) > 1:
                for cfg in matching_cfgs:
                    print("    " + self.glob.lib.rel_path(cfg['metadata']['cfg_file']))
                self.glob.lib.msg.error("Multiple config files found matching search criteria '" + ",".join([key + "=" + search_dict[key] for key in search_dict.keys()]) + "'")

        # No matches after scanning all dirs
        if not matching_cfgs:
            self.glob.lib.msg.error("No config file found matching search criteria '" + ",".join([key + "=" + str(search_dict[key]) for key in search_dict.keys()]) + "'")

    # Check cfg file exists
    def find_cfg_file(self, cfg_type, cfg_name):
        suffix = None
        subdir = None

        # If search input is a string, assume user input and search for cfg in various locations
#        if isinstance(cfg_name, str):
#            cfg_found = self.glob.lib.files.find_in([self.glob.stg['site_sys_cfg_path'],
#                                                    self.glob.stg['sched_cfg_path'],
#                                                    self.glob.ev['BP_HOME']],
#                                                    cfg_name, True)
#            if cfg_found:
#               return cfg_found

        search_path_list = [self.glob.stg['site_sys_cfg_path'],
                            self.glob.stg['sched_cfg_path'],
                            self.glob.ev['BP_HOME']]

        
        for search_path in search_path_list:
            cfg_file = self.search_cfg_with_list(cfg_name, search_path)
            if cfg_file:
                return cfg_file

        # Not found
        if cfg_type:
            self.glob.lib.msg.error("config file containing '" + ", ".join(cfg_name) + "' not found.")

        else:
            self.glob.lib.msg.error("input file containing '" + ", ".join(cfg_name) + "' not found.")
       
    # Error if section heading missing in cfg file
    def check_dict_section(self, cfg_file, cfg_dict, section):
        if not section in cfg_dict:
            self.glob.lib.msg.error("["+section+"] section heading required in " + self.glob.lib.rel_path(cfg_file) + \
                                    ". Consult the documentation.")

    # Error if value missing in cfg file
    def check_dict_key(self, cfg_file, cfg_dict, section, key):
        # If key not found 
        if not key in cfg_dict[section]:
            self.glob.lib.msg.error("'" + key + "' value must be present in section [" + section + \
                                    "] in " + self.glob.lib.rel_path(cfg_file) + ". Consult the documentation.")
        # If key not set
        if not cfg_dict[section][key]:
            self.glob.lib.msg.error("'" + key + "' value must be non-null in section [" + section + \
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

    # Accept a 'overload' section in build/bench config file to overload global settings
    def add_overloads(self, overloads):

        # Add key-values to overload dict
        for key in overloads:
            if key not in self.glob.overload_dict.keys():
                self.glob.overload_dict[key] = str(overloads[key])
            else:
                self.glob.lib.msg.warn("ignoring duplicate overload '" + key + "=" + overloads[key] + "'")

        # Run overload search
        self.glob.lib.overload.replace(None)

    # Check if the additions file is findable
    def additions_file_location(self, additions_file):
        return self.glob.lib.files.find_in([self.glob.stg['user_resource_path'], self.glob.stg['site_resource_path']], additions_file, True)

    # Generate module metadata from user input
    def setup_module_dict(self, cfg_dict):

        # Generate list of default modules
        self.glob.lib.module.set_default_module_list(cfg_dict['general']['module_use'])



        # Process each module
        for key in cfg_dict['modules']:

            mod = cfg_dict['modules'][key]
    
            # Skip if value = NULL
            if not mod:
                self.glob.lib.msg.warn("Ignoring Null module key '" + key + "'")
                continue

            self.glob.modules[key]  = { 'input':    mod,
                                        'full':     self.glob.lib.module.check_module_exists(key, mod),
                                        'label':    key,
                                        'type':     ""
                                      }

            # Get filesystem safe module name from full version
            self.glob.modules[key]['safe']  = self.glob.lib.module.get_label(self.glob.modules[key]['full']) 
           
            # Check name was resolved successfully - fail if compiler or mpi (required)
            if not self.glob.modules[key]['full']:
                self.glob.lib.msg.error("Failed to identify module '" + self.glob.modules[key]['input'] + "'")

            # Store module version
            self.glob.modules[key]['version'] = self.glob.modules[key]['full'].split('/')[-1]

            # Set type for compiler/mpi
            if key in ["compiler", "mpi"]:
                self.glob.modules[key]['type']   = self.glob.modules[key]['full'].split('/')[0]
                

                # Add special version check: intel > 20: type += oneapi
#                if (self.glob.modules[key]['type'] == "intel") and (int(self.glob.modules[key]['version'].split('.')[0]) > 20):
#                    # Prioritize oneapi
#                    self.glob.modules[key]['type'] = "oneapi"


            # Add compiler name conversion for for modules
            if self.glob.modules[key]['type'] in self.glob.mod_name_map: 
                self.glob.modules[key]['type'] = self.glob.mod_name_map[self.glob.modules[key]['type']]



    # Check build config file and add required fields
    def process_build_cfg(self, cfg_dict):
        # Check for missing essential parameters 
        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'general')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'code')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'general', 'version')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'compiler')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'modules', 'mpi')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'config')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'config', 'exe')

        # Instantiate missing optional parameters
        if not 'system'           in cfg_dict['general'].keys():  cfg_dict['general']['system']         = self.glob.system['system']
        if not 'build_prefix'     in cfg_dict['general'].keys():  cfg_dict['general']['build_prefix']   = ""
        if not 'template'         in cfg_dict['general'].keys():  cfg_dict['general']['template']       = ""
        if not 'module_use'       in cfg_dict['general'].keys():  cfg_dict['general']['module_use']     = ""
        if not 'sched_cfg'        in cfg_dict['general'].keys():  cfg_dict['general']['sched_cfg']      = ""

        if not 'arch'             in cfg_dict['config'].keys():    cfg_dict['config']['arch']             = ""
        if not 'opt_flags'        in cfg_dict['config'].keys():    cfg_dict['config']['opt_flags']        = ""  
        if not 'build_label'      in cfg_dict['config'].keys():    cfg_dict['config']['build_label']      = ""
        if not 'bin_dir'          in cfg_dict['config'].keys():    cfg_dict['config']['bin_dir']          = ""
        if not 'collect_stats'    in cfg_dict['config'].keys():    cfg_dict['config']['collect_stats']    = False
        if not 'script_additions' in cfg_dict['config'].keys():    cfg_dict['config']['script_additions'] = ""

        # Add sections if missing
        if not 'requirements'     in cfg_dict.keys():              cfg_dict['requirements']     = {}
        if not 'runtime'          in cfg_dict.keys():              cfg_dict['runtime']          = {}
        if not 'result'           in cfg_dict.keys():              cfg_dict['result']           = {}
        if not 'files'            in cfg_dict.keys():              cfg_dict['files']            = {}
        if not 'overload'         in cfg_dict.keys():              cfg_dict['overload']         = {}

        # --- Apply defaults ---

        # Evaluate expressions in [general]
        self.glob.lib.expr.eval_dict(cfg_dict['general'], False)

        # Convert dtypes
        self.get_val_types(cfg_dict)

        # Add overload params to overload dict
        self.add_overloads(cfg_dict['overload'])

        # ------ Apply overloads -------
        # Need to apply specific overloads before compiler parsing

        self.glob.lib.overload.replace(cfg_dict['general'])
        self.glob.lib.overload.replace(cfg_dict['modules'])
        self.glob.lib.overload.replace(cfg_dict['config'])

        # Process requested modules
        self.setup_module_dict(cfg_dict)

        # Path to application's data directory
        cfg_dict['config']['local_repo'] = self.glob.ev['BP_REPO']

        # Get system from env if not defined
        if not cfg_dict['general']['system']:
            self.glob.lib.msg.log("WARNING: 'system' not defined in " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
            self.glob.lib.msg.log("WARNING: getting system label from :" + self.glob.stg['system_env'] + " " + self.glob.system['system'])
            cfg_dict['general']['system'] = self.glob.system['system']
            if not cfg_dict['general']['system']:
                self.glob.lib.msg.error(self.glob.stg['system_env'] + " not set, unable to continue. Please define 'system' in " + \
                                        self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))

        # Set system variables from system.cfg
        self.glob.lib.get_system_vars(cfg_dict['general']['system'])

        # Confirm additions file exists if set
        if cfg_dict['config']['script_additions']:
            cfg_dict['config']['script_additions'] = self.additions_file_location(cfg_dict['config']['script_additions'])

        # Parse architecture defaults config file 
        arch_file = os.path.join(self.glob.stg['site_sys_cfg_path'], self.glob.stg['arch_cfg_file'])
        arch_dict = self.glob.lib.files.read_cfg(arch_file)

        # Get core count for system
        try:
            cfg_dict['config']['cores'] = self.glob.system['cores_per_node']
            self.glob.lib.msg.log("Core count for " + cfg_dict['general']['system'] + " = " + cfg_dict['config']['cores'])

        except:
            self.glob.lib.msg.error("system profile '" + cfg_dict['general']['system'] + \
                                    "' missing in " + self.glob.lib.rel_path(system_file))

        # If arch requested = 'system', get default arch for this system
        if cfg_dict['config']['arch'] == 'system' or not cfg_dict['config']['arch']:
            cfg_dict['config']['arch'] = self.glob.system['default_arch']
            self.glob.lib.msg.log("Requested build arch='default'. Using system default for " + cfg_dict['general']['system'] + \
                            " = " + cfg_dict['config']['arch'])

        # If using custom opt_flags, must provide build_label
        if cfg_dict['config']['opt_flags'] and not cfg_dict['config']['build_label']:
            self.glob.lib.msg.error("if building with custom optimization flags, please define a " + \
                                    "'build_label in [build] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))

        # Get default optimization flags based on system arch
        if not cfg_dict['config']['opt_flags']:

            # if comp_type available for this architecture
            if 'compiler' in self.glob.modules:
                if self.glob.modules['compiler']['type'] in arch_dict[cfg_dict['config']['arch']].keys():
                        cfg_dict['config']['opt_flags'] = arch_dict[cfg_dict['config']['arch']][self.glob.modules['compiler']['type']]

            # Print warning if no matching compiler key not set for this archicture
                else:
                    self.glob.lib.msg.warn("Unable to determine default optimization flags for '" + \
                                            self.glob.modules['compiler']['type'] + "' compiler label(s) " + \
                                            "on arch '" + cfg_dict['config']['arch'] + "'")
            else:
                self.glob.lib.msg.warn("No compiler module provided.")

        # Set default build label
        if not cfg_dict['config']['build_label']:
            cfg_dict['config']['build_label'] = 'default'

        # ----- Generate metadata ------

        # Generate default build path if one is not defined
        if not cfg_dict['general']['build_prefix']:
            cfg_dict['metadata']['working_dir']  = os.path.join(cfg_dict['general']['system'],
                                                                cfg_dict['config']['arch'],
                                                                self.glob.modules['compiler']['safe'],
                                                                self.glob.modules['mpi']['safe'],
                                                                cfg_dict['general']['code'], str(cfg_dict['general']['version']),
                                                                cfg_dict['config']['build_label'])

            cfg_dict['metadata']['working_path'] = os.path.join(self.glob.bp_apps[-1], 
                                                                cfg_dict['metadata']['working_dir'])

        # Translate 'build_prefix' to 'working_path' for better readability
        else:
            cfg_dict['metadata']['working_path'] = cfg_dict['general']['build_prefix']

        # Get build and install subdirs
        cfg_dict['metadata']['build_path']   = os.path.join(cfg_dict['metadata']['working_path'], self.glob.stg['build_subdir'])
        cfg_dict['metadata']['install_path'] = os.path.join(cfg_dict['metadata']['working_path'], self.glob.stg['install_subdir'])

        # Path to copy files to
        cfg_dict['metadata']['copy_path']    = cfg_dict['metadata']['build_path']

        if self.glob.stg['exec_mode'] == "sched" and not cfg_dict['general']['sched_cfg']:
            cfg_dict['general']['sched_cfg'] = os.path.join(self.glob.stg['sched_cfg_path'], self.glob.system['default_sched'])

        # Set sched nodes to 1 for build jobs
        cfg_dict['config']['nodes'] = 1

        #Set stdout and stderr
        cfg_dict['config']['stdout'] = "stdout.log"
        cfg_dict['config']['stderr'] = "stderr.log"

    # Check bench config file and add required fields
    def process_bench_cfg(self, cfg_dict):
        # Check for missing essential parameters

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'requirements')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'runtime')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'runtime', 'nodes')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'config')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'config', 'dataset')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'config', 'bench_label')

        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'result')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'result', 'method')

        # Add sections if missing
        if not 'general'          in cfg_dict.keys():              cfg_dict['general'] = {}
        if not 'files'            in cfg_dict.keys():              cfg_dict['files'] = {}
        if not 'overload'         in cfg_dict.keys():              cfg_dict['overload'] = {}

        # Instantiate missing optional parameters
        if not 'code'               in cfg_dict['requirements'].keys():  cfg_dict['requirements']['code']       = ""
        if not 'version'            in cfg_dict['requirements'].keys():  cfg_dict['requirements']['version']    = ""
        if not 'build_label'        in cfg_dict['requirements'].keys():  cfg_dict['requirements']['build_label']= ""
        if not 'system'             in cfg_dict['requirements'].keys():  cfg_dict['requirements']['system']     = ""
        if not 'compiler'           in cfg_dict['requirements'].keys():  cfg_dict['requirements']['compiler']   = ""
        if not 'mpi'                in cfg_dict['requirements'].keys():  cfg_dict['requirements']['mpi']        = ""
        if not 'task_id'            in cfg_dict['requirements'].keys():  cfg_dict['requirements']['task_id']    = ""

        if not 'threads'            in cfg_dict['runtime'].keys():  cfg_dict['runtime']['threads']              = 0
        if not 'ranks_per_node'     in cfg_dict['runtime'].keys():  cfg_dict['runtime']['ranks_per_node']       = 0
        if not 'max_running_jobs'   in cfg_dict['runtime'].keys():  cfg_dict['runtime']['max_running_jobs']     = 10
        if not 'gpus'               in cfg_dict['runtime'].keys():  cfg_dict['runtime']['gpus']                 = 0
        if not 'hostfile'           in cfg_dict['runtime'].keys():  cfg_dict['runtime']['hostfile']             = ""
        if not 'hostlist'           in cfg_dict['runtime'].keys():  cfg_dict['runtime']['hostlist']             = ""

        if not 'exe'                in cfg_dict['config'].keys():    cfg_dict['config']['exe']                  = ""
        if not 'template'           in cfg_dict['config'].keys():    cfg_dict['config']['template']             = ""
        if not 'collect_stats'      in cfg_dict['config'].keys():    cfg_dict['config']['collect_stats']        = False
        if not 'script_additions'   in cfg_dict['config'].keys():    cfg_dict['config']['script_additions']     = ""
        if not 'arch'               in cfg_dict['config'].keys():    cfg_dict['config']['arch']                 = ""

        if not 'description'        in cfg_dict['result'].keys():   cfg_dict['result']['description']           = ""
        if not 'output_file'        in cfg_dict['result'].keys():   cfg_dict['result']['output_file']           = ""
        if not 'unit'               in cfg_dict['result'].keys():   cfg_dict['result']['unit']                  = ""

        #if not 'inherit'            in cfg_dict['overload'].keys():	cfg_dict['overload']['inherit']             = ""


        # Convert cfg keys to correct datatype
        self.get_val_types(cfg_dict)

        # Inherit from parent
        #if cfg_dict['overload']['inherit']:
        #    self.inherit("bench", cfg_dict['overload']['inherit'])

        # Add overload params to overload dict
        self.add_overloads(cfg_dict['overload'])

        # Overload params from cmdline
        self.glob.lib.overload.replace(cfg_dict['requirements'])

        # Path to data directory
        cfg_dict['config']['local_repo'] = self.glob.ev['BP_REPO']

        # If system not specified for bench requirements, add current system
        if not cfg_dict['requirements']['system']:
            cfg_dict['requirements']['system'] = self.glob.system['system']

        # Set system variables from system.cfg
        self.glob.lib.get_system_vars(cfg_dict['requirements']['system'])
    
        # Set default 1 rank per core, if not defined
        if not cfg_dict['runtime']['ranks_per_node']:
            cfg_dict['runtime']['ranks_per_node'] = self.glob.system['cores_per_node']

        # Confirm additions file exists if set
        if cfg_dict['config']['script_additions']:
            cfg_dict['config']['script_additions'] = self.additions_file_location(cfg_dict['config']['script_additions'])

        # Expression method
        if cfg_dict['result']['method'] == "expr":
            if not 'expr' in cfg_dict['result']:
                self.glob.lib.msg.error("if using 'expr' result validation method, 'expr'" + \
                                " key is required in [result] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
        # Script method
        elif cfg_dict['result']['method'] == "script":
            if not 'script' in cfg_dict['result']:
                self.glob.lib.msg.error("if using 'script' result validation method, 'script'" + \
                                " key is required in [result] section of " + self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
        # 'method' not == 'expr' or 'script'
        else:
            self.glob.lib.msg.error("'method' key in [result] section of " + \
                                cfg_dict['metadata']['cfg_file'] + "must be either expr or script." )


        # If threads not set, make equal to number of cores per socket
        if not cfg_dict['runtime']['threads']:
            cfg_dict['runtime']['threads'] = self.glob.system['cores_per_socket']

        # Handle comma-delimited lists
        cfg_dict['runtime']['nodes']            = str(cfg_dict['runtime']['nodes']).split(",")
        cfg_dict['runtime']['threads']          = str(cfg_dict['runtime']['threads']).split(",")
        cfg_dict['runtime']['ranks_per_node']   = str(cfg_dict['runtime']['ranks_per_node']).split(",")
        cfg_dict['runtime']['gpus']             = str(cfg_dict['runtime']['gpus']).split(",")

        # num threads must equal num ranks
        if not len(cfg_dict['runtime']['threads']) == len(cfg_dict['runtime']['ranks_per_node']):
            if len(cfg_dict['runtime']['threads']) == 1:
                cfg_dict['runtime']['threads'] = [cfg_dict['runtime']['threads'][0]] * len(cfg_dict['runtime']['ranks_per_node'])
            elif len(cfg_dict['runtime']['ranks_per_node']) == 1:
                cfg_dict['runtime']['ranks_per_node'] = [cfg_dict['runtime']['ranks_per_node'][0]] * len(cfg_dict['runtime']['threads'])
            else:
                self.glob.lib.msg.error("input mismatch: 'threads' and 'ranks_per_node' lists must be of equal length in " + \
                                    self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
    
        # Require label if code not set
        if not cfg_dict['requirements']['code'] and not cfg_dict['config']['bench_label']:
            self.glob.lib.msg.error("if 'code' is not set, provide 'label' in " + \
                                    self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']))
    
        #Check bench_mode in set correctly
        if self.glob.stg['exec_mode'] not in  ["sched", "local"]:
            self.glob.lib.msg.error("Unsupported benchmark execution mode found: '"+glob.stg['bench_mode']+ \
                                    "' in $BP_HOME/user.ini, please specify 'sched' or 'local'.")
    
        # Check for hostfile/hostlist if exec_mode is local (mpirun)
        if self.glob.stg['exec_mode'] == "local":
            # Both hostfile and hostlist is set?
            if cfg_dict['runtime']['hostfile'] and cfg_dict['runtime']['hostlist']:
                self.glob.lib.msg.error("both 'hostlist' and 'hostfile' set in " + \
                                        self.glob.lib.rel_path(cfg_dict['metadata']['cfg_file']) + ", please provide only one.")
    
            # Define --hostfile args
            if cfg_dict['runtime']['hostfile']:
                hostfile = self.find_cfg_file("", cfg_dict['runtime']['hostfile'])
                cfg_dict['runtime']['host_str'] = "-hostfile " + hostfile
    
            # Define -host args
            elif cfg_dict['runtime']['hostlist']:
                cfg_dict['runtime']['host_str'] = "-host " + cfg_dict['runtime']['hostlist'].strip(" ")
    
            # Error if neither is set
            else:
                cfg_dict['runtime']['host_str'] = "-host localhost"


        # Deal with empty values
        if not cfg_dict['runtime']['max_running_jobs']:
            cfg_dict['runtime']['max_running_jobs'] = 10

        #Set stdout and stderr
        cfg_dict['config']['stdout'] = "stdout.log"
        cfg_dict['config']['stderr'] = "stderr.log"

        # Set result output file to stdout if not set in cfg file
        if not cfg_dict['result']['output_file']:
            cfg_dict['result']['output_file'] = cfg_dict['config']['stdout']

    # Check sched config file and add required fields
    def process_sched_cfg(self, cfg_dict):
        # Check for missing essential parameters
        
        self.check_dict_section(cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'type')
        self.check_dict_key(    cfg_dict['metadata']['cfg_file'], cfg_dict, 'sched', 'queue')
   
        # Instantiate missing optional parameters
        if not 'allocation'  in    cfg_dict['sched'].keys():   cfg_dict['sched']['allocation']    = ""
        if not 'reservation' in    cfg_dict['sched'].keys():   cfg_dict['sched']['reservation']   = ""
        if not 'qos'         in    cfg_dict['sched'].keys():   cfg_dict['sched']['qos']           = ""
        if not 'node_exclusive' in cfg_dict['sched'].keys():   cfg_dict['sched']['node_exclusive']= True


        self.glob.lib.overload.replace(cfg_dict['sched'])

        # Fill missing parameters
        if not cfg_dict['sched']['runtime']:
            cfg_dict['sched']['runtime'] = '02:00:00'
            self.glob.lib.msg.log("Set runtime = " + cfg_dict['sched']['runtime'])
        if not cfg_dict['sched']['threads']:
            cfg_dict['sched']['threads'] = 1
            self.glob.lib.msg.log("Set threads = " + cfg_dict['sched']['threads'])


    # Inherit from another .cfg
    def inherit(self, cfg_type, search_str):
        search_dict = glob.lib.parse_bench_str(search_str) 
        self.glob.lib.cfg.ingest(cfg_type, search, True) 
        sys.exit(1) 


    # Read input param config and test 
    def ingest(self, cfg_type, search_dict, inherit=False):

        # Process and store build cfg 
        if cfg_type == 'build':
            cfg_dict = self.search_cfg_with_dict(search_dict, self.glob.build_cfgs, True)
            self.glob.lib.msg.log("Starting build cfg processing.")
            self.process_build_cfg(cfg_dict)
            self.glob.config.update(cfg_dict)
    
        # Process and store bench cfg 
        elif cfg_type == 'bench':
            cfg_dict = self.search_cfg_with_dict(search_dict, self.glob.bench_cfgs, False)
            self.glob.lib.msg.log("Starting bench cfg processing.")
            self.process_bench_cfg(cfg_dict)
            self.glob.config.update(cfg_dict)
    
        # Process and store sched cfg 
        elif cfg_type == 'sched':
            cfg_file = os.path.join(self.glob.stg['sched_cfg_path'], search_dict)
            cfg_dict = self.glob.lib.files.read_cfg(cfg_file)
            self.glob.lib.msg.log("Starting sched cfg processing.")
            self.process_sched_cfg(cfg_dict)
            self.glob.sched.update(cfg_dict)
    
        # Process and store compiler/mpi cfg 
        elif cfg_type == 'compiler':
            # Compiler cfg
            cfg_file = os.path.join(self.glob.stg['site_sys_cfg_path'], self.glob.stg['compile_cfg_file'])
            cfg_dict = self.glob.lib.files.read_cfg(cfg_file)
            self.glob.compiler = cfg_dict
            # MPI cfg
            cfg_file = os.path.join(self.glob.stg['site_sys_cfg_path'], self.glob.stg['mpi_cfg_file'])
            cfg_dict = self.glob.lib.files.read_cfg(cfg_file)
            self.glob.mpi = cfg_dict
    
