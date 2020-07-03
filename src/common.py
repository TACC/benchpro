# System Imports
import configparser as cp
import logging as lg
import os
import pwd
import re
import shutil as su
import subprocess
import sys
import time

# Local Imports
import src.exception as exception

# Contains several useful functions, mostly used by bencher and builder
class init(object):
	def __init__(self, gs):
			self.gs = gs

	# Get relative paths for full paths before printing to stdout
	def rel_path(self, path):
		# if empty str
		if not path:
			return ""
		# if absolute
		if path[0] == self.gs.sl:
			return self.gs.topdir_env_var + path.replace(self.gs.base_dir, '')
		# if not
		else:
			return path

	# Get absolute path 
	def abs_path(self, path):
		# if empty str
		if not path:
			return ""
		# if absolute
		if path[0] == self.gs.sl:
			return path
		# if relative
		else:
			return self.gs.basedir + self.gs.sl + path

	# Start logger and return obj 
	def start_logging(self, name, log_file):
		print("Log file:   " + self.rel_path(log_file))
		print()

		formatter = lg.Formatter("{0}: ".format(name) + self.gs.user + "@" + self.gs.hostname + ": " + \
							 "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

		logger = lg.getLogger(name)
		logger.setLevel(1)

		file_handler = lg.FileHandler(log_file, mode="w", encoding="utf8")
		file_handler.setFormatter(formatter)

		# Print log to stdout
		#stream_handler = lg.StreamHandler(stream=sys.stderr)
		#stream_handler.setFormatter(formatter)

		logger.addHandler(file_handler)
		#logger.addHandler(stream_handler)
		logger.debug(name+" log started")

		return logger

	# Find file in directory
	def find_exact(self, file_name, path):
		# Check file doesn't exist already
		if os.path.isfile(file_name):
			return file_name
		# Search provided path for file
		for root, dirs, files in os.walk(path):
			match = next((s for s in files if file_name == s), None)
			if match:
				return os.path.join(root, match)
		# File not found
		return ""

	# Find *file* in directory
	def find_partial(self, file_name, path):
		# Check file doesn't exist already
		if os.path.isfile(file_name):
			return file_name
		# Search provided path for file
		for root, dirs, files in os.walk(path):
			match = next((s for s in files if file_name in s), None)
			if match:
				return os.path.join(root, match)
		# File not found
		print("file not found")
		return ""

	# Get owner of file
	def file_owner(self, file_name):
		return pwd.getpwuid(os.stat(file_name).st_uid).pw_name

	# Convert module name to usable directory name, Eg: intel/18.0.2 -> intel18
	def get_label(self, module):
		label = module
		if module.count(self.gs.sl) > 0:
			comp_ver = module.split(self.gs.sl)
			label = comp_ver[0] + comp_ver[1].split(".")[0]
		return label

	# Get a list of sub-directories, called by 'search_tree'
	def get_subdirs(self, base):
		return [name for name in os.listdir(base)
			if os.path.isdir(os.path.join(base, name))]

	# Recursive function to scan app directory, called by 'get_installed'
	def search_tree(self, installed_list, app_dir, start_depth, current_depth, max_depth):
		for d in self.get_subdirs(app_dir):
			if d != self.gs.module_basedir:
				new_dir = app_dir + self.gs.sl + d
				# Once tree hits max search depth, append path to list
				if current_depth == max_depth:
					installed_list.append(self.gs.sl.join(new_dir.split(self.gs.sl)[start_depth + 1:]))
				# Else continue to search tree 
				else:
					self.search_tree(installed_list, new_dir, start_depth,current_depth + 1, max_depth)

	# Get list of installed apps
	def get_installed(self):
		app_dir = self.gs.build_path
		start = app_dir.count(self.gs.sl)
		# Send empty list to search function 
		installed_list = []
		self.search_tree(installed_list, app_dir, start, start, start + 5)
		return installed_list

	# Check if a string returns a unique installed application
	def check_if_installed(self, requested_code):
		installed_list = self.get_installed()
		matched_codes = []
		for code_string in installed_list:
			if requested_code in code_string:
				matched_codes.append(code_string)
		# No matches
		if len(matched_codes) == 0:
			print("No installed applications match your selection '" + requested_code + "'")
			print()
			print("Currently installed applications:")
			for code in installed_list:
				print(" " + code)
			sys.exit(1)
		# Unique match
		elif len(matched_codes) == 1:
			return matched_codes[0]
		# More than 1 match
		else:
			print("Multiple installed applications match your selection '" + requested_code + "':")
			for code in matched_codes:
				print("  ->" + code)
			print("Please be more specific.")
			sys.exit(1)

	# Get all results in ./results
	def get_all_results(self):
		return self.get_subdirs(self.gs.bench_path)

	# Get result dirs that have '.capture-failed' file inside
	def check_for_failed_results(self):
		results = self.get_all_results()

		# look for '.captured-failed' file in each result dir
		failed_results = []
		for result_dir in results:
			result_path = self.gs.bench_path + self.gs.sl + result_dir + self.gs.sl
			if os.path.exists(result_path + ".capture-failed"):
				failed_results.append(result_dir)
		return failed_results

	# Get result dirs that have '.capture-complete' file inside
	def check_for_submitted_results(self):
		results = self.get_all_results()

		# look for '.captured-complete' file in each result dir
		complete_results = []
		for result_dir in results:
			result_path = self.gs.bench_path + self.gs.sl + result_dir + self.gs.sl
			if os.path.exists(result_path + ".capture-complete"):
				complete_results.append(result_dir)
		return complete_results

	# Find result dirs that don't have '.capture-complete' or '.capture-failed' file 
	def get_new_results(self):
		results = self.get_all_results()

		# look for .captured file in each result dir
		new_results = []
		for result_dir in results:
			result_path = self.gs.bench_path + self.gs.sl + result_dir + self.gs.sl
			if not os.path.exists(result_path + ".capture-complete") and not os.path.exists(result_path + ".capture-failed") :
				new_results.append(result_dir)
		return new_results

	# Check that job ID is not running 
	def check_job_complete(self, job_id):

		# If job not available in squeue anymore
		try:
			cmd = subprocess.run("sacct -j " + job_id, shell=True, \
							check=True, capture_output=True, universal_newlines=True)
		# Assuming complete
		except:
			return True

		# Job still running
		if "RUNNING" in cmd.stdout.split("\n")[2]:
			return False

		# Job complete
		return True

	# Check if there are uncaptured results
	def check_for_complete_results(self):
		new_results = self.get_new_results()

		completed_results = []
		# Check that job is complete
		for result in new_results:
			job_id = ''
			# Get jobID from bench_report.txt
			with open(self.gs.bench_path + self.gs.sl + result + self.gs.sl + self.gs.bench_report_file, 'r') as inFile:
				for line in inFile:
					if "job_id" in line:
						job_id = line.split("=")[1].strip()
									
			# Check job is completed
			if self.check_job_complete(job_id):
				completed_results.append(result)

		return completed_results

	# Check if there are benchmark jobs running
	def check_for_running_results(self):
		new_results = self.get_new_results()

		running_results = []
		# Check that job is complete
		for result in new_results:
			job_id = ''
			# Get jobID from bench_report.txt
			with open(self.gs.bench_path + self.gs.sl + result + self.gs.sl + self.gs.bench_report_file, 'r') as inFile:
				for line in inFile:
					if "job_id" in line:
						job_id = line.split("=")[1].strip()

			# Check job is completed
			if not self.check_job_complete(job_id):
				running_results.append(result)

		return running_results

	# Get list of uncaptured results and print note to user
	def print_new_results(self):
		# Uncaptured results + job complete
		completed_results = self.check_for_complete_results()
		if completed_results:
			print("NOTE: There are " + str(len(completed_results)) + " uncaptured results found in " + self.rel_path(self.gs.bench_path))
			print("Run 'benchtool --capture' to send to database.")
			print()

	# Log cfg contents
	def send_inputs_to_log(self, label, cfg_list, logger):
		logger.debug(label + " started with the following inputs:")
		logger.debug("======================================")
		for cfg in cfg_list:
			for seg in cfg:
				logger.debug("[" + seg + "]")
				for line in cfg[seg]:
					logger.debug("  " + str(line) + "=" + str(cfg[seg][line]))
		logger.debug("======================================")

	# Check for unpopulated <<<keys>>> in template file
	def test_template(self, template_file, template, logger):
		key = "<<<.*>>>"
		nomatch = re.findall(key, template)
		if len(nomatch) > 0:
			# Conitue regardless
			if not self.gs.exit_on_missing:
				exception.print_warning(logger, "WARNING: Missing parameters were found in template file " + template_file + ":" + ", ".join(nomatch))
				exception.print_warning(logger, "exit_on_missing=False in settings.cfg so continuing anyway...")
			# Error and exit
			else:
				exception.error_and_quit(logger, "Missing parameters were found after populating the template file " + template_file + " and exit_on_missing=True in settings.cfg: " + ' '.join(nomatch))
		else:
			logger.debug("All build parameters were filled, continuing")

	# Create directories if needed
	def create_dir(self, path, logger):
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except:
				exception.error_and_quit(
					logger, "Failed to create directory " + path)

	# Copy tmp files to directory
	def install(self, path, obj, new_obj_name, logger):
		# Get file name
		if not new_obj_name:
			new_obj_name = obj
			if self.gs.sl in obj:
				new_obj_name = obj.split(self.gs.sl)[-1]
			# Strip tmp prefix from file for new filename
			if 'tmp.' in obj:
				new_obj_name = obj[4:]
	
		try:
			su.copyfile(obj, path + self.gs.sl + new_obj_name)
			logger.debug("Copied file " + obj + " into " + path)
		except IOError as e:
			print(e)
			exception.error_and_quit(
				logger, "Failed to move " + obj + " to " + path + self.gs.sl + new_obj_name)

	# Submit script to scheduler
	def submit_job(self, job_path, script_file, logger):
		script_path= job_path + self.gs.sl + script_file
		# If dry_run, quit
		if self.gs.dry_run:
			print("This was a dryrun, job script created at " + self.rel_path(script_path))
			logger.debug("This was a dryrun, job script created at " + script_path)
			# Return jobid and host placeholder 
			return ["dryrun", "dryrun"]

		else:
			print("Job script:")
			print(">  " + self.rel_path(script_path))
			print()
			print("Submitting to scheduler...")
			logger.debug("Submitting " + script_path + " to scheduler...")
			try:
				cmd = subprocess.run("sbatch " + script_path, shell=True, \
									 check=True, capture_output=True, universal_newlines=True)
	
				logger.debug(cmd.stdout)
				logger.debug(cmd.stderr)

				job_id = ''
				i = 0
				jobid_line = "Submitted batch job"

				# Find job ID
				for line in cmd.stdout.splitlines():
					if jobid_line in line:
						job_id = line.split(" ")[-1]

				time.sleep(self.gs.timeout)
				cmd = subprocess.run("squeue -a --job " + job_id, shell=True, \
									 check=True, capture_output=True, universal_newlines=True)
	
				# Get job host
				host = cmd.stdout.split("\n")[1][cmd.stdout.split("\n")[0].find("NODELIST"):]
				print(cmd.stdout)

				print()
				print("Job " + job_id + " output log:")
				print(">  "+ self.rel_path(job_path + self.gs.sl + job_id + ".out"))
				print("Job " + job_id + " error log:")
				print(">  "+ self.rel_path(job_path + self.gs.sl + job_id + ".err"))
				print()

				logger.debug(cmd.stdout)
				logger.debug(cmd.stderr)
				# Return job info
				return [job_id, host]

			except subprocess.CalledProcessError as e:
				exception.error_and_quit(logger, "Failed to submit job to scheduler")
	
