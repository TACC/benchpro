#!/usr/bin/env python3

#System Imports
import configparser as cp
import os 
import shutil as sh
import subprocess
import sys

db = True
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    db = False
    print("No psycopg2 module available, db access will not be available!")
    
glob = None

# ANSI escape squence for text color
class bcolors:
    PASS = '\033[92mPASS:\033[0m'
    FAIL = '\033[91mFAIL:\033[0m'
    CREATE = '\033[94mCREATE:\033[0m'
    SET = '\033[94mSET:\033[0m'

# Check python version 
def check_python_version():
    ver = sys.version.split(" ")[0]
    if (ver[0] ==  3) and (ver[1] < 5):
        print(bcolors.FAIL, "Python version: " + ver)
    else:
        print(bcolors.PASS, "Python version: " + ver)

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
        if os.path.isdir(os.path.expandvars(path)):
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

# Check file permissions
def check_file_perm(filename, perm):
    if os.path.isfile(filename):
        os.chmod(filename, perm)
        print(bcolors.PASS, filename, "permissions set")
    else:
        print(bcolors.FAIL, filename, "not found.")

# Confirm SSH connection is successful
def check_ssh_connect(host, user, key):
    try:
        expr = "ssh -i " + key +" " + user + "@" + host + " -t echo 'Client connection test'"
        cmd = subprocess.run(expr, shell=True, check=True, capture_output=True, universal_newlines=True)
        print(bcolors.PASS, "connected to", host)

    except subprocess.CalledProcessError as e:
        print(bcolors.FAIL, "connected to", host)

def check_db_connect(glob):
    try:
        conn = psycopg2.connect(
            dbname =    glob.stg['db_name'],
            user =      glob.stg['db_user'],
            host =      glob.stg['db_host'],
            password =  glob.stg['db_passwd']
        )
    except Exception as err:
        print (bcolors.FAIL, "connected to", glob.stg['db_name'])
        sys.exit(1)

    print (bcolors.PASS, "connected to", glob.stg['db_name'])



# Validate setup 
def check_setup(glob_obj):
    global glob
    glob = glob_obj

    # Python version
    check_python_version()

    # Sys envs
    base_env = glob.stg['topdir_env_var'].strip("$")
    system_env = glob.stg['system_env'].strip("$")
    check_env_vars([system_env, base_env, 'LMOD_VERSION'])

    # Check priv
    base_dir = os.environ.get(base_env)
    check_write_priv(base_dir)

    # Check paths
    confirm_path_exists([glob.stg['log_path'], glob.stg['build_path'], glob.stg['bench_path'], glob.stg['current_path'], glob.stg['archive_path']])
    ensure_path_exists([glob.stg['benchmark_repo'], glob.stg['config_path'], glob.stg['template_path']])

    # Check exe
    check_exe(['benchtool', 'sinfo', 'sacct'])

    # Check permissions
    check_file_perm(os.path.join(glob.stg['ssh_key_dir'], glob.stg['ssh_key'] ), 0o600)

    # Check db host access
    check_ssh_connect(glob.stg['db_host'], glob.stg['ssh_user'], os.path.join(base_dir, "auth", glob.stg['ssh_key']))

    # Check db access
    if db:
        check_db_connect(glob)
    else: 
        print(bcolors.FAIL, "no psycopg2, no db access")

    # Create validate file
    with open(os.path.join(glob.basedir, ".validated"), 'w'): pass 
