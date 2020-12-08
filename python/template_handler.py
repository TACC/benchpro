# System Imports
import glob as gb
import os
import shutil as su
import sys

# Local Imports
import common as common_funcs
import exception

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

# Add standard lines to build template
def add_standard_build_definitions(template_obj):

    default_template = os.path.join(glob.stg['template_path'], glob.stg['build_tmpl_dir'], "default.template")
    construct_template(template_obj, default_template)

    # export module names
    for mod in glob.code['modules']:
        template_obj.append("export" + mod.rjust(15) + "=" + glob.code['modules'][mod] + "\n")

    template_obj.append("\n")
    template_obj.append("# Load modules \n")
    template_obj.append("ml reset \n")
        
    # add 'module use' if set
    if glob.code['general']['module_use']:
        template_obj.append("ml use " + glob.code['general']['module_use'] + "\n")

    # Add non Null modules 
    for mod in glob.code['modules']:
        if glob.code['modules'][mod]:
            template_obj.append("ml $" + mod + "\n")

    template_obj.append("ml \n")
    template_obj.append("\n")
    template_obj.append("# Create application directories\n")
    template_obj.append("mkdir -p ${build_path} \n")
    template_obj.append("mkdir -p ${install_path} \n")

# Add standard lines to bench template
def add_standard_bench_definitions(template_obj):
    default_template = os.path.join(glob.stg['template_path'], glob.stg['bench_tmpl_dir'], "default.template")
    construct_template(template_obj, default_template)

