# System Imports
import configparser as cp
import copy
import datetime
import os
import shutil as su
import sys

# Local Imports
import src.builder as builder
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.logger as logger
import src.math_handler as math_funcs
import src.template_handler as template_handler

glob = common = build_running = None

# Generate bench report after job is submitted
def generate_bench_report(build_report, jobid):

    bench_report = os.path.join(glob.code['metadata']['working_path'],glob.stg['bench_report_file'])
    glob.log.debug("Benchmark report file:" + bench_report)

    # Build report exists - copy it and append
    if build_report:
        # Copy 'build_report' to 'bench_report'
        su.copyfile(build_report, bench_report)

    with open(bench_report, 'a') as out:
        out.write("[bench]\n")
        out.write("bench_path  = "+ glob.code['metadata']['working_path']   + "\n")
        out.write("system      = "+ glob.system['sys_env']                  + "\n")
        out.write("code        = "+ glob.code['config']['label']            + "\n")
        out.write("nodes       = "+ glob.code['runtime']['nodes']           + "\n")
        out.write("ranks       = "+ glob.code['runtime']['ranks_per_node']  + "\n")
        out.write("threads     = "+ glob.code['runtime']['threads']         + "\n")
        out.write("dataset     = "+ glob.code['config']['dataset']          + "\n")
        out.write("start_time  = "+ str(datetime.datetime.now())            + "\n")
        out.write("job_script  = "+ glob.code['metadata']['job_script']     + "\n")
        out.write("jobid       = "+ jobid                                   + "\n")
        out.write("description = "+ glob.code['result']['description']      + "\n")

        if not jobid == "dry_run":
            out.write("stdout      = "+ jobid+".out"                        + "\n")
            out.write("stderr      = "+ jobid+".err"                        + "\n")
            out.write("result_file = "+ glob.code['config']['output_file']  + "\n")

# Get code info
def get_code_info(input_label, search_dict):

    global build_running
    # Check if code is installed
    glob.code['metadata']['app_mod'] = common.check_if_installed(search_dict)

    # If application is not installed, check if cfg file is available to build
    if not glob.code['metadata']['app_mod']:
        print("Application '" + search_dict['code'] + "' not installed. Attempting to build now...")
        install_cfg = common.check_if_avail(search_dict)

        glob.args.build = common.get_filename_from_path(install_cfg)
        builder.init(copy.deepcopy(glob))
        build_running = True
        glob.code['metadata']['app_mod'] = common.check_if_installed(search_dict)

    # Code is built
    else:
        build_running = False
    
    # Get app info from build report
    install_path = os.path.join(glob.stg['build_path'], glob.code['metadata']['app_mod'])
    build_report = os.path.join(install_path, glob.stg['build_report_file'])
    report_parser     = cp.ConfigParser()
    report_parser.optionxform=str
    report_parser.read(build_report)

    # Get build jobid from build_report, for checking build state
    try:
        build_jobid = report_parser.get('build', 'jobid')
    except:
        exception.error_and_quit(glob.log, "Unable to read build_report.txt file in " + common.rel_path(install_path))

    # Get code label from build_report to find appropriate bench cfg file
    code = report_parser.get('build', 'code')

#    print(report_parser.get('build', 'code'))
#    print(glob.code)

    # Add variables from build report to bench cfg dict
#    glob.code['bench']['code']      = report_parser.get('build', 'code')
#    glob.code['bench']['version']   = report_parser.get('build', 'version')
#    glob.code['bench']['system']    = report_parser.get('build', 'system')

    
    code      = report_parser.get('build', 'code')
    version   = report_parser.get('build', 'version')
    system    = report_parser.get('build', 'system')

    # Get build job depenency
    common.get_build_job_dependency(build_jobid)
    # Build job running
    if glob.dep_list:
        print(code + " build job is still running, creating dependency")
    # Build job complete
    else:
        if not glob.stg['dry_run']:
            if glob.stg['bench_mode'] == 'sched':
                if glob.code['config']['exe']:
                    common.check_exe(glob.code['config']['exe'], install_path)
                else:
                    print("No exe defined, skipping application check.")
            else:
                print("Local build, skipping application exe check.")
        else:
            print("Dry run, skipping application exe check.")

    return code, version, system, build_report


