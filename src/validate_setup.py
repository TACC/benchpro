#!/usr/bin/env python3

#System Imports
import configparser as cp
import os 
import shutil as sh
import subprocess
import sys

glob = None

# ANSI escape squence for text color
class bcolors:
    PASS = '\033[92mPASS:\033[0m'
    FAIL = '\033[91mFAIL:\033[0m'
    CREATE = '\033[94mCREATE:\033[0m'

# Create path
def create_path(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(bcolors.CREATE, path)
    except:
        print(bcolors.FAIL, "cannot create", path)

# Create path if not present
def confirm_path_exists(path_list):
    for path in path_list:
        if not os.path.isdir(path):
            create_path(path)
        else:
            print(bcolors.PASS, path, "found")

# Test if path exists
def ensure_path_exists(path_list):
    for path in path_list:
        if os.path.isdir(path):
            print(bcolors.PASS, path, "found")
        else:
            print(bcolors.FAIL, path, "not found")

# Test if file exists
def ensure_file_exists(f):
    if os.path.isdir(f):
        print(bcolors.PASS, "file", f, "found")
    else:
        print(bcolors.FAIL, "file", f, "not found")

# Test if executable is in PATH
def check_exe(exe_list):
    for exe in exe_list:
        if sh.which(exe):
            print(bcolors.PASS, exe, "in PATH")
        else:
            print(bcolors.FAIL, exe, "not in PATH")

# Test environment variable is set
def check_env_vars(var_list):
    for var in var_list:
        if os.environ.get(var):
            print(bcolors.PASS, var, "is set")
        else:
            print(bcolors.FAIL, var, "not set")
            print("Did you run 'source sourceme'")
            sys.exit(1)
    
# Test write access to dir
def check_write_priv(path):
    if os.access(path, os.W_OK | os.X_OK): 
        print(bcolors.PASS, path, "is writable")
    else:
        print(bcolors.FAIL, path, "is not writable")

# Confirm SSH connection is successful
def check_ssh_connect(host, user, key):
    try:
        expr = "ssh -i " + key +" " + user + "@" + host + " -t echo 'Client connection test'"
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)
        print(bcolors.PASS, "connected to", host)

    except subprocess.CalledProcessError as e:
        print(bcolors.FAIL, "connected to", host)

# Validate setup 
def check_setup(glob_obj):
    global glob
    glob = glob_obj

    base_env = glob.stg['topdir_env_var'].strip("$")
    system_env = glob.stg['system_env'].strip("$")

    check_env_vars([system_env, base_env, 'LMOD_VERSION'])
    base_dir = os.environ.get(base_env)
    check_write_priv(base_dir)

    confirm_path_exists([glob.stg['log_path'], glob.stg['build_path']])

    ensure_path_exists([glob.stg['benchmark_repo'], glob.stg['config_path'], glob.stg['template_path']])
    check_exe(['benchtool', 'sinfo', 'sacct'])
    check_ssh_connect(glob.stg['db_host'], glob.stg['ssh_user'], os.path.join(base_dir, "auth", glob.stg['ssh_key']))
