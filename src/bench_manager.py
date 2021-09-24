# System Imports
import configparser as cp
import copy
import datetime
import os
import shutil as su
import sys

# Local Imports
import src.build_manager as build_manager
import src.logger as logger

glob = glob_master = None

# Get code info
def get_code_info(input_label, search_dict):

    # Evaluate any expressions in the requirements section
    glob.lib.expr.eval_dict(glob.config['requirements'])

    # Check if code is installed
    glob.config['metadata']['code_path'] = glob.lib.check_if_installed(search_dict)

    # If application is not installed, check if cfg file is available to build
    if not glob.config['metadata']['code_path']:
        glob.lib.msg.warning("No installed application meeting benchmark requirements: '" + "', '".join([i + "=" + search_dict[i] for i in search_dict.keys() if i]) + "'") 
        glob.lib.msg.high("Attempting to build now...")

        glob.args.build = search_dict
        glob.quiet_build = True
        build_manager.init(copy.deepcopy(glob))

        if glob.stg['dry_run']:
            glob.config['metadata']['build_running'] = False
        else:
            glob.config['metadata']['build_running'] = True
        glob.config['metadata']['code_path'] = glob.lib.check_if_installed(search_dict)

    # Code is built
    else:

        glob.lib.msg.high("Installed application found, continuing...")
        glob.config['metadata']['build_running'] = False

    # Confirm application is installed after attempt
    if not glob.config['metadata']['code_path']:
        glob.lib.msg.error("it seems the attempt to build your application failed. Consult the logs.")

    # Set application module path to install path
    glob.config['metadata']['app_mod'] = glob.config['metadata']['code_path']

    # Get app info from build report
    install_path = os.path.join(glob.stg['build_path'], glob.config['metadata']['code_path'])
    glob.build_report = glob.lib.report.read(os.path.join(install_path, glob.stg['build_report_file']))['build']

    # If not set, add exe file label from build report in bench cfg for populating template later
    if not glob.config['config']['exe']:
        glob.config['config']['exe'] = glob.build_report['exe_file']

    # Get build job depenency
    glob.lib.sched.get_build_job_dependency()

    # Build job running
    if glob.ok_dep_list:
        glob.lib.msg.low(glob.build_report['code'] + " build job is still running, creating dependency")
    # Build job complete
    else:
        # dry_run=False
        if not glob.stg['dry_run']:
            # check_exe=True
            if glob.stg['check_exe']:
                # bench_mode=sched
                if glob.stg['bench_mode'] == 'sched':
                    # exe not null
                    if glob.build_report['exe_file']:
                        glob.lib.msg.exe_check(glob.build_report['exe_file'], os.path.join(install_path, glob.stg['install_subdir'], glob.build_report['bin_dir']))
                    # exe null
                    else:
                        glob.lib.msg.low("No exe defined, skipping application check.")
                # bench_mode=local
                else:
                    glob.lib.msg.low("Application was built locally, skipping application exe check.")
            # check_exe=False
            else:
                glob.lib.msg.low("'check_exe=False' in settings.ini, skipping application exe check.")

# Generate the bench script
def gen_bench_script():

    # Evaluate math in cfg dict -
    for sect in ['config', 'runtime', 'files', 'result']:
        glob.lib.expr.eval_dict(glob.config[sect])

    # Update GPU default if arch=cuda
    if glob.config['config']['arch'] == "cuda":
        glob.config['runtime']['gpus'] = 1

    gpu_path_str = ""
    gpu_print_str = ""
    # Get GPU string
    if glob.config['runtime']['gpus']:
        gpu_path_str = str(glob.config['runtime']['gpus']).zfill(2) + "G"
        gpu_print_str = ", on " + glob.config['runtime']['gpus'] + " GPUs."

    glob.lib.msg.heading("Task " + str(glob.counter) \
            + ": " + glob.config['config']['bench_label'] + " : " + str(glob.config['runtime']['nodes']) + " nodes, " + str(glob.config['runtime']['threads']) + " threads, " + \
            str(glob.config['runtime']['ranks_per_node']) + " ranks per node" + gpu_print_str + glob.end)

    glob.counter += 1

    # Working Dir
    glob.config['metadata']['working_dir'] =  glob.system['sys_env'] + "_" + \
                                            glob.config['config']['bench_label'] + "_" + \
                                            glob.time_str + "_" + str(glob.config['runtime']['nodes']).zfill(3) + "N_" + \
                                            str(glob.config['runtime']['ranks_per_node']).zfill(2) + "R_" + \
                                            str(glob.config['runtime']['threads']).zfill(2) + "T_" + \
                                            gpu_path_str

    # Check if working dir path already exists
    glob.config['metadata']['working_path'] = glob.lib.files.check_dup_path(os.path.join(glob.stg['pending_path'], glob.config['metadata']['working_dir']))
    # Path to copy files to
    glob.config['metadata']['dest_path']    = glob.config['metadata']['working_path']

    glob.lib.msg.low(["Benchmark working directory:",
                    ">  " + glob.lib.rel_path(glob.config['metadata']['working_path'])])

    # Copy input files
    glob.lib.files.stage()

    # Generate benchmark template
    glob.lib.template.generate_bench_script()

