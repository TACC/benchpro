#!/usr/bin/env python3

# System Imports
import argparse
import pprint as pp
import sys

# Local Imports
try:
    import src.exception as exception
    import src.cleanup as cleanup
except ImportError as e:
    print("You had an import error, you might be using Python2. Please use Python3.")
    print(e)
    sys.exit(1)

def launch_builder(args):

    import src.utils as utils
    # Initialization
#    utils.exception_log.debug("excpetion_log initialized")
#    utils.build_log.debug("build_log initialized")

    # Evaulate & format user inputs
    code_cfg =  utils.read_cfg_file(utils.check_cmd_args(args.code))
    sched_cfg = utils.read_cfg_file(utils.check_cmd_args(args.sched))

    # Build code
    utils.build_code(code_cfg, sched_cfg)

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
    cmd_parser.add_argument("--remove", default="none",
                            help="Remove an installed application, format=[code]/[version]")


    args = cmd_parser.parse_args()

    #cleanup and exit
    if args.clean:
        cleanup.clean()
        print("Exitting")
        sys.exit(0)

    if args.remove != "none":
        cleanup.remove_app(args.remove)
        print("Exitting")
        sys.exit(0)

    launch_builder(args)

    return 0

if __name__ == "__main__":
    sys.exit(main())
