import glob
import os
import shutil as su
import sys
import time

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
		search_dict = ['*.out*',
					   '*.err*',
					   '*.log',
					   'tmp.*'
					   ]

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
		if (parent_dir == self.gs.build_dir) or  (parent_dir == self.gs.module_dir) or (len(glob.glob(parent_path+self.gs.sl+"*")) > 1):
			su.rmtree(path)
		# Else resurse with parent
		else:
			self.prune_tree(parent_path)

	# Detele application and module matching path provided
	def remove_app(self, code_str):

		common = common_funcs.init(self.gs)

		install_path = common.check_if_installed(code_str)

		top_dir = self.gs.base_dir + self.gs.sl + self.gs.build_dir + self.gs.sl

		# Get module dir from app dir, by adding 'modulefiles' prefix and stripping [version] suffix
		mod_dir = top_dir + self.gs.module_dir + self.gs.sl + self.gs.sl.join(install_path.split(self.gs.sl)[:-1])
		app_dir = top_dir + install_path

		print("Found application installed in " + app_dir)
		print('\033[1m' + "Deleting in", self.gs.timeout, "seconds...")
		time.sleep(self.gs.timeout)
		print('\033[0m' + "No going back now...")

		# Delete application dir
		try:
			self.prune_tree(app_dir)
			print("")
			print("Application removed.")
		except:
			print("Warning: Failed to remove application directory " + app_dir)
			print("Skipping")

		print()
		# Detele module dir
		try:
			self.prune_tree(mod_dir)
			print("Module removed.")
		except:
			print("Warning: no associated module located in " + mod_dir)
			print("Skipping")

	# Print build report of installed application
	def query_app(self, code_str):
		common = common_funcs.init(self.gs)
		install_path = common.check_if_installed(code_str)
		build_report = self.gs.base_dir + self.gs.sl + self.gs.build_dir + self.gs.sl + install_path + self.gs.sl + self.gs.build_report_file

		print("Build report for application '"+code_str+"'")
		print("-------------------------------------------")
		with open(build_report, 'r') as report:
			print(report.read())

	# Get all sub directories
	def get_subdirs(self, base):
		return [name for name in os.listdir(base)
				if os.path.isdir(os.path.join(base, name))]

	# Recurse down tree 5 levels to get full applciation installation path
	def recurse_down(self, app_dir, start_depth, current_depth, max_depth):
		for d in self.get_subdirs(app_dir):
			if d != self.gs.module_dir:
				new_dir = app_dir + self.gs.sl + d
				if current_depth == max_depth:
					print(
						"	" + self.gs.sl.join(new_dir.split(self.gs.sl)[start_depth + 1:]))
				else:
					self.recurse_down(new_dir, start_depth,
								 current_depth + 1, max_depth)

	# Print currently installed apps, used together with 'remove'
	def show_installed(self):
		print("Currently installed applications:")
		print("---------------------------------")
		app_dir = self.gs.base_dir + self.gs.sl + "build"
		start = app_dir.count(self.gs.sl)
		self.recurse_down(app_dir, start, start, start + 5)

	# Print applications that can be installed from available cfg files
	def show_available(self):
		print("Available application profiles:")
		print("---------------------------------")
		app_dir = self.gs.base_dir + self.gs.sl + "config" + self.gs.sl + "build" + self.gs.sl
		temp_files = glob.glob(app_dir + "*.cfg")
		for f in temp_files:
			code = f.split('/')[-1]
			if "_build" in code:
				print("	" + code[:-10])
			else:
				print("	" + code[:-4])
