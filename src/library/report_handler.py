# System Imports

import configparser as cp
from datetime import datetime
import os
import shutil as su
import sys
import time

class init(object):
    def __init__(self, glob):
            self.glob = glob


    # Read report file into dict, accepts file path or directory path containing default report file name
    def ingest(self, report_file):

        report_parser    = cp.ConfigParser()
        report_parser.optionxform=str
        report_parser.read(report_file)

        # Return dict of report file sections
        report_dict = {section: dict(report_parser.items(section)) for section in report_parser.sections()}
        return report_dict

    def report_file(self, report_path: str) -> str:

        report_file = None
        # Try append build filename
        if os.path.isfile(os.path.join(report_path, self.glob.stg['build_report_file'])):
            report_file = os.path.join(report_path, self.glob.stg['build_report_file'])

        # Try append bench filename
        elif os.path.isfile(os.path.join(report_path, self.glob.stg['bench_report_file'])):
            report_file = os.path.join(report_path, self.glob.stg['bench_report_file'])
        # Else error
        else:
            self.glob.lib.msg.log("Report file not found in '" + self.glob.lib.rel_path(report_path)  + "'. Skipping.")
            return False
        return report_file

    
    def read(self, report_path: str):

        report_file = self.report_file(report_path)
        if not report_file:
            return False

        # Read report file from disk
        report = self.ingest(report_file)
        return report


        # Compatible report
        #if self.glob.lib.version.compat_report(report):
        #    return report
        # Incompatible
        #else:
        #    self.glob.lib.msg.high("This report file is no longer compatible.")
        #    return False


    # Write generic report to file
    def write(self, content, report_file):
        with open(report_file, 'a') as out:
            for line in content:
                out.write(line + "\n")


    def build(self):

        self.glob.session_id = self.glob.lib.get_unique_id(10)

        # Construct content of report
        content = self.glob.lib.version.report_metadata()
        content.extend( 
                    [ "[build]",
                    "app_id         = "+ self.glob.session_id,
                    "username       = "+ self.glob.user,
                    "system         = "+ self.glob.config['general']['system'],
                    "arch           = "+ self.glob.config['config']['arch'],
                    "code           = "+ self.glob.config['general']['code'],
                    "version        = "+ str(self.glob.config['general']['version']),
                    "build_label    = "+ self.glob.config['config']['build_label'],
                    "compiler       = "+ self.glob.modules['compiler']['full'],
                    "mpi            = "+ self.glob.modules['mpi']['full'],
                    "module_use     = "+ self.glob.config['general']['module_use'],
                    "modules        = "+ ", ".join([self.glob.modules[module]['full'] for module in self.glob.modules.keys()]),
                    "opt_flags      = "+ self.glob.config['config']['opt_flags'],
                    "threads        = "+ str(self.glob.sched['sched']['threads']),
                    "bin_dir        = "+ self.glob.config['config']['bin_dir'],
                    "exe_file       = "+ self.glob.config['config']['exe'],
                    "path           = "+ self.glob.config['metadata']['working_path'],
                    "submit_time    = "+ str(datetime.now().strftime("%Y-%m-%d %H:%M")),
                    "script         = "+ self.glob.job_file,
                    "exec_mode      = "+ self.glob.stg['exec_mode'],
                    "task_id        = "+ str(self.glob.task_id),
                    "stdout         = "+ self.glob.config['config']['stdout'],
                    "stderr         = "+ self.glob.config['config']['stderr']

                  ])

        # Write content to file
        self.write(content, os.path.join(self.glob.config['metadata']['working_path'], self.glob.stg['build_report_file']))

    def bench(self):

        self.glob.session_id = self.glob.lib.get_unique_id(12)

        content = self.glob.lib.version.report_metadata()

        # Check if bench has application dependency
        if self.glob.build_report:

            content.append('[build]')
            # Copy contents of build report file
            for key in self.glob.build_report:
                content.append(key.ljust(15) + "= " + self.glob.build_report[key])

        # Construct content of bench report
        content.extend (["[bench]", 
                        "result_id      = "+ self.glob.session_id,
                        "path           = "+ self.glob.config['metadata']['working_path'],
                        "system         = "+ self.glob.system['system'],
                        "launch_node    = "+ self.glob.hostname,
                        "nodes          = "+ str(self.glob.config['runtime']['nodes']),
                        "ranks          = "+ str(self.glob.config['runtime']['ranks_per_node']),
                        "threads        = "+ str(self.glob.config['runtime']['threads']),
                        "gpus           = "+ str(self.glob.config['runtime']['gpus']),
                        "dataset        = "+ self.glob.config['config']['dataset'],
                        "bench_label    = "+ self.glob.config['config']['bench_label'],
                        "submit_time    = "+ str(datetime.now().strftime("%Y-%m-%d %H:%M")),
                        "script         = "+ self.glob.config['metadata']['job_script'],
                        "exec_mode      = "+ self.glob.stg['exec_mode'],
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

        # Get exec_mode from report file
        report = self.read(report_file)
        if report:
            return report[job_type]['exec_mode']

    # Return task_id value from provided report directory
    def get_task_id(self, job_type, report_file):
        return self.read(report_file)[job_type]['task_id']

    # Return the binary executable value from provided build path
    def get_build_exe(self, report_path):
       return self.read(report_path)['build']['bin_dir'], self.read(report_path)['build']['exe_file']


    def get_build_user(self, report_path):
       return self.read(report_path)['build']['username']

