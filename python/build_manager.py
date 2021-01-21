# System Imports
import copy
import datetime
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import exception
import logger

glob = None

# Check if an existing installation exists
def check_for_previous_install():
    install_path = glob.code['metadata']['working_path']
    # If existing installation is found
    if os.path.isdir(install_path):
        # Delete if overwrite=True
        if glob.stg['overwrite']:
            glob.log.debug("WARNING: It seems this app is already installed. Deleting old build in " +
                         install_path + " because 'overwrite=True' in settings.ini")

            print()
            print("WARNING: Application directory already exists and 'overwrite=True' in settings.ini")
            print("\033[0;31mDeleting in 5 seconds...\033[0m")
            print()

            time.sleep(glob.stg['timeout'])
            print("No going back now...")

            su.rmtree(install_path)
            # Installation not found (after delete)
            return False
        # Else warn and skip build
        else:
            exception.print_warning(glob.log, "It seems this app is already installed in " + glob.lib.rel_path(install_path) +
                                     ".\nThe install directory already exists and 'overwrite=False' in settings.ini. Skipping build.")
            return True
    # Installation not found
    else:
        return False

# Get build job dependency
def get_build_dep(job_limit):
    glob.dep_list = []
    # Get queued/running build jobs
    running_jobids = glob.lib.sched.get_active_jobids('_build')

    # Create dependency on apropriate running job 
    if len(running_jobids) >= job_limit:
        glob.dep_list.append(str(running_jobids[len(running_jobids)-job_limit]))

# Main method for generating and submitting build script
#
# code_label can be string or list of strings, this is handled in cfg_handler
#
def build_code(code_label):

    print("Starting build process for application '" + code_label + "'")

    # Parse config input files
    glob.lib.cfg.ingest('build',    code_label)
    glob.lib.cfg.ingest('compiler', glob.stg['compile_cfg_file'])

    # If build dir already exists, skip this build
    if check_for_previous_install():
        return

    print()
    print("Using application config file:")
    print(">  " + glob.lib.rel_path(glob.code['metadata']['cfg_file']))
    print()

    # Get sched config dict if exec_mode=sched, otherwise set threads 
    if glob.stg['build_mode'] == "sched":
        if not glob.code['general']['sched_cfg']:
            glob.code['general']['sched_cfg'] = glob.lib.get_sched_cfg()
        glob.lib.cfg.ingest('sched', glob.code['general']['sched_cfg'])
        print("Using scheduler config file:")
        print(">  " + glob.lib.rel_path(glob.sched['metadata']['cfg_file']))
        print()
    else:
        glob.sched = {'sched': {'threads':8}}

    # Check for empty overload params

    if not glob.quiet_build:
        glob.lib.check_for_unused_overloads()

    # Print inputs to log
    glob.lib.send_inputs_to_log('Builder')

    #============== GENERATE BUILD & MODULE TEMPLATE  ======================================

    # Generate build script
    glob.lib.template.generate_build_script()

    # Generate module in temp location
    mod_path, mod_file = glob.lib.module.make_mod()

    # ================== COPY INSTALLATION FILES ===================================

    # Make build path and move tmp build script file
    glob.lib.create_dir(glob.code['metadata']['working_path'])
    glob.lib.install(glob.code['metadata']['working_path'], glob.tmp_script, None)

    # Make module path and move tmp module file
    glob.lib.create_dir(mod_path)
    glob.lib.install(mod_path, mod_file, None)

    # Copy code and sched cfg & template files to build dir
    provenance_path = os.path.join(glob.code['metadata']['working_path'], "build_files")
    glob.lib.create_dir(provenance_path)

    glob.lib.install(provenance_path, glob.code['metadata']['cfg_file'], "build.cfg")
    glob.lib.install(provenance_path, glob.code['template'], "build.template")

    # Copy sched config file if building via sched
    if glob.stg['build_mode'] == "sched":
        glob.lib.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
        glob.lib.install(provenance_path, glob.sched['template'], None)

    # Clean up tmp files
    exception.remove_tmp_files(glob.log)

    print(glob.success)

    output_file = ""

    # If dry_run
    if glob.stg['dry_run']:
        print("This was a dryrun, skipping build step. Script created at:")
        print(">  " + glob.lib.rel_path(os.path.join(glob.code['metadata']['working_path'], glob.tmp_script[4:])))
        glob.jobid = "dry_run"

    else:
        # Submit job to sched
        if glob.stg['build_mode'] == "sched":
            # Check max running build jobs
            try:
                job_limit = int(glob.stg['max_build_jobs'])
            except:
                exception.error_and_quit(glob.log, "'max_build_jobs in settings.ini is not an integer")

            get_build_dep(job_limit)

            # Submit build script to scheduler
            glob.lib.sched.submit()
            output_file = glob.jobid + ".out"

        # Or start local shell
        else:
            output_file = "bash.stdout"
            glob.lib.start_local_shell(glob.code['metadata']['working_path'], glob.tmp_script[4:], output_file)
            glob.jobid = "local"

        print("Output file:")
        print(">  " + glob.lib.rel_path(os.path.join(glob.code['metadata']['working_path'], output_file)))

    # Generate build report
    glob.lib.report.build()

# Setup contants and get build label
def init(glob_obj):

    # Get global settings obj
    global glob
    glob = glob_obj

    # Init loggers
    glob.log = logger.start_logging("BUILD", glob.stg['build_log_file'] + "_" + glob.time_str + ".log", glob)

    # Overload settings.ini with cmd line args
    glob.lib.overload_params(glob.stg)

    # Check for new results
    if not glob.quiet_build:
        glob.lib.msg.new_results()

    #Check build_mode in set correctly
    if glob.stg['build_mode'] not in  ['sched', 'local']:
        exception.error_and_quit(glob.log, "Unsupported build execution mode found: '"+glob.stg['bench_mode']+"' in settings.ini, please specify 'sched' or 'local'.")

    # ----------------- IF CODE LABEL IS A STRING (FROM USER INPUT) --------------------------
    if isinstance(glob.args.build, str):

        # Either build codes in suite or user label
        if 'suite' in glob.args.build:
            if glob.args.build in glob.suite.keys():
                code_label_list = glob.stg[glob.args.build].split(',')
                print("Building application suite '" + glob.args.build + "': " + glob.stg[glob.args.build])
                for code_label in code_label_list:
                    build_code(code_label)
            else:
                exception.error_and_quit(glob.log, "No suite '" + glob.args.build + "' in settings.ini. Available suites: " + ', '.join(glob.suite.keys())) 

        # User build input (can be ':' delimited)
        else:
            code_list = glob.args.build.split(":")
            for code_label in code_list:
                build_code(code_label)


    # ----------------- IF CODE LABEL IS A DICT (FROM BENCHER) --------------------------
    else:
        build_code(glob.args.build)
