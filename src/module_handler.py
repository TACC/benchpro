# System Imports
import os
import shutil as su
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception

glob = common = None

# Check inputs for module creation
def check_for_existing_module(mod_path, mod_file):

    # Check if module already exists
    if os.path.isfile(mod_path + glob.stg['sl'] + mod_file):

        if glob.stg['overwrite']:
            exception.print_warning(glob.log, "deleting old module in " + common.rel_path(mod_path) + " because 'overwrite=True' in settings.cfg")
            su.rmtree(mod_path)
            os.makedirs(mod_path)

        else:
            exception.error_and_quit(glob.log, "Module path already exists.")

# Copy template to target dir
def copy_mod_template(module_template, tmp_mod_file):
    #try:
    with open(tmp_mod_file, 'w') as out:
        with open(module_template, 'r') as inp:
                # Add custom module path if set in cfg
            if glob.code['general']['module_use']:
                out.write("prepend_path( \"MODULEPATH\" , \"" + glob.code['general']['module_use'] + "\") \n")

            su.copyfileobj(inp, out)
    #except:
    #    exception.error_and_quit(glob.log, "Failed to copy " + module_template + " to " + mod_file)

# Replace <<<>>> vars in copied template
def populate_mod_template(module):
    # Get comma delimited list of build modules
    mod = {}
    mod['mods'] = ', '.join('"{}"'.format(key) for key in glob.code['modules'].values())
    # Get capitalized code name for env var
    mod['caps_code'] = glob.code['general']['code'].upper().replace("-", "_")

    pop_dict = {**mod, **glob.code['general'], **glob.code['build']}

    for key in pop_dict:
        glob.log.debug("replace " + "<<<" + key + ">>> with " + pop_dict[key])
        module = module.replace("<<<" + key + ">>>", pop_dict[key])
    return module

# Write module to file
def write_mod_file(module, tmp_mod_file):
    with open(tmp_mod_file, "w") as f:
        f.write(module)

# Make module for compiled appliation
def make_mod(glob_obj):

    # Get global settings & glob.log obj
    global glob, common 
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    glob.log.debug("Creating module file for " + glob.code['general']['code'])

    # Get module file path
    mod_path = glob.stg['module_path'] + glob.stg['sl'] + glob.code['general']['system'] +  glob.stg['sl'] + glob.code['build']['arch'] + glob.stg['sl'] + common.get_module_label(glob.code['modules']['compiler']) + \
               glob.stg['sl'] + common.get_module_label(glob.code['modules']['mpi']) + glob.stg['sl'] + glob.code['general']['code'] + glob.stg['sl'] + glob.code['general']['version']

    mod_file = glob.code['build']['build_label'] + ".lua"

    check_for_existing_module(mod_path, mod_file)

    # tmp module file name
    tmp_mod_file = "tmp." + mod_file

    module_template = glob.stg['template_path'] + glob.stg['sl'] + glob.stg['build_tmpl_dir'] + glob.stg['sl'] + glob.code['general']['code'] + "-" + glob.code['general']['version'] + ".module"

    # Use generic module template if not found for this application
    if not os.path.isfile(module_template):
        exception.print_warning(glob.log, "module template not found at " + common.rel_path(module_template))
        exception.print_warning(glob.log, "using a generic module template")
        module_template = glob.stg['template_path'] + glob.stg['sl'] + glob.stg['build_tmpl_dir'] + glob.stg['sl'] + "generic.module"

    glob.log.debug("Using module template file: " + module_template)

    # Copy base module template
    copy_mod_template(module_template, tmp_mod_file)
    module = open(tmp_mod_file).read()

    # Populuate template with config params
    module = populate_mod_template(module)
    # Test module template
    common.test_template(module_template, module)
    # Write module template to file
    write_mod_file(module, tmp_mod_file)

    return mod_path, tmp_mod_file
