
# System Imports
import configparser as cp
import logging as lg
import os
import pprint as pp
import re
import shutil as su
import socket
import subprocess
import sys

# Local Imports
import src.exception as exception
import src.utils as utils
import src.module as module
import src.cfg_handler as cfg_handler

user                = str(os.getlogin())
hostname            = str(socket.gethostname())
if ("." in hostname):
    hostname = '.'.join(map(str, hostname.split('.')[0:2]))

base_dir            = str(os.getcwd())
sl                  = "/"

configs_dir         = "cfgs"

settings_cfg        = "settings.cfg"
settings_section    = "settings"
settings_parser     = cp.RawConfigParser()
settings_parser.read(settings_cfg)

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

    formatter = lg.Formatter("{0} %(levelname)s: ".format(name) + str(hostname) + ": " + str(user) + ": " +
                             "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    logger = lg.getLogger(name)
    logger.setLevel(level)

    file_handler = lg.FileHandler(file, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    stream_handler = lg.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def get_subdirs(base):
    return [name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))]

def recurse_down(app_dir):

    for d in get_subdirs(app_dir):
        if d != 'modulefiles':
            new_dir = app_dir + sl + d
            if d[0].isdigit():
                print("    "+sl.join(new_dir.split(sl, 2)[2:]))
            else:
                recurse_down(new_dir)


def show_installed():
    print("Currently installed applications:")
    print("---------------------------------")
    app_dir = "."+sl+"build" 
    recurse_down(app_dir)

# Create directories if needed
def make_dir(path):

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

# Copy template files for population
def construct_template(sched_template, build_template, job_script):
    with open(job_script,'wb') as out:
        for f in [sched_template, build_template]:
            with open(f,'rb') as fd:
                su.copyfileobj(fd, out)

# Contextualize build template with input.cfg vars
def populate_template(template_opts, script):

    for key in template_opts:
        utils.build_log.debug("replace " + "<<<" + key + ">>> with " + template_opts[key])
        script = script.replace("<<<" + key + ">>>", template_opts[key])
    return script

# Check for unpopulated vars in template file
def test_template(script):

    key = "<<<.*>>>"
    nomatch = re.findall(key,script)
    if len(nomatch) > 0:
        utils.build_log.debug("Missing build parameters were found in build template!")
        utils.build_log.debug(nomatch)
        if exit_on_missing:
            utils.build_log.debug("exit_on_missing=Truet in settings.cfg, exiting")
            sys.exit(1)
    else:
        utils.build_log.debug("All build parameters were filled, continuing")

# Write template to file
def write_template(script_file, script):
    with open(script_file, "w") as f:
        f.write(script)

# Submit build script to scheduler
def submit_job(script_file):
    if dry_run:
        utils.build_log.debug("This was a dryrun, job script created at " + script_file)
    else:
        utils.build_log.debug("Submitting build script to Slurm...")
        try:
            cmd = subprocess.run("sbatch "+script_file, shell=True, check=True, capture_output=True, universal_newlines=True)

            utils.build_log.debug(cmd.stdout)
            utils.build_log.debug(cmd.stderr)

            job_id = ""
            i = 0
            jobid_line = "Submitted batch job"

            # Find job ID
            for line in cmd.stdout.splitlines():
                if jobid_line in line:
                    job_id = line.split(" ")[-1]

            cmd = subprocess.run("squeue -a --job "+job_id, shell=True, check=True, capture_output=True, universal_newlines=True)
            utils.build_log.debug(cmd.stdout)
            utils.build_log.debug(cmd.stderr)

        except subprocess.CalledProcessError as e:
            utils.exception_log.debug("Failed to submit job to scheduler")
            utils.exception_log.debug(e)


# Main methond for generating and submitting build script
def build_code(args):

    # Init loggers
    utils.exception_log = utils.start_logging("EXCEPTION", file=exception_log_file)
    utils.build_log = utils.start_logging("BUILD", file=build_log_file)

    # Process code and scheduler cfg files
    code_cfg =  cfg_handler.check_code_cfg (cfg_handler.read_cfg_file(args.code,  utils.exception_log), use_default_paths, utils.exception_log)
    sched_cfg = cfg_handler.check_sched_cfg(cfg_handler.read_cfg_file(args.sched, utils.exception_log), use_default_paths, utils.exception_log)

    utils.build_log.debug("Builder started with the following inputs:")
    for seg in code_cfg:
        utils.build_log.debug("["+seg+"]")
        for line in code_cfg[seg]:
            utils.build_log.debug("  "+line+"="+code_cfg[seg][line])

    #split input config files
    general_opts    = code_cfg['general']
    mod_opts        = code_cfg['modules']
    build_opts      = code_cfg['build']
    run_opts        = code_cfg['run']

    sched_opts      = sched_cfg['scheduler']

    # alias vars
    system          = general_opts['system']
    code            = general_opts['code']
    version         = general_opts['version']
    arch            = build_opts['arch']

    compiler        = get_label(mod_opts['compiler'])
    mpi             = get_label(mod_opts['mpi'])


    sched           = sched_opts['type']

    # Get file paths for generating build script from templates
    sched_template      = base_dir + sl + "src" + sl + "job-templates" + sl + sched + ".template"
    build_template      = base_dir + sl + "src" + sl + "build-templates" + sl + code + "-" + version + ".template"

    build_path          = ''
    if general_opts['build_prefix']:
        build_path = general_opts['build_prefix']
    else:
        build_path = base_dir + sl + "build" + sl + system + sl + compiler + sl + mpi + sl  + code
        if arch:
            build_path += sl + arch + sl + version
        else:
            build_path += sl + version
        general_opts['build_prefix'] = build_path

    script_file         = build_path + sl + code + "-build." + sched

    build_opts              = utils.set_default_paths(build_opts, build_path)

    utils.make_dir(build_path)

    # Copy template files for population
    utils.construct_template(sched_template, build_template, script_file)

    script = open(script_file).read()

    # Contextualize build template with input.cfg vars
    script = utils.populate_template(general_opts, script)
    script = utils.populate_template(mod_opts, script)
    script = utils.populate_template(build_opts, script)
    script = utils.populate_template(sched_opts, script)

    # Check for unpopulated vars in template file
    utils.test_template(script)

    # Write template to file
    utils.write_template(script_file, script)

    module.make_mod(general_opts, build_opts, mod_opts, exit_on_missing, utils.build_log, utils.exception_log)

    # Submit build script to scheduler
    utils.submit_job(script_file)
