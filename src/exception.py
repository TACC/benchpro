# System Imports
import glob as gb
import os
import sys

# Coloured text
warning = '\033[1;33mWARNING: \033[0m'
error = '\033[0;31mERROR: \033[0m'
success = '\033[0;32mSUCCESS: \033[0m'

# Delete tmp build files if installation fails
def remove_tmp_files(log):
    file_list = gb.glob('tmp.*')
    if file_list:
        for f in file_list:
            try:
                os.remove(f)
                log.debug("Successfully removed tmp file "+f)
            except:
                log.debug("Failed to remove tmp file ", f)

# Print message to log and stdout then continue
def print_warning(log, message):
    log.debug(warning + message)
    print(warning + message)
    print()

# Print message to log and stdout then quit
def error_and_quit(log, message):
    log.debug(error + message)
    log.debug("Quitting.")
    print()
    print()
    print(error + message)
    print("Check log for details.")
    print("Cleaning up tmp files...")
    remove_tmp_files(log)
    print()
    print("Quitting.")
    print()
    print()
    print()
    print()
    sys.exit(1)
