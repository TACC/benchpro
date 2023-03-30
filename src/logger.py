# System imports
import logging as lg
import os

# Local Imports
import src.splash as splash


# Start logger and return obj
def start_logging(log_label, log_file, glob):

    glob.log_file = log_file

    # Log file location
    log_path = os.path.join(glob.stg['log_path'], glob.log_file)

    formatter = lg.Formatter("{0}: ".format(log_label) + glob.user + "@" +
                            glob.hostname + ": " +
                            "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    # Init logger
    glob.log = lg.getLogger(log_label)
    glob.log.setLevel(1)

    file_handler = lg.FileHandler(log_path, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    glob.log.addHandler(file_handler)
    glob.log.debug(log_label + " log started")

    # Print splash
    splash.print_splash(glob)

    # Print hint
    glob.lib.msg.print_hint()
