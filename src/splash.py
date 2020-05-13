from datetime import datetime
import os
import socket

# Print welcome splash
def print_splash():
    print("")
    print("     ___  __  ________   ___  _______")
    print("    / _ )/ / / /  _/ /  / _ \/ __/ _ \\")
    print("   / _  / /_/ // // /__/ // / _// , _/")
    print("  /____/\____/___/____/____/___/_/|_|")
    print("")

    print("--------------------------------------")
    print("User       :", str(os.getlogin()))
    print("System     :", str(socket.gethostname()))
    print("Project dir:", str(os.getcwd()))
    print("Date       :", datetime.now())

