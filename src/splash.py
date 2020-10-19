# System Imports
import os
import socket
from datetime import datetime

# Print welcome splash
def print_splash(glob):
    print("        ____  _______   __________  __   __________  ____  __ ")
    print("       / __ )/ ____/ | / / ____/ / / /  /_  __/ __ \/ __ \/ / ")
    print("      / __  / __/ /  |/ / /   / /_/ /    / / / / / / / / / /  ")
    print("     / /_/ / /___/ /|  / /___/ __  /    / / / /_/ / /_/ / /___")
    print("    /_____/_____/_/ |_/\____/_/ /_/    /_/  \____/\____/_____/")

    print("  ->User         :", glob.user)
    print("  ->System       :", glob.hostname)
    print("  ->$BENCHTOOL   :", glob.basedir)
    print("  ->Date         :", glob.time_str)
    print("------------------------------------------------------------------")

