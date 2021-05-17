# System Imports

import configparser as cp
from datetime import datetime
import os
import shutil as su
import sys

class init(object):
    def __init__(self, glob):
            self.glob = glob

    # Read report file into dict, accepts file path or directory path containing default report file name
    def read(self, report_file):


        # If input is not a file
        if not os.path.isfile(report_file):

            # Try append build filename
            if os.path.isfile(os.path.join(report_file, self.glob.stg['build_report_file'])):
                report_file = os.path.join(report_file, self.glob.stg['build_report_file'])

            # Try append bench filename
            elif os.path.isfile(os.path.join(report_file, self.glob.stg['bench_report_file'])): 
                report_file = os.path.join(report_file, self.glob.stg['bench_report_file'])
            # Else error
            else:
                self.glob.lib.msg.warning("Report file '" + report_file  + "' not found. Skipping.")
                return False

        report_parser    = cp.ConfigParser()
        report_parser.optionxform=str
        report_parser.read(report_file)

        # Return dict of report file sections
        return {section: dict(report_parser.items(section)) for section in report_parser.sections()}

    # Write generic report to file
    def write(self, content, report_file):
        with open(report_file, 'a') as out:
            for line in content:
                out.write(line + "\n")

    def build(self):

        # Construct content of report
        content = [ "[build]",
                    "username       = "+ self.glob.user,
                    "system         = "+ self.glob.config['general']['system'],
                    "code           = "+ self.glob.config['general']['code'],
                    "version        = "+ str(self.glob.config['general']['version']),
                    "build_label    = "+ self.glob.config['config']['build_label'],
                    "compiler       = "+ self.glob.config['modules']['compiler'],
                    "mpi            = "+ self.glob.config['modules']['mpi'],
                    "module_use     = "+ self.glob.config['general']['module_use'],
                    "modules        = "+ ", ".join(self.glob.config['modules'].values()),
                    "opt_flags      = "+ self.glob.config['config']['opt_flags'],
                    "bin_dir        = "+ self.glob.config['config']['bin_dir'],
                    "exe_file       = "+ self.glob.config['config']['exe'],
                    "build_prefix   = "+ self.glob.config['metadata']['working_path'],
                    "build_date     = "+ str(datetime.now()),
                    "script         = "+ self.glob.script_file,
                    "exec_mode      = "+ self.glob.stg['build_mode'],
                    "task_id        = "+ str(self.glob.task_id),
                    "app_id         = "+ self.glob.lib.get_application_id(),
                    "stdout         = "+ self.glob.config['config']['stdout'],
                    "stderr         = "+ self.glob.config['config']['stderr']

                  ]

        # Write content to file
        self.write(content, os.path.join(self.glob.config['metadata']['working_path'], self.glob.stg['build_report_file']))

    def bench(self):

        content = ['[build]']

        # Check if bench has application dependency
        if self.glob.build:
            # Copy contents of build report file
            if os.path.isfile(self.glob.build['build_report']):
                for key, value in self.read(self.glob.build['build_report'])['build'].items():
                        content.append(key.ljust(15) + "= " + value)
        
        # Construct content of bench report
        content.extend (["[bench]", 
                        "bench_prefix   = "+ self.glob.config['metadata']['working_path'],
                        "system         = "+ self.glob.system['sys_env'],
                        "launch_node    = "+ self.glob.hostname,
                        "nodes          = "+ self.glob.config['runtime']['nodes'],
                        "ranks          = "+ self.glob.config['runtime']['ranks_per_node'],
                        "threads        = "+ self.glob.config['runtime']['threads'],
                        "gpus           = "+ self.glob.config['runtime']['gpus'],
                        "dataset        = "+ self.glob.config['config']['dataset'],
                        "start_time     = "+ str(datetime.now()),
                        "script         = "+ self.glob.config['metadata']['job_script'],
                        "exec_mode      = "+ self.glob.stg['bench_mode'],
                        "task_id        = "+ str(self.glob.task_id),
                        "stdout         = "+ self.glob.config['config']['stdout'],
                        "stderr         = "+ self.glob.config['config']['stderr']
                        ])

        # Add result details from cfg file
        content.append("[result]")
        for key in self.glob.config['result']:
            content.append(key.ljust(15) + "= " + self.glob.config['result'][key])

        # Write content to file
        self.write(content, os.path.join(self.glob.config['metadata']['working_path'],self.glob.stg['bench_report_file']))

    # Return sched/local/dry_run from report file
    def get_exec_mode(self, job_type, report_file):

        # Path to job report file
        report_path = os.path.join(self.glob.stg['build_path'], report_file, self.glob.stg['build_report_file'])

        if job_type == "bench":
            # Path to bench report file
            report_path = os.path.join(self.glob.stg['pending_path'], report_file, self.glob.stg['bench_report_file'])

        # Get exec_mode from report file
        return self.read(report_path)[job_type]['exec_mode']

    # Return task_id value from provided report directory
    def get_task_id(self, job_type, report_file):

        # Path to job report file
        report_path = os.path.join(self.glob.stg['build_path'], report_file, self.glob.stg['build_report_file'])
        if job_type == "bench":
            # Path to bench report file
            report_path = os.path.join(self.glob.stg['pending_path'], report_file, self.glob.stg['bench_report_file'])

        if os.path.isfile(report_path):
            return self.read(report_path)[job_type]['task_id']

        return False

    # Return the binary executable value from provided build path
    def build_exe(self, build_path):
        report_path = os.path.join(self.glob.stg['build_path'], build_path, self.glob.stg['build_report_file'])

        if os.path.isfile(report_path):
            return self.read(report_path)['build']['bin_dir'], self.read(report_path)['build']['exe_file']
        return False, False


