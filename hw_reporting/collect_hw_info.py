#!/usr/bin/env python3

from datetime import datetime
import glob
import os
import shutil
import socket
import subprocess
import sys


# Define vars
date = datetime.now().strftime("%Y-%m-%d_%Hh%M")
host = socket.gethostname()
if ("." in host):
    host = '.'.join(map(str, host.split('.')[0:2]))

working_dir = str(os.getcwd())
prefix = "tools"
tool_dir = working_dir+"/"+prefix

check_exe = "lshw"

out_dir = working_dir + "/" + "hw_report-"+host+"-"+date

# Check cmd args
if sys.argv[1] == "clean":
    print("Cleaning up.")
    for d in glob.glob("hw_report-*"):
        shutil.rmtree(d)
    sys.exit(1)


# Make output dir
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

log_file = out_dir+"/hw_collection.log"
f = open(log_file,"w+")

# Wriet log to file & stdout
def write_log(f, log):
    print(log)
    f.write(log)

# Write a cmd output to file
def write_cmd(log_file, content):
    f= open(log_file,"w+")
    for i in content:
        f.write(i)
    f.close()

# File checks
if (not os.path.isfile(tool_dir+"/"+check_exe)):
    write_log(f, tool_dir+"/"+check_exe+" executable not found, something is not right...\n")
    sys.exit(1)
elif(os.stat(tool_dir+"/"+check_exe).st_uid != 0):
    write_log(f, "Insufficient privileges, run change_permissions.sh as root. Quitting for now...\n")
    sys.exit(1)
else:
    write_log(f, "Checks passed, proceeding.\n\n")

# Run commands and capture output
def run_cmd(tasks):
    for cmd in tasks:
        write_log(f, "Collecting "+cmd[0]+"...\n")

        try:
            process = subprocess.run([cmd[1]], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            out_file=out_dir+"/"+host+"-"+date+"_"+cmd[0]+".txt"
            write_log(f, "Writing to "+out_file+"\n")
            write_cmd(out_file, [process.stdout, process.stderr])
            write_log(f, "Done.\n\n")

        except subprocess.CalledProcessError as error:
            write_log(f, error)

# System agnostic info
tasks =	[["cpuid.all.raw", prefix+"/cpuid -r"],
	["cpuid.core0", "taskset -c 0 "+prefix+"/cpuid -1"],
	["lshw", prefix+"/lshw"],
	["TACC_HWP_set", prefix+"/TACC_HWP_set -v -s"],
	["lspci", prefix+"/lspci -xxx"],
	["rdmsr_all", prefix+"/rdmsr_all"],
	["rpm", "rpm -qa"],
	["ml", "ml"],
	["lscpu", "lscpu"]
	]
run_cmd(tasks)

# Frontera specific info
if (os.getenv('TACC_SYSTEM') is "frontera"): 
    tasks = [["ibnetdiscover", prefix+"/ibnetdiscover -p"]
	    ]
    run_cmd(tasks)

f.close()
