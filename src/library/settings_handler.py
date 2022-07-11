#!/usr/bin/env python3

import configparser as cp
import shutil
import os

# Set of functions to manage user's settings.ini file
# Matthew Cawood
# July 2022

# Test whether .settings_master.ini is newer than settings.ini
def new_settings():
    """
    

    """
    bp_home = os.environ("BP_HOME")

    # Genreated file doesn't exist
    if not os.path.isfile(os.path.join(bp_home, "settings.ini")):
        return True
  
    # Get timestamp function

    master = 
    settings = 

    # Settings file exists but master is newer
    if master *newer* settings:
        shutil.move(os.path.join(bp_home, "settings.ini"), os.path.join(bp_home, ".settings.ini.old"))
        return True

    return False


# Compare values between new and old settings files, make updates where needed.
def resync_values()
    """

    """
            
    new = cp.ConfigParser(os.path.join(bp_home, "settings.ini"))
    old = cp.ConfigParser(os.path.join(bp_home, ".settings.ini.old"))

    # Update different value from old settings to new settings file
    for sect in old:
        for key in sect:
            if key in new[sect]:
                if old[sect][key] != new[sect][key]:
                    print("Reassigned " + key + " " + old[sect][key] + " -> " + new[sect][key])
                    new[sect][key] = old[sect][key]
            else:
                print("Disregarded obsolete settings entry '" + key + "=" + old[sect][key]  + "'")

    new.close()
    old.close()

    # Delete old settings file
    shutil.delete(os.path.join(bp_home, ".settings.ini.old"))

# Update settings.ini
def update_settings():
    """

    """
    
    # Copy new version of settings
    if new_settings():

        print("Updating settings.ini...")

        shutil.copy(os.path.join(bp_home, ".settings_master.ini"), os.path.join(bp_home, "settings.ini"))

        # Old settings file exists
        if os.path.isfile(os.path.join(bp_home, ".settings.ini.old"):
            resync_values()

        print("Done.")


