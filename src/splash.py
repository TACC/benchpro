from datetime import datetime
import os
import socket

import src.global_settings as gs

# Print welcome splash
def print_splash():
    print("        ____  _______   __________  __   __________  ____  __ ")
    print("       / __ )/ ____/ | / / ____/ / / /  /_  __/ __ \/ __ \/ / ")
    print("      / __  / __/ /  |/ / /   / /_/ /    / / / / / / / / / /  ")
    print("     / /_/ / /___/ /|  / /___/ __  /    / / / /_/ / /_/ / /___")
    print("    /_____/_____/_/ |_/\____/_/ /_/    /_/  \____/\____/_____/")

    print("------------------------------------------------------------------")
    print("User         :", gs.user)
    print("System       :", gs.hostname)
    print("Working dir  :", gs.base_dir)
    print("Date         :", gs.time_str)
    print("")
