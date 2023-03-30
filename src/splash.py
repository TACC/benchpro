#!/bin/env python3

#
# Splash screen printer
# Prints BenchPRO header (if not in quiet mode)
# Matthew Cawood
# September 2021
# v1.0

import os
import sys


def output(glob):

    splash = ["  ____  _____ _   _  ____ _   _ ____  ____   ___",
              " | __ )| ____| \ | |/ ___| | | |  _ \|  _ \ / _ \\",
              " |  _ \|  _| |  \| | |   | |_| | |_) | |_) | | | |",
              " | |_) | |___| |\  | |___|  _  |  __/|  _ <| |_| |",
              " |____/|_____|_| \_|\____|_| |_|_|   |_| \_\\\\___/",
              "  >User      : " + glob.user,
              "  >System    : " + glob.hostname,
              "  >Version   : " + glob.version_site_full,
              "  >$BP_HOME  : " + glob.ev['BP_HOME']]
    try:
        splash.append(
            "  >Log       : " +
            glob.lib.rel_path(os.path.join(
                glob.stg['log_path'], glob.log_file)))

    except:
        pass

    glob.lib.msg.high(splash)
    glob.lib.msg.brk()


# Print welcome splash
def print_splash(glob):

    if not glob:
        sys.exit(0)

    else:
        if not glob.quiet_build:
            output(glob)
