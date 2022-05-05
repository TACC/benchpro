
# Print welcome splash
def get_splash(glob):
    return ["  ____  _____ _   _  ____ _   _ ____  ____   ___",
            " | __ )| ____| \ | |/ ___| | | |  _ \|  _ \ / _ \\", 
            " |  _ \|  _| |  \| | |   | |_| | |_) | |_) | | | |",
            " | |_) | |___| |\  | |___|  _  |  __/|  _ <| |_| |",
            " |____/|_____|_| \_|\____|_| |_|_|   |_| \_\\\\___/", 
            "  >User      : " + glob.user,
            "  >System    : " + glob.hostname,
            "  >Version   : " + glob.version_str,
            "  >$BP_HOME  : " + glob.bp_home]

