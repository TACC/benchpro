# System Imports
import os
import shutil as su
import sys

# Local Imports
import common as common_funcs
import exception

glob = common = None

# Check inputs for module creation
def check_for_existing_module(mod_path, mod_file):

    # Check if module already exists
    if os.path.isfile(os.path.join(mod_path, mod_file)):

        if glob.stg['overwrite']:
            exception.print_warning(glob.log, "deleting old module in " + common.rel_path(mod_path) + " because 'overwrite=True' in settings.ini")
            su.rmtree(mod_path)
            os.makedirs(mod_path)

        else:
            exception.error_and_quit(glob.log, "Module path already exists.")

# Copy template to target dir
def copy_mod_template(module_template):

    mod_obj = []

    # Add custom module path if set in cfg
    if glob.code['general']['module_use']:

        # Handle env vars in module path
        if glob.code['general']['module_use'].startswith(glob.stg['topdir_env_var']):

            topdir = glob.stg['topdir_env_var'].strip("$")

            mod_obj.append("local " + topdir + " = os.getenv(\"" + topdir + "\") or \"\"\n")
            mod_obj.append("prepend_path(\"MODULEPATH\", pathJoin(" + topdir + ", \"" + glob.code['general']['module_use'][len(topdir)+2:] + "\"))\n")

        else:
            mod_obj.append("prepend_path( \"MODULEPATH\" , \"" + glob.code['general']['module_use'] + "\") \n")

    with open(module_template, 'r') as inp:
        mod_obj.extend(inp.readlines())

    return mod_obj

# Replace <<<>>> vars in copied template
def populate_mod_template(mod_obj):
    # Get comma delimited list of non-Null build modules
    mod_list = []
    for key in glob.code['modules']:
        if glob.code['modules'][key]:
            mod_list.append(glob.code['modules'][key])

    mod = {}
    mod['mods'] = ', '.join('"{}"'.format(m) for m in mod_list)
    # Get capitalized code name for env var
    mod['caps_code'] = glob.code['general']['code'].upper().replace("-", "_")

    pop_dict = {**mod, **glob.code['metadata'], **glob.code['general'], **glob.code['config']}

    for key in pop_dict:
        glob.log.debug("replace " + "<<<" + key + ">>> with " + str(pop_dict[key]))
        mod_obj = [line.replace("<<<" + str(key) + ">>>", str(pop_dict[key])) for line in mod_obj]
        
    return mod_obj

# Write module to file
def write_mod_file(module, tmp_mod_file):
    with open(tmp_mod_file, "w") as f:
        for line in mod_obj:
            f.write(line)

# Make module for compiled appliation
def make_mod(glob_obj):

    # Get global settings & glob.log obj
    global glob, common 
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    glob.log.debug("Creating module file for " + glob.code['general']['code'])

    # Get module file path
    mod_path = os.path.join(glob.stg['module_path'], glob.code['general']['system'], glob.code['config']['arch'], common.get_module_label(glob.code['modules']['compiler']), \
                            common.get_module_label(glob.code['modules']['mpi']), glob.code['general']['code'], str(glob.code['general']['version']))

    mod_file = glob.code['config']['build_label'] + ".lua"

    check_for_existing_module(mod_path, mod_file)
    
    template_filename = glob.code['general']['code'] + "_" + str(glob.code['general']['version']) + ".module" 
    module_template = os.path.join(glob.stg['template_path'], glob.stg['build_tmpl_dir'], template_filename)

    # Use generic module template if not found for this application
    if not os.path.isfile(module_template):
        exception.print_warning(glob.log, "Module template '" + template_filename + "' not found, using a generic module template.")
        module_template = os.path.join(glob.stg['template_path'], glob.stg['build_tmpl_dir'], "generic.module")

    glob.log.debug("Using module template file: " + module_template)

    # Copy base module template to 
    mod_obj = copy_mod_template(module_template)

    # Populuate template with config params
    mod_obj = populate_mod_template(mod_obj)
    # Test module template
    tmp_mod_file = "tmp." + mod_file
    common.test_template(tmp_mod_file, mod_obj)
    # Write module template to file
    common.write_list_to_file(mod_obj, tmp_mod_file)

    return mod_path, tmp_mod_file