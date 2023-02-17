#!/bin/env python3

#
# Notices
# Stand alone notice printer for BenchPRO
# Matthew Cawood
# September 2022
# v1.0

import glob
import os
import subprocess
import sys

# If an urgent message is in $BPS_HOME/notices/urgent, print them and quit

def run_files(notice_path):
    if os.path.isdir(notice_path):
        for notice_file in glob.glob(notice_path+"/*.txt"):
            print("\nNOTICE: " + notice_file + "\n\n")
            with open(notice_file, 'r') as fp:
                print(fp.read())
            
            
# Print urgent (terminating) and non-urgent messages
def print_notices(quiet, force):

        # Skip
    if str(os.environ.get("BP_NOTICE")) != "1" and not force:
        if not quiet:
            print("For info, try any of these:")
            print("bp --help")
            print("bp --notices")
            print("bp --defaults")
            print("bp --env")

        return

    # !!!THIS CAN BE EDITTED: DISABLE NOTICES!!! 
    print_notices = True
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if print_notices or force:

        # Condition
        out_of_date_user = False
        # Quit if old dir exists
        dir_exists = os.path.expandvars("$BP_HOME/config")
        if os.path.isdir(dir_exists):
            out_of_date_user = True

        # PROD
        hard_coded_path = "/scratch1/hpc_tools/benchpro/package/benchpro/notices"
        run_files(hard_coded_path)

    sys.exit(0)



# Print info
def info():

    print("Welcome to BenchPRO, are you new?")
    print()
    print("You may want to read the documentation: https://benchpro.readthedocs.io/en/latest/")
    print()
    print("1. First run 'bp' and follow the prompts to assign first-time parameters with bps (benchset).")
    print()
    print("2. You can view all available applications with bp -a")
    print()
    print("3. You can list all installed applcations with bp -la")
    print()
    print("4. Build the included LAMMPS code with bp -b lammps")
    print()
    print("For more help, try any of these:")
    print("bp --help")
    print("bp --notices")
    print("bp --defaults")
    print("bp --env")
    print()

    sys.exit(0)
    
