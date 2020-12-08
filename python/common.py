# System Imports
import configparser as cp
import copy
import datetime
import glob as gb
import os
import pwd
import re
import shutil as su
import subprocess
import sys
import time

# Local Imports
import exception

# Contains several useful functions, mostly used by bencher and builder
class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Get relative paths for full paths before printing to stdout
    def rel_path(self, path):
        # if empty str
        if not path:
            return None
        # if absolute
        if self.glob.basedir in path:
            return self.glob.stg['topdir_env_var'] + path.replace(self.glob.basedir, "")
        # if not
        else:
            return path

    # Find file in directory
    def find_exact(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name
    
        # Search recursively for file
        files = gb.glob(path+'/**/'+file_name, recursive = True)

        if files:
            return files[0]
        else:
            return None

    # Find *file* in directory
    def find_partial(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name
        # Search provided path for file
        for root, dirs, files in os.walk(path):
            match = next((s for s in files if file_name in s), None)
            if match:
                return os.path.join(root, match)
        # File not found
        return None

    # Get owner of file
    def file_owner(self, file_name):
        return pwd.getpwuid(os.stat(file_name).st_uid).pw_name

    # Get list of default modules
    def get_default_modules(self, cmd_prefix):
        
        try:
            cmd = subprocess.run(cmd_prefix +"ml -t -d av  2>&1", shell=True,
                                check=True, capture_output=True, universal_newlines=True)
        except:
            exception.error_and_quit(self.glob.log, "unable to execute 'ml -t -d av'")
        # Return list of default modules
        return cmd.stdout.split("\n")

    # Gets full module name of default module, eg: 'intel' -> 'intel/18.0.2'
    def get_full_module_name(self, module, default_modules):

        if not '/' in module:
            # Get default module version from 
            for line in default_modules:
                if line.startswith(module):
                    return line
            else:
                exception.error_and_quit(self.glob.log, "failed to process module '" + module + "'")

        else:
            return module

    # Check if module is available on the system
    def check_module_exists(self, module_dict, module_use):

        # Preload custom module path if needed
        cmd_prefix = ""
        if module_use:
            cmd_prefix = "ml use " + module_use + "; "

        # Get list of default system modules
        default_modules = self.get_default_modules(cmd_prefix)

        # Confirm defined modules exist on this system and extract full module name if necessary
        for module in module_dict:
            # If module is non Null
            if module_dict[module]:
                try:
                    cmd = subprocess.run(cmd_prefix + "module spider " + module_dict[module], shell=True,
                                        check=True, capture_output=True, universal_newlines=True)

                except subprocess.CalledProcessError as e:
                    exception.error_and_quit(self.glob.log, module + " module '" + module_dict[module] \
                                                            + "' not available on this system")

                # Update module with full label
                module_dict[module] = self.get_full_module_name(module_dict[module], default_modules)

    # Convert module name to usable directory name, Eg: intel/18.0.2 -> intel18
    def get_module_label(self, module):
        label = module
        if module.count(self.glob.stg['sl']) > 0:
            comp_ver = module.split(self.glob.stg['sl'])
            label = comp_ver[0] + comp_ver[1].split(".")[0]
        return label

    # Confirm application exe is available
    def check_exe(self, exe, code_path):
        exe_search = self.find_exact(exe, code_path)
        if exe_search:
            print("Application executable found at:")
            print(">  " + self.rel_path(exe_search))
            print()
        else:
            exception.error_and_quit(self.glob.log, "failed to locate application executable '" + exe + "'in " + self.rel_path(code_path))

    # Get a list of sub-directories, called by 'search_tree'
    def get_subdirs(self, base):
        return [name for name in os.listdir(base)
            if os.path.isdir(os.path.join(base, name))]

    # Recursive function to scan app directory, called by 'get_installed'
    def search_tree(self, installed_list, app_dir, start_depth, current_depth, max_depth):
        for d in self.get_subdirs(app_dir):
            if d != self.glob.stg['module_basedir']:
                new_dir = os.path.join(app_dir, d)
                # Once tree hits max search depth, append path to list
                if current_depth == max_depth:
                    installed_list.append(self.glob.stg['sl'].join(new_dir.split(self.glob.stg['sl'])[start_depth + 1:]))
                # Else continue to search tree 
                else:
                    self.search_tree(installed_list, new_dir, start_depth,current_depth + 1, max_depth)

    # Get list of installed apps
    def get_installed(self):
        app_dir = self.glob.stg['build_path']
        start = app_dir.count(self.glob.stg['sl'])
        # Send empty list to search function 
        installed_list = []
        self.search_tree(installed_list, app_dir, start, start, start + self.glob.stg['tree_depth'])
        installed_list.sort()
        return installed_list

    # Check that job ID is not running
    def check_job_complete(self, jobid):
        # If job not available in squeue anymore
        try:
            cmd = subprocess.run("sacct -j " + jobid + " --format State", shell=True, \
                            check=True, capture_output=True, universal_newlines=True)
        # Assuming complete
        except:
            return True

        # Strip out bad chars from job state
        state = ''.join(c for c in cmd.stdout.split("\n")[2] if c not in [' ', '*', '+'])

        # Job COMPLETE
        if any (state == x for x in ["COMPLETED", "CANCELLED", "ERROR", "FAILED", "TIMEOUT"]):
            return state

        # Job RUNNING or PENDING
        return False

    # Get results in ./results/current
    def get_current_results(self):
        return self.get_subdirs(self.glob.stg['current_path'])

    # Get results in ./results/archive
    def get_archive_results(self):
        return self.get_subdirs(self.glob.stg['archive_path'])

    # Test list of result dirs for file presence
    def check_for_file(self, result_dir, check_file):
        # Check list for 'check_file'
        if os.path.isfile(os.path.join(result_dir, check_file)):
            return True
        else:
            return False

    # Return list of results meeting capture status 
    def get_captured_results(self, search_list, check_file):
        # List of results to return
        matching_results = []

        # For each result
        for result in copy.deepcopy(search_list):
            if self.check_for_file(os.path.join(self.glob.stg['archive_path'], result), check_file):            
                matching_results.append(result)
                search_list.remove(result)

        return matching_results
    
    # Return jobid for result
    def get_result_jobid(self, result):
        jobid = None
        try:
        # Get jobID from bench_report.txt
            bench_report = os.path.join(self.glob.stg['current_path'], result, self.glob.stg['bench_report_file'])
            report_parser = cp.ConfigParser()
            report_parser.optionxform=str
            report_parser.read(bench_report)
            # Get JOBID in order to get NODELIST from sacct
            return report_parser.get('bench', 'jobid')
        except:
            return False

    # Return list of results meeting jobid status (True = complete, False = running)
    def get_completed_results(self, search_list, is_complete):
        # List of results to return
        matching_results = []
        # For every result
        if search_list:
            for result in copy.deepcopy(search_list):
                # Get jobid and check it is comeplete, if so append to return list and remove from provided list
                jobid = self.get_result_jobid(result)
                state = self.check_job_complete(jobid)
                if (state and is_complete) or (not state and not is_complete):
                    matching_results.append(result)
                    search_list.remove(result)

        matching_results.sort()
        return matching_results

    # Get list of uncaptured results and print note to user
    def print_new_results(self):
        print("Checking for uncaptured results...")
        # Uncaptured results + job complete
        pending_results = self.get_completed_results(self.get_current_results(), True)
        if pending_results:
            print(self.glob.note)
            print("There are " + str(len(pending_results)) + " uncaptured results found in " + self.rel_path(self.glob.stg['current_path']))
            print("Run 'benchtool --capture' to send to database.")
            print()
        else:
            print("No new results found.")

    # Log cfg contents
    def send_inputs_to_log(self, label):
        # List of global dicts containing input data
        cfg_list = [self.glob.code, self.glob.sched, self.glob.compiler]

        self.glob.log.debug(label + " started with the following inputs:")
        self.glob.log.debug("======================================")
        for cfg in cfg_list:
            for seg in cfg:
                self.glob.log.debug("[" + seg + "]")
                for line in cfg[seg]:
                    self.glob.log.debug("  " + str(line) + "=" + str(cfg[seg][line]))
        self.glob.log.debug("======================================")

    # Check for unpopulated <<<keys>>> in template file
    def test_template(self, template_file, template_obj):

        key = "<<<.*>>>"
        unfilled_keys = [re.search(key, line) for line in template_obj]
        unfilled_keys = [match.group(0) for match in unfilled_keys if match]
        
        if len(unfilled_keys) > 0:
            # Conitue regardless
            if not self.glob.stg['exit_on_missing']:
                exception.print_warning(self.glob.log, "Missing parameters were found in '" + template_file + "' template file:" + ", ".join(unfilled_keys))
                exception.print_warning(self.glob.log, "'exit_on_missing=False' in settings.ini so continuing anyway...")
            # Error and exit
            else:
                exception.error_and_quit(self.glob.log, "Missing parameters were found after populating '" + template_file + "' template file and exit_on_missing=True in settings.ini: " + ' '.join(unfilled_keys))
        else:
            self.glob.log.debug("All build parameters were filled, continuing")

    # Create directories if needed
    def create_dir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                exception.error_and_quit(
                    self.glob.log, "Failed to create directory " + path)

    # Copy tmp files to directory
    def install(self, path, obj, new_obj_name):
        # Get file name
        if not new_obj_name:
            new_obj_name = obj
            if self.glob.stg['sl'] in obj:
                new_obj_name = obj.split(self.glob.stg['sl'])[-1]
            # Strip tmp prefix from file for new filename
            if 'tmp.' in obj:
                new_obj_name = obj[4:]
    
        try:
            su.copyfile(obj, path + self.glob.stg['sl'] + new_obj_name)
            self.glob.log.debug("Copied file " + obj + " into " + path)
        except IOError as e:
            print(e)
            exception.error_and_quit(
                self.glob.log, "Failed to move " + obj + " to " + path + self.glob.stg['sl'] + new_obj_name)

    # Get Job IDs of RUNNING AND PENDNIG jobs
    def get_active_jobids(self, job_label):
        # Get list of jobs from sacct
        running_jobs_list = []
        job_list = None
        try:
            cmd = subprocess.run("sacct -u mcawood", shell=True, \
                                check=True, capture_output=True, universal_newlines=True)
            job_list = cmd.stdout.split("\n")

        except:
            pass

        # Add RUNNING job IDs to list
        for job in job_list:
            if "RUNNING" in job or "PENDING" in job:
                # If job label provided
                if job_label:
                    print(job, job_label)
                    # Search for it
                    if job_label in job:
                        running_jobs_list.append(int(job.split(" ")[0]))

                else:
                    running_jobs_list.append(int(job.split(" ")[0]))

        running_jobs_list.sort()

        return running_jobs_list

    # If build job is running, add dependency str
    def get_build_job_dependency(self, jobid):
        if not self.check_job_complete(jobid):
            self.glob.dep_list.append(jobid)

    # Set job dependency if max_running_jobs is reached
    def get_dep_str(self):
        if not self.glob.dep_list:
            return ""
        else:
            return "--dependency=afterany:" + ":".join([str(x) for x in self.glob.dep_list]) + " "

    # Check if host can run mpiexec
    def check_mpi_allowed(self):
        # Get list of hostnames on which mpiexec is banned
        try:
            no_mpi_hosts = self.glob.stg['mpi_blacklist'].split(',')

        except:
            exception.error_and_quit(self.glob.log, "unable to read list of MPI banned nodes (mpi_blacklist) in settings.ini")
        # If hostname contains any of the blacklisted terms, return False
        if any(x in self.glob.hostname for x in no_mpi_hosts):
            return False
        else:
            return True

    # Run script in shell
    def start_local_shell(self, working_dir, script_file, output_dir):

        script_path = os.path.join(working_dir, script_file)

        print("Starting script: " + self.rel_path(script_path))

        try:
            with open(os.path.join(working_dir, output_dir), 'w') as fp:
                cmd = subprocess.Popen(['bash', script_path], stdout=fp, stderr=fp)
                self.glob.prev_pid = cmd.pid

        except:
            exception.error_and_quit(self.glob.log,"failed to start build script in local shell.")

        print("Script started on local machine.")

    # Submit script to scheduler
    def submit_job(self, dep, job_path, script_file):
        script_path = os.path.join(job_path, script_file)
        print("Job script:")
        print(">  " + self.rel_path(script_path))
        print()
        print("Submitting to scheduler...")
        self.glob.log.debug("Submitting " + script_path + " to scheduler...")

        try:
            cmd = subprocess.run("sbatch " + dep + script_path, shell=True, \
                                 check=True, capture_output=True, universal_newlines=True)
    
            self.glob.log.debug(cmd.stdout)
            self.glob.log.debug(cmd.stderr)

            jobid = None
            i = 0
            jobid_line = "Submitted batch job"

            # Find job ID
            for line in cmd.stdout.splitlines():
                if jobid_line in line:
                    jobid = line.split(" ")[-1]

            time.sleep(self.glob.stg['timeout'])

            cmd = subprocess.run("squeue -a --job " + jobid, shell=True, \
                                 check=True, capture_output=True, universal_newlines=True)

            print(cmd.stdout)

            print()
            print("Job " + jobid + " stdout:")
            print(">  "+ self.rel_path(os.path.join(job_path, jobid + ".out")))

            print("Job " + jobid + " stderr:")
            print(">  "+ self.rel_path(os.path.join(job_path, jobid + ".err")))
            print()

            self.glob.log.debug(cmd.stdout)
            self.glob.log.debug(cmd.stderr)
            # Return job info
            return jobid

        except subprocess.CalledProcessError as e:
            print(e)
            exception.error_and_quit(self.glob.log, "failed to submit job to scheduler")

    # Get node suffixes from brackets: "[094-096]" => ['094', '095', '096']
    def get_node_suffixes(self, suffix_str):
        suffix_list = []
        for suf in suffix_str.split(','):
            if '-' in suf:
                start, end = suf.split('-')
                tmp = range(int(start), int(end)+1)
                tmp = [str(t).zfill(3) for t in tmp]
                suffix_list.extend(tmp)
            else:
                suffix_list.append(suf)
        return suffix_list

    # Parse SLURM nodelist to list: "c478-[094,102],c479-[032,094]" => ['c478-094', 'c478-102', 'c479-032', 'c479-094'] 
    def parse_nodelist(self, slurm_nodes):
        node_list = []
        while slurm_nodes:
            prefix_len = 4
            # Expand brackets first
            if '[' in slurm_nodes:
                # Get position of first '[' and ']'
                start = slurm_nodes.index('[')+1
                end = slurm_nodes.index(']')
                # Get node prefix for brackets, eg 'c478-'
                prefix = slurm_nodes[start-6:start-1]
                # Expand brackets 
                suffix = self.get_node_suffixes(slurm_nodes[start:end])
                node_list.extend([prefix + s for s in suffix])
                # Remove parsed nodes
                slurm_nodes = slurm_nodes[:start-6] + slurm_nodes[end+2:]
            # Extract remaining nodes
            else:
                additions = slurm_nodes.split(',')
                node_list.extend([s.strip() for s in additions])
                slurm_nodes = None

        node_list.sort()

        return node_list

    # Get NODELIST from sacct  using JOBID
    def get_nodelist(self, jobid):

        try:
            cmd = subprocess.run("sacct -X -P -j  " + jobid + " --format NodeList", shell=True, \
                                    check=True, capture_output=True, universal_newlines=True)

        except:
            return ""

        # Parse SLURM NODELIST into list
        return self.parse_nodelist(cmd.stdout.split("\n")[1])

    # Overload dict keys with overload key
    def overload(self, overload_key, param_dict):
        # If found matching key
            if overload_key in param_dict:
                old = param_dict[overload_key]

                # If cfg value is a list, skip datatype check
                if "," in self.glob.overload_dict[overload_key]:
                    param_dict[overload_key] = self.glob.overload_dict[overload_key]

                else:
                    datatype = type(param_dict[overload_key])

                    try:
                        # Convert datatypes
                        if datatype is str: 
                            param_dict[overload_key] = str(self.glob.overload_dict[overload_key])
                        elif datatype is int:
                            param_dict[overload_key] = int(self.glob.overload_dict[overload_key])
                        elif datatype is bool:
                            param_dict[overload_key] = self.glob.overload_dict[overload_key] == 'True'
                    except:
                        exception.error_and_quit(self.glob.log, "datatype mismatch for '" + overload_key +"', expected=" + str(datatype) + ", provided=" + str(type(overload_key)))

                print("Overloading " + overload_key + ": '" + str(old) + "' -> '" + str(param_dict[overload_key]) + "'" )
                # Remove key from overload dict
                self.glob.overload_dict.pop(overload_key)

    # Replace cfg params with cmd line inputs 
    def overload_params(self, search_dict):
        for overload_key in list(self.glob.overload_dict):
            # If dealing with code/sched/compiler cfg, descend another level
            if list(search_dict)[0] == "metadata":
                for section_dict in search_dict:
                    self.overload(overload_key, search_dict[section_dict])
            else:
                self.overload(overload_key, search_dict)

    # Print warning if cmd line params dict not empty
    def check_for_unused_overloads(self):
        if len(self.glob.overload_dict):
            print("The following --overload argument does not match existing params:")
            for key in self.glob.overload_dict:
                print("  " + key + "=" + self.glob.overload_dict[key])
            exception.error_and_quit(self.glob.log, "Invalid input arguments.")

    # Write module to file
    def write_list_to_file(self, list_obj, output_file):
        with open(output_file, "w") as f:
            for line in list_obj:
                f.write(line)

    # Get list of files in search path
    def get_files_in_path(self, search_path):
        return gb.glob(os.path.join(search_path, "*.cfg"))

    def get_list_of_cfgs(self, cfg_type):
        # Get cfg subdir name from input
        type_dir = ""
        if cfg_type == "build":
            type_dir = self.glob.stg['build_cfg_dir']
        elif cfg_type == "bench":
            type_dir = self.glob.stg['bench_cfg_dir']
        else:
            exception.error_and_quit(self.glob.log, "unknown cfg type '"+cfg_type+"'. get_list_of_cfgs() accepts either 'build' or 'bench'.")

        search_path = os.path.join(self.glob.stg['config_path'], type_dir)
        # Get list of cfg files in dir
        cfg_list = self.get_files_in_path(search_path)

        # If system subdir exists, scan that too
        if os.path.isdir(os.path.join(search_path,self.glob.system['sys_env'])):
            cfg_list = cfg_list + self.get_files_in_path(os.path.join(search_path,self.glob.system['sys_env']))
        return cfg_list

    # extract filename from absolute path
    def get_filename_from_path(self, full_path):
        return full_path.split(self.glob.stg['sl'])[-1]

    # Print list of available cfg files
    def print_avail_cfgs(self, avail_cfgs):
        cfg_filenames = [self.get_filename_from_path(cfg) for cfg in avail_cfgs]
        cfg_filenames.sort()
        print("Available config files:")
        for cfg in cfg_filenames:
            print("  " + cfg)

    # Check for unique bench config file
    def get_cfg_file(self, input_label):

        # Get list of available bench cfg files in config/bench
        avail_cfgs = self.get_list_of_cfgs("bench")

        # Check for file matching search 
        for cfg_filename in avail_cfgs:
            if input_label in cfg_filename:
                return cfg_filename

        # Print avail and exit
        self.print_avail_cfgs(avail_cfgs)
        exception.error_and_quit(self.glob.log, "input cfg file matching '" + input_label + "' not found.")

    # returns dict of search fields to locate installed application, from bench cfg file
    def get_search_list(self, cfg_file):

        cfg_parser = cp.ConfigParser()
        try:
            with open(cfg_file) as cfile:
                cfg_parser.read_file(cfile)
                search_list = cfg_parser.items('requirements').values()

        except Exception as err:
            print(err)
            exception.error_and_quit(self.glob.log, "failed to read [requirements] section of cfg file " + cfg_file)
        
        return search_list

    # Search code_path with values in search_list
    def search_with_list(self, search_list, code_path):
        match = True
        # Break code path by /
        code_path_elems = code_path.split(self.glob.stg['sl'])

        #Ensure every val that is set in search dict is found in code path
        for search in search_list:
            if search and not search in code_path_elems:
                # Otherwise not code does not match requirements
                match = False
        return match

    # Check if the requirements in bench.cfg need a built code 
    def needs_code(self, search_list):
        # Check if all search_list values are empty
        if not search_list:
            return False
        else:
            return True

    # Check if search_list returns unique installed application
    def check_if_installed(self, search_list):

        # Get list of installed applications
        installed_list = self.get_installed()

        # For each installed code
        results = [app for app in installed_list if self.search_with_list(search_list, app)]

        # Unique result
        if len(results) == 1:
            return results[0]

        # No results
        elif len(results) == 0:

            if self.glob.stg['build_if_missing']:
                return False
            else:
                print("No installed applications match your selection criteria: ", search_list)
                print("And 'build_if_missing'=False in settings.ini")
                print("Currently installed applications:")
                for code in installed_list:
                    print(" " + code)
                sys.exit(1)

        # Multiple results
        elif len(results) > 1:

            print("Multiple installed applications match your selection critera: ", search_list)
            for code in results:
                print("  ->" + code)
            print("Please be more specific.")
            sys.exit(1)

    # Read every build config file and construct a list with format [[cfg_file, code, version, build_label],...]
    def get_avail_codes(self):

        # Get all application build config files
        cfg_list = self.get_list_of_cfgs("build")

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
                exception.error_and_quit(self.glob.log, "failed to read [requirements] section of cfg file " + cfg_file)
        
        # Return list
        return avail_list

    # Check if search dict matches an avaiable application
    def check_if_avail(self, search_list):

        # Get list of available application config files
        avail_list = self.get_avail_codes()

        results = []
        # Check for matching available applications
        for code in avail_list:
            print("&&&", code)
            print("%%%", search_list)
            if search_list[0] in code[1] and search_list[1] in code[2] and search_list[2] in code[3]:
                results.append(code[0])

        # Unique match
        if len(results) == 1:
            return results[0]

        elif len(results) == 0:
            print("No application profile available which meet your search criteria:", search_list)
            sys.exit(1)

        elif len(results) > 1:
            print("There are multiple applications available which meet your search criteria:")
            for result in results:
                print("  " + self.rel_path(result))
            sys.exit(1)

    # Get the process PID for the build
    def get_build_pid(self):
        print("Trying to get PID for build script")
        time.sleep(5)
        try:
            cmd = subprocess.run("ps -aux | grep " + self.glob.user + " | grep bash | grep build", shell=True,
                                    check=True, capture_output=True, universal_newlines=True)

        except subprocess.CalledProcessError as e:
            exception.error_and_quit("Failed to run 'ps -aux'")

        pid = cmd.stdout.split("\n")[0].split(" ")[2]
        if not pid:
            exception.error_and_quit(self.glob.log, "Could not determine PID for build script. ps -aux gave: '" + cmd.stdout + "'")

        return pid

    # Replace SLURM variables in ouput files
    def check_for_slurm_vars(self):
        self.glob.code['result']['output_file'] = self.glob.code['result']['output_file'].replace("$SLURM_JOBID", self.glob.jobid) 

    # Write operation to file
    def write_to_outputs(self, op, label):
        with open(os.path.join(self.glob.basedir, ".outputs"), "a") as f:
            f.write(op + " " + label + "\n")

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
                return "slurm_" + self.glob.sys_env
   
    # Extract system variables from system.cfg
    def get_system_vars(self, system):
    
        system_dict = {'sys_env': system}
        cfg_file = os.path.join(self.glob.stg['config_path'], self.glob.stg['system_cfg_file'])
        system_parser   = cp.RawConfigParser(allow_no_value=True)
        system_parser.read(cfg_file)

        try:
            system_dict['cores']          = system_parser[system]['cores']
            system_dict['cores_per_node'] = system_parser[system]['cores']
            system_dict['default_arch']   = system_parser[system]['default_arch']
            # Set system default sched cfg if available
            if 'default_sched' in system_parser[system]:
                system_dict['default_sched'] = system_parser[system]['default_sched']
            return system_dict

        except:
            return False

