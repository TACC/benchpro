#!/bin/env python3 
# Module file for benchmark reports
# April 2023
# Matthew Cawood

from datetime import datetime
import os
import time
from packaging import version


class Report():

    def read_report(self):

        self.success = True
        self.report         = self.glob.lib.report.read(self.path)
        if not self.report:
            self.success = False
            return 

        try:
            self.metadata           = self.report['metadata']
            self.version            = self.metadata['format_version']
        except:
            self.glob.msg.warn("Report " + self.path + " ")

    def __init__(self, path: str):
        self.path = path
        self.build = {}
        self.bench = {}
        self.result = {}
        self.read_report()

class Application(Report):


    def process(self):
        self.content = self.report['build']
        self.result = None

    def __init__(self, app_path: str):
        super().__init__(app_path)
        if self.success:
            self.process()
            
class Result(Report):

    def process(self):

        self.status = "OLD"
        self.complete = False
        self.value = None

        if self.success:

            self.bench = self.report['bench']
            self.result = self.report['result']
            self.unit = self.result['unit']
            self.task_id        = self.glob.lib.result.task_id(self.bench['task_id'])
            self.status         = self.glob.lib.result.status(self)
            self.complete       = self.glob.lib.result.complete(self)
            self.value          = self.glob.lib.result.retrieve(self.path)
            self.glob.lib.files.cache(self)


    def set_vars(self):
        self.stdout_path    = os.path.join(self.bench['path'], self.bench['stdout'])
        self.stderr_path    = os.path.join(self.bench['path'], self.bench['stderr'])
        self.label          = self.path.split('/')[-1]
        self.task_id        = self.glob.lib.result.task_id(self.bench['task_id'])
        self.result_id      = self.bench['result_id']
        #self.app_id         = self.glob.lib.result.app_id(self.build)
        self.dry_run        = self.glob.lib.result.dry_run(self.bench['task_id'])


    def set_stdout(self) -> None:
        if not hasattr(self, 'stdout_cont'):
            self.stdout_cont    = self.glob.lib.files.read(self.stdout_path)

    def set_stderr(self) -> None:
        if not hasattr(self, 'stderr_cont'):
            self.stderr_cont    = self.glob.lib.files.read(self.stderr_path)

    def get_stdout(self) -> str:
        self.set_stdout()
        return  self.stdout_cont

    def get_stderr(self) -> str:
        self.set_stderr()
        return self.stderr_cont



    def set_start(self) -> None:
        start_line          = self.glob.lib.files.get_timestamp("START", self.get_stdout())
        self.submit_time     = start_line.split(" ")[1]
        self.start_secs     = int(start_line.split(" ")[2])

    def set_end(self) -> None:
        end_line          = self.glob.lib.files.get_timestamp("END", self.get_stdout())
        self.end_time     = end_line.split(" ")[1]
        self.end_secs     = int(end_line.split(" ")[2])

    def get_submit_time(self) -> str:
        if not hasattr(self, 'submit_time'):
            self.set_start()
        return self.submit_time

    def get_end_time(self) -> str:
        if not hasattr(self, 'end_time'):
            self.set_end()
        return self.end_time

    def get_capture_time(self) -> str:
        return str(datetime.now())

    def get_elapsed_secs(self) -> int:
        if not hasattr(self, 'start_secs'):
            self.set_start()
        if not hasattr(self, 'end_secs'):
            self.set_end()

        return self.end_secs - self.start_secs


    def set_nodelist(self) -> None:
        if not hasattr(self, 'nodelist'):
            self.nodelist = self.glob.lib.sched.get_nodelist(self.task_id)


    def get_nodelist(self) -> str:
        self.set_nodelist()
        return ", ".join(self.nodelist)


    def __init__(self, result_path: str) -> None:
        super().__init__(result_path)

        if self.success:
            self.process()
            self.set_vars()
