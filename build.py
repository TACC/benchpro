#!/usr/bin/env python3

# System Imports
import argparse
import os
import pprint as pp
import sys

# Local Imports
try:
    import src.utils as utils
    import src.input_handler as input_handler
except ImportError as e:
    print("You had an import error, you might be using Python2. Please use Python3.")
    print(e)
    sys.exit(1)

def main():

    # Parse cmdline args
    cmd_parser = argparse.ArgumentParser(
        description='Provide the cgf input file for you code you with to compile')
    cmd_parser.add_argument("--code", default="default.cfg",
                            type=str, help="Name of the code cfg file.")
    cmd_parser.add_argument("--sched", default="system",
                            type=str, help="Name of the scheduler cfg file.")
    cmd_parser.add_argument("--clean", default=False, action='store_true',
                            help="Cleanup temp and log files.")
    cmd_parser.add_argument("--installed", default=False, action='store_true',
                            help="Show all installed applications.")
    cmd_parser.add_argument("--available", default=False, action='store_true',
                            help="Show all available application profiles.")
    cmd_parser.add_argument("--remove", default="none",
                            help="Remove an installed application, use output of --show-installed for formatting")


    args = cmd_parser.parse_args()

    # Use system default scheduler profile 
    if args.sched == "system":
        args.sched = "slurm-"+os.getenv('TACC_SYSTEM')+".cfg"

    # Cleanup and exit
    if args.clean:
        input_handler.clean_temp_files()
        sys.exit(0)

    # Show isntalled and exit
    if args.installed:
        input_handler.show_installed()
        sys.exit(0)

    # Show available and exit
    if args.available:
        input_handler.show_available()
        sys.exit(0)

    # Remove installation and exit
    if args.remove != "none":
        input_handler.remove_app(args.remove)
        sys.exit(0)

    # Start builder
    utils.build_code(args)

    return 0

if __name__ == "__main__":
    sys.exit(main())