# Main function to check for installed application, setup benchmark and run it
def run_bench(input_label):

    global build_running

    code = version = system = ""
    build_report = ""
    glob.dep_list = []
    
    # Get benchmark params from cfg file
    cfg_handler.ingest_cfg('bench', input_label, glob)

    # Get application search dict for this benchmark
    search_dict = glob.code['requirements']

    if common.needs_code(search_dict):
        search_dict['system'] = glob.system['sys_env']
        code, version, system, build_report = get_code_info(input_label, search_dict)

        # Directory to add to MODULEPATH
        glob.code['metadata']['base_mod'] = glob.stg['module_path']

    else:    
        print("No code required") 
        glob.code['metadata']['app_mod'] = ""
        build_running = False

    # Get bench config dicts
    if glob.stg['bench_mode'] == "sched":
        cfg_handler.ingest_cfg('sched', glob.args.sched,  glob)

        # Get job label
        glob.sched['sched']['job_label'] = code+"_bench"

        sched_template = common.find_exact(glob.sched['sched']['type'] + ".template", os.path.join(glob.stg['template_path'], glob.stg['sched_tmpl_dir']))

    glob.code['metadata']['build_running'] = build_running

    print()

    # Check for empty overload params
    common.check_for_unused_overloads()

    if not glob.code['config']['label']:
        glob.code['config']['label'] = glob.code['requirements']['code']

    # Print inputs to log
    #common.send_inputs_to_log('Bencher')

    jobs = glob.code['runtime']['nodes']
    counter = 1
    prev_jobid = []


    # Init math handler
    math_handler = math_funcs.init(glob)
    # Create backup on benchmark cfg params, to be modified by each loop 
    backup_dict = copy.deepcopy(glob.code) 

    thread_list = glob.code['runtime']['threads']
    rank_list = glob.code['runtime']['ranks_per_node']

    # for each nodes in list
    for node in jobs:
        glob.log.debug("Write script for " + node + " nodes")

        # Iterate over thread/rank pairs
        for i in range(len(thread_list)):
            # Grab a new copy of code_dict for this iteration (resets variables to be repopulated)
            glob.code = copy.deepcopy(backup_dict)
            glob.code['runtime']['nodes'] = node
            glob.code['runtime']['threads'] = thread_list[i]
            glob.code['runtime']['ranks_per_node'] = rank_list[i]

            # Evaluate math in cfg dict
            math_handler.eval_dict(glob.code['runtime'])
            math_handler.eval_dict(glob.code['config'])


            print()
            print("Building script " + str(counter)  + " of " + str(len(jobs)*len(thread_list)) + ": " + str(node) + " nodes, " + str(thread_list[i]) + " threads, " + str(rank_list[i]) + " ranks per node.")

            # Get working_path
            # Path to benchmark session directory
            glob.code['metadata']['base_path'] = os.path.join(glob.stg['bench_path'], glob.system['sys_env'] + "_" + glob.code['config']['label'] + "_" + glob.time_str)
            # Path to application's data directory
            glob.code['metadata']['benchmark_repo'] = glob.stg['benchmark_repo']

            subdir = node.zfill(3) + "N_" + str(rank_list[i]).zfill(2) + "R_" + str(thread_list[i]).zfill(2) + "T"
            glob.code['metadata']['working_path'] = glob.code['metadata']['base_path'] + "_" + subdir
            print("Benchmark working directory:")
            print(">  " + common.rel_path(glob.code['metadata']['working_path']))
            print()

            # Get total ranks from nodes * ranks_per_node

            glob.code['runtime']['ranks'] = int(node) * int(glob.code['runtime']['ranks_per_node'])

            # Generate mpi_exec str 
            if glob.stg['bench_mode'] == "sched":
                glob.code['runtime']['mpi_exec'] = glob.stg['sched_mpi'] + " "

            else:
                glob.code['runtime']['mpi_exec'] = "\"" + glob.stg['local_mpi'] + " -np " + str(glob.code['runtime']['ranks']) + " -ppn " \
                                                    + str(glob.code['runtime']['ranks_per_node']) + " " + glob.code['runtime']['host_str'] + "\""

            # Generate benchmark template
            template_handler.generate_bench_script(glob)

            # Make bench path and move tmp bench script file
            common.create_dir(glob.code['metadata']['working_path'])
            common.install(glob.code['metadata']['working_path'], glob.tmp_script, None)

            # Copy bench cfg & template files to bench dir
            provenance_path = os.path.join(glob.code['metadata']['working_path'], "bench_files")
            common.create_dir(provenance_path)

            common.install(provenance_path, glob.code['metadata']['cfg_file'], "bench.cfg")
            common.install(provenance_path, glob.code['template'], "bench.template")

            # If bench_mode == sched
            if glob.stg['bench_mode'] == "sched":
                common.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
                common.install(provenance_path, sched_template, None)

            # Delete tmp job script
            exception.remove_tmp_files(glob.log)

            print(glob.success)

            # Dry_run
            if glob.stg['dry_run']:
                print("This was a dryrun, skipping exec step. Script created at:")
                print(">  " + common.rel_path(os.path.join(glob.code['metadata']['working_path'], glob.tmp_script[4:])))
                jobid = "dry_run"

            else:
                # Sched run
                if glob.stg['bench_mode'] == "sched":
                    # Get dep list
                    try:
                        job_limit = int(glob.code['runtime']['max_running_jobs'])
                    except:
                        exception.error_and_quit(glob.log, "'max_running_jobs' value '" + glob.code['runtime']['max_running_jobs'] + "' is not an integer")

                    if len(prev_jobid) >= job_limit:
                        print("Max running jobs reached, creating dependency")
                        glob.dep_list.append(prev_jobid[-1 * job_limit])

                    # Submit job
                    jobid = common.submit_job(common.get_dep_str(), glob.code['metadata']['working_path'], glob.code['metadata']['job_script'])
                    prev_jobid.append(jobid)
    
                # Local run
                elif glob.stg['bench_mode'] == "local":
                    # Check if MPI is allow on this host
                    if not common.check_mpi_allowed():
                        exception.error_and_quit(glob.log, "MPI execution is not allowed on this host!")

                    common.start_local_shell(glob.code['metadata']['working_path'], glob.tmp_script[4:])
                    jobid = "local"

            # Generate bench report
            generate_bench_report(build_report, jobid)

            counter += 1

# Check input
def init(glob_obj):

    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    # Start logger
    glob.log = logger.start_logging("RUN", glob.stg['bench_log_file'] + "_" + glob.time_str + ".log", glob)

    # Check for new results
    common.print_new_results()

    # Overload settings.ini with cmd line args
    common.overload_params(glob.stg)

    # Either bench codes in suite or user label
    input_list = []
    if 'suite' in glob.args.bench:
        print("**", glob.suite)
        if glob.args.bench in glob.suite.keys():
            input_list = glob.suite[glob.args.bench].split(',')
            print("Benching application set '" + glob.args.bench + "': " + str(input_list))
        else:
            exception.error_and_quit(glob.log, "No suite '" + glob.args.bench + "' in settings.ini. Available suites: " + ', '.join(glob.suite.keys()))

    else:
        input_list = glob.args.bench.split(":")

    # Run benchmark on list of inputs
    for inp in input_list:
        run_bench(inp)
        glob.code = {}
        glob.args.params = None


