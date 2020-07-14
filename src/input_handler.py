# System Imports
import glob
import os
import shutil as su
import sys
import time

# Local Imports
import src.common as common_funcs

class init(object):
	def __init__(self, gs):
		self.gs = gs

	# Get list of files matching search
	def find_matching_files(self, search_dict):
		file_list = []
		for search in search_dict:
			file_list += glob.glob(self.gs.base_dir + self.gs.sl + search)
		return file_list

	# Delete matching files
	def clean_matching_files(self, file_list):
		tally = 0
		for f in file_list:
			try:
				os.remove(f)
				tally += 1
			except:
				print("Error cleaning the file", f)
		return tally

	# Clean up temp files such as logs
	def clean_temp_files(self):
		print("Cleaning up temp files...")
		# Search space for tmp files
		search_dict = ['*.out*',
					   '*.err*',
					   '*.log',
					   'tmp.*']

		file_list = self.find_matching_files(search_dict)

		if file_list:
			print("Found the following files to delete:")
			for f in file_list:
				print(f)

			print('\033[1m' + "Deleting in", self.gs.timeout, "seconds...")
			time.sleep(self.gs.timeout)
			print('\033[0m' + "No going back now...")
			deleted = self.clean_matching_files(file_list)
			print("Done, " + str(deleted) + " files successfuly cleaned.")

		else:
			print("No temp files found.")

	# Prune dir tree until not unique
	def prune_tree(self, path):
		path_elems  = path.split(self.gs.sl)
		parent_path = self.gs.sl.join(path.split(self.gs.sl)[:-1])
		parent_dir  = path_elems[-2]

		# If parent dir is root ('build' or 'modulefile') or if it contains more than this subdir, delete this subdir
		if (parent_dir == self.gs.build_basedir) or  (parent_dir == self.gs.module_basedir) or (len(glob.glob(parent_path+self.gs.sl+"*")) > 1):
			su.rmtree(path)
		# Else resurse with parent
		else:
			self.prune_tree(parent_path)

	# Detele application and module matching path provided
	def remove_app(self, code_str):
		common = common_funcs.init(self.gs)
		install_path = common.check_if_installed(code_str)

		# Get module dir from app dir, by adding 'modulefiles' prefix and stripping [version] suffix
		mod_dir = self.gs.module_path + self.gs.sl + self.gs.sl.join(install_path.split(self.gs.sl)[:-1])
		app_dir = self.gs.build_path + self.gs.sl +  install_path

		print("Found application '" + code_str + "' installed in:")
		print(">  " + common.rel_path(app_dir))
		print()
		print('\033[1m' + "Deleting in", self.gs.timeout, "seconds...")
		time.sleep(self.gs.timeout)
		print('\033[0m' + "No going back now...")

		# Delete application dir
		try:
			self.prune_tree(app_dir)
			print("")
			print("Application removed.")
		except:
			print("Warning: Failed to remove application directory:")
			print(">  "  + common.rel_path(app_dir))
			print("Skipping")

		print()
		# Detele module dir
		try:
			self.prune_tree(mod_dir)
			print("Module removed.")
		except:
			print("Warning: no associated module located in:")
			print(">  " + common.rel_path(mod_dir))
			print("Skipping")

	# Print build report of installed application
	def query_app(self, code_str):
		common = common_funcs.init(self.gs)
		install_path = self.gs.build_path + self.gs.sl + common.check_if_installed(code_str)
		build_report = install_path + self.gs.sl + self.gs.build_report_file

		exe = ""
		print("Build report for application '"+code_str+"'")
		print("-------------------------------------------")
		with open(build_report, 'r') as report:
			content = report.read()
			print(content)
			for line in content.split("\n"):
				if line[0:3] == "exe":
					exe = line.split('=')[1].strip()

		exe_search = common.find_exact(exe, install_path)
		if exe_search:
			print("Executable found: " + common.rel_path(exe_search[0]))
		else:
			print("WARNING: executable '" + exe + "' not found in build directory.")

	# Print currently installed apps, used together with 'remove'
	def show_installed(self):
		common = common_funcs.init(self.gs)
		print("Currently installed applications:")
		print("---------------------------------")
		for app in common.get_installed():
			print("  " + common.rel_path(self.gs.build_path) + self.gs.sl  + app)

	# Print applications that can be installed from available cfg files
	def show_available(self):
		print("Available application profiles:")
		print("---------------------------------")
		app_dir = self.gs.config_path + self.gs.sl + self.gs.build_cfg_dir + self.gs.sl
		temp_files = glob.glob(app_dir + "*.cfg")
		for f in temp_files:
			code = f.split('/')[-1]
			if "_build" in code:
				print("	" + code[:-10])
			else:
				print("	" + code[:-4])
