# System Imports
import configparser as cp
from datetime import datetime
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

# Local Imports
import src.utils as utils
import src.exception as exception
import src.module_handler as module_handler
import src.cfg_handler as cfg_handler
import src.template_handler as template_handler
import src.splash as splash

user                = str(os.getlogin())
hostname            = str(socket.gethostname())
if ("." in hostname):
    hostname = '.'.join(map(str, hostname.split('.')[0:2]))

time_str            = datetime.now().strftime("%Y-%m-%d_%Hh%M")

sl                  = "/"
base_dir            = sl.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1])

timeout             = 5

settings_cfg        = "settings.cfg"
settings_section    = "settings"
settings_parser     = cp.RawConfigParser()
settings_parser.read(base_dir + sl + settings_cfg)

template_dir        = "templates"

dry_run = settings_parser.getboolean(           settings_section,   "dry_run")
use_default_paths = settings_parser.getboolean( settings_section,   "use_default_paths")
overwrite = settings_parser.getboolean(         settings_section,   "overwrite")
exit_on_missing = settings_parser.getboolean(   settings_section,   "exit_on_missing")
log_level = settings_parser.getint(             settings_section,   "log_level")
exception_log_file = settings_parser.get(       settings_section,   "exception_log_file")
build_log_file = settings_parser.get(           settings_section,   "build_log_file")

error_installing = False

exception_log=''
build_log=''