# Add things to the bottom of the build script
def template_epilog(template_obj):

    # Add sanity check
    if glob.code['config']['exe']:
        template_obj.append("ldd " + os.path.join("${install_path}", glob.code['config']['bin_dir'], glob.code['config']['exe']) + " \n")

    # Add hardware collection script to job script
    if glob.code['config']['collect_hw_stats']:
        if common.file_owner(os.path.join(glob.stg['utils_path'], "lshw")) == "root":
            template_obj.append(glob.stg['src_path'] + glob.stg['sl'] + "collect_hw_info.sh " + glob.stg['utils_path'] + " " + \
                            glob.code['metadata']['working_path'] + glob.stg['sl'] + "hw_report" + "\n")
        else:
            exception.print_warning(glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")

# Add dependency to build process (if building locally)
def add_process_dep(template_obj):

    glob.log.debug("Adding dependency to benchmark script, waiting for PID: " + glob.prev_pid)

    dep_file = os.path.join(glob.stg['template_path'], glob.stg['pid_dep_file'])
    if os.path.isfile(dep_file):
        with open(dep_file, 'r') as fd:
            template_obj.extend(fd.readlines())

    else:
        exception.error_and_quit(glob.log, "unable to read pid dependency template " + common.rel_path(dep_file))

# Contextualizes template script with variables from a list of config dicts
def populate_template(cfg_dicts, template_obj):
    glob.log.debug("Populating template file " + glob.tmp_script)
    # For each config dict
    for cfg in cfg_dicts:
        # For each key, find and replace <<<key>>> in template file
        for key in cfg:
            template_obj = [line.replace("<<<" + str(key) + ">>>", str(cfg[key])) for line in template_obj]
            glob.log.debug("replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))

    return template_obj

def get_build_templates():

    # Temp build script
    glob.tmp_script = "tmp." + glob.code['general']['code'] + "-build." + glob.stg['build_mode']
    # === Scheduler template file ===

    if glob.stg['build_mode'] == "sched":
        glob.sched['template'] = common.find_exact(glob.sched['sched']['type'] + ".template", glob.stg['template_path'])

    # === Application template file ===

    # Get application template file name from cfg, otherwise use cfg_label to look for it
    if glob.code['general']['template']:
        glob.code['template'] = glob.code['general']['template']
    else:
        glob.code['template'] = glob.code['metadata']['cfg_label']

    # Search for application template file
    build_template_search = common.find_partial(glob.code['template'], os.path.join(glob.stg['template_path'], glob.stg['build_tmpl_dir']))

    # Error if not found
    if not build_template_search:
        exception.error_and_quit(glob.log, "failed to locate build template '" + glob.code['template'] + "' in " + \
                                common.rel_path(glob.stg['template_path'] + glob.stg['sl'] + glob.stg['build_tmpl_dir']))
    
    glob.code['template'] = build_template_search


    # === Compiler template file ===

    # Get compiler cmds for gcc/intel/pgi, otherwise compiler type is unknown
    known_compiler_type = True
    try:
        glob.compiler['common'].update(glob.compiler[glob.code['config']['compiler_type']])
        glob.compiler['template'] = common.find_exact(glob.stg['compile_tmpl_file'], glob.stg['template_path'])
    except:
        glob.compiler['template'] = None

# Combine template files and populate
def generate_build_script(glob_obj):

    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    template_obj = []

    template_obj.append("#!/bin/bash \n")

    # Parse template file names
    get_build_templates()

    # Add scheduler directives if contructing job script
    if glob.stg['build_mode'] == "sched":
        # Get ranks from threads (?)
        glob.sched['sched']['ranks'] = 1
        # Get job label
        glob.sched['sched']['job_label'] = glob.code['general']['code'] + "_build"


        # Take multiple input template files and combine them to generate unpopulated script
        construct_template(template_obj, glob.sched['template'])

        # Add reservation line to SLURM params if set
        add_reservation(template_obj)

    # Add standard lines to template
    add_standard_build_definitions(template_obj)

    construct_template(template_obj, glob.compiler['template'])
    construct_template(template_obj, glob.code['template'])

    template_epilog(template_obj)

    # Populate template list with cfg dicts
    print("Populating template...")
    template_obj = populate_template([glob.code['metadata'], \
                                      glob.code['general'], \
                                      glob.code['modules'], \
                                      glob.code['config'], \
                                      glob.sched['sched'], \
                                      glob.compiler['common']], \
                                      template_obj)


    template_obj.append("date \n")

    # Test for missing parameters
    print("Validating template...")
    common.test_template(glob.tmp_script, template_obj)

    # Write populated script to file
    common.write_list_to_file(template_obj, glob.tmp_script)

def get_bench_templates():
    # Template files

    # Temp job script 
    glob.tmp_script = "tmp." + glob.code['config']['label']  + "-bench." + glob.stg['bench_mode'] 
    
    # Scheduler template file
    if glob.stg['bench_mode'] == "sched":
        glob.sched['template'] = common.find_exact(glob.sched['sched']['type'] + ".template", os.path.join(glob.stg['template_path'], glob.stg['sched_tmpl_dir']))

    # Set bench template to default, if set in bench.cfg: overload
    if glob.code['config']['template']:
        glob.code['template'] = glob.code['config']['template']
    else:
        glob.code['template'] = glob.code['config']['label']

    matches = gb.glob(os.path.join(glob.stg['template_path'], glob.stg['bench_tmpl_dir'], "*" + glob.code['template'] + "*"))
    matches.sort()

    # If more than 1 template match found
    if len(matches) > 1: 
        matches[0] = min(matches, key=len)

    # if no template match found 
    if not matches:
        exception.error_and_quit(glob.log, "failed to locate bench template '" + glob.code['template'] + "' in " + common.rel_path(os.path.join(glob.stg['template_path'], glob.stg['bench_tmpl_dir'])))
    else:
        glob.code['template'] = matches[0]

    glob.code['metadata']['job_script'] = glob.code['config']['label'] + "-bench." + glob.stg['bench_mode']


def generate_bench_script(glob_obj):

    # Get global settings obj
    global glob, common
    glob = glob_obj

    # Instantiate common_funcs
    common = common_funcs.init(glob)

    template_obj = []

    template_obj.append("#!/bin/bash \n")

    # Create dep to running build shell on local node
    if glob.prev_pid:
        glob.code['config']['pid'] = glob.prev_pid
        add_process_dep(template_obj)  

    get_bench_templates()

    # If generate sched script
    if glob.stg['bench_mode'] == "sched":
        construct_template(template_obj, glob.sched['template'])
        add_reservation(template_obj)

  
    # Add start time line
    template_obj.append("echo \"START `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

    # Add standard lines to script
    add_standard_bench_definitions(template_obj)

    # Add bench templat to script
    construct_template(template_obj, glob.code['template'])

    # Add hardware collection script to job script
    if glob.code['config']['collect_hw_stats']:
        if common.file_owner(os.path.join(glob.stg['utils_path'], "lshw")) == "root":
            template_obj.append(os.path.join(glob.stg['src_path'], "collect_hw_info.sh " + glob.stg['utils_path'] + " " + glob.code['metadata']['working_path'], "hw_report \n"))
        else:
            exception.print_warning(glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")

    template_obj.append("date \n")

    print("Populating template...")
    # Take multiple config dicts and populate script template
    if glob.stg['bench_mode'] == "sched":
        template_obj = populate_template([glob.code['metadata'], \
                                         glob.code['runtime'], \
                                         glob.code['config'], \
                                         glob.code['result'], \
                                         glob.sched['sched'], \
                                         glob.code['requirements']], \
                                         template_obj)
    
    else:
        template_obj = populate_template([glob.code['metadata'], \
                                        glob.code['runtime'], \
                                        glob.code['config'], \
                                        glob.code['result'], \
                                        glob.code['requirements']], \
                                        template_obj)

    # Add end time line
    template_obj.append("echo \"END `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

    print("Validating template...")
    # Test for missing parameters
    common.test_template(glob.tmp_script, template_obj)

    # Write populated script to file
    common.write_list_to_file(template_obj, glob.tmp_script)

