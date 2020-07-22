# System Imports
import os
import shutil as su
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception

glob = common = None

# Combines list of input templates to single script file
def construct_template(template_obj, input_template):

    # Check template file is defined - handles None type (in case of unknown compiler type = None compiler template)
    if input_template:
        glob.log.debug("Ingesting template file " + input_template)
        # Test if input template file exists
        if not os.path.exists(input_template):
            exception.error_and_quit(glob.log, "failed to locate template file '" + input_template + "' in " + common.rel_path(glob.stg['template_path'])  + ".")

        # Copy input template file to temp obj
        with open(input_template, 'r') as fd:
            template_obj.extend(fd.readlines())

# Add sched reservation
def add_reservation(template_obj):

    if glob.sched['sched']['reservation']:
            template_obj.append("#SBATCH --reservation=" + glob.sched['sched']['reservation'] + "\n")

# Add modules from build.cfg
def fill_modules(template_obj):

    template_obj.append("\n")
    template_obj.append("ml reset \n")
        
    # add 'module use' if set
    if glob.code['general']['module_use']:
        template_obj.append("ml use " + glob.code['general']['module_use'] + "\n")

    for mod in glob.code['modules']:
        template_obj.append("ml " + glob.code['modules'][mod] + "\n")
    template_obj.append("ml \n")

# Add things to the bottom of the build script
def template_epilog(template_obj):

    # Add sanity check
    if glob.code['build']['exe']:
        template_obj.append("ldd $(which " + glob.code['build']['exe'] + ") \n")

    # Add hardware collection script to job script
    if glob.code['build']['collect_hw_stats']:
        if common.file_owner(glob.stg['utils_path'] + glob.stg['sl'] + "lshw") == "root":
            template_obj.append(glob.stg['src_path'] + glob.stg['sl'] + "collect_hw_info.sh " + glob.stg['utils_path'] + " " + \
                            glob.code['general']['working_path'] + glob.stg['sl'] + "hw_report" + "\n")
        else:
            exception.print_warning(glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")

# Contextualizes template script with variables from a list of config dicts
def populate_template(template_obj):
    glob.log.debug("Populating template file " + glob.build_script)
    # For each config dict
    for cfg in [glob.code['general'], glob.code['modules'], glob.code['build'], glob.sched['sched'], glob.compiler['common']]:
        # For each key, find and replace <<<key>>> in template file
        for key in cfg:
            template_obj = [line.replace("<<<" + str(key) + ">>>", str(cfg[key])) for line in template_obj]
            glob.log.debug("replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))

def get_build_templates():

    # Temp build script
    glob.build_script = "tmp." + glob.code['general']['code'] + "-build." + glob.sched['sched']['type']

    # === Scheduler template file ===

    glob.sched['template'] = common.find_exact(glob.sched['sched']['type'] + ".template", glob.stg['template_path'])

    # === Application template file ===

    # Get application template file name from cfg, otherwise use cfg_label to look for it
    if glob.code['general']['template']:
        glob.code['template'] = glob.code['general']['template']
    else:
        glob.code['template'] = glob.code['metadata']['cfg_label'] + ".build"

    # Search for application template file
    build_template_search = common.find_partial(glob.code['template'], glob.stg['template_path'] + glob.stg['sl'] + glob.stg['build_tmpl_dir'])

    # Error if not found
    if not build_template_search:
        exception.error_and_quit(glob.log, "failed to locate build template '" + build_template + "' in " + \
                                common.rel_path(glob.stg['template_path'] + glob.stg['sl'] + glob.stg['build_tmpl_dir']))
    
    glob.code['template'] = build_template_search


    # === Compiler template file ===

    # Get compiler cmds for gcc/intel/pgi, otherwise compiler type is unknown
    known_compiler_type = True
    try:
        glob.compiler['common'].update(glob.compiler[glob.code['build']['compiler_type']])
        glob.compiler['template'] = common.find_exact(glob.stg['compile_tmpl_file'], glob.stg['template_path'])
    except:
        glob.compiler['template'] = None

# Combine template files and populate
def generate_build_template(glob_obj):

    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    template_obj = []

    # Get ranks from threads (?)
    glob.sched['sched']['ranks'] = 1
    # Get job label
    glob.sched['sched']['job_label'] = glob.code['general']['code'] + "_build"

    # Parse template file names
    get_build_templates()

    # Take multiple input template files and combine them to generate unpopulated script
    construct_template(template_obj, glob.sched['template'])
    # Add reservation line to SLURM params if set
    add_reservation(template_obj)

    # Fill modules from cfg
    fill_modules(template_obj)

    construct_template(template_obj, glob.compiler['template'])
    construct_template(template_obj, glob.code['template'])

    template_epilog(template_obj)

    # Take multiple config dicts and populate script template
    populate_template(template_obj)
    # Test for missing parameters
    common.test_template(template_obj)

    # Write populated script to file
    with open(glob.build_script, "w") as f:
        for line in template_obj:
            f.write(line + "\n")

def generate_bench_template(input_cfgs, input_templates, script_file, glob_obj):

    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    # Take multiple input template files and combine them to generate unpopulated script
    construct_template(input_templates[0], script_file)
    # Add reservation line to SLURM params if set
    add_reservation(script_file)

    construct_template(input_templates[1], script_file)

    # Take multiple config dicts and populate script template
    script = populate_template(input_cfgs, script_file)
    # Test for missing parameters
    common.test_template(script_file, script)

    # Write populated script to file
    with open(script_file, "w") as f:
        f.write(script)



