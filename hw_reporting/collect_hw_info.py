import os
import sys
from datetime import datetime
import socket
import subprocess

date = datetime.now().strftime("%Y-%m-%d_%Hh%M")
host = socket.gethostname()
if ("." in host):
    host = '.'.join(map(str, host.split('.')[0:2]))

prefix = "./tools"
check_exe = "lshw"
out_dir = "hw_report-"+host+"-"+date
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

log_file = out_dir+"/hw_info.log"
log = open(log_file,"w+")

# File checks
if (not os.path.isfile(prefix+"/"+check_exe)):
    log.write(prefix+"/"+check_exe+"executable not found, somethings not right...\n")
elif(os.stat(prefix+"/"+check_exe).st_uid != 0):
    log.write("Insufficient privileges, run change_permissions.sh as root. Quitting for now...\n")
else:
    log.write("Checks passed, proceeding.\n")

# Write a log file
def write_log(log_file, content):
    f= open(log_file,"w+")
    f.write(content)
    f.close()

# Run commands and capture output
def run_cmd(label, cmd):
    for i in range(len(label)):
        log.write("Collecting "+label[i]+"...\n")

        try:
            process = subprocess.run([cmd[i]], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output = process.stdout
            write_log(out_dir+"/"+host+"-"+date+"_"+label[i]+".txt", output)
            log.write("Done.\n\n")

        except subprocess.CalledProcessError as error:
            print(error) 


# System agnostic collecetion
label =	["cpuid.all.raw", 
	"cpuid.core0",
	"lshw",
	"TACC_HWP_set",
	"lspci",
	"rdmsr_all",
	"rpm",
	"lscpu"
	]

cmd = 	[prefix+"/cpuid -r",
	"taskset -c 0 "+prefix+"/cpuid -1",
	prefix+"/lshw",
	prefix+"/TACC_HWP_set -v -s",
	prefix+"/lspci -xxx",
	prefix+"/rdmsr_all",
	"rpm -qa",
	"lscpu"
	]
run_cmd(label, cmd)

# Frontera specific collection
if (os.getenv('TACC_SYSTEM') is "frontera"): 
    label = ["ibnetdiscover"
	    ]

    cmd =   [prefix+"/ibnetdiscover -p"
	    ]
    run_cmd(label, cmd)

log.close()
