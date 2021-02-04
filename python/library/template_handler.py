# System Imports
import glob as gb
import os
import shutil as su
import sys

# Local Imports
import exception

class init(object):
    def __init__(self, glob):
            self.glob = glob

    # Combines list of input templates to single script file
    def construct_template(self, template_obj, input_template):

        # Check template file is defined - handles None type (in case of unknown compiler type = None compiler template)
        if input_template:
            self.glob.log.debug("Ingesting template file " + input_template)
            # Test if input template file exists
            if not os.path.exists(input_template):
                exception.error_and_quit(self.glob.log, "failed to locate template file '" + input_template + "' in " + self.glob.lib.rel_path(self.glob.stg['template_path'])  + ".")

            # Copy input template file to temp obj
            with open(input_template, 'r') as fd:
                template_obj.extend(fd.readlines())

    # Add sched reservation
    def add_reservation(self, template_obj):

        if self.glob.sched['sched']['reservation']:
                template_obj.append("#SBATCH --reservation=" + self.glob.sched['sched']['reservation'] + "\n")

    # Add standard lines to build template
    def add_standard_build_definitions(self, template_obj):
    
        default_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir'], "default.template")
        self.construct_template(template_obj, default_template)

        # export module names
        for mod in self.glob.code['modules']:
            template_obj.append("export" + mod.rjust(15) + "=" + self.glob.code['modules'][mod] + "\n")

        template_obj.append("\n")
        template_obj.append("# Load modules \n")
        template_obj.append("ml reset \n")
        
        # add 'module use' if set
        if self.glob.code['general']['module_use']:
            template_obj.append("ml use " + self.glob.code['general']['module_use'] + "\n")

        # Add non Null modules 
        for mod in self.glob.code['modules']:
            if self.glob.code['modules'][mod]:
                template_obj.append("ml $" + mod + "\n")

        template_obj.append("ml \n")
        template_obj.append("\n")
        template_obj.append("# Create application directories\n")
        template_obj.append("mkdir -p ${build_path} \n")
        template_obj.append("mkdir -p ${install_path} \n")

    # Add standard lines to bench template
    def add_standard_bench_definitions(self, template_obj):
        default_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], "default.template")
        self.construct_template(template_obj, default_template)

    # Add things to the bottom of the build script
    def template_epilog(self, template_obj):

        # Add sanity check
        if self.glob.code['config']['exe']:
            template_obj.append("ldd " + os.path.join("${install_path}", self.glob.code['config']['bin_dir'], self.glob.code['config']['exe']) + " \n")

        # Add hardware collection script to job script
        if self.glob.code['config']['collect_hw_stats']:
            if self.glob.lib.file_owner(os.path.join(self.glob.stg['utils_path'], "lshw")) == "root":
                template_obj.append(self.glob.stg['src_path'] + self.glob.stg['sl'] + "collect_hw_info.sh " + self.glob.stg['utils_path'] + " " + \
                                self.glob.code['metadata']['working_path'] + self.glob.stg['sl'] + "hw_report" + "\n")
            else:
                exception.print_warning(self.glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")

    # Add dependency to build process (if building locally)
    def add_process_dep(self, template_obj):

        self.glob.log.debug("Adding dependency to benchmark script, waiting for PID: " + self.glob.prev_pid)

        dep_file = os.path.join(self.glob.stg['template_path'], self.glob.stg['pid_dep_file'])
        if os.path.isfile(dep_file):
            with open(dep_file, 'r') as fd:
                template_obj.extend(fd.readlines())

        else:
            exception.error_and_quit(self.glob.log, "unable to read pid dependency template " + self.glob.lib.rel_path(dep_file))

    # Contextualizes template script with variables from a list of config dicts
    def populate_template(self, cfg_dicts, template_obj):
        self.glob.log.debug("Populating template file " + self.glob.tmp_script)
        # For each config dict
        for cfg in cfg_dicts:
            # For each key, find and replace <<<key>>> in template file
            for key in cfg:
                template_obj = [line.replace("<<<" + str(key) + ">>>", str(cfg[key])) for line in template_obj]
                self.glob.log.debug("replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))

        return template_obj

    def set_build_files(self):

        # Temp build script
        self.glob.tmp_script = "tmp." + self.glob.code['general']['code'] + "-build." + self.glob.stg['build_mode']
        # === Scheduler template file ===

        if self.glob.stg['build_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.find_exact(self.glob.sched['sched']['type'] + ".template", self.glob.stg['template_path'])

        # === Application template file ===

        # Get application template file name from cfg, otherwise use cfg_label to look for it
        if self.glob.code['general']['template']:
            self.glob.code['template'] = self.glob.code['general']['template']
        else:
            self.glob.code['template'] = self.glob.code['metadata']['cfg_label']

        # Search for application template file
        build_template_search = self.glob.lib.find_partial(self.glob.code['template'], os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir']))

        # Error if not found
        if not build_template_search:
            exception.error_and_quit(self.glob.log, "failed to locate build template '" + self.glob.code['template'] + "' in " + \
                                    self.glob.lib.rel_path(self.glob.stg['template_path'] + self.glob.stg['sl'] + self.glob.stg['build_tmpl_dir']))
    
        self.glob.code['template'] = build_template_search


        # === Compiler template file ===

        # Get compiler cmds for gcc/intel/pgi, otherwise compiler type is unknown
        known_compiler_type = True
        try:
            self.glob.compiler['self.glob.lib'].update(self.glob.compiler[self.glob.code['config']['compiler_type']])
            self.glob.compiler['template'] = self.glob.lib.find_exact(self.glob.stg['compile_tmpl_file'], self.glob.stg['template_path'])
        except:
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
            self.glob.sched['sched']['job_label'] = self.glob.code['general']['code'] + "_build"


            # Take multiple input template files and combine them to generate unpopulated script
            self.construct_template(template_obj, self.glob.sched['template'])

            # Add reservation line to SLURM params if set
            self.add_reservation(template_obj)

        # Add standard lines to template
        self.add_standard_build_definitions(template_obj)

        self.construct_template(template_obj, self.glob.compiler['template'])
        self.construct_template(template_obj, self.glob.code['template'])

        self.template_epilog(template_obj)

        # Populate template list with cfg dicts
        print("Populating template...")
        template_obj = self.populate_template(  [self.glob.code['metadata'], \
                                                self.glob.code['general'], \
                                                self.glob.code['modules'], \
                                                self.glob.code['config'], \
                                                self.glob.sched['sched'], \
                                                self.glob.compiler['common']], \
                                                template_obj)


        template_obj.append("date \n")

        # Test for missing parameters
        print("Validating template...")
        self.glob.lib.test_template(self.glob.tmp_script, template_obj)

        # Write populated script to file
        print("Writing template... ")
        self.glob.lib.write_list_to_file(template_obj, self.glob.tmp_script)
        print()

    def set_bench_files(self):
        # Template files

        # Temp job script 
        self.glob.tmp_script = "tmp." + self.glob.code['config']['bench_label']  + "-bench." + self.glob.stg['bench_mode'] 
    
        # Scheduler template file
        if self.glob.stg['bench_mode'] == "sched":
            self.glob.sched['template'] = self.glob.lib.find_exact(self.glob.sched['sched']['type'] + ".template", os.path.join(self.glob.stg['template_path'], self.glob.stg['sched_tmpl_dir']))

        # Set bench template to default, if set in bench.cfg: overload
        if self.glob.code['config']['template']:
            self.glob.code['template'] = self.glob.code['config']['template']
        else:
            self.glob.code['template'] = self.glob.code['config']['bench_label']

        matches = gb.glob(os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'], "*" + self.glob.code['template'] + "*"))
        matches.sort()

        # If more than 1 template match found
        if len(matches) > 1: 
            matches[0] = min(matches, key=len)

        # if no template match found 
        if not matches:
            exception.error_and_quit(self.glob.log, "failed to locate bench template '" + self.glob.code['template'] + "' in " + self.glob.lib.rel_path(os.path.join(self.glob.stg['template_path'], self.glob.stg['bench_tmpl_dir'])))
        else:
            self.glob.code['template'] = matches[0]

        self.glob.code['metadata']['job_script'] = self.glob.code['config']['bench_label'] + "-bench." + self.glob.stg['bench_mode']


    def generate_bench_script(self):

        template_obj = []

        template_obj.append("#!/bin/bash \n")

        # Create dep to running build shell on local node
        if self.glob.prev_pid:
            self.glob.code['config']['pid'] = self.glob.prev_pid
            self.add_process_dep(template_obj)  

        self.set_bench_files()

        # If generate sched script
        if self.glob.stg['bench_mode'] == "sched":
            self.construct_template(template_obj, self.glob.sched['template'])
            self.add_reservation(template_obj)

  
        # Add start time line
        template_obj.append("echo \"START `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        # Add standard lines to script
        self.add_standard_bench_definitions(template_obj)

        # Add bench templat to script
        self.construct_template(template_obj, self.glob.code['template'])

        # Add hardware collection script to job script
        if self.glob.code['config']['collect_hw_stats']:
            if self.glob.lib.file_owner(os.path.join(self.glob.stg['utils_path'], "lshw")) == "root":
                template_obj.append(os.path.join(self.glob.stg['src_path'], "collect_hw_info.sh " + self.glob.stg['utils_path'] + " " + self.glob.code['metadata']['working_path'], "hw_report \n"))
            else:
                exception.print_warning(self.glob.log, "Requested hardware stats but persmissions not set, run 'sudo hw_utils/change_permissions.sh'")

        template_obj.append("date \n")

        print("Populating template...")
        # Take multiple config dicts and populate script template
        if self.glob.stg['bench_mode'] == "sched":
            template_obj = self.populate_template([self.glob.code['metadata'], \
                                             self.glob.code['runtime'], \
                                             self.glob.code['config'], \
                                             self.glob.code['result'], \
                                             self.glob.sched['sched'], \
                                             self.glob.code['requirements']], \
                                             template_obj)
    
        else:
            template_obj = self.populate_template([self.glob.code['metadata'], \
                                            self.glob.code['runtime'], \
                                            self.glob.code['config'], \
                                            self.glob.code['result'], \
                                            self.glob.code['requirements']], \
                                            template_obj)

        # Add end time line
        template_obj.append("echo \"END `date +\"%Y\"-%m-%dT%T` `date +\"%s\"`\" \n")

        print("Validating template...")
        # Test for missing parameters
        self.glob.lib.test_template(self.glob.tmp_script, template_obj)

        # Write populated script to file
        print("Writing template... ")
        self.glob.lib.write_list_to_file(template_obj, self.glob.tmp_script)
        print()

