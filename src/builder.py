# System Imports
import datetime
import os
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.logger as logger
import src.module_handler as module_handler
import src.template_handler as template_handler

glob = common = None

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
            exception.print_warning(glob.log, "It seems this app is already installed in " + common.rel_path(install_path) +
                                     ".\nThe install directory already exists and 'overwrite=False' in settings.ini. Skipping build.")
            return True
    # Installation not found
    else:
        return False

# Generate build report after job is submitted
def generate_build_report(jobid):
    report_file = os.path.join(glob.code['metadata']['working_path'], glob.stg['build_report_file'])

    with open(report_file, 'a') as out:
        out.write("[build]\n")
        out.write("code           = "+ glob.code['general']['code']             + "\n")
        out.write("version        = "+ str(glob.code['general']['version'])     + "\n")
        out.write("system         = "+ glob.code['general']['system']           + "\n")
        out.write("compiler       = "+ glob.code['modules']['compiler']         + "\n")
        out.write("mpi            = "+ glob.code['modules']['mpi']              + "\n")
        out.write("module_use     = "+ glob.code['general']['module_use']       + "\n")
        out.write("modules        = "+ ", ".join(glob.code['modules'].values()) + "\n")
        out.write("optimization   = "+ glob.code['config']['opt_flags']         + "\n")    
        out.write("exe            = "+ glob.code['config']['exe']               + "\n")
        out.write("build_prefix   = "+ glob.code['metadata']['working_path']    + "\n")
        out.write("build_date     = "+ str(datetime.datetime.now())             + "\n")
        out.write("jobid          = "+ jobid                                    + "\n")

# Get build job dependency
def get_build_dep(job_limit):
    glob.dep_list = []
    # Get queued/running build jobs
    running_jobids = common.get_active_jobids('_build')

    # Create dependency on apropriate running job 
    if len(running_jobids) >= job_limit:
        glob.dep_list.append(str(running_jobids[len(running_jobids)-job_limit]))

# Main method for generating and submitting build script
def build_code(code_label):

    # Parse config input files
    cfg_handler.ingest_cfg('build',    code_label,                  glob)
    cfg_handler.ingest_cfg('compiler', glob.stg['compile_cfg_file'],glob)

    # If build dir already exists, skip this build
    if check_for_previous_install():
        return

    print()
    print("Using application config file:")
    print(">  " + common.rel_path(glob.code['metadata']['cfg_file']))
    print()

    # Get sched config dict if exec_mode=sched, otherwise set threads 
    if glob.stg['build_mode'] == "sched":
        cfg_handler.ingest_cfg('sched',    glob.args.sched,             glob)
        print("Using scheduler config file:")
        print(">  " + common.rel_path(glob.sched['metadata']['cfg_file']))
        print()
    else:
        glob.sched = {'sched': {'threads':8}}

    print()
    # Check for empty overload params
    common.check_for_unused_overloads()

    # Print inputs to log
    common.send_inputs_to_log('Builder')

    #============== GENERATE BUILD & MODULE TEMPLATE  ======================================

    # Generate build script
    template_handler.generate_build_script(glob)

    # Generate module in temp location
    mod_path, mod_file = module_handler.make_mod(glob)

    # ================== COPY INSTALLATION FILES ===================================

    # Make build path and move tmp build script file
    common.create_dir(glob.code['metadata']['working_path'])
    common.install(glob.code['metadata']['working_path'], glob.tmp_script, None)
    print()
    print("Build script location:")
    print(">  " + common.rel_path(glob.code['metadata']['working_path']))
    print()

    # Make module path and move tmp module file
    common.create_dir(mod_path)
    common.install(mod_path, mod_file, None)

    print("Module file location:")
    print(">  " + common.rel_path(mod_path))
    print()

    # Copy code and sched cfg & template files to build dir
    provenance_path = os.path.join(glob.code['metadata']['working_path'], "build_files")
    common.create_dir(provenance_path)

    common.install(provenance_path, glob.code['metadata']['cfg_file'], "build.cfg")
    common.install(provenance_path, glob.code['template'], "build.template")

    # Copy sched config file if building via sched
    if glob.stg['build_mode'] == "sched":
        common.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
        common.install(provenance_path, glob.sched['template'], None)

    # Clean up tmp files
    exception.remove_tmp_files(glob.log)

    print(glob.success)

    output_file = ""

    # If dry_run
    if glob.stg['dry_run']:
        print("This was a dryrun, skipping build step. Script created at:")
        print(">  " + common.rel_path(os.path.join(glob.code['metadata']['working_path'], glob.tmp_script[4:])))
        jobid = "dry_run"

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
            jobid = common.submit_job(common.get_dep_str(), glob.code['metadata']['working_path'], glob.tmp_script[4:])
            output_file = jobid + ".out"

        # Or start local shell
        else:
            output_file = "bash.stdout"
            common.start_local_shell(glob.code['metadata']['working_path'], glob.tmp_script[4:], output_file)
            jobid = "local"

        print("Output file:")
        print(">  " + common.rel_path(os.path.join(glob.code['metadata']['working_path'], output_file)))


    # Generate build report
    generate_build_report(jobid)

# Setup contants and get build label
def init(glob_obj):

    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Init loggers
    glob.log = logger.start_logging("BUILD", glob.stg['build_log_file'] + "_" + glob.time_str + ".log", glob)

    # Instantiate common_funcs
    common = common_funcs.init(glob)
    
    # Overload settings.ini with cmd line args
    common.overload_params(glob.stg)

    # Check for new results
    common.print_new_results()


    #Check build_mode in set correctly
    if glob.stg['build_mode'] not in  ['sched', 'local']:
        exception.error_and_quit(glob.log, "Unsupported build execution mode found: '"+glob.stg['bench_mode']+"' in settings.ini, please specify 'sched' or 'local'.")

    # Either build codes in suite or user label
    if 'suite' in glob.args.build:
        if glob.args.build in glob.suite.keys():
            code_label_list = glob.stg[glob.args.build].split(',')
            print("Building application set '" + glob.args.build + "': " + str(code_label_list))
            for code_label in code_label_list:
                build_code(code_label)
        else:
            exception.error_and_quit(glob.log, "No suite '" + glob.args.build + "' in settings.ini. Available suites: " + ', '.join(glob.suite.keys())) 

    # User build input (can be ':' delimited)
    else:
        code_list = glob.args.build.split(":")
        for code in code_list:
            build_code(code)

