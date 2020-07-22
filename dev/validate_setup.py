
import os 
import shutil as sh
import sys

def create_path(path)
    try:
        os.makedirs(path, exist_ok=True)
    except:
        print("Cannot create directory", path)
        sys.exit(2)

def confirm_path_exists(path):
    if not os.path.isdir(path):
        create_path(path)


def ensure_path_exists(path):
    if not os.path.isdir(path):
        print("Directory not found: ", path)
        sys.exit(2)


def ensure_file_exists(f):
    if not os.path.isdir(f):
        print("File not found: ", f)
        sys.exit(2)


def check_exe(exe):
    if not sh.which(exe):
        print("EXE not in PATH: ", exe)



#Check env vars - TACC_SYSTEM
