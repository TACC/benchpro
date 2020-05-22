import logging as lg
import os
import shutil as su
import sys

class init(object):
	def __init__(self, gs):
			self.gs = gs

	def start_logging(self, name, file):
	
		print("Log file for this session:   " + str(file))

		formatter = lg.Formatter("{0}: ".format(name) + self.gs.user + "@" + self.gs.hostname + ": " +
							 "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

		logger = lg.getLogger(name)
		logger.setLevel(self.gs.log_level)

		file_handler = lg.FileHandler(file, mode="w", encoding="utf8")
		file_handler.setFormatter(formatter)

		#stream_handler = lg.StreamHandler(stream=sys.stderr)
		# stream_handler.setFormatter(formatter)

		logger.addHandler(file_handler)
		# logger.addHandler(stream_handler)

		return logger


	def get_subdirs(self, base):
		return [name for name in os.listdir(base)
			if os.path.isdir(os.path.join(base, name))]


	def recurse_down(self, installed_list, app_dir, start_depth, current_depth, max_depth):
		for d in self.get_subdirs(app_dir):
			if d != 'modulefiles':
				new_dir = app_dir + self.gs.sl + d
				if current_depth == max_depth:
					installed_list.append(self.gs.sl.join(new_dir.split(self.gs.sl)[start_depth + 1:]))
				else:
					self.recurse_down(installed_list, new_dir, start_depth,current_depth + 1, max_depth)

	# Print currently installed apps, used together with 'remove'

	def get_installed(self):
		app_dir = self.gs.base_dir + self.gs.sl + self.gs.build_dir
		start = app_dir.count(self.gs.sl)
		installed_list = []
		self.recurse_down(installed_list, app_dir, start, start, start + 5)
		return installed_list

	def check_if_installed(self, requested_code):
		installed_list = self.get_installed()
		matched_codes = []
		for code_string in installed_list:
			if requested_code in code_string:
				matched_codes.append(code_string)

		if len(matched_codes) == 0:
			print("No installed applications match your selection '" + requested_code + "'")
			print("Currently installed applications:")
			for code in installed_list:
				print(" " + code)
			sys.exit(1)

		elif len(matched_codes) == 1:
			return matched_codes[0]

		else:
			print("Multiple installed applications match your selection '" +
			  	requested_code + "':")
			for code in matched_codes:
				print(" " + code)
			print("Please be more specific.")
			sys.exit(1)

	# Create directories if needed
	def create_install_dir(self, path, logger):
		# Try to create build directory
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except:
				exception.error_and_quit(
					logger, "Failed to make directory " + path)

	# Move files to install directory
	def install(self, path, obj, logger):
	
		# Get file name
		new_obj_name = obj
		if self.gs.sl in obj:
			new_obj_name = obj.split(self.gs.sl)[-1]
		# Strip tmp prefix from file
		if 'tmp.' in obj:
			new_obj_name = obj[4:]
	
		try:
			su.copyfile(obj, path + self.gs.sl + new_obj_name)
		except IOError as e:
			print(e)
			exception.error_and_quit(
				logger, "Failed to move " + obj + " to " + path + self.gs.sl + new_obj_name)

	# Submit build script to scheduler
	def submit_job(self, script_file, logger):
		print()
		if self.gs.dry_run:
			print("This was a dryrun, job script created at " + script_file)
			logger.debug("This was a dryrun, job script created at " + script_file)
		else:
			print("Submitting " + script_file + " to scheduler...")
			logger.debug("Submitting build script to scheduler...")
			try:
				cmd = subprocess.run("sbatch " + script_file, shell=True,
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
	
				time.sleep(2)
				cmd = subprocess.run("squeue -a --job " + job_id, shell=True,
									 check=True, capture_output=True, universal_newlines=True)
	
				print(cmd.stdout)
				logger.debug(cmd.stdout)
				logger.debug(cmd.stderr)
	
			except subprocess.CalledProcessError as e:
				exception.error_and_quit(logger, "Failed to submit job to scheduler")
	
