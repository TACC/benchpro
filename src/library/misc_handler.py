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
        app_path = self.glob.stg['sl'].join(path.split(self.glob.stg['sl'])[path.split(self.glob.stg['sl']).index(self.glob.stg['build_topdir'])+1:-1])
        mod_path = os.path.join(self.glob.stg['module_path'],  app_path)

        # Delete application dir
        try:
            self.glob.lib.files.prune_tree(path)
            print("Application removed.")
        except:
            print("Warning: Failed to remove application directory:")
            print(">  "  + self.glob.lib.rel_path(path))
            print("Do you own this application?")
            print("Skipping")
        print()
        # Detele module dir
        try:
            self.glob.lib.files.prune_tree(mod_path)
            print("Module removed.")
        except:
            print("Warning: no associated module located in:")
            print(">  " + self.glob.lib.rel_path(mod_dir))
            print("Do you own this module?")
            print("Skipping")
        print()
       

    def prep_delete(self, app_list, msg_str):
        
        print("Deleting " + msg_str)

        # Timeout
        print()
        print("\033[0;31mDeleting in", self.glob.stg['timeout'], "seconds\033[0m")
        self.glob.lib.msg.wait()
        print("\nNo going back now...")

        for path in app_list:
            self.delete_app_path(path)


    # Find an application to delete
    def id_app_to_remove(self, search):

        if search == "all":
            return self.glob.installed_apps_list

        else:
            matching_apps = []
            # Iterate over installed apps looking for search matches

            for app in self.glob.installed_apps_list:
                if search in app.values():
                    matching_apps.append(app)

            if len(matching_apps) > 1:
                self.glob.lib.msg.high("Application selection was not unique")
                self.glob.lib.msg.print_app_table(matching_apps)
                self.glob.lib.msg.error("Please provide unique identifier")

            elif len(matching_apps) == 0:
                self.glob.lib.msg.error("No matching app found.")

            else:
                return matching_apps[0]

    def remove_app(self, app_path=None):

        remove_list = []

        # OPTION 1: App path provided
        if app_path:
            self.prep_delete([app_path], "application in " + self.glob.lib.rel_path(app_path))

        # OPTION 2: Use args
        else:
            # Split arg string by ","
            arg_list = self.glob.args.delApp
            self.glob.lib.set_installed_apps()

            # OPTION 2.a: args = all; get list of installed apps
            if arg_list[0] == 'all':

                del_list = self.glob.installed_apps_list

                if not del_list:
                    print("No applications installed.")
                    return

                # Print apps to remove
                self.glob.lib.msg.print_app_table(None)

                # Delete
                self.prep_delete([app['path'] for app in del_list], "all aplications")

            # OPTION 2.b: Delete comma delimited arg list of apps
            else:
                # Accept space delimited list of apps
                for app in arg_list:
                    # Create search dict from search elements
                    #search_dict = {}
               
                    # If input str is int
                    #if self.int_input(app):
                    #    search_dict = self.glob.lib.app_list_to_dict(self.get_app_list_from_id(app))

                    # Handle / delimited paths
                    #if "/" in app:
                    #    for elem in app.split("/"):
                    #        search_dict[elem] = elem

                    # Handle , delimited couples
                    #else:
                    #    for elem in app.split(","):
                    #        if not "=" in elem:
                    #            search_dict['code'] = elem
                    #        else:
                    #            search_dict[elem.split("=")[0]] = elem.split("=")[1]

                    # If installed, add to remove list
                    #installed = self.glob.lib.check_if_installed(search_dict)

                    app_dict = self.id_app_to_remove(app)
                    self.prep_delete([app_dict['path']], "app in " + self.glob.lib.rel_path(app_dict['path']))


                    #if installed:
                    #    self.prep_delete([installed['path']], "")

                    #else:
                    #    print("No installed application matching '" + app + "'")

    # Print build report of installed application
    def query_app(self, arg):
        search_dict = {}

        # Input is string
        if not "/" in arg:
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
                    self.glob.lib.msg.print_file_tail(os.path.join(report_dict['build']['path'], report_dict['build'][stream]))       


    # Print currently installed apps as well as their exe status
    def show_installed(self):

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
                self.print_heading(app_dir)
                self.print_config(atype, gb.glob(app_dir + "*.cfg"))
                print()

    # return True for input is type int
    def int_input(self, arg):
        return arg.isdigit()

    # Get app path from int ID
    def get_app_tuple_from_id(self, idx):

        # Populate app table if empty
        if not self.glob.installed_apps_list:
            self.glob.lib.set_installed_apps()

        app_list, app_path  = None, None

        # Get path[i] and list[i] where list[i][0] == input. 
        # I.e. get corresponding path for app ID
        for installed_app in self.glob.installed_apps_list:
            if installed_app['task_id'] == str(idx):
                app_list = installed_app
                app_path = installed_app['path']

        if not app_path:
            self.glob.lib.msg.error("No application ID '" + idx  + "'")

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
        
        print()

        # User or all
        search_locs = self.glob.stg['build_cfg_path']

        if self.glob.args.avail in ['apps', 'all']:
            self.print_avail_type("application", search_locs)

        # User or all
        search_locs = self.glob.stg['bench_cfg_path']

        if self.glob.args.avail in ['bench', 'all']:
            self.print_avail_type("benchmark", search_locs)

        if self.glob.args.avail in ['suite']:
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
        if value:
            print("  " + key.ljust(18) + " = " + str(value))
        else:
            print("  " + key.ljust(18) + " = " + "\033[0;31mMISSING\033[0m")

    # Print default params from settings.ini
    def print_defaults(self):

        # Run overloads
        self.glob.lib.overload.replace(None)

        # Print site info
        print("------------------------------------------------------")
        print("Setup info:")
        [self.print_setting(key[0], key[1]) for key in [        ["User", self.glob.user], \
                                                                ["Host", self.glob.hostname.split(".")[0]], \
                                                                ["System", self.glob.system['system']], \
                                                                ["CWD", self.glob.cwd]]]
        
        # Print scheduler defaults for this system if available
        self.glob.lib.get_system_vars(self.glob.system['system'])

        sched_cfg = self.glob.lib.get_sched_cfg()
        try:
            with open(os.path.join(self.glob.stg['sched_cfg_path'], sched_cfg)) as fp:
                print("------------------------------------------------------")
                print("Scheduler defaults for " + self.glob.system['system'] + ":")
                for line in fp.readlines():
                    if "=" in line:
                        print("  " + line.split("=")[0].strip().ljust(19) + "= " + line.split("=")[1].strip() )

        except Exception as err:
            print("Unable to read " + str(sched_cfg))
            print(err)

        # Print BenchPRO settings
        print("------------------------------------------------------")
        print("$BP_HOME/settings.ini")
        [self.print_setting(setting.split("=")[0].strip(), setting.split("=")[1].strip()) for setting in self.glob.defs_overload_list]
        print("------------------------------------------------------")
        print()
        print("Overload with '-o [SETTING1=ARG] [SETTING2=ARG]' on the command line for one-time changes.")
        print("Edit $BP_HOME/settings.ini to apply persistant changes.")
        print("Use the 'bps' command to apply these persistant changes via the CLI, e.g.")
        print(">   bps dry_run=False\n\n")

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

        with open(os.path.join(self.glob.ev['BP_HOME'], ".history"), 'r') as fp:
            lines = fp.readlines()
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

    # Print EV matching prefix str
    def print_env_matching_str(self, prefix):
        
        for k, v in os.environ.items():
            if prefix in k:
                print(k.ljust(18, " ") + "= " + v)

    # Print BP_ and BPS_ EVs
    def print_env(self):
        print("Editable environment variables:")
        self.print_env_matching_str("BP_")
        print()
        print("Non-editable environment variables:")
        self.print_env_matching_str("BPS_")
        print()
        

