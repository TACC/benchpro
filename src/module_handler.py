
# System Imports
import os
import re
import shutil as su
import sys

import src.exception as exception

sl = "/"
top_dir = sl.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1])

# Check inputs for module creation
def check_inputs(mod_dict, mod_path, overwrite, build_logger, exception_logger):

    if (not mod_dict['system']) or (not mod_dict['compiler']) or (not mod_dict['mpi']) or (not mod_dict["code"]) or (not mod_dict['version']):
        exception_logger.debug("Missing full application definition:")
        exception_logger.debug("----------------------------")
        exception_logger.debug("System".ljust(10),   ":", mod_dict['system'])
        exception_logger.debug("Compiler".ljust(10), ":", mod_dict['compiler'])
        exception_logger.debug("MPI".ljust(10),      ":", mod_dict['mpi'])
        exception_logger.debug("Code".ljust(10),     ":", mod_dict["code"])
        exception_logger.debug("Version".ljust(10),  ":", mod_dict['version'])
        exception_logger.debug("----------------------------")
        exception_logger.debug("Exitting")
        sys.exit(1)

    if not ("/" in mod_dict['compiler']):
        exception.error_and_quit(exception_logger, "Please provide full compiler module name. Eg: 'intel/18.0.2'")

    if not ("/" in mod_dict['mpi']):
        exception.error_and_quit(exception_logger, "Please provide full MPI module name. Eg: 'impi/18.0.2'")

    # Check if module already exists
    if os.path.isdir(mod_path):

        if overwrite:
            build_logger.debug("WARNING: Deleting old module in "+mod_path+" because 'overwrite=True' in settings.cfg")
            su.rmtree(mod_path)
            os.makedirs(mod_path)

        else:
            exception.error_and_quit(exception_logger, "Module path already exists.")

# Convert compiler/MPI string to directory label
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]
    return label

# Copy template to target dir
def copy_mod_template(template_file, mod_file, exception_logger):
    try:
        with open(mod_file,'wb') as out:
            with open(template_file,'rb') as inp:
                su.copyfileobj(inp, out)
    except:
        exception.error_and_quit(exception_logger, "Failed to "+template_file + " to " + mod_file)

# Replace <<<>>> vars in copied template
def populate_mod_template(module, mod_dict, build_logger, exception_logger):
    mod_dict['mods'] = ', '.join('"{0}"'.format(w) for w in mod_dict['mods'])
    mod_dict['caps_code'] = mod_dict['code'].upper()

    mod_dict['install_dir'] = top_dir + sl + "build" + sl + mod_dict['system'] + sl + get_label(mod_dict['compiler']) + sl + get_label(mod_dict['mpi']) + sl + mod_dict['code'] + sl + mod_dict['opt_label'] + sl + mod_dict['version'] + sl + "install"

    if mod_dict['bin_dir']: mod_dict += sl + mod_dict['bin_dir']

    for key in mod_dict:
        build_logger.debug("replace " + "<<<" + key + ">>> with " + mod_dict[key])
        module = module.replace("<<<" + key + ">>>", mod_dict[key])
    return module

def test_mod_file(module, exit_on_missing, build_logger, exception_logger):
    key = "<<<.*>>>"
    nomatch = re.findall(key,module)
    if len(nomatch) > 0:
        exception_log.debug("Missing module parameters were found in module file!")
        exception_log.debug(nomatch)
        if exit_on_missing:
            exception.error_and_quit(exception_logger, "Missing module parameters were found in module file and exit_on_missing=True in settings.cfg")

    else:
        build_logger.debug("All module parameters were filled, continuing")

def write_mod_file(module, mod_file):
    with open(mod_file, "w") as f:
        f.write(module)

# Make module for compiled appliation
def make_mod(template_file, general_opts, build_opts, mod_opts, exit_on_missing, overwrite, build_logger, exception_logger):

    mod_dict = {'mods' : []}
    mod_dict['compiler'] = mod_opts['compiler']
    mod_dict['mpi']      = mod_opts['mpi']

    build_logger.debug("Creating module file for "+general_opts['code'])

    for mod in mod_opts:
       mod_dict['mods'] += [mod_opts[mod]]

    mod_dict.update(general_opts)
    mod_dict.update(build_opts)

    mod_path = top_dir + sl + "build" + sl + "modulefiles" + sl + mod_dict['system'] + sl + get_label(mod_dict['compiler']) + sl + get_label(mod_dict['mpi']) + sl + mod_dict['code'] + sl + mod_dict['opt_label']

    check_inputs(mod_dict, mod_path, overwrite, build_logger, exception_logger)

    mod_file = "tmp." + mod_dict['version'] + ".lua"

    copy_mod_template(template_file, mod_file, exception_logger)

    module = open(mod_file).read()
    module = populate_mod_template(module, mod_dict, build_logger, exception_logger)
    test_mod_file(module, exit_on_missing, build_logger, exception_logger)
    write_mod_file(module, mod_file)

    return mod_path, mod_file