# Execute the bench, locally or through sched
def start_task():
    # Make bench path and move tmp bench script file
    glob.lib.files.create_dir(glob.config['metadata']['working_path'])
    glob.lib.files.install(glob.config['metadata']['working_path'], glob.tmp_script, None, True)

    # Copy bench cfg & template files to bench dir
    provenance_path = os.path.join(glob.config['metadata']['working_path'], "bench_files")
    glob.lib.files.create_dir(provenance_path)

    glob.lib.files.install(provenance_path, glob.config['metadata']['cfg_file'], "bench.cfg", False)
    glob.lib.files.install(provenance_path, glob.config['template'], "bench.template", False)

    # If bench_mode == sched
    if glob.stg['bench_mode'] == "sched":
        glob.lib.files.install(provenance_path, glob.sched['metadata']['cfg_file'], None, False)
        glob.lib.files.install(provenance_path, glob.sched_template, None, False)

    # Delete tmp job script
    glob.lib.files.remove_tmp_files()

    glob.lib.msg.high(glob.success)
    # dry_run = True
    if glob.stg['dry_run']:
        glob.lib.msg.low(["This was a dryrun, skipping exec step. Script created at:",
                        ">  " + glob.lib.rel_path(os.path.join(glob.config['metadata']['working_path'], glob.script_file))])
        glob.task_id = "dry_run"

    # dry_run = False
    else:
        # bench_mode = sched
        if glob.stg['bench_mode'] == "sched":
            # Get dep list
            try:
                job_limit = int(glob.config['runtime']['max_running_jobs'])
            except:
                glob.lib.msg.error("'max_running_jobs' value '" + \
                                        glob.config['runtime']['max_running_jobs'] + "' is not an integer")

            if len(glob.prev_task_id) >= job_limit:
                glob.lib.msg.low("Max running jobs reached, creating dependency")
                glob.any_dep_list.append(glob.prev_task_id[-1 * job_limit])

            # Submit job
            glob.lib.sched.submit()
            #glob.task_id = glob.lib.submit_job( glob.lib.get_dep_str(), \
            #                                glob.config['metadata']['working_path'], \
            #                                glob.config['metadata']['job_script'])
            glob.prev_task_id.append(glob.task_id)

        # bench_mode = local
        elif glob.stg['bench_mode'] == "local":
            # For local bench, use default output file name if not set (can't use stdout)
            if not glob.config['result']['output_file']:
                glob.config['result']['output_file'] = glob.stg['output_file']

            # Start task in local script
            glob.lib.proc.start_local_shell()

            # Store PID for report
            glob.task_id = glob.prev_pid

    # Use stdout for output if not set
    if not glob.config['result']['output_file']:
        glob.config['result']['output_file'] = glob.task_id + ".out"


    #glob.lib.check_for_slurm_vars()

    # Generate bench report
    glob.lib.report.bench()

    # Write to output file
    glob.lib.write_to_outputs("bench", glob.config['metadata']['working_dir'])

