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
    print("You had an import error, you might be using Python2. Please run 'source load.sh'")
    print(e)
    sys.exit(1)

def main():

    # Parse cmdline args
    cmd_parser = argparse.ArgumentParser(
        description='This is a builder tool for managing appliation benchmarks.')
    cmd_parser.add_argument("--install", default=False,
                            type=str, help="Name of the code cfg file to install")
    cmd_parser.add_argument("--sched", default="system",
                            type=str, help="Name of the scheduler cfg file.")
    cmd_parser.add_argument("--run", default=False,
                            type=str, help="Run an installed application, run '--show-installed' for valid options.")
    cmd_parser.add_argument("--clean", default=False, action='store_true',
                            help="Cleanup temp and log files.")
    cmd_parser.add_argument("--installed", default=False, action='store_true',
                            help="Show all installed applications.")
    cmd_parser.add_argument("--avail", default=False, action='store_true',
                            help="Show all available application profiles.")
    cmd_parser.add_argument("--remove", default=False,
                            help="Remove an installed application, run '--show-installed' for valid options.")


    args = cmd_parser.parse_args()
    print()

    # Use system default scheduler profile 
    if args.sched == "system":
        args.sched = "slurm-"+os.getenv('TACC_SYSTEM')+".cfg"

    # Start builder
    if args.install:
        utils.build_code(args)

    # Start runner
    elif args.run:
        utils.build_code(args)

    # Cleanup and exit
    elif args.clean:
        input_handler.clean_temp_files()

    # Show isntalled and exit
    elif args.installed:
        input_handler.show_installed()

    # Show available and exit
    elif args.avail:
        input_handler.show_available()

    # Remove installation and exit
    elif args.remove:
        input_handler.remove_app(args.remove)

    # No seletion provided
    else:
        print("Try 'build.py --help' for more information.")

    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())