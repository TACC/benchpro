# System Imports
import copy
import glob as gb
import os
import shutil as su
import sys

class init(object):
    def __init__(self, glob):
            self.glob = glob

    def read_template(self, input_template):
        # Check template file is defined - handles None type (in case of unknown compiler type = None compiler template)
        if input_template:
            self.glob.log.debug("Reading template file " + input_template)
            # Test if input template file exists
            if not os.path.exists(input_template):
                self.glob.lib.msg.error("failed to locate template file '" + input_template + "' in " + self.glob.lib.rel_path(self.glob.stg['template_path'])  + ".")

            template = []
            # Copy input template file to temp obj
            with open(input_template, 'r') as fd:
                template = fd.readlines()

            return template             

    # Combines list of input templates to single script file
    def construct_template(self, template_obj, input_template):
            # Copy input template file to temp obj
            with open(input_template, 'r') as fd:
                template_obj.extend(self.read_template(input_template))

    # Add sched reservation
    def add_reservation(self, template_obj):
        if self.glob.sched['sched']['reservation']:
                template_obj.append("#SBATCH --reservation=" + self.glob.sched['sched']['reservation'] + "\n")

    # Add standard lines to build template
    def add_standard_build_definitions(self, template_obj):
    
        header_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir'], self.glob.stg['header_file'])
        self.construct_template(template_obj, header_template)

        # export module names
        for mod in self.glob.config['modules']:
            template_obj.append("export" + mod.rjust(15) + "=" + self.glob.config['modules'][mod] + "\n")

        template_obj.append("\n")
        template_obj.append("# Load modules \n")
        template_obj.append("ml reset \n")
        
        # add 'module use' if set
        if self.glob.config['general']['module_use']:
            template_obj.append("ml use " + self.glob.config['general']['module_use'] + "\n")

        # Add non Null modules 
        for mod in self.glob.config['modules']:
            if self.glob.config['modules'][mod]:
                template_obj.append("ml $" + mod + "\n")

        template_obj.append("ml \n")

    # Add standard lines to bench template
    def add_standard_bench_definitions(self, template_obj):
        header_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], self.glob.stg['header_file'])
        self.construct_template(template_obj, header_template)

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

    # If the setting in enabled, add the provenance data collection script to the script
    def collect_stats(self, template_obj):
        if self.glob.config['config']['collect_stats']:
            if self.glob.lib.file_owner(os.path.join(self.glob.stg['utils_path'], "lshw")) == "root":
                template_obj.append("\n# Provenance data collection script \n")
                template_obj.append(os.path.join(self.glob.stg['src_path'], "collect_hw_info.sh") + " " + \
                                    self.glob.stg['utils_path'] + " " + 
                                    os.path.join(self.glob.config['metadata']['working_path'], "hw_report") + "\n")
            else:
                self.glob.lib.msg.warning(["Requested hardware stats but script permissions not set",
                                                "Run 'sudo -E $BENCHTOOL/resources/scripts/change_permissions.sh'"])

    # Add things to the bottom of the build script
    def build_epilog(self, template_obj):

        # Add sanity check
        if self.glob.config['config']['exe']:
            template_obj.append("ldd " + os.path.join("${install_path}", self.glob.config['config']['bin_dir'], self.glob.config['config']['exe']) + " \n")

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
        self.glob.log.debug("Populating template file " + self.glob.tmp_script)
        # For each config dict
        for cfg in cfg_dicts:
            # For each key, find and replace <<<key>>> in template file
            for key in cfg:
                template_obj = [line.replace("<<<" + str(key) + ">>>", str(cfg[key])) for line in template_obj]
                self.glob.log.debug("Replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))

        return template_obj

    # Get template files required to constuct build script
    def set_build_files(self):
        # Temp build script
        self.glob.script_file = self.glob.config['general']['code'] + "-build." + self.glob.stg['build_mode']
        self.glob.tmp_script = os.path.join(self.glob.basedir, "tmp." + self.glob.script_file)

        if self.glob.stg['build_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.find_exact(self.glob.sched['sched']['type'] + ".template", self.glob.stg['template_path'])

        # Get application template file name from cfg, otherwise use cfg_label to look for it
        if self.glob.config['general']['template']:
            self.glob.config['template'] = self.glob.config['general']['template']
        else:
            self.glob.config['template'] = self.glob.config['metadata']['cfg_label']

        # Search for application template file
        build_template_search = self.glob.lib.find_partial(self.glob.config['template'], os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir']))

        # Error if not found
        if not build_template_search:
            self.glob.lib.msg.error("failed to locate build template '" + self.glob.config['template'] + "' in " + \
                                    self.glob.lib.rel_path(self.glob.stg['template_path'] + self.glob.stg['sl'] + self.glob.stg['build_tmpl_dir']))
    
        self.glob.config['template'] = build_template_search

        # Get compiler cmds for gcc/intel/pgi, otherwise compiler type is unknown
        known_compiler_type = True
        try:
            self.glob.compiler['common'] = self.glob.compiler[self.glob.config['config']['compiler_type']]
            self.glob.compiler['template'] = self.glob.lib.find_exact(self.glob.stg['compile_tmpl_file'], self.glob.stg['template_path'])
        except:
            known_compiler_type = False
            self.glob.compiler['template'] = None

    # Combine template files and populate
    def generate_build_script(self):

        template_obj = []

        template_obj.append("#!/bin/bash \n")

        # Parse template file names
        self.set_build_files()

        # Add scheduler directives if contructing job script
        if self.glob.stg['build_mode'] == "sched":
            # Get ranks from threads (?)
            self.glob.sched['sched']['ranks'] = 1
            # Get job label
            self.glob.sched['sched']['job_label'] = self.glob.config['general']['code'] + "_build"

            # Take multiple input template files and combine them to generate unpopulated script
            self.construct_template(template_obj, self.glob.sched['template'])

            # Add reservation line to SLURM params if set
            self.add_reservation(template_obj)

        # Add standard lines to template
        self.add_standard_build_definitions(template_obj)

        self.construct_template(template_obj, self.glob.compiler['template'])
        self.construct_template(template_obj, self.glob.config['template'])

        self.build_epilog(template_obj)

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
        self.glob.lib.test_template(self.glob.tmp_script, template_obj)

        # Write populated script to file
        self.glob.lib.msg.low(["Writing template... ", ""])
        self.glob.lib.write_list_to_file(template_obj, self.glob.tmp_script)

    # Get template files required to construct bench script
    def set_bench_files(self):
        # Temp job script 
        self.glob.script_file = self.glob.config['config']['bench_label']  + "-bench." + self.glob.stg['bench_mode']
        self.glob.tmp_script = os.path.join(self.glob.basedir, "tmp." + self.glob.script_file) 
    
        # Scheduler template file
        if self.glob.stg['bench_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.find_exact(self.glob.sched['sched']['type'] + ".template", os.path.join(self.glob.stg['template_path'], self.glob.stg['sched_tmpl_dir']))

        # Set bench template to default, if set in bench.cfg: overload
        if self.glob.config['config']['template']:
            self.glob.config['template'] = self.glob.config['config']['template']
        else:
            self.glob.config['template'] = self.glob.config['config']['bench_label']

        matches = gb.glob(os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], "*" + self.glob.config['template'] + "*"))
        matches.sort()

        # If more than 1 template match found
        if len(matches) > 1: 
            matches[0] = min(matches, key=len)

        # if no template match found 
        if not matches:
            self.glob.lib.msg.error("failed to locate bench template '" + self.glob.config['template'] + "' in " + self.glob.lib.rel_path(os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'])))
        else:
            self.glob.config['template'] = matches[0]

        self.glob.config['metadata']['job_script'] = self.glob.config['config']['bench_label'] + "-bench." + self.glob.stg['bench_mode']

    # If requested multiple runs, check for supporting syntax in template
    def get_bench_pagmas(self, template):
        # Get line number of @start and @end in benchmark template file
        start = [i for i, s in enumerate(template) if '@start' in s]
        end = [i for i, s in enumerate(template) if '@end' in s]

        if not len(start) or not len(end):
            self.glob.lib.msg.error("Multiple tasks per job were requested but '@start' and/or '@end' are missing from the benchmark template")

        return start[0], end[0]
  
    # Sets the mpi_exec string for schduler or local exec modes
    def set_mpi_exec_str(self):

        # Set total ranks for schduler\
        self.glob.config['runtime']['ranks'] = int(self.glob.config['runtime']['ranks_per_node'])*int(self.glob.config['runtime']['nodes'])

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
        template = self.read_template(self.glob.config['template']) 

        #self.glob.lib.expr.eval_dict(self.glob.config['runtime'])

        # Add start time line
        template_obj.append("echo \"START `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")
        template_obj.extend(template)
        # Add end time line
        template_obj.append("echo \"END `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

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
            self.construct_template(template_obj, self.glob.sched['template'])
            self.add_reservation(template_obj)

        # Add standard lines to script
        self.add_standard_bench_definitions(template_obj)

        # Add custom additions if provided
        if self.glob.config['config']['script_additions']:
            self.glob.lib.msg.low("Adding contents of '" + self.glob.lib.rel_path(self.glob.config['config']['script_additions']) + "' to benchmark script.")
            self.construct_template(template_obj, self.glob.config['config']['script_additions'])
            template_obj.append("\n")

        # Add bench template to script
        template_obj = self.add_bench(template_obj)

        # Add epilog to end of script
        self.bench_epilog(template_obj)

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
        self.glob.lib.test_template(self.glob.tmp_script, template_obj)

        # Write populated script to file
        self.glob.lib.msg.low(["Writing template... ", ""])
        self.glob.lib.write_list_to_file(template_obj, self.glob.tmp_script)

