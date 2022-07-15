# System Imports
import copy
import glob as gb
import os
import re
import shutil as su
import sys

class init(object):
    def __init__(self, glob):
            self.glob = glob

    def read_template(self, input_template):
        # Check template file is defined - handles None type (in case of unknown compiler type = None compiler template)
        if input_template:
            self.glob.lib.msg.log("Reading template file " + input_template)
            # Test if input template file exists
            if not os.path.exists(input_template):
                self.glob.lib.msg.error("failed to locate template file '" + input_template + "' in " + self.glob.lib.rel_path(self.glob.stg['template_path'])  + ".")

            template = []
            # Copy input template file to temp obj
            with open(input_template, 'r') as fd:
                template = fd.readlines()

            return template             

    # Combines list of input templates to single script file
    def append_to_template(self, template_obj, input_template):

        if not input_template:
            self.glob.lib.msg.error("A template addition was not generated successfully.")

        # Copy input template file to temp obj
        with open(input_template, 'r') as fd:
            template_obj.extend(self.read_template(input_template))

    # Add user defined section of template
    def add_user_section(self, template_obj, input_template):
        template_obj.append("#------USER SECTION------\n")
        self.append_to_template(template_obj, input_template)
        template_obj.append("#------------------------\n")

    # Add sched reservation
    def add_reservation(self, template_obj):
        if self.glob.sched['sched']['reservation']:
                template_obj.append("#SBATCH --reservation=" + self.glob.sched['sched']['reservation'] + "\n")

    # Add standard lines to build template
    def add_standard_build_definitions(self, template_obj):
    
        header_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir'], self.glob.stg['header_file'])
        self.append_to_template(template_obj, header_template)

        # Add config key-values
        template_obj.append("\n# [config]\n")
        for key in self.glob.config['config']:
            template_obj.append("export "+ key.rjust(20) + "=" + str(self.glob.config['config'][key]) + "\n")

        template_obj.append("\n# [modules]\n")
        # export module names
        for mod in self.glob.config['modules']:
            template_obj.append("export" + mod.rjust(20) + "=" + self.glob.config['modules'][mod] + "\n")

        template_obj.append("\n")

        # Stage input files
        if not self.glob.stg['sync_staging']:
            template_obj.append("# [files]\n")
            self.stage_input_files(template_obj)

        # Add module loads
        template_obj.append("# Load modules \n")
