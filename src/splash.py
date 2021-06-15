
# Print welcome splash
def get_splash(glob):
    return ["        ____  _______   __________  __   __________  ____  __ ",
                        "       / __ )/ ____/ | / / ____/ / / /  /_  __/ __ \/ __ \/ / ",
                        "      / __  / __/ /  |/ / /   / /_/ /    / / / / / / / / / /  ",
                        "     / /_/ / /___/ /|  / /___/ __  /    / / / /_/ / /_/ / /___",
                        "    /_____/_____/_/ |_/\____/_/ /_/    /_/  \____/\____/_____/",

                        "  ->User         : " + glob.user,
                        "  ->System       : " + glob.hostname,
                        "  ->$BENCHTOOL   : " + glob.basedir,
                        "  ->Date         : " + glob.time_str]

