# System imports
import logging as lg
import os

#Local Imports 
import src.splash as splash

# Start logger and return obj
def start_logging(log_label, log_file, glob):

    log_path = os.path.join(glob.stg['log_path'], log_file)

    formatter = lg.Formatter("{0}: ".format(log_label) + glob.user + "@" + glob.hostname + ": " + \
                             "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    glob.log = lg.getLogger(log_label)
    glob.log.setLevel(1)

    file_handler = lg.FileHandler(log_path, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    glob.log.addHandler(file_handler)
    glob.log.debug(log_label+" log started")

    # Print info
    stdout = splash.get_splash(glob)
    glob.lib.msg.high(stdout + 
                    ["  ->Log          : " + os.path.join(glob.stg['project_env_var'], glob.stg['log_dir'], log_file)]
                    +["------------------------------------------------------------------"])
    
