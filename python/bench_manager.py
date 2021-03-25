# System Imports
import configparser as cp
import copy
import datetime
import os
import shutil as su
import sys

# Local Imports
import build_manager
import logger

glob = glob_master = None

# Get code info
def get_code_info(input_label, search_dict):

    # Evaluate any expressions in the requirements section
    glob.lib.math.eval_dict(glob.code['requirements'])

    # Check if code is installed
    glob.code['metadata']['code_path'] = glob.lib.check_if_installed(search_dict)

    # If application is not installed, check if cfg file is available to build
    if not glob.code['metadata']['code_path']:
        glob.lib.msg.warning("No installed application meeting benchmark requirements: '" + "', '".join([i + "=" + search_dict[i] for i in search_dict.keys() if i]) + "'") 
        glob.lib.msg.high("Attempting to build now...")

        glob.args.build = search_dict
        glob.quiet_build = True
        build_manager.init(copy.deepcopy(glob))

        if glob.stg['dry_run']:
            glob.code['metadata']['build_running'] = False
        else:
            glob.code['metadata']['build_running'] = True
        glob.code['metadata']['code_path'] = glob.lib.check_if_installed(search_dict)

    # Code is built
    else:

        glob.lib.msg.high("Installed application found, continuing...")
        glob.code['metadata']['build_running'] = False

    # Confirm application is installed after attempt
    if not glob.code['metadata']['code_path']:
        glob.lib.msg.error("it seems the attempt to build your application failed. Consult the logs.")

    # Set application module path to install path
    glob.code['metadata']['app_mod'] = glob.code['metadata']['code_path']

    glob.build = {}

    # Get app info from build report
    install_path = os.path.join(glob.stg['build_path'], glob.code['metadata']['code_path'])
    glob.build['build_report'] = os.path.join(install_path, glob.stg['build_report_file'])
    report_parser     = cp.ConfigParser()
    report_parser.optionxform=str
    report_parser.read(glob.build['build_report'])

    # Get build jobid from build_report, for checking build state
    try:
        build_jobid = report_parser.get('build', 'jobid')
    except:
        glob.lib.msg.error("Unable to read build_report.txt file in " + glob.lib.rel_path(install_path))

    # Get code label from build_report to find appropriate bench cfg file

    glob.build['code']      = report_parser.get('build', 'code')
    glob.build['version']   = report_parser.get('build', 'version')
    glob.build['system']    = report_parser.get('build', 'system')

    # Get build job depenency
    glob.lib.get_build_job_dependency(build_jobid)
    # Build job running
    if glob.ok_dep_list:
        glob.lib.msg.low(glob.build['code'] + " build job is still running, creating dependency")
    # Build job complete
    else:
        # dry_run=False
        if not glob.stg['dry_run']:
            # check_exe=True
            if glob.stg['check_exe']:
                # bench_mode=sched
                if glob.stg['bench_mode'] == 'sched':
                    # exe not null
                    if glob.code['config']['exe']:
                        glob.lib.check_exe(glob.code['config']['exe'], install_path)
                    # exe null
                    else:
                        glob.lib.msg.low("No exe defined, skipping application check.")
                # bench_mode=local
                else:
                    glob.lib.msg.low("Application was built locally, skipping application exe check.")
            # check_exe=False
            else:
                glob.lib.msg.low("'check_exe=False' in settings.ini, skipping application exe check.")
        # dry_run=True
        else:
            glob.lib.msg.low("This is a dry run, skipping application exe check.")

# Generate the bench script
def gen_bench_script():

    # Evaluate math in cfg dict -
    glob.lib.math.eval_dict(glob.code['config'])

    gpu_path_str = ""
    gpu_print_str = ""
    # Get GPU string
    if glob.code['runtime']['gpus']:
        gpu_path_str = str(glob.code['runtime']['gpus']).zfill(2) + "G"
        gpu_print_str = ", on " + glob.code['runtime']['gpus'] + " GPUs."
        

    glob.lib.msg.heading("Task " + str(glob.counter) \
            + ": " + glob.code['config']['bench_label'] + " : " + str(glob.code['runtime']['nodes']) + " nodes, " + str(glob.code['runtime']['threads']) + " threads, " + \
            str(glob.code['runtime']['ranks_per_node']) + " ranks per node" + gpu_print_str + glob.end)

    glob.counter += 1

    # Working Dir
    glob.code['metadata']['working_dir'] =  glob.system['sys_env'] + "_" + \
                                            glob.code['config']['bench_label'] + "_" + \
                                            glob.time_str + "_" + str(glob.code['runtime']['nodes']).zfill(3) + "N_" + \
                                            str(glob.code['runtime']['ranks_per_node']).zfill(2) + "R_" + \
                                            str(glob.code['runtime']['threads']).zfill(2) + "T" + \
                                            gpu_path_str

    # Check if working dir path already exists
    glob.code['metadata']['working_path'] = glob.lib.check_dup_path(os.path.join(glob.stg['pending_path'], glob.code['metadata']['working_dir']))

    glob.lib.msg.low(["Benchmark working directory:",
                    ">  " + glob.lib.rel_path(glob.code['metadata']['working_path'])])

    # Generate benchmark template
    glob.lib.template.generate_bench_script()

