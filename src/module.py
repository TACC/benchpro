
# System Imports
import os
import re
import shutil as su
import sys

sl = "/"
top_dir = str(os.getcwd())

# Check inputs for module creation
def check_inputs(mod_dict, mod_path, build_log, exception_log):

    if (not mod_dict['system']) or (not mod_dict['compiler']) or (not mod_dict['mpi']) or (not mod_dict["code"]) or (not mod_dict['version']):
        exception_log.debug("Missing full application definition:")
        exception_log.debug("----------------------------")
        exception_log.debug("System".ljust(10),   ":", mod_dict['system'])
        exception_log.debug("Compiler".ljust(10), ":", mod_dict['compiler'])
        exception_log.debug("MPI".ljust(10),      ":", mod_dict['mpi'])
        exception_log.debug("Code".ljust(10),     ":", mod_dict["code"])
        exception_log.debug("Version".ljust(10),  ":", mod_dict['version'])
        exception_log.debug("----------------------------")
        exception_log.debug("Exitting")
        sys.exit(1)

    if not mod_dict['arch']:
        build_log.debug("Warning: optional 'arch' property not defined. Continuing without archiecture definition.")


    if not ("/" in mod_dict['compiler']):
        exception_log.debug("Please provide full compiler module name. Eg: 'intel/18.0.2'")
        exception_log.debug("Exitting")
        sys.exit(1)

    if not ("/" in mod_dict['mpi']):
        exception_log.debug("Please provide full MPI module name. Eg: 'impi/18.0.2'")
        exception_log.debug("Exitting")
        sys.exit(1)

    # Check if module already exists
    if os.path.isdir(mod_path):
        exception_log.debug("Module path already exists.")
        exception_log.debug("Exitting")
        sys.exit(1)

# Convert compiler/MPI string to directory label
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]
    return label

# Copy template to target dir
def copy_mod_template(template_file, code, mod_file, build_log, exception_log):

    if not os.path.exists(template_file):
        build_log.debug("WARNING: "+code+" module template file not available at "+template_file)
        build_log.debug("WARNING: using a generic module template")
        template_file = "/".join(template_file.split("/")[:-1])+sl+"generic.module"

    with open(mod_file,'wb') as out:
        with open(template_file,'rb') as inp:
            su.copyfileobj(inp, out)

# Replace <<<>>> vars in copied template
def populate_mod_template(module, mod_dict, build_log, exception_log):
    mod_dict['mods'] = ', '.join('"{0}"'.format(w) for w in mod_dict['mods'])
    mod_dict['caps_code'] = mod_dict['code'].upper()

    if not mod_dict['bin_dir']:
        mod_dict['bin_dir'] = 'bin'

    mod_dict['install_dir'] = top_dir + sl + "build" + sl + mod_dict['system'] + sl + get_label(mod_dict['compiler']) + sl + get_label(mod_dict['mpi']) + sl + mod_dict['code'] + sl + mod_dict['arch'] + sl + mod_dict['version'] + sl + "install"

    for key in mod_dict:
        build_log.debug("replace " + "<<<" + key + ">>> with " + mod_dict[key])
        module = module.replace("<<<" + key + ">>>", mod_dict[key])
    return module

def test_mod_file(module, exit_on_missing, build_log, exception_log):
    key = "<<<.*>>>"
    nomatch = re.findall(key,module)
    if len(nomatch) > 0:
        exception_log.debug("Missing module parameters were found in module file!")
        exception_log.debug(nomatch)
        if exit_on_missing:
            exception_log.debug("exit_on_missing=True in settings.cfg")
            exception_log.debug("Exiting")
            sys.exit(1)
    else:
        build_log.debug("All module parameters were filled, continuing")

def write_mod_file(module, mod_file):
    with open(mod_file, "w") as f:
        f.write(module)

# Make module for compiled appliation
def make_mod(template_file, general_opts, build_opts, mod_opts, exit_on_missing, build_log, exception_log):

    mod_dict = {'mods' : []}
    mod_dict['compiler'] = mod_opts['compiler']
    mod_dict['mpi']      = mod_opts['mpi']

    build_log.debug("Creating module file for "+general_opts['code'])

    for mod in mod_opts:
       mod_dict['mods'] += [mod_opts[mod]]

    mod_dict.update(general_opts)
    mod_dict.update(build_opts)

    mod_path = top_dir + sl + "build" + sl + "modulefiles" + sl + mod_dict['system'] + sl + get_label(mod_dict['compiler']) + sl + get_label(mod_dict['mpi']) + sl + mod_dict['code']
    if mod_dict['arch']:
        mod_path = mod_path + sl + mod_dict['arch']

    check_inputs(mod_dict, mod_path, build_log, exception_log)

    mod_file = mod_dict['version'] + ".lua"

    copy_mod_template(template_file, mod_dict['code'], mod_file, build_log, exception_log)

    module = open(mod_file).read()
    module = populate_mod_template(module, mod_dict, build_log, exception_log)
    test_mod_file(module, exit_on_missing, build_log, exception_log)
    write_mod_file(module, mod_file)

    return mod_path, mod_file

