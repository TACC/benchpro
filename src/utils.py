# System Imports
import configparser as cp
from datetime import datetime
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
import src.input_tester as input_tester
import src.module as module
import src.cfg_handler as cfg_handler
import src.template_handler as template_handler
import src.splash as splash

user                = str(os.getlogin())
hostname            = str(socket.gethostname())
if ("." in hostname):
    hostname = '.'.join(map(str, hostname.split('.')[0:2]))

time_str            = datetime.now().strftime("%Y-%m-%d_%Hh%M")

base_dir            = str(os.getcwd())
sl                  = "/"

settings_cfg        = "settings.cfg"
settings_section    = "settings"
settings_parser     = cp.RawConfigParser()
settings_parser.read(settings_cfg)

template_dir        = "templates"

dry_run = settings_parser.getboolean(           settings_section,   "dry_run")
use_default_paths = settings_parser.getboolean( settings_section,   "use_default_paths")
overwrite = settings_parser.getboolean(         settings_section,   "overwrite")
exit_on_missing = settings_parser.getboolean(   settings_section,   "exit_on_missing")
log_level = settings_parser.getint(             settings_section,   "log_level")
exception_log_file = settings_parser.get(       settings_section,   "exception_log_file")
build_log_file = settings_parser.get(           settings_section,   "build_log_file")

exception_log=''
build_log=''

def start_logging(name,
                  file,
                  level=log_level):

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

# Create directories if needed
def install(path, script):

    if not os.path.exists(path):
        os.makedirs(path)

    elif overwrite:
        utils.build_log.debug("Deleting old build project in "+path+" because 'overwrite=True' in settings.cfg")
        su.rmtree(path)
        os.makedirs(path)

    else:
       utils.exception_log.debug("Project directory "+path+" already exists and 'overwrite=False' in settings.cfg.") 
       utils.exception_log.debug("Exitting")
       sys.exit(1)

    os.rename(script, path+sl+script)

# Log cfg contents
def send_inputs_to_log(cfg):
    utils.build_log.debug("Builder started with the following inputs:")
    for seg in cfg:
        utils.build_log.debug("["+seg+"]")
        for line in cfg[seg]:
            utils.build_log.debug("  "+line+"="+cfg[seg][line])

# Convert module name to directory name
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]
    return label

# Check build params, add defaults if needed
def set_default_paths(build_dict, build_path):

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
    # Init loggers
    utils.exception_log = utils.start_logging("EXCEPTION", file=exception_log_file+"_"+time_str)
    utils.build_log = utils.start_logging("BUILD", file=build_log_file+"_"+time_str)

    # Print splash
    splash.print_splash()

    # Parse config input files
    code_cfg  =    cfg_handler.get_cfg('code',     args.code,           use_default_paths, utils.build_log, utils.exception_log)
    sched_cfg =    cfg_handler.get_cfg('sched',    args.sched,          use_default_paths, utils.build_log, utils.exception_log)
    compiler_cfg = cfg_handler.get_cfg('compiler', 'compile-flags.cfg', use_default_paths, utils.build_log, utils.exception_log) 

    # Print inputs to log
    send_inputs_to_log(code_cfg)
    send_inputs_to_log(sched_cfg)

    #split input config files
    general_opts    = code_cfg['general']
    mod_opts        = code_cfg['modules']
    build_opts      = code_cfg['build']
    run_opts        = code_cfg['run']

    sched_opts      = sched_cfg['scheduler']

    compiler_opts   = compiler_cfg['common']

    # Input Checks 
    for mod in mod_opts: 
        input_tester.check_module_exists(mod_opts[mod], utils.exception_log)    

    # Check if version is string, if so make int alias using date
    
    compiler_type   = mod_opts['compiler'].split('/')[0]
    compiler_opts.update(compiler_cfg[compiler_type])

    build_path          = ''
    if general_opts['build_prefix']:
        build_path = general_opts['build_prefix']
    else:
        build_path = base_dir + sl + "build" + sl + general_opts['system'] + sl + get_label(mod_opts['compiler']) + sl + get_label(mod_opts['mpi']) + sl  + general_opts['code']
        if build_opts['arch']:
            build_path += sl + build_opts['arch'] + sl + general_opts['version']
        else:
            build_path += sl + general_opts['version']
        general_opts['build_prefix'] = build_path

    script_file         = general_opts['code'] + "-build." + sched_opts['type']

    build_opts          = utils.set_default_paths(build_opts, build_path)

    sched_template      = base_dir + sl + template_dir + sl + "sched" + sl + sched_opts['type'] + ".template"
    build_template      = base_dir + sl + template_dir + sl + "codes" + sl + general_opts['code'] + "-" + general_opts['version'] + ".build"
    compiler_template   = base_dir + sl + template_dir + sl + "compile_flags.template" 
    module_template     = base_dir + sl + template_dir + sl + "codes" + sl + general_opts['code'] + "-" + general_opts['version'] + ".module"

    # Generate build script
    template_handler.construct_template(sched_template, compiler_template, build_template, script_file)
    script = open(script_file).read()

    script = template_handler.populate_template(general_opts, script, utils.build_log)
    script = template_handler.populate_template(mod_opts, script, utils.build_log)
    script = template_handler.populate_template(build_opts, script, utils.build_log)
    script = template_handler.populate_template(sched_opts, script, utils.build_log)
    script = template_handler.populate_template(compiler_opts, script, utils.build_log)

    template_handler.test_template(script, exit_on_missing, utils.build_log, utils.exception_log)


    template_handler.write_template(script_file, script)
    
    mod_path, mod_file = module.make_mod(module_template, general_opts, build_opts, mod_opts, exit_on_missing, utils.build_log, utils.exception_log)

    # Make project and module directories, move build and module files
    utils.install(build_path, script_file)
    print("Build script location:", build_path)
    utils.install(mod_path, mod_file)
    print("Module file location :,", mod_path)

    # Submit build script to scheduler
    utils.submit_job(script_file)

