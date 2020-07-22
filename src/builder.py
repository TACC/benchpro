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
    path = glob.code['general']['working_path']
    if os.path.exists(path):
        if glob.stg['overwrite']:
            glob.log.debug("WARNING: It seems this app is already installed. Deleting old build in " +
                         path + " because 'overwrite=True' in settings.cfg")

            print()
            print("WARNING: Application directory already exists and 'overwrite=True' in settings.cfg, continuing in 5 seconds...")
            print()

            time.sleep(glob.stg['timeout'])
            print("No going back now...")

            su.rmtree(path)
        else:
            exception.error_and_quit(glob.log, "It seems this app is already installed in " + common.rel_path(path) +
                                     ". The install directory already exists and 'overwrite=False' in settings.cfg")

# Generate build report after job is submitted
def generate_build_report(jobid):
    report_file = glob.code['general']['working_path'] + glob.stg['sl'] + glob.stg['build_report_file']

    with open(report_file, 'a') as out:
        out.write("[build]\n")
        out.write("code         = "+ glob.code['general']['code']             + "\n")
        out.write("version      = "+ glob.code['general']['version']          + "\n")
        out.write("system       = "+ glob.code['general']['system']           + "\n")
        out.write("compiler     = "+ glob.code['modules']['compiler']         + "\n")
        out.write("mpi          = "+ glob.code['modules']['mpi']              + "\n")
        if glob.code['general']['module_use']:
            out.write("module_use   = "+ glob.code['general']['module_use']   + "\n")
        out.write("modules      = "+ ", ".join(glob.code['modules'].values()) + "\n")
        out.write("optimization = "+ glob.code['build']['opt_flags']          + "\n")    
        out.write("exe          = "+ glob.code['build']['exe']                + "\n")
        out.write("build_prefix = "+ glob.code['general']['working_path']     + "\n")
        out.write("build_date   = "+ str(datetime.datetime.now())             + "\n")
        out.write("jobid        = "+ jobid                                    + "\n")

# Main methond for generating and submitting build script
def build_code(glob_obj):


    #=========================   INIT AND STARTUP CHECKS   ============================================
    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Init loggers
    glob.log = logger.start_logging("BUILD", glob.stg['build_log_file'] + "_" + glob.time_str + ".log", glob)

    # Instantiate common_funcs
    common = common_funcs.init(glob)
    
    # Overload settings.cfg with cmd line args
    common.overload_params(glob.stg)

    # Check for new results
    common.print_new_results()

    #=========================== INGEST PARAMS FROM CFGS   ========================================

    # Parse config input files
    cfg_handler.ingest_cfg('build',    glob.args.build,              glob)
    cfg_handler.ingest_cfg('sched',    glob.args.sched,              glob)
    cfg_handler.ingest_cfg('compiler', glob.stg['compile_cfg_file'], glob)

    print()
    # Check for empty overload params
    common.check_for_unused_overloads()

    print()
    print("Using application config file:") 
    print(">  " + common.rel_path(glob.code['metadata']['cfg_file']))
    print()
    print("Using scheduler config file:")
    print(">  " + common.rel_path(glob.sched['metadata']['cfg_file']))
    print()

    # Print inputs to log
    common.send_inputs_to_log('Builder', [glob.code, glob.sched, glob.compiler])

    # Check if build dir already exists
    check_for_previous_install()

    #============== GENERATE BUILD & MODULE TEMPLATE  ======================================


    # Generate build script
    template_handler.generate_build_script(glob)

    # Generate module in temp location
    mod_path, mod_file = module_handler.make_mod(glob)


    # ================== COPY INSTALLATION FILES ===================================


    # Make build path and move tmp build script file
    common.create_dir(glob.code['general']['working_path'])
    common.install(glob.code['general']['working_path'], glob.tmp_script, None)
    print()
    print("Build script location:")
    print(">  " + common.rel_path(glob.code['general']['working_path']))
    print()

    # Make module path and move tmp module file
    common.create_dir(mod_path)
    common.install(mod_path, mod_file, None)

    print("Module file location:")
    print(">  " + common.rel_path(mod_path))
    print()

    # Copy code and sched cfg & template files to build dir
    provenance_path = glob.code['general']['working_path'] + glob.stg['sl'] + "build_files"
    common.create_dir(provenance_path)

    common.install(provenance_path, glob.code['metadata']['cfg_file'], "build.cfg")
    common.install(provenance_path, glob.code['template'], "build.template")

    common.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
    common.install(provenance_path, glob.sched['template'], None)

    # Clean up tmp files
    exception.remove_tmp_files(glob.log)

    # Submit build script to scheduler
    jobid = common.submit_job(glob.code['general']['working_path'], glob.tmp_script[4:])

    # Generate build report
    generate_build_report(jobid)
