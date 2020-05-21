
# System Imports
import os
import re
import shutil as su
import sys

import src.exception as exception

logger, gs = ''

# Check inputs for module creation


def check_inputs(mod_dict, mod_path):

    if (not mod_dict['system']) or (not mod_dict['compiler']) or (not mod_dict['mpi']) or (not mod_dict["code"]) or (not mod_dict['version']):
        logger.debug("Missing full application definition:")
        logger.debug("----------------------------")
        logger.debug("System".ljust(10),   ":", mod_dict['system'])
        logger.debug("Compiler".ljust(10), ":", mod_dict['compiler'])
        logger.debug("MPI".ljust(10),      ":", mod_dict['mpi'])
        logger.debug("Code".ljust(10),     ":", mod_dict["code"])
        logger.debug("Version".ljust(10),  ":", mod_dict['version'])
        logger.debug("----------------------------")
        logger.debug("Exitting")
        sys.exit(1)

    # Check if module already exists
    if os.path.isdir(mod_path):

        if gs.overwrite:
            logger.debug("WARNING: Deleting old module in " +
                         mod_path + " because 'overwrite=True' in settings.cfg")
            su.rmtree(mod_path)
            os.makedirs(mod_path)

        else:
            exception.error_and_quit(logger, "Module path already exists.")

# Convert compiler/MPI string to directory label


def get_label(compiler):
    label = compiler
    if compiler.count(gs.sl) > 0:
        comp_ver = compiler.split(gs.sl)
        label = comp_ver[0] + comp_ver[1].split(".")[0]
    return label

# Copy template to target dir


def copy_mod_template(template_file, mod_file):
    try:
        with open(mod_file, 'wb') as out:
            with open(template_file, 'rb') as inp:
                su.copyfileobj(inp, out)
    except:
        exception.error_and_quit(
            logger, "Failed to " + template_file + " to " + mod_file)

# Replace <<<>>> vars in copied template


def populate_mod_template(module, mod_dict):
    mod_dict['mods'] = ', '.join('"{0}"'.format(w) for w in mod_dict['mods'])
    mod_dict['caps_code'] = mod_dict['code'].upper()

    mod_dict['install_dir'] = gs.base_dir + gs.sl + "build" + gs.sl + mod_dict['system'] + gs.sl + get_label(mod_dict['compiler']) + gs.sl + get_label(
        mod_dict['mpi']) + gs.sl + mod_dict['code'] + gs.sl + mod_dict['opt_label'] + gs.sl + mod_dict['version'] + gs.sl + "install"

    for key in mod_dict:
        logger.debug("replace " + "<<<" + key + ">>> with " + mod_dict[key])
        module = module.replace("<<<" + key + ">>>", mod_dict[key])
    return module


def test_mod_file(module, logger):
    key = "<<<.*>>>"
    nomatch = re.findall(key, module)
    if len(nomatch) > 0:
        exception_log.debug(
            "Missing module parameters were found in module file!")
        exception_log.debug(nomatch)
        if gs.exit_on_missing:
            exception.error_and_quit(
                logger, "Missing module parameters were found in module file and exit_on_missing=True in settings.cfg")

    else:
        logger.debug("All module parameters were filled, continuing")


def write_mod_file(module, mod_file):
    with open(mod_file, "w") as f:
        f.write(module)

# Make module for compiled appliation


def make_mod(template_file, general_opts, build_opts, mod_opts, settings, log_to_use):

    global logger, gs
	logger = log_to_use
    gs = settings

    mod_dict = {'mods': []}
    mod_dict['compiler'] = mod_opts['compiler']
    mod_dict['mpi'] = mod_opts['mpi']

    logger.debug("Creating module file for " + general_opts['code'])

    for mod in mod_opts:
        mod_dict['mods'] += [mod_opts[mod]]

    mod_dict.update(general_opts)
    mod_dict.update(build_opts)

    mod_path = gs.base_dir + gs.sl + "build" + gs.sl + "modulefiles" + gs.sl + mod_dict['system'] + gs.sl + get_label(
        mod_dict['compiler']) + gs.sl + get_label(mod_dict['mpi']) + gs.sl + mod_dict['code'] + gs.sl + mod_dict['opt_label']

    check_inputs(mod_dict, mod_path, logger)

    mod_file = "tmp." + mod_dict['version'] + ".lua"

    copy_mod_template(template_file, mod_file, logger)

    module = open(mod_file).read()
    module = populate_mod_template(module, mod_dict, logger)
    test_mod_file(module, logger)
    write_mod_file(module, mod_file)

    return mod_path, mod_file
