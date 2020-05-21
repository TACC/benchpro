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
import src.global_settings as gs
import src.splash as splash
import src.template_handler as template_handler

logger              = ''

# Check input
def get_subdirs(base):
    return [name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))]

def recurse_down(installed_list, app_dir, start_depth, current_depth, max_depth):
    for d in get_subdirs(app_dir):
        if d != 'modulefiles':
            new_dir = app_dir + gs.sl + d
            if current_depth == max_depth:
                installed_list.append(gs.sl.join(new_dir.split(gs.sl)[start_depth+1:]))
            else:
                recurse_down(installed_list, new_dir, start_depth, current_depth+1, max_depth)

# Print currently installed apps, used together with 'remove'
def get_installed():
    app_dir = gs.base_dir + gs.sl + "build"
    start = app_dir.count(gs.sl)
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
        print("Using application installed in: "+matched_codes[0])
        return matched_codes[0]

    else:
        print("Multiple installed applications match your selection '"+requested_code+"':")
        for code in matched_codes: print("    "+code)
        print("Please be more specific.")
        sys.exit(1)

def run_bench(args):

    global logger
    logger = builder.start_logging("RUN", file=gs.base_dir + gs.sl + gs.run_log_file + "_"+ gs.time_str + ".log")

    # Get path to application
    code_path = check_if_installed(args.run)
    code_dict = code_path.split('/')
    system    = code_dict[0]
    code      = code_dict[3]
    version   = code_dict[5]


    if not args.params:
        args.params = code
        print("WARNING: No input parameters (--params) given, using defaults for debugging." )        
        

    param_cfg = cfg_handler.get_cfg('run',   args.params, logger)
    sched_cfg = cfg_handler.get_cfg('sched', args.sched,  logger)

    session = code+"-"+gs.time_str

    # Path to benchmark session directory
    param_cfg['bench']['working_path']     = gs.base_dir + gs.sl + 'build' + gs.sl + code_path + gs.sl + session
    # Path to application's data directory
    param_cfg['bench']['dataset_path']     = gs.base_dir + gs.sl + 'datasets' + gs.sl + code 
    # Directory to add to MODULEPATH
    param_cfg['bench']['base_mod']     = gs.base_dir + gs.sl + 'build' + gs.sl + 'modulefiles' 
    # Directory to application installation
    param_cfg['bench']['app_mod']      = code_path
    # Get total ranks from nodes * ranks_per_node
    param_cfg['sched']['ranks'] = int(param_cfg['sched']['nodes']) * int(param_cfg['sched']['ranks_per_node'])

    # Template files
    sched_template    = gs.sched_tmpl_dir + gs.sl + sched_cfg['scheduler']['type'] + ".template"
    run_template      = gs.run_tmpl_dir + gs.sl + code + "-" + version + ".run"
 
    script_file         = "tmp." + code + "-run." + sched_cfg['scheduler']['type']

    # Generate template
    template_handler.generate_template([param_cfg['sched'], param_cfg['bench'], sched_cfg['scheduler']], 
                                       [sched_template, run_template],
                                       script_file, logger)
    
    print("Benchmark working directory = "+param_cfg['bench']['working_path'])

    builder.create_install_dir(param_cfg['bench']['working_path'], logger)

    builder.install(param_cfg['bench']['working_path'], script_file, logger)   

    exception.remove_tmp_files()

    builder.submit_job(param_cfg['bench']['working_path'] + gs.sl + script_file[4:], logger)
