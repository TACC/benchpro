# System Imports
import glob as gb
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.result_manager as result_manager

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Get list of files matching search
    def find_matching_files(self, search_list):
        file_list = []
        for search in search_list:
            file_list += gb.glob(os.path.join(self.glob.ev['BP_HOME'], search))
        return file_list

    # Delete matching files
    def clean_matching_files(self, file_list):
        tally = 0
        for f in file_list:
            try:
                os.remove(f)
                tally += 1
            except:
                print("Error cleaning the file", f)
        return tally

    # Clean up temp files such as logs
    def clean_temp_files(self):
        print("Cleaning up temp files...")
        # Search space for tmp files
        search_list = [ "*.out*",
                        "*.err*",
                        "log/*",
                        "tmp.*",
                        ".history",
                        "*.csv",
                        ".outputs"]

        file_list = self.find_matching_files(search_list)

        if file_list:
            print("Found the following files to delete:")
            for f in file_list:
                print(self.glob.lib.rel_path(f))

            print("\033[0;31mDeleting in", self.glob.stg['timeout'], "seconds...\033[0m")
            time.sleep(self.glob.stg['timeout'])
            print("No going back now...")
            deleted = self.clean_matching_files(file_list)
            print("Done, " + str(deleted) + " files successfuly cleaned.")

        else:
            print("No temp files found.")

    # Delete app path and associated module
    def delete_app_path(self, path):
        
        # Get module dir from app dir, by adding 'modulefiles' prefix and stripping [version] suffix
        mod_dir = os.path.join(self.glob.stg['module_path'],  self.glob.stg['sl'].join(path.split(self.glob.stg['sl'])[:-1]))
        app_dir = os.path.join(self.glob.ev['BP_APPS'], path)

        print("/".join(app_dir.split("/")[-3:]) + ":")
        # Delete application dir
        try:
            self.glob.lib.files.prune_tree(app_dir)
            print("Application removed.")
        except:
            print("Warning: Failed to remove application directory:")
            print(">  "  + self.glob.lib.rel_path(app_dir))
            print("Skipping")
            print()
        # Detele module dir
        try:
            self.glob.lib.files.prune_tree(mod_dir)
            print("Module removed.")
        except:
            print("Warning: no associated module located in:")
            print(">  " + self.glob.lib.rel_path(mod_dir))
            print("Skipping")
        print()
        
    # Delete application and module matching path provided
    def remove_app(self):
        input_list = self.glob.args.delApp

        remove_list = []
        # If 'all' provided, add all installed apps to list to remove
        if input_list[0] == 'all':
            self.glob.lib.set_installed_apps()

            if not self.glob.installed_apps:
                print("No applications installed.")
                return

            print("Deleting all installed applications:")

            # Print apps to remove
            self.glob.lib.msg.print_app_table([code_dict['table'] for code_dict in self.glob.installed_apps])

            # Timeout
            print()
            print("\033[0;31mDeleting in", self.glob.stg['timeout'], "seconds\033[0m")
            self.glob.lib.msg.wait(self.glob.stg['timeout'])
            print("\nNo going back now...")

            # Delete
            for app in self.glob.installed_apps:
                self.delete_app_path(app['path'])

        # Else check each input is installed then add to list
        else:
            # Accept space delimited list of apps
            for app in input_list:
                # Create search dict from search elements
                search_dict = {}
               
                # If input str is int
                if self.int_input(app):
                    search_dict = self.glob.lib.app_list_to_dict(self.get_app_list_from_id(app))

                # Handle / delimited paths
                elif "/" in app:
                    for elem in app.split("/"):
                        search_dict[elem] = elem

                # Handle , delimited couples
                else:
                    for elem in app.split(","):
                        if not "=" in elem:
                            search_dict['code'] = elem
                        else:
                            search_dict[elem.split("=")[0]] = elem.split("=")[1]

                # If installed, add to remove list
                installed = self.glob.lib.check_if_installed(search_dict)

                if installed:
                    app_path = installed['path']
                    print("\033[0;31mDeleting in", self.glob.stg['timeout'], "seconds\033[0m")
                    self.glob.lib.msg.wait(self.glob.stg['timeout'])
                    print("No going back now...")
                    self.delete_app_path(app_path)
                else:
                    print("No installed application matching search term '" + app + "'")

    # Print build report of installed application
    def query_app(self, arg):
        search_dict = {}

        # Check input is ID
        if self.int_input(arg):
            # ID -> install_dir_list -> search_dict  
            search_dict = self.glob.lib.app_list_to_dict(self.get_app_list_from_id(arg))

        # Input is string
        elif not "/" in arg:
            search_dict["code"] = arg

        # Input is key-values
        else:
            # Disect search string into search dict
            for search_elem in arg.split("/"):
                search_dict[search_elem] =  search_elem
        
        # Get installation directory from search dict
        app_dir = self.glob.lib.check_if_installed(search_dict)
        if not app_dir:
            print("Not found.")
            sys.exit(1)   
            
        app_path = app_dir['path']

        # No matches found
        if not app_path:
            self.glob.lib.msg.error("Application '" + arg + "' is not installed.")

        app_full_path = os.path.join(self.glob.ev['BP_APPS'], app_path)
        build_report = os.path.join(app_full_path, self.glob.stg['build_report_file'])
        install_path = os.path.join(app_full_path, self.glob.stg['install_subdir'])

        # Read contents of build report file
        report_dict = self.glob.lib.report.read(build_report)

        if not report_dict: 
            print("Failed to read " + self.glob.lib.rel_path(build_report))
            sys.exit(1)

        print("Build report for application '" + report_dict['build']['code'] + "'")
        print("-------------------------------------------")

        # Print contents of report file 
        for sec in report_dict:
            print("["+sec+"]")
            for key in report_dict[sec]:
                print(key.ljust(15) + "= " + report_dict[sec][key])

        print("-------------------------------------------")
        print()

        status = ""
        gap = max(len(report_dict['build']['exe_file']) + 9, 20)

        # Dry_run - do nothing
        if report_dict['build']['task_id']  == "dry_run":
            print("Build job was dry_run. Skipping executable check")
    
        else:
            # Local build        
            if report_dict['build']['exec_mode'] == "local":

                running = self.glob.lib.proc.pid_running(report_dict['build']['task_id'])
                
                if running:
                    print("Local build PID still running:")
                    self.glob.lib.proc.print_local_pid(report_dict['build']['task_id'])

                else:
                    status = "COMPLETED"

            # Sched build
            else:
                status = self.glob.lib.sched.get_job_status(report_dict['build']['task_id'])
                
                col=None
                stream=None
                
                if status == "PENDING":
                    col = "\033[1;33m"       
                # Running
                elif status == "RUNNING":
                    col = "\033[1;33m"
                    stream = 'stdout'
                # Job failed
                elif status != "COMPLETED":
                    col = "\033[1;31m" 
                    stream = 'stderr'

                elif status == "COMPLETED":
                    col = "\033[0;32m"

                elif status == "UNKNOWN":
                    col = "\033[1;33m"

                print(("Job " + report_dict['build']['task_id'] + " status: ").ljust(gap) + col + status + "\033[0m")

                if status == "COMPLETED":
                    stat_str = ""
                    if self.glob.lib.files.exists(report_dict['build']['exe_file'], os.path.join(install_path, report_dict['build']['bin_dir'])):
                        stat_str = "\033[0;32mFOUND\033[0m"
                    else:
                        stat_str = "\033[0;31mMISSING\033[0m"
                        stream = 'stderr'

                    print(("File "+report_dict['build']['exe_file']+": ").ljust(gap) + stat_str)

                if stream:
                    self.glob.lib.msg.print_file_tail(os.path.join(report_dict['build']['build_prefix'], report_dict['build'][stream]))       


    # Print currently installed apps as well as their exe status
    def show_installed(self):

        # Get list of installed application paths
        self.glob.lib.set_installed_apps()
        # Print table
        print("Installed applications:")
        self.glob.lib.msg.print_app_table(None)

    # Get run string for given config file
    def get_cmd_string(self, keys, config_dict):
        cmd_str = []
        # For each section-key pair in input list
        for sect, key in keys:
            # If section present
            if sect in config_dict:     
                # If key present
                if key in config_dict[sect]:
                    # If value set
                    if config_dict[sect][key]:
                        cmd_str.append(key+"="+config_dict[sect][key])
        return ",".join(cmd_str)

    # Print list of code strings
    def print_config(self, atype, config_list):
        config_list.sort()

        fnames = [config.split('/')[-1] for config in config_list]
        
        for config in config_list:
            contents = self.glob.lib.files.read_cfg(config)

            # Column width
            column = 30
            
            # App config
            if atype == "application":
                print("| " + contents['metadata']['cfg_label'].ljust(column) + "| -b " + \
                        self.get_cmd_string([['general', 'code'], ['general', 'version'], ['general', 'system'], ['config', 'build_label']], \
                        contents))

            # Bench config
            else:
                print("| " + contents['metadata']['cfg_label'].ljust(column) + "| -B " + \
                        self.get_cmd_string([['requirements', 'code'], ['requirements', 'version'], ['requirements', 'build_label'], ['config', 'bench_label']], \
                        contents))

    def print_heading(self, search_path):
        print(self.glob.lib.rel_path(search_path) + ":")
        print("------------------------------------------------------------")
        print("| Config file".ljust(32) + "| Run with")

    # Print applications that can be installed from available cfg files
    def print_avail_type(self, atype, search_path_list):
        print(self.glob.bold + "Available " + atype + " profiles:" + self.glob.end)
        print(self.glob.bold, "------------------------------------------------------------", self.glob.end)
        for search_path in search_path_list:
            self.print_heading(search_path)
            # Scan config/build
            app_dir = search_path + self.glob.stg['sl']
            self.print_config(atype, gb.glob(app_dir + "*.cfg"))
            print()
            # Scan config/build/[system]
            app_dir = app_dir + self.glob.system['system'] + self.glob.stg['sl']
            if os.path.isdir(app_dir):
                print("------------------------------------------------------------")
                self.print_heading(search_path)
                self.print_config(atype, gb.glob(app_dir + "*.cfg"))
                print()

    # return True for input is type int
    def int_input(self, arg):
        return arg.isdigit()

    # Get app path from int ID
    def get_app_tuple_from_id(self, idx):

        # Populate app table if empty
        if not self.glob.installed_app_list:
            self.glob.lib.set_installed_apps()

        app_list, app_path  = None, None

        # Get path[i] and list[i] where list[i][0] == input. 
        # I.e. get corresponding path for app ID
        for i in range(0,len(self.glob.installed_app_paths)):
            if self.glob.installed_app_list[i][0] == str(idx):
                app_list = self.glob.installed_app_list[i]
                app_path = self.glob.installed_app_paths[i]

        if not app_path:
            self.glob.lib.msg.error("No application ID matching '" + idx  + "'")

        # Return path
        return app_list, app_path


    def get_app_path_from_id(self, idx : int) -> str:
        app_list, app_path = self.get_app_tuple_from_id(idx)
        return app_path

    def get_app_list_from_id(self, idx : int) -> list: 
        """
        Get a list containing application's install path dirs
        :param idx: Application ID, from --listApps table 
        :type idx:  integer
        :return:    List of app's path elements         
        :rtype:     list
        """

        app_list, app_path = self.get_app_tuple_from_id(idx)
        return app_list

    def show_available(self):
        if self.glob.args.avail in ['code', 'all']:
            self.print_avail_type("application", self.glob.stg['build_cfg_path'])

        print()
        print()

        if self.glob.args.avail in ['bench', 'all']:
            self.print_avail_type("benchmark", self.glob.stg['bench_cfg_path'])

        if self.glob.args.avail in ['suite', 'all']:
            print()
            print(self.glob.bold, "Available benchmark suites:", self.glob.end)
            print(self.glob.bold, "------------------------------------------------------------", self.glob.end)
            print("Label".ljust(32) + "| Contents")
            for key in self.glob.suite:
                print ("  " + key.ljust(30) + "| "+ self.glob.suite[key])

        if self.glob.args.avail not in ['code', 'bench', 'suite', 'all']:
            print("Invalid input '"+self.glob.args.avail+"'")
            
    # Print key/value pair from setting.ini dict
    def print_setting(self, key, value):
        print("  " + key.ljust(18) + " = " + str(value))

    # Print default params from settings.ini
    def print_defaults(self):
        print()

        # Print site info
        print("Setup info:")
        [self.print_setting(key[0], key[1]) for key in [        ["User", self.glob.user], \
                                                                ["Host", self.glob.hostname.split(".")[0]], \
                                                                ["System", self.glob.system['system']], \
                                                                ["CWD", self.glob.cwd]]]
        
        # Print BenchPRO settings
        print()
        print("Benchtool defaults:")
        [self.print_setting(key, self.glob.stg[key]) for key in ['dry_run', \
                                                                'debug', \
                                                                'exit_on_missing', \
                                                                'overwrite', \
                                                                'build_mode', \
                                                                'build_if_missing', \
                                                                'bench_mode',\
                                                                'check_modules', \
                                                                'sync_staging']]
        print()
        # Print scheduler defaults for this system if available
        self.glob.lib.get_system_vars(self.glob.system['system'])

        sched_cfg = self.glob.lib.get_sched_cfg()
        try:
            with open(os.path.join(self.glob.stg['sched_cfg_path'], sched_cfg)) as f:
                print("Scheduler defaults for " + self.glob.system['system'] + ":")
                for line in f.readlines():
                    if "=" in line:
                        print("  " + line.split("=")[0].strip().ljust(19) + "= " + line.split("=")[1].strip() )

        except Exception as err:
            print("Unable to read " + str(sched_cfg))
            print(err)
    
        print()
        print("Overload with '-o [SETTING1=ARG] [SETTING2=ARG]' on the command line for one-time changes.")
        print("Or by editting $BP_HOME/settings.ini which apply persist changes over the defaults.")
        print("You can now use the 'bps' utility to manipulate these persitant changes, e.g.")
        print(">   bps dry_run False")
    # Print command line history file
    def print_history(self):
        history_file = os.path.join(self.glob.ev['BP_HOME'], ".history")
        if os.path.isfile(history_file):
            with open(history_file, "r") as hist:
                content = hist.read()
                for line in content.split("\n"):
                    print(line)

    # Print version file and quit
    def print_version(self):
        print("benchpro " + self.glob.version_site_full) #+ " (" + self.glob.version_site_date + ")")

    # Return the last line of the .outputs file
    def get_last_history(self):

        if not os.path.isfile(os.path.join(self.glob.ev['BP_HOME'], ".history")):
            print("No previous outputs found.")
            sys.exit(0)

        with open(os.path.join(self.glob.ev['BP_HOME'], ".history"), 'r') as f:
            lines = f.readlines()
            if len(lines) == 0:
                print("No previous outputs found.")    
                sys.exit(0)
       
        # Return requested line in output file
        return lines[min(len(lines), self.glob.args.last) * -1].rstrip('\n')

    # Print report from the last build or bench command
    def print_last(self):

        # Get requested 
        last = self.get_last_history()

        task_id = last.split("|")[1].strip()
        output = last.split("|")[2].strip()
        op = last.split(" ")[1]

        # If last output was from build task
        if op in ["--build", "-b"]:
            self.query_app(output)

        # If last output was from bench task
        elif op in ["--bench", "-B"]:
            result_manager.query_result(self.glob, output)

    # Generate input string with complete parameterization for history entry

    def get_input_str(self):
       
        # Build op
        if self.glob.args.build:
            return  "benchpro --build" + \
                    " code="            + self.glob.config['general']['code']           + \
                    ",version="         + str(self.glob.config['general']['version'])   + \
                    ",compiler="        + self.glob.modules['compiler']['safe']         + \
                    ",mpi="             + self.glob.modules['mpi']['safe']              + \
                    " | " + str(self.glob.task_id)                                      + \
                    " | " + self.glob.config['metadata']['working_dir']
        # Bench op
        elif self.glob.args.bench:

            return  "benchpro --bench"  + \
                    " dataset="         + self.glob.config['config']['dataset']             + \
                    ",code="            + self.glob.config['requirements']['code']          + \
                    ",version="         + str(self.glob.config['requirements']['version'])  + \
                    ",nodes="           + self.glob.config['runtime']['nodes']              + \
                    ",ranks_per_node="  + self.glob.config['runtime']['ranks_per_node']     + \
                    ",threads="         + self.glob.config['runtime']['threads']            + \
                    ",gpus="            + self.glob.config['runtime']['gpus']               + \
                    " | " + str(self.glob.task_id)                                          + \
                    " | " + self.glob.config['metadata']['working_dir'] 
