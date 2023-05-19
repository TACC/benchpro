# System Imports
import os
import sys
import subprocess

class init(object):
    def __init__(self, glob):
            self.glob = glob

    # Run script in shell
    def start_local_shell(self):

        # Path to bash script
        script_path = os.path.join(self.glob.config['metadata']['working_path'], self.glob.job_file)
        self.glob.lib.msg.low("Starting script: " + self.glob.lib.rel_path(script_path))

        # Get full paths for redirection
        stdout_path = os.path.join(self.glob.config['metadata']['working_path'], self.glob.config['config']['stdout'])
        stderr_path = os.path.join(self.glob.config['metadata']['working_path'], self.glob.config['config']['stderr'])
        try:
            # Redirect stdout and stderr to files
            with open(stdout_path, 'wb') as out_file, open(stderr_path, 'wb') as err_file:

                # Start bash script
                cmd = subprocess.Popen(['bash', script_path], stdout=out_file, stderr=err_file)
                # Store PID
                self.glob.prev_pid = cmd.pid

        except subprocess.CalledProcessError as e:
            print(e)
            self.glob.lib.msg.error("failed to start script in local shell.")

        self.glob.lib.msg.low("Script started on local machine.")

    # Check if pid is running or not
    def complete(self, pid: int) -> bool:
        # Check for pid in /proc
        if os.path.isdir(os.path.join("/proc", str(pid))):
            return False
        return True


    def task_status(self, pid: str) -> str:
        if self.complete(pid):
            return "COMPLETED"
        return "RUNNING"


    # Display local shells to assist with determining if local job is still busy
    def print_local_pid(self, pid):

        try:
            cmd = subprocess.run("ps -aux | grep " + pid, shell=True,
                                    check=True, capture_output=True, universal_newlines=True)

        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.error("Failed to run 'ps -aux'")

        for line in cmd.stdout.split("\n"):
            if "bash" in line:
                print(" " + line)

