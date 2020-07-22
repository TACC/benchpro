import logging as lg

# Start logger and return obj
def start_logging(log_label, log_file, glob):

    log_path = glob.stg['log_path'] + glob.stg['sl'] + log_file

    print("Log file:   " + glob.stg['topdir_env_var'] + glob.stg['sl'] + glob.stg['log_dir'] + log_file)
    print()

    formatter = lg.Formatter("{0}: ".format(log_label) + glob.user + "@" + glob.hostname + ": " + \
                             "%(asctime)s: %(filename)s;%(funcName)s();%(lineno)d: %(message)s")

    log = lg.getLogger(log_label)
    log.setLevel(1)

    file_handler = lg.FileHandler(log_path, mode="w", encoding="utf8")
    file_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    log.debug(log_label+" log started")

    return log

