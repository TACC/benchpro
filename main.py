#!/usr/bin/env python3

# System Imports
import argparse
import pprint as pp
import sys

# Local Imports
try:
    import src.utils as utils
    import src.exception as exception
    import src.cleanup as cleanup
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
    cmd_parser.add_argument("--sched", default="sched.cfg",
                            type=str, help="Name of the scheduler cfg file.")
    cmd_parser.add_argument("--clean", default=False, action='store_true',
                            help="Cleanup temp and log files.")
    cmd_parser.add_argument("--show", default=False, action='store_true',
                            help="Show all installed applications.")
    cmd_parser.add_argument("--remove", default="none",
                            help="Remove an installed application, format=[code]/[version]")


    args = cmd_parser.parse_args()

    # Cleanup and exit
    if args.clean:
        cleanup.clean_temp_files()
        print("")
        print("")
        print("Done")
        sys.exit(0)

    # Print list and exit
    if args.show:
        utils.show_installed()
        print("")
        print("")
        print("Done")
        sys.exit(0)

    # Remove installation and exit
    if args.remove != "none":
        cleanup.remove_app(args.remove)
        print("")
        print("")
        print("Done")
        sys.exit(0)



    # Start builder
    utils.build_code(args)

    return 0

if __name__ == "__main__":
    sys.exit(main())