# Execute the bench, locally or through sched
def start_task():
    # Make bench path and move tmp bench script file
    glob.lib.create_dir(glob.code['metadata']['working_path'])
    glob.lib.install(glob.code['metadata']['working_path'], glob.tmp_script, None)

    # Copy bench cfg & template files to bench dir
    provenance_path = os.path.join(glob.code['metadata']['working_path'], "bench_files")
    glob.lib.create_dir(provenance_path)

    glob.lib.install(provenance_path, glob.code['metadata']['cfg_file'], "bench.cfg")
    glob.lib.install(provenance_path, glob.code['template'], "bench.template")

    # If bench_mode == sched
    if glob.stg['bench_mode'] == "sched":
        glob.lib.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
        glob.lib.install(provenance_path, glob.sched_template, None)

    # Delete tmp job script
    glob.lib.files.remove_tmp_files()

    glob.lib.msg.high(glob.success)
    # dry_run = True
    if glob.stg['dry_run']:
        glob.lib.msg.low(["This was a dryrun, skipping exec step. Script created at:",
                        ">  " + glob.lib.rel_path(os.path.join(glob.code['metadata']['working_path'], glob.tmp_script[4:]))])
        glob.jobid = "dry_run"

    # dry_run = False
    else:
        # bench_mode = sched
        if glob.stg['bench_mode'] == "sched":
            # Get dep list
            try:
                job_limit = int(glob.code['runtime']['max_running_jobs'])
            except:
                glob.lib.msg.error("'max_running_jobs' value '" + \
                                        glob.code['runtime']['max_running_jobs'] + "' is not an integer")

            if len(glob.prev_jobid) >= job_limit:
                glob.lib.msg.low("Max running jobs reached, creating dependency")
                glob.any_dep_list.append(glob.prev_jobid[-1 * job_limit])

            # Submit job
            glob.lib.sched.submit()
            #glob.jobid = glob.lib.submit_job( glob.lib.get_dep_str(), \
            #                                glob.code['metadata']['working_path'], \
            #                                glob.code['metadata']['job_script'])
            glob.prev_jobid.append(glob.jobid)

        # bench_mode = local
        elif glob.stg['bench_mode'] == "local":
            # For local bench, use default output file name if not set (can't use stdout)
            if not glob.code['result']['output_file']:
                glob.code['result']['output_file'] = glob.stg['output_file']

            glob.lib.start_local_shell(   glob.code['metadata']['working_path'], \
                                        glob.tmp_script[4:], \
                                        glob.code['result']['output_file'])

            glob.jobid = "local"

    # Use stdout for output if not set
    if not glob.code['result']['output_file']:
        glob.code['result']['output_file'] = glob.jobid + ".out"


    glob.lib.check_for_slurm_vars()


    glob.lib.msg.low(["Output file:",
                    ">  " + glob.lib.rel_path(os.path.join(glob.code['metadata']['working_path'], glob.code['result']['output_file']))])

    # Generate bench report
    glob.lib.report.bench()

    # Write to output file
    glob.lib.write_to_outputs("bench", glob.code['metadata']['working_dir'])

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
    search_dict = glob.code['requirements']

    glob.lib.msg.low(["Found matching benchmark config file:",
                    ">  " + glob.lib.rel_path(glob.code['metadata']['cfg_file'])]) 

    if glob.lib.needs_code(search_dict):
        get_code_info(input_dict, search_dict)

        # Directory to add to MODULEPATH
        glob.code['metadata']['base_mod'] = glob.stg['module_path']

    else:    
        glob.lib.msg.low("No installed appication required!") 
        glob.code['metadata']['code_path'] = ""
        glob.code['metadata']['build_running'] = False

    # Get bench config cfgs
    if glob.stg['bench_mode'] == "sched":
        glob.lib.cfg.ingest('sched', glob.lib.get_sched_cfg())

        # Get job label
        glob.sched['sched']['job_label'] = glob.build['code']+"_bench"

        glob.sched_template = glob.lib.find_exact(glob.sched['sched']['type'] + ".template", \
                                            os.path.join(glob.stg['template_path'], glob.stg['sched_tmpl_dir']))

    # Check for empty overload params
    glob.lib.check_for_unused_overloads()

    # Check if MPI is allow on this host
    if glob.stg['bench_mode'] == "local" and not glob.stg['dry_run'] and not glob.lib.check_mpi_allowed():
            glob.lib.msg.error("MPI execution is not allowed on this host!")

    # Use code name for label if not set
    if not glob.code['config']['bench_label']:
        glob.code['config']['bench_label'] = glob.code['requirements']['code']

    # Print inputs to log
    glob.lib.send_inputs_to_log('Bencher')

    glob.prev_jobid = glob.lib.sched.get_active_jobids('_bench')
    prev_pid = 0

    # Create backup on benchmark cfg params, to be modified by each loop 
    backup_dict = copy.deepcopy(glob.code) 

    node_list = glob.code['runtime']['nodes']
    thread_list = glob.code['runtime']['threads']
    rank_list = glob.code['runtime']['ranks_per_node']

    # for each nodes in list
    for node in node_list:
        glob.log.debug("Write script for " + node + " nodes")

        # Iterate over thread/rank pairs
        for i in range(len(thread_list)):
            # Grab a new copy of code_dict for this iteration (resets variables to be repopulated)
            glob.code = copy.deepcopy(backup_dict)
            glob.code['runtime']['nodes'] = node
            glob.code['runtime']['threads'] = thread_list[i]
            glob.code['runtime']['ranks_per_node'] = rank_list[i]

            # Iterate over GPU values
            gpu_list = glob.code['runtime']['gpus']
            for gpu in gpu_list:
                glob.code['runtime']['gpus'] = gpu

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

        # Start benchmark session and collect number of runs
        glob.counter = run_bench(glob.lib.parse_bench_str(inp), glob_copy)

