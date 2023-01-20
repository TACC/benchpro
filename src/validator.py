#!/usr/bin/env python3

# System Imports
import configparser as cp
import grp
import os
from packaging import version
from pathlib import Path
import shutil as sh
import stat
import subprocess
import sys
import time

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
    WARN = '\033[1;33mWARNING \033[0m'

# Check python version
def check_python_version():
    ver = sys.version.split(" ")[0]
    if (ver[0] == 3) and (ver[1] < 5):
        print(bcolors.FAIL, "Python version: " + ver)
        sys.exit(1)
    else:
        print(bcolors.PASS, "Python version: " + ver)

# Create path
def create_path(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(bcolors.CREATE, path)
    except BaseException:
        print(bcolors.FAIL, "cannot create", path)
        sys.exit(1)

# Check that the user belongs to the 'gid' they provided 
def check_group_membership():

    if glob.stg['set_gid']:
        gid = glob.stg['gid']
        if not gid[0].isdigit(): 
            gid = int(gid.split('-')[1])
        
        grouplist = os.getgrouplist(os.environ.get('USER'), 100)
        if not gid in grouplist:
            print(bcolors.FAIL, "you don't belong to gid " + glob.stg['gid'] + " (" + gid + ")")
            sys.exit(1)

# Walk FS and recursively chown everything (i.e. chgrp -R) (yes, there is no function for this)
def chgrp(path, group):

    gid = grp.getgrnam(group).gr_gid

    if os.path.isdir(path):
        # Chgrp on top dir
        os.chown(path, -1, gid)
    
        try:

            for curDir,subDirs,subFiles in os.walk(path):
                # Chgrp on subFiles
                for file in subFiles:
                    absPath = os.path.join(curDir,file)
                    os.chown(absPath,-1,gid)
                # Recurse through subDirs
                for dir in subDirs:
                    chgrp(os.path.join(curDir,dir), group)
        except:
            pass

# Set group set bit 
def sticky_bit(path):
    os.chmod(path, 0o3775) 
    try:
        subprocess.call(['setfacl', '-d', '-m', 'group::rX', path])
    except:
        print(bcolors.FAIL, "Can't execute setfacl...")
        sys.exit(1)

    print(bcolors.SET, path, "ACLs")

# Open group access
def give_group_access(path_list):

    for path in path_list:
        try:
            os.chmod(path, 0o755)
            print(bcolors.SET, path, "755")
            parent = str(Path(path).parent.absolute())
            give_group_access([parent])
        except Exception as e:
            pass

# Set perms on output dirs
def set_permissions(path_list):
    if glob.stg['set_gid']:
        print("path_list", path_list)
        for path in path_list:
            chgrp(path, glob.stg['gid'])
            sticky_bit(path)
            print(bcolors.SET, path, glob.stg['gid'])
        
# Create path if not present
def confirm_path_exists(path_list):
    for path in path_list:
        # We got a path list 
        if isinstance(path, list): 
            # Assume [0] = user, [1] = site
            path = path[0]

        if path[0:2] == "./":
            path = os.path.join(glob.ev['BP_HOME'], path[2:])
            print("path", path)
            sys.exit(1)
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
            sys.exit(1)

# Test if file exists
def ensure_file_exists(f):
    if os.path.isfile(f):
        print(bcolors.PASS, "file", f, "found")
    else:
        print(bcolors.FAIL, "file", f, "not found")
        sys.exit(1)

# Test if executable is in PATH
def check_exe(exe_list):
    for exe in exe_list:
        if sh.which(exe):
            print(bcolors.PASS, exe, "in PATH")
        else:
            print(bcolors.FAIL, exe, "not in PATH")
            sys.exit(1)

# Test environment variable is set
def check_env_vars(var_list):
    for var in var_list:
        if os.environ.get(var):
            print(bcolors.PASS, var, "is set")
        else:
            print(bcolors.FAIL, var, "not set")
            print("Is benchpro module loaded?")
            sys.exit(1)

# Test write access to dir
def check_write_priv(path_list):
    for path in path_list:
        if os.access(path, os.W_OK | os.X_OK):
            print(bcolors.PASS, path, "is writable")
        else:
            print(bcolors.FAIL, path, "is not writable")
            sys.exit(1)

# Check file permissions
def check_file_perm(filename, perm):
    if os.path.isfile(filename):
        os.chmod(filename, perm)
        print(bcolors.PASS, filename, "permissions set")
    else:
        print(bcolors.WARN, filename, "not found.")

# Confirm SSH connection is successful
def check_db_access(glob):

    if glob.stg['db_host']:
        # Test connection
        try:
            status = subprocess.getstatusoutput(
                "ping -c 1 " + glob.stg['db_host'])
            # Pass
            if status[0] == 0:
                print(bcolors.PASS, "connected to", glob.stg['db_host'])
                return True

            # Fail
            else:
                print(
                    bcolors.WARN,
                    "Unable to access " +
                    glob.stg['db_host'] +
                    " from this server")
                return False

        # Fail
        except subprocess.CalledProcessError as e:
            print(
                bcolors.WARN,
                "Unable to access " +
                glob.stg['db_host'] +
                " from this server")
            return False

    # Fail
    else:
        print(
            bcolors.WARN,
            "Unable to access " +
            glob.stg['db_host'] +
            " from this server")
        return False

# Confirm database connection
def check_db_connect(glob):
    try:
        conn = psycopg2.connect(
            dbname=glob.stg['db_name'],
            user=glob.stg['db_user'],
            host=glob.stg['db_host'],
            password=glob.stg['db_passwd']
        )
    except Exception as err:
        print(
            bcolors.WARN,
            "unable to connect to " +
            glob.stg['db_name'] +
            " from this server")
        print("    This server is not on the database access whitelist, contact your maintainer.")

        return

    print(bcolors.PASS, "connected to", glob.stg['db_name'])

# Ensure client and site versions match
def check_benchpro_version(glob):

    # Check client/site versions match
    if not glob.lib.version_match():
        print(
            bcolors.FAIL,
            "version mismatch, site version='" +
            glob.version_site +
            "', your version='" +
            glob.version_client +
            "'")
        print("run git -C $BP_HOME pull")
        sys.exit(1)
    else:
        print(bcolors.PASS, "BenchPRO version " + glob.version_site)

def run():

    # Python version
    check_python_version()


    # Check benchpro version
    #check_benchpro_version(glob)

    # Sys envs
    home_env    = glob.stg['home_env'].strip("$")
    repo_env    = glob.stg['repo_env'].strip("$")
    site_env    = glob.stg['site_env'].strip("$")
    apps_env    = glob.stg['apps_env'].strip("$")
    results_env = glob.stg['results_env'].strip("$")
    system_env  = glob.stg['system_env'].strip("$")

    # check EVs set
    check_env_vars([home_env,
                    repo_env,
                    site_env,
                    apps_env,
                    results_env,
                    system_env,
                    'BPS_VERSION',
                    'LMOD_VERSION'])

    # Check priv

    # Check group memebership
    #check_group_membership()

    # Check paths
    confirm_path_exists([glob.ev['BP_HOME'],
                        glob.ev['BP_REPO'],
                        glob.ev['BP_APPS'],
                        glob.ev['BP_RESULTS'],
                        glob.stg['build_tmpl_path'],
                        glob.stg['build_cfg_path'],
                        glob.stg['bench_tmpl_path'],
                        glob.stg['bench_cfg_path'],
                        glob.stg['user_bin_path'],
                        glob.stg['user_resource_path'],
                        glob.stg['log_path'],
                        glob.stg['pending_path'],
                        glob.stg['captured_path'],
                        glob.stg['failed_path']])

    # Check user write access
    check_write_priv([glob.ev['BP_HOME'],
                    glob.ev['BP_APPS'],
                    glob.ev['BP_RESULTS']])


    # Set access
    give_group_access([glob.ev['BP_APPS'],
                       glob.ev['BP_RESULTS']])

    # Set perms
#    set_permissions([glob.ev['BP_APPS'],
#                     glob.ev['BP_RESULTS']])

    # Error if dir not found
    ensure_path_exists([glob.ev['BPS_HOME'],
                        glob.ev['BPS_COLLECT']])

    # Check exe
    check_exe(['benchpro', 'benchset', 'stage', 'sinfo', 'sacct', 'git'])

    # Check db host access
    connection = check_db_access(glob)

    # Check db connection
    if db and connection:
        check_db_connect(glob)
    else:
        print(bcolors.WARN, "database access check disabled")

    # Create validate file
    with open(os.path.join(glob.ev['BP_HOME'], ".validated"), 'w') as val:
        val.write(os.environ.get("BPS_VERSION_STR").split(".")[-1])
    print("Done.")
    return

# Test if our validation is out to date
def we_need_to_validate():
    if os.path.isfile(os.path.join(glob.ev['BP_HOME'], ".validated")):
        # File exists
        with open(os.path.join(glob.ev['BP_HOME'], ".validated"), 'r') as fp:
            your_ver = fp.read().strip()

        req_ver = os.environ.get("BPS_VERSION_STR").split(".")[-1]
        # Compare validation versions
        if str(your_ver) == str(req_ver):
            return False

    return True

# Check if validation has been run
def check(glob_obj, force):

    global glob
    glob = glob_obj

    if we_need_to_validate() or force:
        run()

