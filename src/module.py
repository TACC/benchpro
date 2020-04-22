
# System Imports
import os
import re
import shutil as su
import sys

sl = "/"
top_dir = str(os.getcwd())

# Check inputs for module creation
def check_inputs(code_dict, build_log, exception_log):

    if (not code_dict['system']) or (not code_dict['compiler']) or (not code_dict['mpi']) or (not code_dict["code"]) or (not code_dict['version']):
        exception_log.debug("Missing full application definition:")
        exception_log.debug("----------------------------")
        exception_log.debug("System".ljust(10),   ":", code_dict['system'])
        exception_log.debug("Compiler".ljust(10), ":", code_dict['compiler'])
        exception_log.debug("MPI".ljust(10),      ":", code_dict['mpi'])
        exception_log.debug("Code".ljust(10),     ":", code_dict["code"])
        exception_log.debug("Version".ljust(10),  ":", code_dict['version'])
        exception_log.debug("----------------------------")
        exception_log.debug("Exitting")
        sys.exit(1)

    if not code_dict['arch']:
        build_log.debug("Warning: optional 'arch' property not defined. Continuing without archiecture definition.")


    if not ("/" in code_dict['compiler']):
        exception_log.debug("Please provide full compiler module name. Eg: 'intel/18.0.2'")
        exception_log.debug("Exitting")
        sys.exit(1)

    if not ("/" in code_dict['mpi']):
        exception_log.debug("Please provide full MPI module name. Eg: 'impi/18.0.2'")
        exception_log.debug("Exitting")
        sys.exit(1)

# Convert compiler/MPI string to directory label
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]
    return label

# Make module directory tree
def make_mod_dir(code_dict, build_log, exception_log):

    mod_dir = top_dir + sl + "build" + sl + "modulefiles" + sl + code_dict['system'] + sl + get_label(code_dict['compiler']) + sl + get_label(code_dict['mpi']) + sl + code_dict['code']

    if code_dict['arch']:
        mod_dir = mod_dir + sl + code_dict['arch']

    try:
        os.makedirs(mod_dir)
        build_log.debug("Created module directory "+mod_dir)

    except OSError as e:
        exception_log.debug("Failed to create directory "+mod_dir)
        exception_log.debug(e)
        exception_log.debug("Exitting")
        sys.exit(1)

    return mod_dir

# Copy template to target dir
def copy_mod_template(code, mod_file, build_log, exception_log):

    template_file = top_dir + sl + "src" + sl + "module-templates" + sl + code + ".template"

    if not os.path.exists(template_file):
        exception_log.debug(code+" template file not available at "+template_file)
        exception_log.debug("Exitting")

    with open(mod_file,'wb') as out:
        with open(template_file,'rb') as inp:
            su.copyfileobj(inp, out)

# Replace <<<>>> vars in copied template
def populate_mod_template(module, code_dict, build_log, exception_log):

    code_dict['mods'] = ', '.join('"{0}"'.format(w) for w in code_dict['mods'])
    code_dict['caps_code'] = code_dict['code'].upper()

    if not code_dict['bin_dir']:
        code_dict['bin_dir'] = 'bin'

    code_dict['install_dir'] = top_dir + sl + "build" + sl + code_dict['system'] + sl + get_label(code_dict['compiler']) + sl + get_label(code_dict['mpi']) + sl + code_dict['code'] + sl + code_dict['version'] + sl + "install"



    for key in code_dict:
        build_log.debug("replace " + "<<<" + key + ">>> with " + code_dict[key])
        module = module.replace("<<<" + key + ">>>", code_dict[key])
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
def make_mod(general_opts, build_opts, mod_opts, exit_on_missing, build_log, exception_log):

    code_dict = {'mods' : []}
    code_dict['compiler'] = mod_opts['compiler']
    code_dict['mpi']      = mod_opts['mpi']

    build_log.debug("Creating module file for "+general_opts['code'])

    for mod in mod_opts:
       code_dict['mods'] += [mod_opts[mod]]

    code_dict.update(general_opts)
    code_dict.update(build_opts)

    check_inputs(code_dict, build_log, exception_log)
    mod_file = make_mod_dir(code_dict, build_log, exception_log) + sl + code_dict['version'] + ".lua"
    copy_mod_template(code_dict['code'], mod_file, build_log, exception_log)

    module = open(mod_file).read()
    module = populate_mod_template(module, code_dict, build_log, exception_log)
    test_mod_file(module, exit_on_missing, build_log, exception_log)
    write_mod_file(module, mod_file)