def start_logging(name,
                  file,
                  level=log_level):

    print('{:25}'.format(name+' log file'), ":", str(file))

    formatter = lg.Formatter("{0}: ".format(name) + str(user) + "@" +str(hostname) + ": " +
                             "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    logger = lg.getLogger(name)
    logger.setLevel(level)

    file_handler = lg.FileHandler(file, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    #stream_handler = lg.StreamHandler(stream=sys.stderr)
    #stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    #logger.addHandler(stream_handler)

    return logger

# Check if an existing installation exists
def check_for_previous_install(path):
    if os.path.exists(path):
        if overwrite:
            utils.build_log.debug("WARNING: It seems this app is already installed. Deleting old build in "+path+" because 'overwrite=True' in settings.cfg")

            print()
            print("WARNING: Application directory already exists and 'overwrite=True' in settings.cfg, continuing in 5 seconds...")
            print()

            time.sleep(timeout)            
            print("No going back now...")

            su.rmtree(path)
        else:
            exception.error_and_quit(utils.exception_log, "It seems this app is already installed in "+path+". The install directory already exists and 'overwrite=False' in settings.cfg")

# Create directories if needed
def create_install_dir(path):
    # Try to create build directory
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            exception.error_and_quit(utils.exception_log, "Failed to make directory "+path)

# Move files to install directory
def install(path, obj):

    # Get file name
    new_obj_name = obj
    if '/' in obj: new_obj_name = obj.split("/")[-1]
    # Strip tmp prefix from file
    if 'tmp.' in obj: new_obj_name = obj[4:]

    try: 
        su.copyfile(obj, path+sl+new_obj_name)
    except IOError  as e:
        print(e)
        exception.error_and_quit(utils.exception_log, "Failed to move "+obj+" to "+path+sl+new_obj_name)

# Check if module is available on the system
def check_module_exists(module):
    try:
        cmd = subprocess.run("module spider "+module, shell=True, check=True, capture_output=True, universal_newlines=True)

    except subprocess.CalledProcessError as e:
       exception.error_and_quit(utils.exception_log, "module "+module+" not available on this system")

# Log cfg contents
def send_inputs_to_log(cfg):
    utils.build_log.debug("Builder started with the following inputs:")
    for seg in cfg:
        utils.build_log.debug("["+seg+"]")
        for line in cfg[seg]:
            utils.build_log.debug("  "+line+"="+cfg[seg][line])

# Check build params, add defaults if needed
def set_build_paths(build_dict, build_path):

    if not "project_path" in build_dict.keys():
        build_dict["project_path"] = build_path

    if not "build_path" in build_dict.keys():
        build_dict["build_path"] = build_path + sl + "build"

    if not "install_path" in build_dict.keys():
        build_dict["install_path"] = build_path + sl + "install"

    return build_dict

# Submit build script to scheduler
def submit_job(script_file):
    if dry_run:
        print("This was a dryrun, job script created at " + script_file)
        utils.build_log.debug("This was a dryrun, job script created at " + script_file)
    else:
        print("Submitting build script to scheduler")
        utils.build_log.debug("Submitting build script to scheduler...")
        try:
            cmd = subprocess.run("sbatch "+script_file, shell=True, check=True, capture_output=True, universal_newlines=True)

            utils.build_log.debug(cmd.stdout)
            utils.build_log.debug(cmd.stderr)

            job_id = ''
            i = 0
            jobid_line = "Submitted batch job"

            # Find job ID
            for line in cmd.stdout.splitlines():
                if jobid_line in line:
                    job_id = line.split(" ")[-1]

            time.sleep(2)
            cmd = subprocess.run("squeue -a --job "+job_id, shell=True, check=True, capture_output=True, universal_newlines=True)

            print(cmd.stdout)
            utils.build_log.debug(cmd.stdout)
            utils.build_log.debug(cmd.stderr)

        except subprocess.CalledProcessError as e:
            utils.exception_log.debug("Failed to submit job to scheduler")
            utils.exception_log.debug(e)

# Main methond for generating and submitting build script
def build_code(args):

    # Print splash
    splash.print_splash()

    # Init loggers
    utils.exception_log = utils.start_logging("EXCEPTION", file=exception_log_file+"_"+time_str+".log")
    utils.build_log = utils.start_logging("BUILD", file=build_log_file+"_"+time_str+".log")

    # Parse config input files
    code_cfg  =    cfg_handler.get_cfg('code',     args.install,           use_default_paths, utils.build_log, utils.exception_log)
    sched_cfg =    cfg_handler.get_cfg('sched',    args.sched,          use_default_paths, utils.build_log, utils.exception_log)
    compiler_cfg = cfg_handler.get_cfg('compiler', 'compile-flags.cfg', use_default_paths, utils.build_log, utils.exception_log) 

    print('{:25}'.format('Using application config'), ":", code_cfg['metadata']['cfg_file'])
    print('{:25}'.format('Using scheduler config'), ":", sched_cfg['metadata']['cfg_file'])

    # Print inputs to log
    send_inputs_to_log(code_cfg)
    send_inputs_to_log(sched_cfg)

    #split input config file)s
    general_opts    = code_cfg['general']
    mod_opts        = code_cfg['modules']
    build_opts      = code_cfg['build']
    run_opts        = code_cfg['run']

    sched_opts      = sched_cfg['scheduler']

    compiler_opts   = compiler_cfg['common']

    # Input Checks 
    for mod in mod_opts: 
        check_module_exists(mod_opts[mod])    

    # Check if version is string, if so make int alias using date
    
    compiler_type   = mod_opts['compiler'].split('/')[0]
    compiler_opts.update(compiler_cfg[compiler_type])

    # Check if build dir already exists
    check_for_previous_install(general_opts['build_prefix'])

    # Add build dirs to dict
    build_opts          = utils.set_build_paths(build_opts, general_opts['build_prefix'])

    # Name of tmp build script
    script_file         = "tmp." + general_opts['code'] + "-build." + sched_opts['type']

    # Template files
    sched_template      = base_dir + sl + template_dir + sl + "sched" + sl + sched_opts['type'] + ".template"
    build_template      = base_dir + sl + template_dir + sl + "codes" + sl + general_opts['code'] + "-" + general_opts['version'] + ".build"
    compiler_template   = base_dir + sl + template_dir + sl + "compile_flags.template" 
    module_template     = base_dir + sl + template_dir + sl + "codes" + sl + general_opts['code'] + "-" + general_opts['version'] + ".module"

    # Use generic module template if not found for this application
    if not os.path.exists(module_template):
        utils.build_log.debug("WARNING: "+general_opts['code']+" module template file not available at "+module_template)
        utils.build_log.debug("WARNING: using a generic module template")
        module_template = "/".join(module_template.split("/")[:-1])+sl+"generic.module"

    # Generate build script
    template_handler.construct_template(sched_template, compiler_template, build_template, script_file)
    script = open(script_file).read()

    script = template_handler.populate_template(general_opts, script, utils.build_log)
    script = template_handler.populate_template(mod_opts, script, utils.build_log)
    script = template_handler.populate_template(build_opts, script, utils.build_log)
    script = template_handler.populate_template(sched_opts, script, utils.build_log)
    script = template_handler.populate_template(compiler_opts, script, utils.build_log)

    template_handler.test_template(script, exit_on_missing, utils.build_log, utils.exception_log)

    # Write build script to temp location
    template_handler.write_template(script_file, script)
    
    # Generate module in temp location
    mod_path, mod_file = module_handler.make_mod(module_template, general_opts, build_opts, mod_opts, exit_on_missing, overwrite, utils.build_log, utils.exception_log)

    
    # Make build dir and move tmp file
    utils.create_install_dir(general_opts['build_prefix'])
    utils.install(general_opts['build_prefix'], script_file)
    print('{:25}'.format('Build script location'), ":", general_opts['build_prefix'])

    # Make module dir and move tmp file
    utils.create_install_dir(mod_path)
    utils.install(mod_path, mod_file)
    print('{:25}'.format('Module file location'), ":", mod_path)

    # Copy code and sched cfg & template files for building run scripts
    provenance_path = general_opts['build_prefix']+sl+"build_files"
    utils.create_install_dir(provenance_path)

    utils.install(provenance_path, code_cfg['metadata']['cfg_file'])
    utils.install(provenance_path, sched_cfg['metadata']['cfg_file'])
    utils.install(provenance_path, sched_template)
    utils.install(provenance_path, build_template)
    utils.install(provenance_path, module_template)

    # Clean up tmp files
    exception.remove_tmp_files()

    # Submit build script to scheduler
    utils.submit_job(general_opts['build_prefix']+sl+script_file[4:])

