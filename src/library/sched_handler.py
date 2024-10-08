# System Imports
import os
import sys
import subprocess
import time

class init(object):
    def __init__(self, glob):
            self.glob = glob

    # Run schduler related command 
    def slurm_exec(self, cmd_line):

        try:
            cmd = subprocess.run(cmd_line, shell=True, check=True, \
                                    capture_output=True, universal_newlines=True)

        # If command failed
        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.log(e.output.split("\n"))
            return False, "", e.output.split("\n")

        # If command succeeded
        return True, cmd.stdout, cmd.stderr

    # Return job status for job ID
    def task_status(self, jobid: int) -> str:

            # Assume dry run jobs are complete
            if "dry" in str(jobid):
                return "COMPLETED"

            # Local jobs
            if "local" in str(jobid):
                return "COMPLETED"

            # Query Slurm slurm accounting with job ID
            success, stdout, stderr = self.slurm_exec("sacct -j " + str(jobid) + " --format State")
            if success:
                # Strip out bad chars from job state
                if (len(stdout.split("\n")) > 2):
                    return ''.join(c for c in stdout.split("\n")[2] if c not in [' ', '*', '+'])
            
            return "UNKNOWN"

    # If build job is running, add dependency str
    def get_build_job_dependency(self):

        # Build job exec_mode=sched
        if self.glob.build_report['exec_mode'] == "sched":
            if not self.glob.lib.sched.check_job_complete(self.glob.build_report['task_id']):
                self.glob.ok_dep_list.append(self.glob.build_report['task_id'])

        # Build job exec_mode=local
        elif self.glob.build_report['exec_mode'] == "local":
            if not self.glob.lib.proc.complete(self.glob.build_report['task_id']):
                self.glob.prev_pid = self.glob.build_report['task_id']

    # Check that job ID is not running
    def check_job_complete(self, jobid):

        # Strip out bad chars from job state
        state = self.task_status(jobid)

        # Job COMPLETE
        if any (state == x for x in ["COMPLETED", "CANCELLED", "ERROR", "FAILED", "TIMEOUT", "UNKNOWN"]):
            return state
        # Job RUNNING or PENDING
        return False


    # Get Job IDs of RUNNING AND PENDNIG jobs
    def get_active_jobids(self, job_label):
        # Get list of jobs from sacct
        running_jobs_list = []
        job_list = None

        success, stdout, stderr = self.slurm_exec("sacct -u " + self.glob.user)
        job_list = stdout.split("\n")

        # Add RUNNING job IDs to list
        for job in job_list:
            if "RUNNING" in job or "PENDING" in job:
                # Check if job label matches
                if job_label in job:
                    running_jobs_list.append(int(job.split(" ")[0]))

        # Sort
        running_jobs_list.sort()
        return running_jobs_list


    # Get node suffixes from brackets: "[094-096]" => ['094', '095', '096']
    def expand_range(self, suffix_str):
        suffix_list = []
        for suf in suffix_str.split(','):
            if '-' in suf:
                start, end = suf.split('-')
                tmp = range(int(start), int(end)+1)
                tmp = [str(t).zfill(3) for t in tmp]
                suffix_list.extend(tmp)
            else:
                suffix_list.append(suf)
        return suffix_list

    # Parse SLURM nodelist to list: "c478-[094,102],c479-[032,094]" => ['c478-094', 'c478-102', 'c479-032', 'c479-094']
    def parse_nodelist(self, slurm_nodes):
        node_list = []
        while slurm_nodes:
            prefix_len = 4
            # Expand brackets first
            if '[' in slurm_nodes:
                # Get position of first '[' and ']'
                start = slurm_nodes.index('[')+1
                end = slurm_nodes.index(']')
                # Get node prefix for brackets, eg 'c478-'
                prefix = slurm_nodes[start-6:start-1]
                # Expand brackets
                suffix = self.expand_range(slurm_nodes[start:end])
                node_list.extend([prefix + s for s in suffix])
                # Remove parsed nodes
                slurm_nodes = slurm_nodes[:start-6] + slurm_nodes[end+2:]
            # Extract remaining nodes
            else:
                additions = slurm_nodes.split(',')
                node_list.extend([s.strip() for s in additions])
                slurm_nodes = None

        node_list.sort()
        return node_list

    # Get NODELIST from sacct  using JOBID
    def get_nodelist(self, jobid: int) -> str:

        success, stdout, stderr = self.slurm_exec("sacct -X -P -j  " + str(jobid) + " --format NodeList")
        if success:
            return self.parse_nodelist(stdout.split("\n")[1])

        return ""

    # Set job dependency if max_running_jobs is reached
    def get_dep_str(self):

        dep = ""

        if self.glob.any_dep_list:
            dep += "--dependency=afterany:" + ":".join([str(x) for x in self.glob.any_dep_list]) + " "

        if self.glob.ok_dep_list:
            dep += "--dependency=afterok:" + ":".join([str(x) for x in self.glob.ok_dep_list]) + " " 

        if dep:
            self.glob.lib.msg.low("Job dependency string: " + dep)

        return dep

    # Submit script to scheduler
    def submit(self):

        script_path = os.path.join(self.glob.config['metadata']['working_path'], self.glob.job_file)
        self.glob.lib.msg.low(["Job script:",
                                ">  " + self.glob.lib.rel_path(script_path),
                                "",
                                "Submitting to scheduler..."])

        success, stdout, stderr = self.slurm_exec("sbatch " + self.get_dep_str() + script_path)

        if not success:
            self.glob.lib.msg.error(["failed to submit job to scheduler:"] + stderr)

        self.glob.lib.msg.log(stdout)
        self.glob.lib.msg.log(stderr)

        jobid = None
        jobid_line = "Submitted batch job"
        
        # Find job ID
        for line in stdout.splitlines():
            if jobid_line in line:
                jobid = line.split(" ")[-1]

        # Wait for slurm to queue job
        time.sleep(1)
            
        # Get job in queue
        success, stdout, stderr = self.slurm_exec("squeue -a --job " + jobid)

        self.glob.lib.msg.low(stdout.split("\n") +
                    ["",
                    "Job stdout:",
                    ">  "+ self.glob.lib.rel_path(
                        os.path.join(self.glob.config['metadata']['working_path'], 
                                     self.glob.config['config']['stdout'])),
                    "Job stderr:",
                    ">  "+ self.glob.lib.rel_path(
                        os.path.join(self.glob.config['metadata']['working_path'], 
                                     self.glob.config['config']['stderr']))])

        self.glob.lib.msg.log(stdout)
        self.glob.lib.msg.log(stderr)

        # Store jobid in shared global object
        self.glob.task_id = jobid

    # Get usable string of application status
    def get_status_str(self, app):

        # Get execution mode (sched or local) from application report file
        exec_mode = self.glob.lib.report.get_exec_mode("build", app)

        # Handle dry run applications
        if "dry" in exec_mode:
            return '\033[1;33mDRYRUN\033[0m'

        # Get Jobid from report file and check if status = COMPLETED
        task_id = self.glob.lib.report.get_task_id("build", app)

        # Unable to get task ID from report file
        if not task_id and not self.glob.args.delApp:
            self.glob.lib.msg.warn(["Unable read build report file for " + str(app),
                                        "Please cleanup with:",
                                        "bp -da "+str(app)])
            
            return '\033[0;31mUNKNOWN\033[0m' 

        if "dry" in task_id:
            return "\033[1;33mDRY RUN\033[0m"

        status = None 
        if exec_mode == "sched":
            status = self.task_status(task_id)

        if exec_mode == "local":
            # Check if PID is running
            if self.glob.lib.proc.complete(task_id):
                status = "COMPLETED"
            else:
                return "\033[1;33mPID STILL RUNNING\033[0m"

        # Complete state
        if status == "COMPLETED":

            bin_dir, exe = self.glob.lib.report.get_build_exe(app)
            if exe:
                if self.glob.lib.files.exists(exe, os.path.join(self.glob.ev['BP_APPS'], 
                                                                app, 
                                                                self.glob.stg['install_subdir'])): 
                                                                #bin_dir)):
                    return self.glob.success

            return '\033[0;31mFAILED\033[0m'

        if status in ["RUNNING","PENDING"]:
            return '\033[0;33mJOB '+status+'\033[0m'


        # Failed state
        if status in ["FAILED", "TIMEOUT"]:
            return '\033[0;31mJOB '+status+'\033[0m'

        # Status not found
        if not status:
            self.glob.lib.msg.log("Unable to determine status of job ID " + str(task_id))
        return '\033[0;31mUNKNOWN\033[0m'



