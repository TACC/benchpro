
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

user                = str(os.getlogin())
hostname            = str(socket.gethostname())
base_dir            = str(os.getcwd())
sl                  = "/"

configs_dir         = "cfgs"

settings_cfg        = "settings.cfg"
settings_section    = "settings"
settings_parser     = cp.RawConfigParser()
settings_parser.read(settings_cfg)

dry_run = settings_parser.getboolean(           settings_section,   "dry_run")
exit_on_missing = settings_parser.getboolean(   settings_section,   "exit_on_missing")
exit_on_missing = settings_parser.getboolean(   settings_section,   "exit_on_missing")
log_level = settings_parser.getint(             settings_section,   "log_level")
exception_log_file = settings_parser.get(       settings_section,   "exception_log_file")
build_log_file = settings_parser.get(           settings_section,   "build_log_file")



def start_logging(name,
                  file,
                  level=log_level):

    formatter = lg.Formatter("{0} %(levelname)s : ".format(name) + str(hostname) + ": " + str(user) + ": " +
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

exception_log = utils.start_logging("EXCEPTION", file=exception_log_file)
build_log = utils.start_logging("BUILD", file=build_log_file)

def check_cmd_args(arg):

    if not ".cfg" in arg:
        arg += ".cfg"

    if not os.path.isfile(arg):
        arg = "." + sl + configs_dir + sl + arg
        if not os.path.isfile(arg):
            exception.input_missing(input, exception_log)

    return arg

# Read cfg file into dict
def read_cfg_file(cfg):

    utils.build_log.debug("parsing " + cfg + " file")

    cfg_parser = cp.RawConfigParser()
    cfg_parser.read(cfg)

    cfg_dict = {}
    for section in cfg_parser.sections():
        cfg_dict[section] = {}
        for value in cfg_parser.options(section):
            cfg_dict[section][value] = cfg_parser.get(section, value)

    utils.build_log.debug(cfg + " file parsed contents:")
    utils.build_log.debug(pp.pformat(cfg_dict))
    return cfg_dict

# Create directories if needed
def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Check build params, add defaults if needed
def set_default_paths(build_dict, build_path):

    if not "build_path" in build_dict.keys():
        build_dict["build_path"] = build_path + sl + "build"

    if not "install_prefix" in build_dict.keys():
        build_dict["install_prefix"] = build_path + sl + "install"

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
        print("replace " + "<<<" + key + ">>> with " + template_opts[key])
        script = script.replace("<<<" + key + ">>>", template_opts[key])
    return script

# Check for unpopulated vars in template file
def test_template(script):

    key = "<<<.*>>>"
    nomatch = re.findall(key,script)
    if len(nomatch) > 0:
        print("Missing build parameters were found in build template!")
        print(nomatch)
        if exit_on_warn:
            print ("Exit on warn is set in settings.cfg, exiting")
            sys.exit(1)
    else:
        print("All build parameters were filled, continuing")

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
            process = subprocess.run("sbatch "+script_file, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            utils.exception_log.debug("Failed to submit job to scheduler")
            utils.exception_log.debug(e)


# Main methond for generating and submitting build script
def build_code(code_cfg, sched_cfg):

    #split input config files
    general_opts    = code_cfg['general']
    sched_opts      = sched_cfg['scheduler']

    code    = general_opts['code']
    version = general_opts['version']
    sched   = sched_opts['type']

    # Get file paths for generating build script from templates
    sched_template      = base_dir + sl + "src" + sl + "job-scripts" + sl + sched + ".template"
    build_template      = base_dir + sl + "src" + sl + "code-templates" + sl + code + "-" + version + ".template"
    build_path          = base_dir + sl + "build" + sl + code + sl + version
    script_file         = build_path + sl + code + "-build." + sched

    build_opts              = utils.set_default_paths(code_cfg['build'], build_path)
    build_opts["code"]      = code
    build_opts["version"]   = version

    utils.make_dir(build_path)

    # Copy template files for population
    utils.construct_template(sched_template, build_template, script_file)

    script = open(script_file).read()

    # Contextualize build template with input.cfg vars
    script = utils.populate_template(build_opts, script)
    script = utils.populate_template(sched_opts, script)

    # Check for unpopulated vars in template file
    utils.test_template(script)

    # Write template to file
    utils.write_template(script_file, script)

    # Submit build script to scheduler
    utils.submit_job(script_file)
