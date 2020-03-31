#!/usr/bin/env python3

# System Imports
import argparse
import pprint as pp
import sys

# Local Imports
import src.exception as exception
import src.utils as utils


def main():
    # Initialization
    utils.init_log.debug("init_log initialized")
    utils.exception_log.debug("excpetion_log initialized")
    utils.build_log.debug("build_log initialized")

    # Parse cmd line args
    cmd_parser = argparse.ArgumentParser(
        description='Provide the cgf input file for you code you with to compile')
    cmd_parser.add_argument("--code", default="code.cfg",
                            type=str, help="Name of the code cfg file.")
    cmd_parser.add_argument("--sched", default="sched.cfg",
                            type=str, help="Name of the scheduler cfg file.")

    args = cmd_parser.parse_args()



    code_cfg = utils.read_cfg_file(utils.check_cmd_args(args.code))
    sched_cfg = utils.read_cfg_file(args.sched)


    #exception.var_not_filled(utils.exception_log)

    utils.build_code(code_cfg, sched_cfg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
