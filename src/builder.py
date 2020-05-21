# System Imports
import configparser as cp
import glob
import logging as lg
import os
import pprint as pp
import re
import shutil as su
import socket
import subprocess
import sys
import time
from datetime import datetime

# Local Imports
import src.cfg_handler as cfg_handler
import src.exception as exception
import src.module_handler as module_handler
import src.template_handler as template_handler

gs     = ''

def start_logging(name, file):

    print("Log file for this session:   " + str(file))

    formatter = lg.Formatter("{0}: ".format(name) + gs.user + "@" + gs.hostname + ": " +
                             "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    logger = lg.getLogger(name)
    logger.setLevel(gs.log_level)

    file_handler = lg.FileHandler(file, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    #stream_handler = lg.StreamHandler(stream=sys.stderr)
    # stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler)

    return logger

# Check if an existing installation exists


def check_for_previous_install(path):
    if os.path.exists(path):
        if gs.overwrite:
            logger.debug("WARNING: It seems this app is already installed. Deleting old build in " +
                         path + " because 'overwrite=True' in settings.cfg")

            print()
            print("WARNING: Application directory already exists and 'overwrite=True' in settings.cfg, continuing in 5 seconds...")
            print()

            time.sleep(gs.timeout)
            print("No going back now...")

            su.rmtree(path)
        else:
            exception.error_and_quit(logger, "It seems this app is already installed in " + path +
                                     ". The install directory already exists and 'overwrite=False' in settings.cfg")

# Create directories if needed


def create_install_dir(path, logger):
    # Try to create build directory
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            exception.error_and_quit(
                logger, "Failed to make directory " + path)

# Move files to install directory


def install(path, obj, logger):

    # Get file name
    new_obj_name = obj
    if gs.sl in obj:
        new_obj_name = obj.split(gs.sl)[-1]
    # Strip tmp prefix from file
    if 'tmp.' in obj:
        new_obj_name = obj[4:]

    try:
        su.copyfile(obj, path + gs.sl + new_obj_name)
    except IOError as e:
        print(e)
        exception.error_and_quit(
            logger, "Failed to move " + obj + " to " + path + gs.sl + new_obj_name)

# Check if module is available on the system


def check_module_exists(module):
    try:
        cmd = subprocess.run("module spider " + module, shell=True,
                             check=True, capture_output=True, universal_newlines=True)

    except subprocess.CalledProcessError as e:
        exception.error_and_quit(
            logger, "module " + module + " not available on this system")

# Log cfg contents


def send_inputs_to_log(cfg):

    logger.debug("Builder started with the following inputs:")
    for seg in cfg:
        logger.debug("[" + seg + "]")
        for line in cfg[seg]:
            logger.debug("  " + str(line) + "=" + str(cfg[seg][line]))

# Check build params, add defaults if needed


def set_build_paths(build_dict, build_path):

    if not "working_path" in build_dict.keys():
        build_dict["working_path"] = build_path

    if not "build_path" in build_dict.keys():
        build_dict["build_path"] = build_path + gs.sl + "build"

    if not "install_path" in build_dict.keys():
        build_dict["install_path"] = build_path + gs.sl + "install"

    return build_dict

# Submit build script to scheduler


def submit_job(script_file, logger):
    print()
    if gs.dry_run:
        print("This was a dryrun, job script created at " + script_file)
        logger.debug("This was a dryrun, job script created at " + script_file)
    else:
        print("Submitting " + script_file + " to scheduler...")
        logger.debug("Submitting build script to scheduler...")
        try:
            cmd = subprocess.run("sbatch " + script_file, shell=True,
                                 check=True, capture_output=True, universal_newlines=True)

            logger.debug(cmd.stdout)
            logger.debug(cmd.stderr)

            job_id = ''
            i = 0
            jobid_line = "Submitted batch job"

            # Find job ID
            for line in cmd.stdout.splitlines():
                if jobid_line in line:
                    job_id = line.split(" ")[-1]

            time.sleep(2)
            cmd = subprocess.run("squeue -a --job " + job_id, shell=True,
                                 check=True, capture_output=True, universal_newlines=True)

            print(cmd.stdout)
            logger.debug(cmd.stdout)
            logger.debug(cmd.stderr)

        except subprocess.CalledProcessError as e:
            exception.error_and_quit(
                logger, "Failed to submit job to scheduler")

# Main methond for generating and submitting build script


def build_code(args, settings):

    global gs
	gs = settings

    # Init loggers
    logger = start_logging("BUILD", file=gs.base_dir +
                           gs.sl + gs.build_log_file + "_" + gs.time_str + ".log")

    # Parse config input files
    code_cfg =     cfg_handler.get_cfg('build',    args.install,        gs, logger)
    sched_cfg =    cfg_handler.get_cfg('sched',    args.sched,          gs, logger)
    compiler_cfg = cfg_handler.get_cfg('compiler', 'compile-flags.cfg', gs, logger)

    print('{:25}'.format('Using application config'),
          ":", code_cfg['metadata']['cfg_file'])
    print('{:25}'.format('Using scheduler config'),
          ":",   sched_cfg['metadata']['cfg_file'])

    # Print inputs to log
    send_inputs_to_log(code_cfg)
    send_inputs_to_log(sched_cfg)
    send_inputs_to_log(compiler_cfg)

    # Get compiler cmds for gcc/intel
    compiler_cfg['common'].update(
        compiler_cfg[code_cfg['build']['compiler_type']])

    # Input Checks
    for mod in code_cfg['modules']:
        check_module_exists(code_cfg['modules'][mod])

    # Check if build dir already exists
    check_for_previous_install(code_cfg['general']['build_prefix'])

    # Add build dirs to dict
    code_cfg['build'] = set_build_paths(
        code_cfg['build'], code_cfg['general']['build_prefix'])

    # Name of tmp build script
    script_file = "tmp." + \
        code_cfg['general']['code'] + "-build." + \
        sched_cfg['scheduler']['type']

    # Template files
    sched_template = gs.sched_tmpl_dir + gs.sl + \
        sched_cfg['scheduler']['type'] + ".template"
    build_template = gs.build_tmpl_dir + gs.sl + \
        code_cfg['general']['code'] + "-" + \
        code_cfg['general']['version'] + ".build"
    compiler_template = "compile_flags.template"
    module_template = gs.build_tmpl_dir + gs.sl + \
        code_cfg['general']['code'] + "-" + \
        code_cfg['general']['version'] + ".module"

    # Use generic module template if not found for this application
    if not os.path.exists(module_template):
        logger.debug("WARNING: " + code_cfg['general']['code'] +
                     " module template file not available at " + module_template)
        logger.debug("WARNING: using a generic module template")
        module_template = "/".join(module_template.split("/")
                                   [:-1]) + gs.sl + "generic.module"

    # Generate build script
    template_handler.generate_template([code_cfg['general'], code_cfg['modules'], code_cfg['build'], code_cfg['run'], sched_cfg['scheduler'], compiler_cfg['common']],
                                       [sched_template, compiler_template,
                                           build_template],
                                       script_file, gs, logger)

    # Generate module in temp location
    mod_path, mod_file = module_handler.make_mod(
        module_template, code_cfg['general'], code_cfg['build'], code_cfg['modules'], gs, logger)

    # Make build dir and move tmp file
    create_install_dir(code_cfg['general']['build_prefix'], logger)
    install(code_cfg['general']['build_prefix'], script_file, logger)
    print('{:25}'.format('Build script location'),
          ":", code_cfg['general']['build_prefix'])

    # Make module dir and move tmp file
    create_install_dir(mod_path, logger)
    install(mod_path, mod_file, logger)
    print('{:25}'.format('Module file location'), ":", mod_path)

    # Copy code and sched cfg & template files for building run scripts
    provenance_path = code_cfg['general']['build_prefix'] + \
        gs.sl + "build_files"
    create_install_dir(provenance_path, logger)

    install(provenance_path, code_cfg['metadata']['cfg_file'], logger)
    install(provenance_path, sched_cfg['metadata']['cfg_file'], logger)
    install(provenance_path, sched_template, logger)
    install(provenance_path, build_template, logger)
    install(provenance_path, module_template, logger)

    # Clean up tmp files
    exception.remove_tmp_files()

    # Submit build script to scheduler
    submit_job(code_cfg['general']['build_prefix'] +
               gs.sl + script_file[4:], logger)
