import glob
import os
import sys

# Delete tmp build files if installation fails


def remove_tmp_files():
    file_list = glob.glob('tmp.*')
    if file_list:
        for f in file_list:
            try:
                os.remove(f)
            except:
                print("Failed to remove tmp file", f)

# Print message to log and stdout then quit


def error_and_quit(logger, message):
    logger.debug("ERROR: " + message)
    logger.debug("Quitting")
    print()
    print()
    print("ERROR: " + message)
    print("Check log for details.")
    print("Cleaning up tmp files...")
    remove_tmp_files()
    print()
    print("Quitting")
    print()
    print()
    print()
    print()
    sys.exit(1)
