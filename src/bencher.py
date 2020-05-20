# System Imports
import configparser as cp
from datetime import datetime
import argparse
import os
import sys
import time

# Local Imports
import src.builder as builder
import src.exception as exception
import src.cfg_handler as cfg_handler
import src.splash as splash
import src.template_handler as template_handler

sl = '/'
base_dir            = sl.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1])
time_str            = datetime.now().strftime("%Y-%m-%d_%Hh%M")

# Check input
def get_subdirs(base):
    return [name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))]

def recurse_down(installed_list, app_dir, start_depth, current_depth, max_depth):
    for d in get_subdirs(app_dir):
        if d != 'modulefiles':
            new_dir = app_dir + sl + d
            if current_depth == max_depth:
                installed_list.append(sl.join(new_dir.split(sl)[start_depth+1:]))
            else:
                recurse_down(installed_list, new_dir, start_depth, current_depth+1, max_depth)

# Print currently installed apps, used together with 'remove'
def get_installed():
    app_dir = base_dir+sl+"build"
    start = app_dir.count(sl)
    installed_list = []
    recurse_down(installed_list, app_dir, start, start, start+5)
    return installed_list


def check_if_installed(requested_code):
    installed_list = get_installed()
    matched_codes = []
    for code_string in installed_list:
        if requested_code in code_string:
            matched_codes.append(code_string)

    if len(matched_codes) == 0:
        print("No installed applications match your selection '"+requested_code+"'")
        print("Currently installed applications:")
        for code in installed_list: print("    "+code)
        sys.exit(1)

    elif len(matched_codes) == 1:
        print("Using application installed in:")
        print("    "+matched_codes[0])
        return matched_codes[0]

    else:
        print("Multiple installed applications match your selection '"+requested_code+"':")
        for code in matched_codes: print("    "+code)
        print("Please be more specific.")
        sys.exit(1)

def run_bench(args):

    run_log = builder.start_logging("RUN", file=base_dir+sl+builder.run_log_file+"_"+time_str+".log")

    # Get path to application
    code_path = check_if_installed(args.run)
    code_dict = code_path.split('/')
    system    = code_dict[0]
    code      = code_dict[3]
    version   = code_dict[5]

    param_cfg = cfg_handler.get_cfg('param',    args.inputs, builder.use_default_paths, run_log, run_log)
    sched_cfg = cfg_handler.get_cfg('sched',    args.sched,  builder.use_default_paths, run_log, run_log)

    session = code+"-"+time_str

    param_cfg['bench']['run_path']     = base_dir + sl + 'build' + sl + code_path + sl + session
    param_cfg['bench']['base_mod']     = base_dir + sl + 'build' + sl + 'modulefiles' 
    param_cfg['bench']['app_mod']      = code_path
    param_cfg['bench']['project_path'] = param_cfg['bench']['run_path']

    param_cfg['sched']['ranks'] = int(param_cfg['sched']['nodes']) * int(param_cfg['sched']['ranks_per_node'])

    # Template files
    sched_template    = base_dir + sl + builder.template_dir + sl + "sched" + sl + sched_cfg['scheduler']['type'] + ".template"
    run_template      = base_dir + sl + builder.template_dir + sl + "codes" + sl + code + "-" + version + ".run"
 
    script_file         = "tmp." + code + "-run." + sched_cfg['scheduler']['type']

    # Copy template files
    template_handler.construct_template([sched_template, run_template], script_file)
    script = open(script_file).read()

    # Populate template
    script = template_handler.populate_template(param_cfg['sched'], script, run_log)
    script = template_handler.populate_template(param_cfg['bench'], script, run_log)
    script = template_handler.populate_template(sched_cfg['scheduler'], script, run_log)

    template_handler.test_template(script, builder.exit_on_missing, run_log, run_log)
    template_handler.write_template(script_file, script)

    print("Benchmark working directory = "+param_cfg['bench']['run_path'])

    builder.create_install_dir(param_cfg['bench']['run_path'], run_log)

    builder.install(param_cfg['bench']['run_path'], script_file, run_log)   

    exception.remove_tmp_files()

    builder.submit_job(param_cfg['bench']['run_path']+sl+script_file[4:], run_log, run_log)
