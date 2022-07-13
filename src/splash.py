
# Print welcome splash
def print_splash(glob):

    if not glob.quiet_build:

        glob.msg.high(  ["  ____  _____ _   _  ____ _   _ ____  ____   ___"],
                        [" | __ )| ____| \ | |/ ___| | | |  _ \|  _ \ / _ \\"], 
                        [" |  _ \|  _| |  \| | |   | |_| | |_) | |_) | | | |"],
                        [" | |_) | |___| |\  | |___|  _  |  __/|  _ <| |_| |"],
                        [" |____/|_____|_| \_|\____|_| |_|_|   |_| \_\\\\___/"], 
                        ["  >User      : " + glob.user],
                        ["  >System    : " + glob.hostname],
                        ["  >Version   : " + glob.version_site_full],
                        ["  >$BP_HOME  : " + glob.bp_home])

        if glob.log_file:
        
            glob.msg.high("  >Log       : " +
                           glob.lib.rel_path(os.path.join(glob.stg['log_path'], glob.log_file)))

        glob.msg.brk();