#        template_obj.append("ml reset \n")
    
        # add 'module use' if set
        if self.glob.config['general']['module_use']:
            template_obj.append("ml use " + self.glob.config['general']['module_use'] + "\n")

        # Add non Null modules 
        for mod in self.glob.modules:
            if self.glob.modules[mod]['full']:
                template_obj.append("ml " + self.glob.modules[mod]['full'] + "\n")
        template_obj.append("ml \n")

        # Compiler variables
        template_obj.append("\n# Compiler variables")
        self.append_to_template(template_obj, self.glob.compiler['template'])

        template_obj.append("\n")

    # Add standard lines to bench template
    def add_standard_bench_definitions(self, template_obj):
        header_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], self.glob.stg['header_file'])
        self.append_to_template(template_obj, header_template)

        # add parameters from [config] section of cfg file to script
        for key in self.glob.config['config']:
            template_obj.append("export "+ key.rjust(20) + "=" + str(self.glob.config['config'][key]) + "\n")
        template_obj.append("export " + "OMP_NUM_THREADS".rjust(20) + "=${threads} \n")
        template_obj.append("\n")

        # Add module loads if application must be loaded
        if self.glob.config['metadata']['app_mod']:
            template_obj.append("# Load Modules \n")
            template_obj.append("ml reset \n")
            template_obj.append("ml use ${base_module} \n")
            template_obj.append("ml ${app_module} \n")
            template_obj.append("ml \n")
            template_obj.append("\n")

        template_obj.append("# Create working directory \n")
        template_obj.append("mkdir -p ${working_path} && cd ${working_path} \n")

    # Get input files asynchronously
    def stage_input_files(self, template_obj):

        for op in self.glob.stage_ops:
            self.glob.lib.msg.log("Adding file op to template: " + op + "...")
            template_obj.append(op + "\n")

        template_obj.append("\n")

    # If the setting in enabled, add the provenance data collection script to the script
    def collect_stats(self, template_obj):
        if self.glob.config['config']['collect_stats']:
            if self.glob.lib.files.file_owner(os.path.join(self.glob.stg['utils_path'], "lshw")) == "root":
                template_obj.append("\n# Provenance data collection script \n")
                template_obj.append(os.path.join(self.glob.stg['script_path'], "collect_hw_info") + " " + \
                                    self.glob.stg['utils_path'] + " " + \
                                    os.path.join(self.glob.config['metadata']['working_path'], "hw_report") + "\n")
            else:
                self.glob.lib.msg.warning(["Requested hardware stats but script permissions not set",
                                                "Run 'sudo -E $BP_HOME/resources/scripts/change_permissions'"])

    # Add things to the bottom of the build script
    def build_epilog(self, template_obj):

        # Add sanity check
        if self.glob.config['config']['exe']:
            template_obj.append("ldd " + os.path.join("${install_path}", self.glob.config['config']['bin_dir'], \
                                self.glob.config['config']['exe']) + " \n")

        # Add hardware collection script to job script
        self.collect_stats(template_obj)

    # Add things to the bootom of the bench script
    def bench_epilog(self, template_obj):
        # Collect stats
        self.collect_stats(template_obj)

    # Add dependency to build process (if building locally)
    def add_process_dep(self, template_obj):

        self.glob.lib.msg.low("Adding dependency to benchmark script, waiting for PID: " + self.glob.prev_pid)

        dep_file = os.path.join(self.glob.stg['template_path'], self.glob.stg['pid_dep_file'])
        if os.path.isfile(dep_file):
            with open(dep_file, 'r') as fd:
                template_obj.extend(fd.readlines())

        else:
            self.glob.lib.msg.error("Unable to read pid dependency template " + self.glob.lib.rel_path(dep_file))

    # Contextualizes template script with variables from a list of config dicts
    def populate_template(self, cfg_dicts, template_obj):
        self.glob.lib.msg.log("Populating template file " + self.glob.tmp_job_file)
        # For each config dict
        for cfg in cfg_dicts:
            # For each key, find and replace <<<key>>> in template file
            for key in cfg:
                template_obj = [line.replace("<<<" + str(key) + ">>>", str(cfg[key])) for line in template_obj]
                self.glob.lib.msg.log("Replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))

        return template_obj

    # Check for unpopulated <<<keys>>> in template file
    def test_template(self, template_file, template_obj):

        key = "<<<.*>>>"
        unfilled_keys = [re.search(key, line) for line in template_obj]
        unfilled_keys = [match.group(0) for match in unfilled_keys if match]

        if len(unfilled_keys) > 0:
            # Conitue regardless
            if not self.glob.stg['exit_on_missing']:
                self.glob.lib.msg.warning("Missing parameters were found in '" + self.glob.lib.rel_path(template_file) + \
                                            "':" + ", ".join(unfilled_keys))
                self.glob.lib.msg.warning("'exit_on_missing=False' in $BP_HOME/settings.ini so continuing anyway...")
            # Error and exit
            else:
               # Write file to disk
                self.glob.lib.files.write_list_to_file(template_obj, self.glob.tmp_job_file)
                self.glob.lib.msg.error("Missing parameters were found after populating '" + \
                                        self.glob.lib.rel_path(template_file) +              \
                                        "' and exit_on_missing=True in $BP_HOME/settings.ini: " + ' '.join(unfilled_keys))
        else:
            self.glob.lib.msg.log("All build parameters were filled, continuing")

    # Get template files required to constuct build script
    def set_build_files(self):
        # Temp build script
        self.glob.job_file = self.glob.stg['build_job_file']
        self.glob.tmp_job_file = os.path.join(self.glob.bp_home, "tmp." + self.glob.stg['build_job_file'])

        if self.glob.stg['build_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.files.find_exact(self.glob.sched['sched']['type'] + \
                                                                        ".template", self.glob.stg['template_path'])

        # Get application template file name from cfg, otherwise use cfg_label to look for it
        if self.glob.config['general']['template']:
            self.glob.config['template'] = self.glob.config['general']['template']
        else:
            self.glob.config['template'] = self.glob.config['metadata']['cfg_label']

        # Search for application template file
        build_template_search = self.glob.lib.files.find_partial(self.glob.config['template'], \
                                        os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir']))

        # Error if not found
        if not build_template_search:
            self.glob.lib.msg.error("failed to locate build template '" + self.glob.config['template'] + "' in " + \
                                    self.glob.lib.rel_path(self.glob.stg['template_path'] + self.glob.stg['sl'] + \
                                                            self.glob.stg['build_tmpl_dir']))
    
        self.glob.config['template'] = build_template_search


        # Error if compiler type not recongnized
        if not self.glob.modules['compiler']['type'] in self.glob.compiler.keys():
            self.glob.lib.msg.error("Unrecognized compiler type '" + self.glob.modules['compiler']['type']  + "'")

        # Get compiler cmds for gcc/intel/pgi, otherwise compiler type is unknown
        self.glob.compiler['common'] = self.glob.compiler[self.glob.modules['compiler']['type']]
        self.glob.compiler['template'] = self.glob.lib.files.find_exact(self.glob.stg['compile_tmpl_file'], \
                                                                            self.glob.stg['template_path'])
    # Combine template files and populate
    def generate_build_script(self):

        template_obj = []

        template_obj.append("#!/bin/bash \n")

        # Parse template file names
        self.set_build_files()

        # Add scheduler directives if constructing job script
        if self.glob.stg['build_mode'] == "sched":
            # Get ranks from threads (?)
            self.glob.sched['sched']['ranks'] = 1
            # Get job label
            self.glob.sched['sched']['job_label'] = self.glob.config['general']['code'] + "_build"

            # Take multiple input template files and combine them to generate unpopulated script
            self.append_to_template(template_obj, self.glob.sched['template'])

            # Add reservation line to SLURM params if set
            self.add_reservation(template_obj)

        # Timestamp
        template_obj.append("echo \"START `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        # Add standard lines to template
        self.add_standard_build_definitions(template_obj)

        # Copy user portion of build template
        self.add_user_section(template_obj, self.glob.config['template'])

        self.build_epilog(template_obj)

        # Timestamp
        template_obj.append("echo \"END `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        # Populate template list with cfg dicts
        self.glob.lib.msg.low("Populating template...")
        template_obj = self.populate_template(  [self.glob.config['metadata'], \
                                                self.glob.config['general'], \
                                                self.glob.config['modules'], \
                                                self.glob.config['config'], \
                                                self.glob.sched['sched'], \
                                                self.glob.compiler['common'], \
                                                self.glob.system], \
                                                template_obj)

        # Test for missing parameters
        self.glob.lib.msg.low("Validating template...")
        self.test_template(self.glob.tmp_job_file, template_obj)

        # Write populated script to file
        self.glob.lib.msg.low(["Writing template... ", ""])
        self.glob.lib.files.write_list_to_file(template_obj, self.glob.tmp_job_file)

    # Get template files required to construct bench script
    def set_bench_files(self):
        # Temp job script 
        self.glob.job_file = self.glob.stg['bench_job_file']
        self.glob.tmp_job_file = os.path.join(self.glob.bp_home, "tmp." + self.glob.stg['bench_job_file']) 
    
        # Scheduler template file
        if self.glob.stg['bench_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.files.find_exact(self.glob.sched['sched']['type'] + ".template", \
                                                                        os.path.join(self.glob.stg['template_path'], \
                                                                        self.glob.stg['sched_tmpl_dir']))

        # Set bench template to default, if set in bench.cfg: overload
        if self.glob.config['config']['template']:
            self.glob.config['template'] = self.glob.config['config']['template']
        else:
            self.glob.config['template'] = self.glob.config['config']['bench_label']

        matches = gb.glob(os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], "*" + \
                                        self.glob.config['template'] + "*"))
        matches.sort()

        # If more than 1 template match found
        if len(matches) > 1: 
            matches[0] = min(matches, key=len)

        # if no template match found 
        if not matches:
            self.glob.lib.msg.error("failed to locate bench template '" + self.glob.config['template'] + \
                                    "' in " + self.glob.lib.rel_path(os.path.join(self.glob.stg['template_path'], \
                                                                    self.glob.stg['bench_tmpl_dir'])))
        else:
            self.glob.config['template'] = matches[0]

        self.glob.config['metadata']['job_script'] = self.glob.config['config']['bench_label'] + "-bench." + \
                                                        self.glob.stg['bench_mode']

    # Sets the mpi_exec string for schduler or local exec modes
    def set_mpi_exec_str(self):

        # Set total ranks for schduler\
        self.glob.config['runtime']['ranks'] = int(self.glob.config['runtime']['ranks_per_node'])* \
                                                int(self.glob.config['runtime']['nodes'])

        # Standard ibrun call
        if self.glob.stg['bench_mode'] == "sched":
            self.glob.config['runtime']['mpi_exec'] = self.glob.stg['sched_mpi'] + " "

        # MPI exec for local host
        elif self.glob.stg['bench_mode'] == "local":
            self.glob.config['runtime']['mpi_exec'] = "\"" + self.glob.stg['local_mpi'] + " -np " + \
                                                str(self.glob.config['runtime']['ranks']) + " -ppn " + \
                                                str(self.glob.config['runtime']['ranks_per_node']) + \
                                                " " + self.glob.config['runtime']['host_str'] + "\""

    # Add contents of benchmark template to script
    def add_bench(self, template_obj):

        # Get template file contents
        user_script = self.read_template(self.glob.config['template']) 

        # Add start time line
        template_obj.append("#-------USER SECTION------\n\n")
        template_obj.extend(user_script)
        # Add end time line
        template_obj.append("#-------------------------\n\n")

        return template_obj

    # Combine template files and populate
    def generate_bench_script(self):

        # Find matching bench template 
        self.set_bench_files()

        # Set MPI cmd
        self.set_mpi_exec_str()

        template_obj = []

        template_obj.append("#!/bin/bash \n")

        # Create dep to running build shell on local node
        if self.glob.prev_pid:
            self.glob.config['config']['pid'] = self.glob.prev_pid
            self.add_process_dep(template_obj)  

        # If generate sched script
        if self.glob.stg['bench_mode'] == "sched":
            self.append_to_template(template_obj, self.glob.sched['template'])
            self.glob.sched['sched']['job_label'] = self.glob.config['config']['bench_label']
            self.add_reservation(template_obj)

        # Timestamp
        template_obj.append("echo \"START `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        # Add standard lines to script
        self.add_standard_bench_definitions(template_obj)

        # Add custom additions if provided
        if self.glob.config['config']['script_additions']:
            self.glob.lib.msg.low("Adding contents of '" + self.glob.lib.rel_path(self.glob.config['config']['script_additions']) + \
                                                            "' to benchmark script.")
            self.append_to_template(template_obj, self.glob.config['config']['script_additions'])
            template_obj.append("\n")

        # Stage files
        if not self.glob.stg['sync_staging']:
            self.stage_input_files(template_obj)

        # Add bench template to script
        template_obj = self.add_bench(template_obj)

        # Add epilog to end of script
        self.bench_epilog(template_obj)

        # Timestamp
        template_obj.append("echo \"END `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        self.glob.lib.msg.low("Populating template...")
        # Take multiple config dicts and populate script template
        if self.glob.stg['bench_mode'] == "sched":
            template_obj = self.populate_template([self.glob.config['metadata'], \
                                             self.glob.config['runtime'], \
                                             self.glob.config['config'], \
                                             self.glob.config['result'], \
                                             self.glob.sched['sched'], \
                                             self.glob.config['requirements'], \
                                             self.glob.system], \
                                             template_obj)
    
        else:
            template_obj = self.populate_template([self.glob.config['metadata'], \
                                            self.glob.config['runtime'], \
                                            self.glob.config['config'], \
                                            self.glob.config['result'], \
                                            self.glob.config['requirements'], \
                                            self.glob.system], \
                                            template_obj)

        self.glob.lib.msg.low("Validating template...")
        # Test for missing parameters
        self.test_template(self.glob.tmp_job_file, template_obj)

        # Write populated script to file
        self.glob.lib.msg.low(["Writing template... ", ""])
        self.glob.lib.files.write_list_to_file(template_obj, self.glob.tmp_job_file)

