#!/usr/bin/env python3

import argparse
import os
import sys

try:
    import src.utils as utils
except ImportError as e:
    print("You had an import error, you might be using Python2. Please use Python3.")
    print(e)
    sys.exit(1)

sl = '/'
# Check input

def get_subdirs(base):
    return [name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))]

def recurse_down(installed_list, app_dir, depth):
    for d in get_subdirs(app_dir):
        if d != 'modulefiles':
            new_dir = app_dir + sl + d
            if depth == 5:
                installed_list.append(sl.join(new_dir.split(sl, 2)[2:]))
            else:
                recurse_down(installed_list, new_dir, depth+1)

# Print currently installed apps, used together with 'remove'
def get_installed():
    app_dir = "."+sl+"build"
    installed_list = []
    recurse_down(installed_list, app_dir, 0)
    return installed_list


def check_if_installed(requested_code):
    installed_list = get_installed()
    matched_codes = []
    for code_string in installed_list:
        if requested_code in code_string:
            matched_codes.append(code_string)

    if len(matched_codes) == 0:
        print("No installed applications match your selection '"+requested_code+"'")
        print("Currently installed applications:")
        for code in installed_list: print("    "+code)
        sys.exit(1)

    elif len(matched_codes) == 1:
        print("Using application installed in:")
        print("    "+matched_codes[0])
        return matched_codes[0]

    else:
        print("Multiple installed applications match your selection '"+requested_code+"':")
        for code in matched_codes: print("    "+code)
        print("Please be more specific.")
        sys.exit(1)


cmd_parser = argparse.ArgumentParser(
    description='Provide the cgf input file for you code you want to compile')
cmd_parser.add_argument("--code", default="default.cfg",
                        type=str, help="Name of the code to run.")
cmd_parser.add_argument("--sched", default="system",
                        type=str, help="Name of the scheduler cfg file.")
cmd_parser.add_argument("--config", default="default",
                        type=str, help="Custom cfg file.")

args = cmd_parser.parse_args()

code_path = check_if_installed(args.code)

#get_installed()
