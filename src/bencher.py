# System Imports
import configparser as cp
import datetime
import os
import shutil as su

# Local Imports
import src.cfg_handler as cfg_handler
import src.common as common_funcs
import src.exception as exception
import src.logger as logger
import src.template_handler as template_handler

glob = common = None

# Generate bench report after job is submitted
def generate_bench_report(build_report, jobid):
    bench_report = glob.code['bench']['working_path'] + glob.stg['sl'] + glob.stg['bench_report_file']
    glob.log.debug("Benchmark report file:" + bench_report)
        
    # Copy 'build_report' to 'bench_report'
    su.copyfile(build_report, bench_report)

    with open(bench_report, 'a') as out:
        out.write("[bench]\n")
        out.write("bench_path  = "+ glob.code['bench']['working_path']   + "\n")
        out.write("nodes       = "+ glob.code['sched']['nodes']          + "\n")
        out.write("ranks       = "+ glob.code['sched']['ranks_per_node'] + "\n")
        out.write("threads     = "+ glob.code['sched']['threads']        + "\n")
        out.write("dataset     = "+ glob.code['bench']['dataset']        + "\n")
        out.write("bench_date  = "+ str(datetime.datetime.now())         + "\n")
        out.write("job_script  = "+ glob.code['bench']['job_script']     + "\n")
        out.write("jobid       = "+ jobid                                + "\n")
        out.write("description = "+ glob.code['result']['description']   + "\n")

        if not jobid == "dry_run":
            out.write("stdout      = "+ jobid+".out"                       + "\n")
            out.write("stderr      = "+ jobid+".err"                       + "\n")
            out.write("result_file = "+ glob.code['bench']['output_file']+ "\n")

