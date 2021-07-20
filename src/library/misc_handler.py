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
            file_list += gb.glob(os.path.join(self.glob.basedir, search))
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

    # Prune dir tree until not unique
    def prune_tree(self, path):
        path_elems  = path.split(self.glob.stg['sl'])
        parent_path = self.glob.stg['sl'].join(path.split(self.glob.stg['sl'])[:-1])
        parent_dir  = path_elems[-2]

        # If parent dir is root ('build' or 'modulefile') or if it contains more than this subdir, delete this subdir
        if (parent_dir == self.glob.stg['build_dir']) or  (parent_dir == self.glob.stg['module_path']) or (len(gb.glob(os.path.join(parent_path,"*"))) > 1):
            su.rmtree(path)
        # Else resurse with parent
        else:
            self.prune_tree(parent_path)

    # Delete app path and associated module
    def delete_app_path(self, path):
        
            # Get module dir from app dir, by adding 'modulefiles' prefix and stripping [version] suffix
            mod_dir = os.path.join(self.glob.stg['module_path'],  self.glob.stg['sl'].join(path.split(self.glob.stg['sl'])[:-1]))
            app_dir = os.path.join(self.glob.stg['build_path'], path)

            print("Found application installed in:")
            print(">  " + self.glob.lib.rel_path(app_dir))
            print()
            print("\033[0;31mDeleting in", self.glob.stg['timeout'], "seconds...\033[0m")
            time.sleep(self.glob.stg['timeout'])
            print("No going back now...")

            # Delete application dir
            try:
                self.prune_tree(app_dir)
                print()
                print("Application removed.")
            except:
                print("Warning: Failed to remove application directory:")
                print(">  "  + self.glob.lib.rel_path(app_dir))
                print("Skipping")

            print()
            # Detele module dir
            try:
                self.prune_tree(mod_dir)
                print("Module removed.")
                print()
            except:
                print("Warning: no associated module located in:")
                print(">  " + self.glob.lib.rel_path(mod_dir))
                print("Skipping")

    # Delete application and module matching path provided
    def remove_app(self):
        input_list = self.glob.args.delApp

        remove_list = []
        # If 'all' provided, add all installed apps to list to remove
        if input_list[0] == 'all':
            print("Deleting all installed applications")
            remove_list = self.glob.lib.get_installed()

            for app in remove_list:
                self.delete_app_path(app)

        # Else check each input is installed then add to list
        else:
            # Accept space delimited list of apps
            for app in input_list:
                # Create search dict from search elements
                search_dict = {}
                for elem in app.split(":"):
                    if not "=" in elem:
                        search_dict['code'] = elem
                    else:
                        search_dict[elem.split("=")[0]] = elem.split("=")[1]

                # If installed, add to remove list
                tmp = self.glob.lib.check_if_installed(search_dict)
                if tmp:
                    self.delete_app_path(tmp)        

                else:
                    print("No installed application matching search term '" + app + "'")

    # Print build report of installed application
    def query_app(self, app_label):

        search_dict = {}
        
        # Disect search string into search dict
        for search_elem in app_label.split("/"):
            search_dict[search_elem] =  search_elem
        
        app_dir = self.glob.lib.check_if_installed(search_dict)

        if not app_dir:
            print("Application '"+app_label+"' is not installed.")
            sys.exit(1)

        app_path = os.path.join(self.glob.stg['build_path'], self.glob.lib.check_if_installed(search_dict))
        build_report = os.path.join(app_path, self.glob.stg['build_report_file'])
        install_path = os.path.join(app_path, self.glob.stg['install_subdir'])

        # Read contents of build report file
        report_dict = self.glob.lib.report.read(build_report)

        if not report_dict: 
            print("Failed to read " + self.glob.lib.rel_path(build_report))
            sys.exit(1)

        print("Build report for application '"+app_label+"'")
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

                if status == "RUNNING":
                    print(("Job " + report_dict['build']['task_id'] + " status: ").ljust(gap) + "\033[1;33m" + status + "\033[0m")
                elif not status == "COMPLETED":
                    print(("Job " + report_dict['build']['task_id'] + " status: ").ljust(gap) + "\033[0;31m" + status + "\033[0m")

            # If complete, Look for exe
            if status == "COMPLETED":
                print(("Build job status: ").ljust(gap) + "\033[0;32m" + status + "\033[0m")

                if self.glob.lib.files.exists(report_dict['build']['exe_file'], os.path.join(install_path, report_dict['build']['bin_dir'])):
                    print(("File "+report_dict['build']['exe_file']+": ").ljust(gap) + "\033[0;32mFOUND\033[0m")
                else:
                    print(("File "+report_dict['build']['exe_file']+": ").ljust(gap) + ")\033[0;31mMISSING\033[0m")

    # Get usable string of application status
    def get_status_str(self, app):


        # Get execution mode (sched or local) from application report file
        exec_mode = self.glob.lib.report.get_exec_mode("build", app)

        # Handle dry run applications
        if exec_mode == "dry_run":
            return '\033[1;33mDRYRUN\033[0m'

        # Get Jobid from report file and check if status = COMPLETED
        task_id = self.glob.lib.report.get_task_id("build", app)

        status = None
        if exec_mode == "sched":
            status = self.glob.lib.sched.get_job_status(task_id)

        elif exec_mode == "local":
            # Check if PID is running
            if self.glob.lib.proc.pid_running(task_id):
                return "\033[1;33mPID STILL RUNNING\033[0m"
            else:
                status = "COMPLETED"

        # Complete state
        if status == "COMPLETED":

            bin_dir, exe = self.glob.lib.report.build_exe(app)
            if exe:
                if self.glob.lib.files.exists(exe, os.path.join(self.glob.stg['build_path'], app, self.glob.stg['install_subdir'], bin_dir)):
                    return '\033[0;32mEXE FOUND\033[0m'

            return '\033[0;31mEXE NOT FOUND\033[0m'

        return '\033[1;33mJOB '+status+'\033[0m'

    # Print currently installed apps as well as their exe status
    def show_installed(self):
        print("Installed applications:")

        # Get list of installed application paths
        installed_list = self.glob.lib.get_installed()

        
        split_list = [["SYSTEM", "ARCH", "COMPILER", "MPI", "CODE", "VERSION", "LABEL"]]

        # Split app path into catagories and add status 
        for app in installed_list:
            split_list.append(app.split(self.glob.stg['sl']) + [app])

        elems = len(split_list[0])
        lengths = [0] * elems

        # Get max length of each table column (for spacing)
        for i in range(elems):
            for app in split_list:
                if len(app[i]) > lengths[i]:
                    lengths[i] = len(app[i])

        # Buffer each column 3 chars
        lengths = [i + 3 for i in lengths]

        # Print table
        print(self.glob.bold + split_list[0][0].ljust(lengths[0]) + "| " +
            split_list[0][1].ljust(lengths[1]) + "| " +
            split_list[0][2].ljust(lengths[2]) + "| " +
            split_list[0][3].ljust(lengths[3]) + "| " +
            split_list[0][4].ljust(lengths[4]) + "| " +
            split_list[0][5].ljust(lengths[5]) + "| " +
            split_list[0][6].ljust(lengths[6]) + "| " +
            "STATUS" + self.glob.end)

        for app in split_list[1:]:
            print(app[0].ljust(lengths[0]) + "| " +
                    app[1].ljust(lengths[1]) + "| " +
                    app[2].ljust(lengths[2]) + "| " +
                    app[3].ljust(lengths[3]) + "| " +
                    app[4].ljust(lengths[4]) + "| " +
                    app[5].ljust(lengths[5]) + "| " +
                    app[6].ljust(lengths[6]) + "| " +
                    self.get_status_str(app[7]))


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
        return ":".join(cmd_str)


    # Print list of code strings
    def print_config(self, atype, config_list):
        config_list.sort()

        fnames = [config.split('/')[-1] for config in config_list]
        
        for config in config_list:
            contents = self.glob.lib.cfg.read_file(config)

            column = 30

            if atype == "application":
                print("| " + contents['metadata']['cfg_label'].ljust(column) + "| -b " + self.get_cmd_string([['general', 'code'], ['general', 'version'], ['general', 'system']], contents))

            else:
                print("| " + contents['metadata']['cfg_label'].ljust(column) + "| -B " + self.get_cmd_string([['requirements', 'code'], ['requirements', 'version'], ['requirements', 'build_label'], ['config', 'dataset']], contents))


    # Print applications that can be installed from available cfg files
    def print_avail_type(self, atype, search_path):
        print(self.glob.bold + "Available " + atype + " profiles:" + self.glob.end)
        print("------------------------------------------------------------")
        print(self.glob.lib.rel_path(search_path) + ":")
        print("------------------------------------------------------------")
        print("| Config file".ljust(32) + "| Run with")
        # Scan config/build
        app_dir = search_path + self.glob.stg['sl']
        self.print_config(atype, gb.glob(app_dir + "*.cfg"))

        # Scan config/build/[system]
        app_dir = app_dir + self.glob.sys_env + self.glob.stg['sl']
        if os.path.isdir(app_dir):
            print("------------------------------------------------------------")
            print(self.glob.lib.rel_path(os.path.join(search_path, self.glob.sys_env)) + ":")
            print("------------------------------------------------------------")
            print("| Config file".ljust(32) + "| Run with")
            self.print_config(atype, gb.glob(app_dir + "*.cfg"))

    # Print available code/bench/suite depending on user input
    def show_available(self):
        if self.glob.args.avail in ['code', 'all']:
            search_path = os.path.join(self.glob.stg['config_path'], self.glob.stg['build_cfg_dir'])
            self.print_avail_type("application", search_path)

        print()
        print()

        if self.glob.args.avail in ['bench', 'all']:
            search_path = os.path.join(self.glob.stg['config_path'], self.glob.stg['bench_cfg_dir'])
            self.print_avail_type("benchmark", search_path)

        if self.glob.args.avail in ['suite', 'all']:
            print()
            print("Available benchmark suites:")
            print("------------------------------------------------------------")
            print("Label".ljust(32) + "| Contents")
            for key in self.glob.suite:
                print ("  " + key.ljust(30) + "| "+ self.glob.suite[key])

        if self.glob.args.avail not in ['code', 'bench', 'suite', 'all']:
            print("Invalid input '"+self.glob.args.avail+"'")
            
    # Print key/value pair from setting.ini dict
    def print_setting(self, key):
        print("  " + key.ljust(18) + " = " + str(self.glob.stg[key]))

    # Print default params from settings.ini
    def print_setup(self):
        print()
        print("Benchtool defaults:")
        [self.print_setting(key) for key in ['dry_run', \
                                            'debug', \
                                            'exit_on_missing', \
                                            'overwrite', \
                                            'build_mode', \
                                            'build_if_missing', \
                                            'bench_mode',\
                                            'check_modules']]
        print()
        # Print scheduler defaults for this system if available
        self.glob.system = self.glob.lib.get_system_vars(self.glob.sys_env)
        if self.glob.system:

            sched_cfg = self.glob.lib.get_sched_cfg()
            try:
                with open(os.path.join(self.glob.stg['config_path'], self.glob.stg['sched_cfg_dir'], sched_cfg)) as f:
                    print("Scheduler defaults for " + self.glob.sys_env + ":")
                    for line in f.readlines():
                        print("  " + line.strip())

            except:
                print("Unable to read " + sched_cfg)
                print()
        else:
            print("No default scheduler settings found for system " + self.glob.sys_env + ".")
            print() 
    
        print()
        print("Overload with '-o [SETTING1=ARG] [SETTING2=ARG]'")
        print()

    # Print command line history file
    def print_history(self):
        history_file = os.path.join(self.glob.basedir, ".history")
        if os.path.isfile(history_file):
            with open(history_file, "r") as hist:
                content = hist.read()
                for line in content.split("\n"):
                    print(line)

    # Print version file and quit
    def print_version(self):
        with open(os.path.join(self.glob.basedir, ".version")) as f:
            print(f.read())

    # Return the last line of the .outputs file
    def get_last_output(self):

        if not os.path.isfile(os.path.join(self.glob.basedir, ".history")):
            print("No previous outputs found.")
            sys.exit(0)

        with open(os.path.join(self.glob.basedir, ".history"), "r") as f:
            lines = f.readlines()
            if len(lines) == 0:
                print("No previous outputs found.")    
                sys.exit(0)
       
        # Return requested line in output file
        return lines[min(len(lines), self.glob.args.last) * -1].rstrip('\n')

    # Print report from the last build or bench command
    def print_last(self):

        # Get requested 
        last = self.get_last_output()
        command = last.replace("benchtool ", "")
        
        op = command
        label = ""
        if len(command.split(" ")) > 1:
            op = command.split(" ")[0]
            label = command.split(" ")[1]

        # If last output was from build task
        if op == "--build" or op == "-b":
            self.query_app(label)

        # If last output was from bench task
        elif op == "bench" or op == "-B":
            result_manager.query_result(self.glob, label)
        else:
            print("benchtool", op, label)

