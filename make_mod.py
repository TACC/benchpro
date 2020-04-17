#!/usr/bin/env python3

import os
import re
import shutil as su
import sys

sl = "/"
top_dir = str(os.getcwd())

# Check inputs for module creation
def check_inputs(code_dict):

    if (not code_dict['system']) or (not code_dict['compiler']) or (not code_dict['mpi']) or (not code_dict["code"]) or (not code_dict['version']):
        print("Missing full application definition:")
        print("----------------------------")
        print("System".ljust(10),   ":", code_dict['system'])
        print("Compiler".ljust(10), ":", code_dict['compiler'])
        print("MPI".ljust(10),      ":", code_dict['mpi'])
        print("Code".ljust(10),     ":", code_dict["code"])
        print("Version".ljust(10),  ":", code_dict['version'])
        print("----------------------------")
        print("Quitting module creation")
        sys.exit(1)

    if not code_dict['arch']:
        print("Warning: optional 'arch' property not defined. Continuing without archiecture definition.")


    if not ("/" in code_dict['compiler']):
        print("Please provide full compiler module name. Eg: 'intel/18.0.2'")
        print("Quitting module creation")
        sys.exit(1)

    if not ("/" in code_dict['mpi']):
        print("Please provide full MPI module name. Eg: 'impi/18.0.2'")
        print("Quitting module creation")
        sys.exit(1)

# Convert compiler/MPI string to directory label
def get_label(compiler):
    comp_ver = compiler.split("/")
    label = comp_ver[0]+comp_ver[1].split(".")[0]

    return label

# Make module directory tree
def make_mod_dir(code_dict):

    mod_dir = top_dir + sl + "build" + sl + "modulefiles" + sl + code_dict['system'] + sl + get_label(code_dict['compiler']) + sl + get_label(code_dict['mpi']) + sl + code_dict['code']

    if code_dict['arch']:
        mod_dir = mod_dir + sl + code_dict['arch']

    try:
        os.makedirs(mod_dir)
        print("Created module directory "+mod_dir)

    except OSError as e:
        print("Failed to create directory "+mod_dir)
        print(e)
        print("Quitting module creation")
        sys.exit(1)

    return mod_dir

# Copy template to target dir
def copy_mode_template(code, mod_file):

    template_file = top_dir + sl + "src" + sl + "module-templates" + sl + code + ".template"

    if not os.path.exists(template_file):
        print(code+" template file not available at "+template_file)
        print("Quitting module creation")

    with open(mod_file,'wb') as out:
        with open(template_file,'rb') as inp:
            su.copyfileobj(inp, out)

# Replace <<<>>> vars in copied template
def populate_mod_template(module, code_dict):

    code_dict['mods'] = ', '.join('"{0}"'.format(w) for w in code_dict['mods'])
    code_dict['caps_code'] = code_dict['code'].upper()
    code_dict['bin_dir'] = 'bin'
    code_dict['install_dir'] = top_dir + sl + "build" + sl + code_dict['system'] + sl + get_label(code_dict['compiler']) + sl + get_label(code_dict['mpi']) + sl + code_dict['code'] + sl + code_dict['version'] + sl + "install"

    for key in code_dict:
        print("replace " + "<<<" + key + ">>> with " + code_dict[key])
        module = module.replace("<<<" + key + ">>>", code_dict[key])
    return module

def test_mod_file(module):
    key = "<<<.*>>>"
    nomatch = re.findall(key,module)
    if len(nomatch) > 0:
        print("Missing module parameters were found in module file!")
        print(nomatch)
        #if exit_on_missing:
        #    utils.build_log.debug("exit_on_missing=Truet in settings.cfg, exiting")
        #    sys.exit(1)
    else:
        print("All module parameters were filled, continuing")

def write_mod_file(module, mod_file):
    with open(mod_file, "w") as f:
        f.write(module)

# Make module for compiled appliation
def make_mod():
    code_dict = {'system':   'stampede',
                 'compiler': 'intel/18.0.2',
                 'mpi':      'impi/18.0.2',
                 'code':     'wrf',
                 'version':  '4.1.5',
                 'arch':     '',
                 'mods':     ["intel/18.0.2", "impi/18.0.2"]
                }

    check_inputs(code_dict)
    mod_file = make_mod_dir(code_dict) + sl + code_dict['version'] + ".lua"
    copy_mode_template(code_dict['code'], mod_file)

    module = open(mod_file).read()
    module = populate_mod_template(module, code_dict)
    test_mod_file(module)
    write_mod_file(module, mod_file)


make_mod()
