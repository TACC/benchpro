import os
import sys
from datetime import datetime
import socket
import subprocess

DATE = datetime.now().strftime("%Y-%m-%d_%HH%M")
HOST = "stampede.tacc" #socket.gethostname()
if ("." in HOST):
    HOST = '.'.join(map(str, HOST.split('.')[0:2]))

PREFIX = "./tools"
CHECK_EXE = "lshw"
OUT_DIR = "hw_report-"+HOST+"-"+DATE
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

LOG_FILE = OUT_DIR+"/hw_info.log"
log = open(LOG_FILE,"w+")

# File checks
if (not os.path.isfile(PREFIX+"/"+CHECK_EXE)):
    log.write(PREFIX+"/"+CHECK_EXE+"executable not found, somethings not right...")
elif(stat(PREFIX+"/"+CHECK_EXE).st_uid != 0):
    log.write("Insufficient privileges, run change_permissions.sh as root. Quitting for now...")
else:
    log.write("Checks passed, proceeding.")

# Write a log file
def write_log(log_file, content):
    f= open(log_file,"w+")
    f.write(content)
    f.close()

# Run commands and capture output
def run_cmd(label, cmd):
    print(label)
    for i in range(len(label)):
        log.write("Collecting "+label[i]+" info...")
        report = subprocess.run([cmd[i]], stdout=subprocess.PIPE)
        write_log(OUT_DIR+"/"+HOST+"-"+DATE+"_"+label+".txt", report.stdout)
        log.write("Done.")


label = ["cpuid.all.raw", "cpuid.core0"]
cmd = [PREFIX+"/cpuid -r", "taskset -c 0 "+PREFIX+"/cpuid -1"]
run_cmd(label, cmd)
log.close()
