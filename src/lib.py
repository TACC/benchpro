# System Imports
import configparser as cp
import copy
import glob         as gb
import hashlib
from packaging      import version
from operator       import itemgetter
import os
import sys
import time

# Local Imports
import src.library.cfg_handler          as cfg_handler
import src.library.db_handler           as db_handler
import src.library.expr_handler         as expr_handler
import src.library.file_handler         as file_handler
import src.library.misc_handler         as misc_handler
import src.library.module_handler       as module_handler
import src.library.msg_handler          as msg_handler
import src.library.overload_handler     as overload_handler
import src.library.process_handler      as proc_handler
import src.library.report_handler       as report_handler
import src.library.sched_handler        as sched_handler
import src.library.template_handler     as template_handler

# Contains several useful functions, mostly used by bench_manager and build_manager
class init(object):
    def __init__(self, glob):
        self.glob = glob

        # Init all sub-libraries
        self.cfg      = cfg_handler.init(self.glob)
        self.db       = db_handler.init(self.glob)
        self.expr     = expr_handler.init(self.glob)
        self.files    = file_handler.init(self.glob)
        self.misc     = misc_handler.init(self.glob)
        self.module   = module_handler.init(self.glob)
        self.msg      = msg_handler.init(self.glob)
        self.overload = overload_handler.init(self.glob)
        self.proc     = proc_handler.init(self.glob)
        self.report   = report_handler.init(self.glob)
        self.sched    = sched_handler.init(self.glob)
        self.template = template_handler.init(self.glob)

    # Get relative paths for full paths before printing to stdout
    def rel_path(self, path):
        # if empty str
        if not path:
            return ""
        # if in project path
        if self.glob.ev['BP_HOME'] in path:
            return os.path.join(self.glob.stg['home_env'] + path.replace(self.glob.ev['BP_HOME'], ""))
        # if in application path
        elif self.glob.ev['BP_APPS'] in path:
            return os.path.join(self.glob.stg['app_env'] + path.replace(self.glob.ev['BP_APPS'], ""))
        # if in result path
        elif self.glob.ev['BP_RESULTS'] in path:
            return os.path.join(self.glob.stg['result_env'] + path.replace(self.glob.ev['BP_RESULTS'], ""))
        # local repo
        elif self.glob.stg['local_repo'] in path:
            return os.path.join(self.glob.stg['local_repo_env'] + path.replace(self.glob.stg['local_repo'], ""))

        # if not any of the above
        return path

    # Convert key-less application list to dict 
    def app_list_to_dict(self, app_list):
        return {"code":     app_list[5], 
                "version":  app_list[6],
                "system":   app_list[1],
                "arch":     app_list[2],
                "compiler": app_list[3],
                "mpi":      app_list[4]}

    # Get list of installed apps
    def set_installed_apps(self):

        # Reset 
        self.glob.installed_apps  = []

        app_dir = self.glob.ev['BP_APPS']
        start = app_dir.count(self.glob.stg['sl'])

        # Get directory paths
        app_paths = self.files.search_tree(app_dir, start, start, start + self.glob.stg['tree_depth'])

        # Split app path into catagories and add status
        for path in app_paths:
            status = self.glob.lib.sched.get_status_str(path)
            idx = self.report.get_task_id("build", path) 
            self.glob.installed_apps.append({'task_id': idx, 'table': [idx] + path.split(self.glob.stg['sl']) + [status], 'path': path})

        # Sort by task_id
        self.glob.installed_apps = sorted(self.glob.installed_apps, key=lambda x: x['task_id'], reverse=True)

        # Add ID column
        #for i in range(0,len(self.glob.installed_app_list)):
        #   self.glob.installed_app_list[i] = [str(i+1)] + self.glob.installed_app_list[i]

    # Get results in $BP_RESULTS/pending
    def get_pending_results(self):
        complete =  self.files.get_subdirs(self.glob.stg['pending_path'])
        complete.sort()
        return complete

    # Get results in ./results/captured
    def get_captured_results(self):
        captured = self.files.get_subdirs(self.glob.stg['captured_path'])
        captured.sort()
        return captured

    # Get results in ./results/failed
    def get_failed_results(self):
        failed = self.files.get_subdirs(self.glob.stg['failed_path'])
        failed.sort()
        return failed

    # Return list of results meeting task_id status, look_for_complete: True = complete, False = running
    def get_completed_results(self, search_list, look_for_complete):
        # List of results to return
        matching_results = []

        # For every result
        if search_list:
            for result in copy.deepcopy(search_list):

                # Get job type (sched/local/dry_run)
                exec_mode = self.report.get_exec_mode("bench", result)
                complete = False

                # Sched exec type - get status from task_id
                if exec_mode == "sched":
                    # Get task_id and check it is comeplete, if so append to return list and remove from provided list
                    task_id = self.report.get_task_id("bench", result)
                    complete = self.sched.check_job_complete(task_id)
                
                # Local exec type - get status from PID
                elif exec_mode == "local":
                    pid = self.report.get_task_id("bench", result)
                    # pid_running=False -> complete=True
                    complete = not self.proc.pid_running(pid)


                # Dry_run - skip to next result
                else:
                    continue

                if (complete and look_for_complete) or (not complete and not look_for_complete):
                        matching_results.append(result)
                search_list.remove(result)

        matching_results.sort()
        return matching_results

    # Log cfg contents
    def send_inputs_to_log(self, label):
        # List of global dicts containing input data
        cfg_list = [self.glob.config, self.glob.modules, self.glob.sched, self.glob.compiler]

        self.glob.lib.msg.log(label + " started with the following inputs:")
        self.glob.lib.msg.log("======================================")
        for cfg in cfg_list:
            for seg in cfg:
                self.glob.lib.msg.log("[" + seg + "]")
                for line in cfg[seg]:
                    self.glob.lib.msg.log("  " + str(line) + "=" + str(cfg[seg][line]))
        self.glob.lib.msg.log("======================================")

    # Check if host can run mpiexec
    def check_mpi_allowed(self):
        # Get list of hostnames on which mpiexec is banned
        try:
            no_mpi_hosts = self.glob.stg['mpi_blacklist'].split(',')

        except:
            self.msg.error("unable to read list of MPI banned nodes (mpi_blacklist) in $BP_HOME/settings.ini")
        # If hostname contains any of the blacklisted terms, return False
        if any(x in self.glob.hostname for x in no_mpi_hosts):
            return False
        else:
            return True

    # Search code_path with values in search_list
    def search_with_dict(self, search_dict, code_path):
        match = True
        # Break code path by /
        code_path_elems = code_path.split(self.glob.stg['sl'])

        #Ensure every val that is set in search dict is found in code path
        for search in search_dict.values():
            if search and not any(search in x for x in code_path_elems):
                # Otherwise not code does not match requirements
                match = False

        return match

    # Add fields to application search dict
    def generate_requirements(self, input_dict):

        # 1. CMDline arguments 

        # For each input
        for key in input_dict:
            # If in requirements
            if key in self.glob.config['requirements']:
                # If not set
                if not self.glob.config['requirements'][key]:
                    # Replace
                    self.glob.config['requirements'][key] = input_dict[key]

        # 2. Overloads
        self.overload.replace(None) 

    # Check if the requirements in bench.cfg need a built code 
    def needs_code(self, search_dict):

        # Check if all search_list values are empty (system is always set)
        num_requirements = 0
        for key in search_dict:
            if search_dict[key]:
                num_requirements += 1

        if num_requirements > 1:
            return True

        return False

    # Check if search_list returns unique installed application
    def check_if_installed(self, search_dict):

        # Set list of installed applications
        self.set_installed_apps()

        # For each installed code
        matching_apps = [code_dict for code_dict in self.glob.installed_apps if self.search_with_dict(search_dict, code_dict['path'])]

        # Unique result
        if len(matching_apps) == 1:
            return matching_apps[0]['path']

        # No matches
        elif len(matching_apps) == 0:

            if self.glob.stg['build_if_missing']:
                return False
            else:
                self.msg.error(["No installed applications match your selection criteria: ", ", ".join([search_dict[key] for key in search_dict]),
                                "And 'build_if_missing=False' in $BP_HOME/settings.ini",
                                "Currently installed applications:"] + self.glob.installed_app_paths)

        # Multiple multiple matches
        elif len(matching_apps) > 1:

            self.msg.high("Multiple applications match your criteria: " + ", ".join([key + "=" + search_dict[key] for key in search_dict if search_dict[key]]))
            self.msg.print_app_table([code_dict['table'] for code_dict in matching_apps]) 
            self.msg.error("Please be more specific (use task_ID)")

    # Read every build config file and construct a list with format [[cfg_file, code, version, build_label],...]
    def get_avail_codes(self):

        # Get all application build config files
        cfg_list = self.files.get_cfg_list("build")

        avail_list = []
        for cfg_file in cfg_list:

            # Read each application cfg file 
            cfg_parser = cp.ConfigParser()
            try:
                with open(cfg_file) as cfile:
                    cfg_parser.read_file(cfile)
                    # Append application info to list
                    avail_list.append([cfg_file, cfg_parser['general']['code'], cfg_parser['general']['version'], cfg_parser['config']['build_label']])

            except Exception as err:
                print(err)
                self.msg.error("failed to read [requirements] section of cfg file " + cfg_file)
        
        # Return list
        return avail_list

    # Check if search dict matches an avaiable application
    def check_if_avail(self, search_list):

        # Get list of available application config files
        avail_list = self.get_avail_codes()

        results = []
        # Check for matching available applications
        for code in avail_list:
            if search_list[0] in code[1] and search_list[1] in code[2] and search_list[2] in code[3]:
                results.append(code[0])

        # Unique match
        if len(results) == 1:
            return results[0]

        elif len(results) == 0:
            self.msg.error(["No application profile available which meets your search criteria:"] + search_list)

        elif len(results) > 1:
            self.msg.error(["There are multiple applications available which meet your search criteria:"] + [self.rel_path(result) for result in results])

    # Get scheduler config filename based on user input or defaults
    def get_sched_cfg(self):
        # If user provided custom sched cfg cmdline arg
        if not self.glob.args.sched == "system":
            return self.glob.args.sched 
        # Using default sched cfg file
        else:
            # If default_sched set in system.cfg file
            if 'default_sched' in self.glob.system:
                return self.glob.system['default_sched']
            # Use generic filename string and hope
            else:
                return "slurm_" + self.glob.system['system']
   
    # Extract system variables from system.cfg
    def get_system_vars(self, system):
    
        self.glob.system['system'] = system
        cfg_file = os.path.join("benchpro/system/config", self.glob.stg['system_cfg_file'])
        
        # Check system cfg file exists
        if not os.path.isfile(cfg_file):
           self.glob.lib.msg.error(self.glob.stg['system_cfg_file'] + " file not found in " + self.glob.lib.rel_path(self.glob.stg['config_path'])) 

        system_parser   = cp.RawConfigParser(allow_no_value=True)
        system_parser.read(cfg_file)

        try:
            self.glob.system['sockets']              = system_parser[system]['sockets']
            self.glob.system['cores']                = system_parser[system]['cores']
            self.glob.system['cores_per_socket']     = int(int(self.glob.system['cores']) / int(self.glob.system['sockets']))
            self.glob.system['cores_per_node']       = system_parser[system]['cores']
            self.glob.system['default_arch']         = system_parser[system]['default_arch']
            # Set system default sched cfg if available
            if 'default_sched' in system_parser[system]:
                self.glob.system['default_sched'] = system_parser[system]['default_sched']

        except:
            self.glob.lib.msg.error(["No default scheduler settings found for system '" + self.glob.system['system'] + "'.", 
                                "Add system profile to " + self.glob.lib.rel_path(cfg_file)])
                

    # Generate unique application ID based on current time
    def get_application_id(self):
        app_id = hashlib.sha1()
        app_id.update(str(time.time()).encode('utf-8'))
        return app_id.hexdigest()[:10]

    # Parse all build cfg files into list
    def get_cfg_list(self, path):

        cfg_list = []

        # Get common cfgs
        cfg_files = gb.glob(os.path.join(path, "*.cfg"))
        
        # Get system specific cfgs
        if os.path.isdir(os.path.join(path,self.glob.system['system'])):
            cfg_files += gb.glob(os.path.join(path, self.glob.system['system'], "*.cfg"))

        # Construct
        for cfg in cfg_files:
            cfg_list.append(self.files.read_cfg(cfg))
    
        return cfg_list
    
    # Set a list of build cfg file contents in glob
    def set_build_cfg_list(self):
        self.glob.build_cfgs =  self.get_cfg_list(os.path.join(self.glob.stg['config_path'],self.glob.stg['build_cfg_dir']))

    # Set a list of bench cfg file contents in glob
    def set_bench_cfg_list(self):
        self.glob.bench_cfgs = self.get_cfg_list(os.path.join(self.glob.stg['config_path'],self.glob.stg['bench_cfg_dir']))

    # Convert cmdline string into a dict
    def parse_input_str(self, input_str, default):

        # Handle plain application label : --build lammps
        if not "=" in input_str:
            return {default: input_str}

        input_dict = {}

        # Split by comma delimiter
        for keyval in input_str.split(","):

            if not "=" in keyval:
            # Convert to dict
                self.msg.error("invalid input format detected: " + input_str)

            # Add keyval to dict
            input_dict[keyval.split("=")[0]] = keyval.split("=")[1]

        return input_dict

    # Parse input string for --build 
    def parse_build_str(self, input_str):
        return self.parse_input_str(input_str, "code")

    # Parse input string for --bench
    def parse_bench_str(self, input_str):
        return self.parse_input_str(input_str, "bench_label")

    def version_match(self):
        # Compare versions
        if version.parse(self.glob.version_site) > version.parse(self.glob.version_client):
            return False
        return True

    # Check if the client version is up-to-date with site version
    def check_version(self):
            if not self.version_match():
                self.msg.warning(["You are using BenchPRO " + self.glob.version_client + ", the site package is using " + self.glob.version_site + ".", \
                                 "Update with: git -C ~/benchpro pull", \
                                 "Continuing..."])
                time.sleep(self.glob.stg['timeout'])


