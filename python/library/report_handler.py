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
                    "system         = "+ self.glob.code['general']['system'],
                    "code           = "+ self.glob.code['general']['code'],
                    "version        = "+ str(self.glob.code['general']['version']),
                    "build_label    = "+ self.glob.code['config']['build_label'],
                    "compiler       = "+ self.glob.code['modules']['compiler'],
                    "mpi            = "+ self.glob.code['modules']['mpi'],
                    "module_use     = "+ self.glob.code['general']['module_use'],
                    "modules        = "+ ", ".join(self.glob.code['modules'].values()),
                    "opt_flags      = "+ self.glob.code['config']['opt_flags'],
                    "exe_file       = "+ self.glob.code['config']['exe'],
                    "build_prefix   = "+ self.glob.code['metadata']['working_path'],
                    "build_date     = "+ str(datetime.now()),
                    "jobid          = "+ self.glob.jobid,
                    "app_id         = "+ self.glob.lib.get_application_id()
                  ]

        # Write content to file
        self.write(content, os.path.join(self.glob.code['metadata']['working_path'], self.glob.stg['build_report_file']))

    def bench(self):

        content = ['[build]']

        # Copy contents of build report file
        if os.path.isfile(self.glob.build['build_report']):
            for key, value in self.read(self.glob.build['build_report'])['build'].items():
                    content.append(key.ljust(15) + "= " + value)
        
        # Construct content of bench report
        content.extend (["[bench]", 
                        "bench_prefix   = "+ self.glob.code['metadata']['working_path'],
                        "system         = "+ self.glob.system['sys_env'],
                        "launch node    = "+ self.glob.hostname,
                        "nodes          = "+ self.glob.code['runtime']['nodes'],
                        "ranks          = "+ self.glob.code['runtime']['ranks_per_node'],
                        "threads        = "+ self.glob.code['runtime']['threads'],
                        "gpus           = "+ self.glob.code['runtime']['gpus'],
                        "dataset        = "+ self.glob.code['config']['dataset'],
                        "start_time     = "+ str(datetime.now()),
                        "job_script     = "+ self.glob.code['metadata']['job_script'],
                        "jobid          = "+ self.glob.jobid
                        ])

        # Add stdout/err for sched jobs
        if not self.glob.jobid == "dry_run":
            content.append("stdout         = "+ self.glob.jobid+".out")
            content.append("stderr         = "+ self.glob.jobid+".err")

        # Add result details from cfg file
        content.append("[result]")
        for key in self.glob.code['result']:
            content.append(key.ljust(15) + "= " + self.glob.code['result'][key])

        # Write content to file
        self.write(content, os.path.join(self.glob.code['metadata']['working_path'],self.glob.stg['bench_report_file']))

    # Return jobid value from provided report directory
    def get_jobid(self, job_type, report_file):

        report_path = os.path.join(self.glob.stg['build_path'], report_file, self.glob.stg['build_report_file'])
        if job_type == "bench":
            report_path = os.path.join(self.glob.stg['pending_path'], report_file, self.glob.stg['bench_report_file'])

        if os.path.isfile(report_path):
            return self.read(report_path)[job_type]['jobid']
        return False

    # Return the binary executable value from provided build path
    def build_exe(self, build_path):
        report_path = os.path.join(self.glob.stg['build_path'], build_path, self.glob.stg['build_report_file'])

        if os.path.isfile(report_path):
            return self.read(report_path)['build']['exe_file']
        return False

    # Confirm required values are in report
    def test_report(self):
        print()



