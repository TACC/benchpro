# System Imports
import glob as gb
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.common as common_funcs

class init(object):
    def __init__(self, glob):
        self.glob = glob
        self.common = common_funcs.init(self.glob) 

    # Get list of files matching search
    def find_matching_files(self, search_dict):
        file_list = []
        for search in search_dict:
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
        search_dict = ['*.out*',
                       '*.err*',
                       '*.log',
                       'tmp.*',
                       '.history']

        file_list = self.find_matching_files(search_dict)

        if file_list:
            print("Found the following files to delete:")
            for f in file_list:
                print(f)

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
        if (parent_dir == self.glob.stg['build_basedir']) or  (parent_dir == self.glob.stg['module_basedir']) or (len(gb.glob(parent_path+self.glob.stg['sl']+"*")) > 1):
            su.rmtree(path)
        # Else resurse with parent
        else:
            self.prune_tree(parent_path)

    # Delete application and module matching path provided
    def remove_app(self):
        code_str = self.glob.args.remove
 
        remove_list = []
        if code_str == 'all':
            remove_list = self.common.get_installed()
        else:
            search_dict = {}
            for code_elem in code_str.split(self.glob.stg['sl']):
                search_dict[code_elem] = code_elem
            remove_list.append(self.common.check_if_installed(search_dict))

        for app in remove_list:
            # If not installed
            if not app:
                print(self.glob.error + "'" + code_str  + "' is not installed.")
                break

            # Get module dir from app dir, by adding 'modulefiles' prefix and stripping [version] suffix
            mod_dir = os.path.join(self.glob.stg['module_path'],  self.glob.stg['sl'].join(app.split(self.glob.stg['sl'])[:-1]))
            app_dir = os.path.join(self.glob.stg['build_path'], app)

            print("Found application installed in:")
            print(">  " + self.common.rel_path(app_dir))
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
                print(">  "  + self.common.rel_path(app_dir))
                print("Skipping")

            print()
            # Detele module dir
            try:
                self.prune_tree(mod_dir)
                print("Module removed.")
                print()
            except:
                print("Warning: no associated module located in:")
                print(">  " + self.common.rel_path(mod_dir))
                print("Skipping")

    # Display local shells to assist with determining if local job is still busy
    def print_local_shells(self):

        print("Running bash shells:")
        try:
            cmd = subprocess.run("ps -aux | grep " + self.glob.user + " | grep bash | grep bench", shell=True,
                                    check=True, capture_output=True, universal_newlines=True)

        except subprocess.CalledProcessError as e:
            exception.error_and_quit("Failed to run 'ps -aux'")

        for line in cmd.stdout.split("\n"):
            print(" " + line)

    # Print build report of installed application
    def query_app(self):

        code_str = self.glob.args.queryApp
        search_dict = {}
        
        # Disect search string into search dict
        for search_elem in code_str.split("/"):
            search_dict[search_elem] = search_elem
        
        app_dir = self.common.check_if_installed(search_dict)

        if not app_dir:
            print("Application '"+code_str+"' is not installed.")
            sys.exit(1)

        app_path = os.path.join(self.glob.stg['build_path'], self.common.check_if_installed(search_dict))
        build_report = os.path.join(app_path, self.glob.stg['build_report_file'])
        install_path = os.path.join(app_path, self.glob.stg['install_subdir'])

        exe = None
        jobid = None
        print("Build report for application '"+code_str+"'")
        print("-------------------------------------------")
        with open(build_report, 'r') as report:
            content = report.read()
            print(content)
            for line in content.split("\n"):
                if line[0:3] == "exe":
                    exe = line.split('=')[1].strip()
                elif line[0:5] == "jobid":
                    jobid = line.split('=')[1].strip()

        # Dry_run - do nothing
        if jobid == "dry_run":
            print("Build job was dry_run. Skipping executable check")
    
        else:
            # Local build        
            if jobid == "local":
                self.print_local_shells()
            # Sched build
            else:
                complete = self.common.check_job_complete(jobid)

                if complete:
                    print("Build job " + jobid + " state: " + complete)
                else:
                    print("Build job " + jobid + " for '" + code_str + "' is still running.")

            # Look for exe 
            exe_search = self.common.find_exact(exe, install_path)
            if exe_search:
                print("Executable found: " + self.common.rel_path(exe_search))
            else:
                print("WARNING: executable '" + exe + "' not found in application directory.")


    # Print currently installed apps, used together with 'remove'
    def show_installed(self):
        print("Currently installed applications:")
        print("---------------------------------")
        for app in self.common.get_installed():
            print("  " + os.path.join(self.common.rel_path(self.glob.stg['build_path']), app))

    def print_codes(self, code_list):
        code_list.sort()
        for code in code_list:
            code = code.split('/')[-1]
            if "_build" in code:
                print("    " + code[:-10])
            else:
                print("    " + code[:-4])

    # Print applications that can be installed from available cfg files
    def show_available(self, label, search_path):
        print("Available " + label + " profiles:")
        print("---------------------------------")
        print(self.common.rel_path(search_path) + ":")
        # Scan config/build
        app_dir = search_path + self.glob.stg['sl']
        self.print_codes(gb.glob(app_dir + "*.cfg"))

        # Scan config/build/[system]
        app_dir = app_dir + self.glob.sys_env + self.glob.stg['sl']
        if os.path.isdir(app_dir):
            print(self.common.rel_path(os.path.join(search_path, self.glob.sys_env)) + ":")
            self.print_codes(gb.glob(app_dir + "*.cfg"))
        print()

    def show_available_codes(self):
        search_path = os.path.join(self.glob.stg['config_basedir'], self.glob.stg['build_cfg_dir'])
        self.show_available("application", search_path)

    
    def show_available_benches(self):
        search_path = os.path.join(self.glob.stg['config_basedir'], self.glob.stg['bench_cfg_dir'])
        self.show_available("benchmark", search_path)

    def show_available_suites(self):
        print("Available benchmark suites:")
        print("---------------------------------")
        for key in self.glob.suite:
            print ("  " + key)


    # Print key/value pair from setting.ini dict
    def print_setting(self, key):
        print("  " + key.ljust(18) + " = " + str(self.glob.stg[key]))

    # Print default params from settings.ini
    def print_defaults(self):
        print("Default options in settings.ini:")
        print()
        [self.print_setting(key) for key in ['dry_run', \
                                            'exit_on_missing', \
                                            'overwrite', \
                                            'build_mode', \
                                            'build_if_missing', \
                                            'bench_mode',\
                                            'check_modules']]
        print("")
        print("Overload with '--overload [SETTING1=ARG]:[SETTING2=ARG]'")

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
        with open(os.path.join(self.glob.basedir, ".version")) as vfile:
            print(vfile.read())
        
