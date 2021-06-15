# System Imports
import copy
import datetime
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.logger as logger

glob = None

# Check if an existing installation exists
def check_for_previous_install():
    install_path = glob.config['metadata']['working_path']

    # If existing installation is found
    if os.path.isdir(install_path):
        # Delete if overwrite=True
        if glob.stg['overwrite']:

            glob.lib.msg.warning(["It seems this app is already installed. Deleting old build in " +
                         glob.lib.rel_path(install_path) + " because 'overwrite=True' in settings.ini",
                         "\033[0;31mDeleting in 5 seconds...\033[0m"])

            time.sleep(glob.stg['timeout'])
            glob.lib.msg.high("No going back now...")

            su.rmtree(install_path)
            # Installation not found (after delete)
            return False
        # Else warn and skip build
        else:
            glob.lib.msg.warning("Application already installed.") 
            glob.lib.msg.low(["Install path: " + glob.lib.rel_path(install_path),
                            "The install directory already exists and 'overwrite=False' in settings.ini"])
            glob.lib.msg.high("Skipping build.")
            return True
    # Installation not found
    else:
        return False

# Get build job dependency
def get_build_dep(job_limit):

    # Reset dependency lists
    glob.any_dep_list = []
    glob.ok_dep_list = []

    # Get queued/running build jobs
    running_task_ids = glob.lib.sched.get_active_jobids('_build')

    # Create dependency on apropriate running job 
    if len(running_task_ids) >= job_limit:
        glob.any_dep_list.append(str(running_task_ids[len(running_task_ids)-job_limit]))

# Main method for generating and submitting build script
def build_code(input_dict, glob_copy):

    # Use copy of glob for this build
    global glob
    glob = glob_copy

    
    print(glob)
    print("dict", hex(id(glob.overload_dict)))

    glob.lib.msg.heading("Building application:  '" + ",".join([i + "=" + input_dict[i] for i in input_dict.keys() if i]) + "'")

    # Parse config input files
    glob.lib.cfg.ingest('build',    input_dict)
    glob.lib.cfg.ingest('compiler', glob.stg['compile_cfg_file'])

    # If build dir already exists, skip this build
    if check_for_previous_install():
        print("end", glob)
        return

    glob.lib.msg.low(["", 
                    "Found matching application config file:",
                    ">  " + glob.lib.rel_path(glob.config['metadata']['cfg_file'])])

    # Get sched config dict if exec_mode=sched, otherwise set default threads for local build
    if glob.stg['build_mode'] == "sched":
        # If sched config file not specified, use system default
        if not glob.config['general']['sched_cfg']:
            glob.config['general']['sched_cfg'] = glob.lib.get_sched_cfg()
        # Ingest sched config from file
        glob.lib.cfg.ingest('sched', glob.config['general']['sched_cfg'])

        # Low priority stdout message
        glob.lib.msg.low(["Using scheduler config file:",
                        ">  " + glob.lib.rel_path(glob.sched['metadata']['cfg_file'])])
    else:
        glob.sched = {'sched': {'threads':8}}

    # Check for unused overload params (unless run from bench_manager)
    if not glob.quiet_build:
        glob.lib.check_for_unused_overloads()

    # Print inputs to log
    glob.lib.send_inputs_to_log('Builder')

    #============== GENERATE BUILD & MODULE TEMPLATE  ======================================

    # Generate build script
    glob.lib.template.generate_build_script()

    # Generate module file
    mod_path, mod_file = glob.lib.module.make_mod()

    # ================== COPY INSTALLATION FILES ===================================

    # Make build path and move tmp build script file
    glob.lib.create_dir(glob.config['metadata']['working_path'])
    glob.lib.install(glob.config['metadata']['working_path'], glob.tmp_script, None)

    # Make module path and move tmp module file
    glob.lib.create_dir(mod_path)
    glob.lib.install(mod_path, mod_file, None)

    # Copy code and sched cfg & template files to build dir
    provenance_path = os.path.join(glob.config['metadata']['working_path'], "build_files")
    glob.lib.create_dir(provenance_path)

    glob.lib.install(provenance_path, glob.config['metadata']['cfg_file'], "build.cfg")
    glob.lib.install(provenance_path, glob.config['template'], "build.template")

    # Copy sched config file if building via sched
    if glob.stg['build_mode'] == "sched":
        glob.lib.install(provenance_path, glob.sched['metadata']['cfg_file'], None)

    # Clean up tmp files
    glob.lib.files.remove_tmp_files()

    glob.lib.msg.high(glob.success)

# If dry_run
    if glob.stg['dry_run']:
        glob.lib.msg.low(["This was a dryrun, skipping build step. Script created at:",
                        ">  " + glob.lib.rel_path(os.path.join(glob.config['metadata']['working_path'], glob.script_file))])
        glob.task_id = "dry_run"

    else:
        # Submit job to sched
        if glob.stg['build_mode'] == "sched":
            # Check max running build jobs
            try:
                job_limit = int(glob.stg['max_build_jobs'])
            except:
                glob.lib.msg.error("'max_build_jobs in settings.ini is not an integer")

            get_build_dep(job_limit)

            # Submit build script to scheduler
            glob.lib.sched.submit()

        # Or start local shell
        else:
            glob.lib.proc.start_local_shell()
            #Store PID for report
            glob.task_id = glob.prev_pid

        glob.lib.msg.low(["Output file:",
                        ">  " + glob.lib.rel_path(os.path.join(glob.config['metadata']['working_path'], glob.config['config']['stdout']))])

    # Generate build report
    glob.lib.report.build()
    glob.lib.msg.high("Done.") 

# Setup contants and get build label
def init(glob):

    # Init logger
    logger.start_logging("BUILD", glob.stg['build_log_file'] + "_" + glob.time_str + ".log", glob)

    # Get list of avail cfgs
    glob.lib.set_build_cfg_list()

    # Overload settings.ini with cmd line args
    glob.lib.overload_params(glob.stg)

    # Check for new results
    if not glob.quiet_build:
        glob.lib.msg.new_results()

    #Check build_mode in set correctly
    if glob.stg['build_mode'] not in  ['sched', 'local']:
        glob.lib.msg.error(["Unsupported build execution mode found: '" + glob.stg['bench_mode']+"' in settings.ini",
                                    "Please specify 'sched' or 'local'."])

    # ----------------- IF CODE LABEL IS A LIST (FROM USER INPUT) --------------------------
    if isinstance(glob.args.build, list):

        build_list  = glob.args.build
        # If user input is a suite - get string from settings.ini
        if glob.args.build[0] in glob.suite.keys():

            build_list = glob.stg[glob.args.build[0]].split(" ")
            glob.lib.msg.heading(["Building suite '" + glob.args.build[0] + "': " + ", ".join(build_list), ""])


        # User build input (can be ' ' delimited)
        for build_str in build_list:
            print("*",glob.overload_dict)

            # Get a copy of the global object for use in this benchmark session
            glob_copy = copy.deepcopy(glob)


            glob_copy.overload_dict = copy.deepcopy(glob.overload_dict)

            print(build_str, glob_copy)

            build_code(glob.lib.parse_build_str(build_str), glob_copy)
            glob.lib.msg.brk()

    # ----------------- IF CODE LABEL IS A DICT (FROM BENCHER) --------------------------
    else:
        # Get a copy of the global object for use in this benchmark session
        glob_copy = copy.deepcopy(glob)

        # Start build
        build_code(glob.args.build, glob_copy)
        
