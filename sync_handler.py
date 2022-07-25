#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# sync_handler.py
# Copyright (C) 2022 TACC and contributors
# Set of functions to synchronize versions and manage user's settings.ini file
# Matthew Cawood
# July 2022

import configparser as cp
from git import Repo
from packaging import version
import shutil
import sys
import os

# Test whether .settings_master.ini is newer than settings.ini
def new_settings():
    """
    

    """
    bp_home = os.environ.get("BP_HOME")

    # Genreated file doesn't exist
    if not os.path.isfile(os.path.join(bp_home, "settings.ini")):
        return True
  
    # Get timestamp function

    #master = 
    #settings = 

    # Settings file exists but master is newer
    if master *newer* settings:
        shutil.move(os.path.join(bp_home, "settings.ini"), os.path.join(bp_home, ".settings.ini.old"))
        return True

    return False


# Compare values between new and old settings files, make updates where needed.
def resync_values():
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
        if os.path.isfile(os.path.join(bp_home, ".settings.ini.old")):
            resync_values()

        print("Done.")

# Get user's version        
def get_user_branch_from_env():
    branch = os.environ.get("BP_BRANCH")
    if branch and (branch != "[your-branch]"):
        return branch
    print("To checkout a remote branch, export BP_BRANCH=[your-branch]")
    return False

def get_current_user_branch():
    return git.Repo(search_parent_directories=True).active_branch.name

# 
def update_repo():
    branch = get_user_branch_from_env()

# 
def clone_repo():
    branch = get_user_branch_from_env()
    url = "https://github.com/mrcawood/csa.git"
    dest = os.path.join(os.environ.get("HOME"), ".benchpro")
    try:
        print("Cloning benchpro...")
        repo = Repo.clone_from(url, dest, progress=None)
        git_ = repo.git
        git_ = checkout(branch)

    except:
        print("Failed to clone repo " + url)
        sys.exit(1)

    for remote in repo.remotes:
        remote.fetch()

        print("Branch '" + branch + "' not found in remote repo:")
        print("------------------------------------------------")
        [print(n) for n in repo_heads_names]

# Compare client and site versions
def user_version():
    try:
        with open(os.path.join(os.environ.get("BP_HOME"),".version"), 'r') as ver:
            return version.parse(ver.readline().split(" ")[-1][1:].strip())
    except:
        return False

# Read site version from env
def site_version():
    return version.parse(os.environ.get("BP_SITE_VERSION"))

# Driver function to resync repos
def resync():

    # Get the version of the user files
    uv = user_version()
    sv = site_version()
    
    # No existing version found
    if not uv:
        clone_repo()

    # User is out of date
    elif uv < sv:    
        print("Your client files are behind BenchPRO's site version: v" + str(uv) + " < v" + str(sv))
        print("Updating now...")
        update_repo()

    # User is ahead (probably me)
    elif uv > sv: 
        print("Your client is ahead of the BenchPRO site version: v" + str(uv) + " > v" + str(sv))
        print("Did you checkout origin/dev ?")
        print("If so, make sure you're using the development site:")
        print("> ml use /scratch1/08780/benchpro/benchpro-dev/modulefiles")
        sys.exit(1)

    # Versions match - carry on
    elif uv == sv: 
        return

    # Catch-all
    else:
        print("Unknown version state:", uv, sv)
        sys.exit(1)