# Main function to check for installed application, setup benchmark and run it
def run_bench(input_dict, glob_copy):

    global glob
    glob = glob_copy

    # Reset dependency lists
    glob.any_dep_list = []
    glob.ok_dep_list = []

    glob.lib.msg.heading("Starting benchmark with criteria '" + ", ".join([i + "=" + input_dict[i] for i in input_dict]) + "'")

    # Get benchmark params from cfg file
    glob.lib.cfg.ingest('bench', input_dict)

    # Get application search list for this benchmark
    search_dict = glob.config['requirements']

    glob.lib.msg.low(["Found matching benchmark config file:",
                    ">  " + glob.lib.rel_path(glob.config['metadata']['cfg_file'])]) 

    # Directory to add to MODULEPATH
    glob.config['metadata']['base_mod'] = glob.stg['module_path']

    if glob.lib.needs_code(search_dict):
        get_code_info(input_dict, search_dict)

    else:    
        glob.lib.msg.high("No appication required!") 
        glob.config['metadata']['app_mod'] = ""
        glob.config['metadata']['code_path'] = ""
        glob.config['metadata']['build_running'] = False

    # Get bench config cfgs
    if glob.stg['bench_mode'] == "sched":
        glob.lib.cfg.ingest('sched', glob.lib.get_sched_cfg())

        # Get job label
        glob.sched['sched']['job_label'] = glob.config['config']['dataset']+"_bench"

        glob.sched_template = glob.lib.files.find_exact(glob.sched['sched']['type'] + ".template", \
                                            os.path.join(glob.stg['template_path'], glob.stg['sched_tmpl_dir']))

    # Check for empty overload params
    glob.lib.check_for_unused_overloads()

    # Check if MPI is allow on this host
    if glob.stg['bench_mode'] == "local" and not glob.stg['dry_run'] and not glob.lib.check_mpi_allowed():
            glob.lib.msg.error("MPI execution is not allowed on this host!")

    # Use code name for label if not set
    if not glob.config['config']['bench_label']:
        glob.config['config']['bench_label'] = glob.config['requirements']['code']

    # Print inputs to log
    glob.lib.send_inputs_to_log('Bencher')

    glob.prev_task_id = glob.lib.sched.get_active_jobids('_bench')
    prev_pid = 0

    # Create backup on benchmark cfg params, to be modified by each loop 
    backup_dict = copy.deepcopy(glob.config) 

    node_list = glob.config['runtime']['nodes']
    thread_list = glob.config['runtime']['threads']
    rank_list = glob.config['runtime']['ranks_per_node']

    # for each nodes in list
    for node in node_list:
        glob.log.debug("Write script for " + node + " nodes")

        # Iterate over thread/rank pairs
        for i in range(len(thread_list)):
            # Grab a new copy of code_dict for this iteration (resets variables to be repopulated)
            glob.config = copy.deepcopy(backup_dict)
            glob.config['runtime']['nodes'] = node
            glob.config['runtime']['threads'] = thread_list[i]
            glob.config['runtime']['ranks_per_node'] = rank_list[i]

            # Iterate over GPU values
            gpu_list = glob.config['runtime']['gpus']
            for gpu in gpu_list:
                glob.config['runtime']['gpus'] = gpu

                # Generate bench script
                gen_bench_script()
                start_task()
                glob.lib.msg.brk()

    # Return number of tasks compeleted for this benchmark 
    return glob.counter

# Check input
def init(glob):

    glob.counter = 1

    # Start logger
    logger.start_logging("RUN", glob.stg['bench_log_file'] + "_" + glob.time_str + ".log", glob)

    # Get list of avail cfgs
    glob.lib.set_bench_cfg_list()

    # Check for new results
    glob.lib.msg.new_results()

    # Overload settings.ini with cmd line args
    glob.lib.overload_params(glob.stg)

    # Input is benchmark suite
    input_list = glob.args.bench
    if glob.args.bench[0] in glob.suite:
        input_list = glob.suite[glob.args.bench[0]].split(" ")
        glob.lib.msg.high("Running benchmark suite '" + glob.args.bench[0] + "' containing: '" + "' ,'".join(input_list) + "'")

    # Run benchmark on list of inputs
    for inp in input_list:

        # Get a copy of the global object for use in this benchmark session
        glob_copy = copy.deepcopy(glob)
        glob_copy.overload_dict = copy.deepcopy(glob.overload_dict)

        # Start benchmark session and collect number of runs
        glob.counter = run_bench(glob.lib.parse_bench_str(inp), glob_copy)