# Check input
def run_bench(glob_obj):

    global glob, common
    glob = glob_obj
    common = common_funcs.init(glob)

    # Start logger
    glob.log = logger.start_logging("RUN", glob.stg['bench_log_file'] + "_" + glob.time_str + ".log", glob)

    # Check for new results
    common.print_new_results()

    # Overload settings.cfg with cmd line args
    common.overload_params(glob.stg)

    # Get app info from build report
    code_dir = common.check_if_installed(glob.args.bench)
    code_path = glob.stg['build_path'] + glob.stg['sl'] + code_dir
    build_report = code_path + glob.stg['sl'] + glob.stg['build_report_file']
    report_parser     = cp.ConfigParser()
    report_parser.optionxform=str
    report_parser.read(build_report)

    # Get code labee from build_report, for finding default params (if needed)
    try:
        jobid     = report_parser.get('build', 'jobid')
    except:
        exception.error_and_quit(glob.log, "Unable to read build_report.txt file in " + common.rel_path(code_path))

    # Check build job is complete
    if not common.check_job_complete(jobid):
        exception.error_and_quit(glob.log, "Job ID " + jobid + "is RUNNING. It appears '" + glob.args.bench + "' is still compiling.")

    # Get code label from build_report to find appropriate bench cfg file
    code = report_parser.get('build', 'code')

    # Print warning when using default benchmark inputs
    if not glob.args.params:
        glob.args.params = code
        print("WARNING: No input parameters (--params) given, using defaults for debugging.")
        glob.log.debug("WARNING: No input parameters (--params) given, using defaults for debugging.")

    # Get bench config dicts
    cfg_handler.ingest_cfg('bench', glob.args.params, glob)
    cfg_handler.ingest_cfg('sched', glob.args.sched,  glob)

    print()
    # Check for empty overload params
    common.check_for_unused_overloads()

    # Check application exe
    common.check_exe(glob.code['bench']['exe'], code_path)

    # Add variables from build report to bench cfg dict
    glob.code['bench']['code']      = report_parser.get('build', 'code')
    glob.code['bench']['version']   = report_parser.get('build', 'version')
    glob.code['bench']['system']    = report_parser.get('build', 'system')

    # Get job label
    glob.sched['sched']['job_label'] = code+"_bench"

    # Path to benchmark session directory
    glob.code['bench']['base_path'] = glob.stg['bench_path'] + glob.stg['sl'] + glob.code['bench']['system'] + "_" + glob.code['bench']['code'] + "_" + glob.time_str
    # Path to application's data directory
    glob.code['bench']['benchmark_repo'] = glob.stg['benchmark_repo']
    # Directory to add to MODULEPATH
    glob.code['bench']['base_mod'] = glob.stg['module_path']
    # Directory to application installation
    glob.code['bench']['app_mod'] = code_dir

    # Print inputs to log
    common.send_inputs_to_log('Bencher', [glob.code, glob.sched])

    # Template files
    sched_template = common.find_exact(glob.sched['sched']['type'] + ".template", glob.stg['template_path'] + glob.stg['sl'] + glob.stg['sched_tmpl_dir'])

    # Set bench template to default, if set in bench.cfg: overload
    bench_template = None
    if glob.code['bench']['template']:
        bench_template = glob.code['bench']['template']
    else:
        bench_template = glob.code['bench']['code'] + "-" + glob.code['bench']['version'] + ".bench"
    
    bench_template_search = common.find_partial(bench_template, glob.stg['template_path'] + glob.stg['sl'] + glob.stg['bench_tmpl_dir'])
    
    if not bench_template_search:
        exception.error_and_quit(glob.log, "failed to locate bench template '" + bench_template + "' in " + common.rel_path(glob.stg['template_path'] + glob.stg['sl'] + glob.stg['bench_tmpl_dir']))
    else:
        bench_template = bench_template_search

    glob.code['bench']['job_script'] = glob.code['bench']['code'] + "-bench." + glob.sched['sched']['type']
    script_file = "tmp." + glob.code['bench']['job_script']

    jobs = glob.code['sched']['nodes']
    counter = 1

    # for each nodes in list
    for node in jobs:
        glob.log.debug("Write script for " + node + " nodes")

        print()
        print("Building script " + str(counter)  + " of " + str(len(jobs)) + ": " + str(node) + " nodes.")

        # Update node var
        glob.code['sched']['nodes'] = node

        # Get working_path
        subdir = node.zfill(3) + "nodes"
        glob.code['bench']['working_path'] = glob.code['bench']['base_path'] + "_" + subdir
        print("Benchmark working directory:")
        print(">  " + common.rel_path(glob.code['bench']['working_path']))
        print()

        # Get total ranks from nodes * ranks_per_node
        glob.code['sched']['ranks'] = int(node) * int(glob.code['sched']['ranks_per_node'])

        # Generate benchmark template
        template_handler.generate_bench_template([glob.code['sched'], glob.code['bench'], glob.sched['sched']],
                                       [sched_template, bench_template],
                                       script_file, glob)

        # Add hardware collection script to job script
        if glob.code['bench']['collect_hw_stats']:
            if common.file_owner(glob.stg['utils_path'] + glob.stg['sl'] + "lshw") == "root":
                with open(script_file, 'a') as f:    
                    f.write(glob.stg['src_path'] + glob.stg['sl'] + "collect_hw_info.sh " + glob.stg['utils_path'] + " " + glob.code['bench']['working_path'] + glob.stg['sl'] + "hw_report \n")
            else:
                exception.print_warning(glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")


        # Make bench path and move tmp bench script file
        common.create_dir(glob.code['bench']['working_path'])
        common.install(glob.code['bench']['working_path'], script_file, None)

        # Copy bench cfg & template files to bench dir
        provenance_path = glob.code['bench']['working_path'] + glob.stg['sl'] + "bench_files"
        common.create_dir(provenance_path)

        common.install(provenance_path, glob.code['metadata']['cfg_file'], "bench.cfg")
        common.install(provenance_path, bench_template, "bench.template")

        common.install(provenance_path, glob.sched['metadata']['cfg_file'], None)
        common.install(provenance_path, sched_template, None)

        # Delete tmp job script
        exception.remove_tmp_files(glob.log)
        # Submit job
        jobid = common.submit_job(glob.code['bench']['working_path'], glob.code['bench']['job_script'])

        # Generate bench report
        generate_bench_report(build_report, jobid)

        counter += 1

