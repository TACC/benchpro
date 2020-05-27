# System Imports
import glob
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime

# Local Imports
import src.common as common_funcs
import src.global_settings as gs
import src.exception as exception

gs = logger = ''
check_exe = "lshw"

# File checks
def check_tools():
	# Check if file exists
	if not os.path.isfile(gs.utils_path + gs.sl + check_exe):
		exception.error_and_quit(logger, tool_dir + gs.sl + check_exe + " executable not found, something is not right...")

	# Check if permissions are correct
	elif(os.stat(gs.utils_path + gs.sl + check_exe).st_uid != 0):
		exception.error_and_quit(logger, "Insufficient privileges, run change_permissions.sh as root.")
	# Continue
	else:
		logger.debug("Util checks passed, proceeding.")

# Write a cmd output to file
def write_cmd(out_file, content):
	f = open(out_file, "w+")
	for i in content:
		f.write(i)
	f.close()

def run_cmd(cmd, output_dir):

	try:
		process = subprocess.run(cmd[1], shell=True, check=True,
								 stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
		out_file = output_dir + gs.sl + cmd[0] + ".txt"
		logger.debug("Writing to " + out_file)
		write_cmd(out_file, [process.stdout, process.stderr])

	except subprocess.CalledProcessError as error:
		exception.error_and_quit(logger, "failed to run '" + cmd[1] + "'")

# Run commands and capture output
def collect_info(output_dir, settings, log_to_use):

	global gs, logger
	gs = settings
	logger = log_to_use

	common = common_funcs.init(gs)
	
	logger.debug("Hardware info collection started.")

	# Check utils
	check_tools()

	# Create dir
	common.create_install_dir(output_dir, logger)

	# System agnostic info - [label][cmd]
	tasks = [["cpuid.all.raw", gs.utils_path + gs.sl + "cpuid -r"],
		 	["cpuid.core0", "taskset -c 0 " + gs.utils_path + gs.sl + "cpuid -1"],
		 	["lshw", gs.utils_path + gs.sl + "lshw"],
		 	["TACC_HWP_set", gs.utils_path + gs.sl + "TACC_HWP_set -v -s"],
		 	["lspci", gs.utils_path + gs.sl + "lspci -xxx"],
		 	["rdmsr_all", gs.utils_path + gs.sl + "rdmsr_all"],
		 	["rpm", "rpm -qa"],
		 	["ml", "ml"],
		 	["lscpu", "lscpu"]
			]

	for cmd in tasks:
		logger.debug("Collecting info from tool "+cmd[0])
		run_cmd(cmd, output_dir)

	# Frontera specific info
	if (os.getenv('TACC_SYSTEM') is "frontera"):
		tasks = [["ibnetdiscover", gs.utils_path + gs.sl + "ibnetdiscover -p"]
				 ]
		for cmd in tasks:
			logger.debug("Collecting info from tool "+cmd[0])
			run_cmd(cmd, output_dir)

