from datetime import datetime
import os
import socket

sl           = '/'

# Print welcome splash
def print_splash():
    print("")
    print("        ____  _______   __________  __   __________  ____  __ ")
    print("       / __ )/ ____/ | / / ____/ / / /  /_  __/ __ \/ __ \/ / ")
    print("      / __  / __/ /  |/ / /   / /_/ /    / / / / / / / / / /  ")
    print("     / /_/ / /___/ /|  / /___/ __  /    / / / /_/ / /_/ / /___")
    print("    /_____/_____/_/ |_/\____/_/ /_/    /_/  \____/\____/_____/")
    print("")

    print("------------------------------------------------------------------")
    print("User         :", str(os.getlogin()))
    print("System       :", str(socket.gethostname()))
    print("Working dir  :", sl.join(os.path.dirname(os.path.abspath(__file__)).split('/')[:-1]))
    print("Date         :", datetime.now())
    print("")
