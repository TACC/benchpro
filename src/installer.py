import configparser as cp
import fileinput
import glob
import os
import shutil
import sys
import time


# Package dir containing install files
src_dir = os.path.join("/", *os.path.dirname(os.path.abspath(__file__)).split("/")[:-1], "src")
path_dict = {}
key_path = None

# Read install param file
def read_ini(settings):
   
    global key_path, path_dict

    # default install.ini file
    install_file = os.path.join(src_dir, "data", "install.ini")

    # if user settings file defined
    if settings:
        if os.path.isfile(settings):
            install_file = settings
        else:
            print("Input file '" + settings + "' not found!")
            exit(1)

    # Read install.ini file
    ini_parser    = cp.ConfigParser()
    ini_parser.optionxform=str

    ini_parser.read(install_file)

    print("Checking installation paths...")

    # Check paths are defined
    for key in ['home_dir', 'build_dir', 'bench_dir']:
        if not ini_parser.has_option('paths', key):
            print("Input file '" + os.path.basename(install_file) + "' missing required key '" + key + "' in [paths]")
            sys.exit(1)

    # Read SSH key location
    if ini_parser.has_option('key','key'):
        if ini_parser['key']['key']:
            key_path = ini_parser['key']['key']

    # Parse install paths
    ini = dict(ini_parser.items('paths'))
    for path in list(ini.keys()):
        path_dict[path] = os.path.expandvars(ini[path])
        # Check envvars are resolved 
        if "$" in path_dict[path]:
            print("Unable to resolve variable in " + path_dict[path])
            sys.exit(1)

        #Set envvar for resolving other paths
        os.environ[path] = path_dict[path]

# Check that existing install isn't present
def check_status():
    for path in list(path_dict.keys()):
        # Check if installed already
        if os.path.isdir(path_dict[path]):
            print("Existing installation files found in " + path_dict[path])
            print("Please clean up before installing.")
            sys.exit(1)

    # Make install directory
    try:
        os.makedirs(path_dict['home_dir'])
    except OSError as e:
        print("Failed to create directory")
        print(e)

# Copy packge files to user directory
def copy_files(install_dict):

    # Copy files into install directory
    for dest in list(install_dict.keys()):
        for item in install_dict[dest]:
            print("Installing " + item + "...")
            # Assume directory copy
            try:
                shutil.copytree(os.path.join(src_dir, "data", item), os.path.join(dest, item))
            except OSError as e:
                # Try file copy
                try:
                    os.makedirs(dest, exist_ok=True)
                    shutil.copy(os.path.join(src_dir, "data", item), dest)
                # Copy fail
                except OSError as e:
                    print("Failed to install " + os.path.join(src_dir, "data", item) + " to " + dest)
                    print(e)
                    sys.exit(1)


def install_files():
    install_dict = {path_dict['home_dir']:  [".version",
                                                "settings.ini",
                                                "install.ini",
                                                "README.md",
                                                "config/",
                                                "templates/",
                                                "resources/"]
#                    path_dict['build_dir']:   ["modulefiles/benchtool/"]
                    }
    copy_files(install_dict)

def update_files():
    install_dict = {path_dict['home_dir']:  [".version",
                                                "settings.ini",
                                                "install.ini",
                                                "README.md",
                                                "config/",
                                                "templates/",
                                                "resources/"]
                    }
    copy_files(install_dict)

# Insert contextualized paths in settings.ini
def update_settings():

    global path_dict
    # Update settings.ini keys with install.ini paths
    setting_parser    = cp.ConfigParser()
    setting_parser.optionxform=str
    setting_parser.read(os.path.join(path_dict['home_dir'], "settings.ini"))

    print("Updating settings.ini...")

    # Check each section
    for section in setting_parser.sections():
        # For matching key
        for key in path_dict.keys():
            if setting_parser.has_option(section, key):
                setting_parser.set(section, key, path_dict[key])

    # Write updates
    setting_parser.write(open(os.path.join(path_dict['home_dir'], "settings.ini"), 'w'))

# Update module
def update_module():
    print("Updating module file...")
    mod_file = glob.glob(os.path.join(path_dict['build_dir'], "modulefiles", "benchtool", "*.lua"))
    version = ".".join(os.path.basename(mod_file[0]).split(".")[:-1])
    # Update module file with project paths
    with fileinput.FileInput(mod_file, inplace=True) as fp:
        for line in fp:
            if "local project_dir" in line:
                print("local project_dir     = \"" + path_dict['home_dir'] + "\"", end = '\n')
            elif "local app_dir" in line:
                print("local app_dir         = \"" + path_dict['build_dir'] + "\"", end = '\n')
            elif "local result_dir" in line:
                print("local result_dir      = \"" + path_dict['bench_dir'] + "\"", end = '\n' )
            elif "local version" in line:
                print("local version         = \"" + version + "\"", end = '\n' )
            else:
                print(line, end ='')

# Add benchtool in user .bashrc
def update_bash():
    print("Updating .bashrc...")
    # Check its not in bash file already
    in_bash = False
    with open(os.path.expandvars("$HOME/.bashrc")) as fp:
        if "benchtool" in fp.read():
            in_bash = True

    # Update .bachrc
    if not in_bash:
        with open(os.path.expandvars("$HOME/.bashrc"), "a") as fp: 
            fp.write("# BENCHTOOL \n")
            fp.write("export MODULEPATH=$MODULEPATH:" + os.path.join(path_dict['build_dir'], "modulefiles") + "\n" )
            fp.write("ml benchtool")

# Copy SSH key if its defined
def copy_key():

    global key_path
    if key_path:
        print("Copying SSH key...")
        try:
            if os.path.isfile(key_path):
                dest = os.path.join(path_dict['home_dir'], "auth")
                os.makedirs(dest, exist_ok=True)
                shutil.copy(key_path, os.path.join(dest, os.path.basename(key_path)))
            else:
                print("Provided key not found, skipping...")
        except:
            print("Unable to copy SSH key provided in install.ini")
    else:
        print("No key provided, skipping...")

# Touch file to indicate successful install
def success():
    open(os.path.join(path_dict['home_dir'], ".installed"),'w')

def ml():
    os.environ['MODULEPATH'] = os.environ['MODULEPATH'] + ":" + os.path.join(path_dict['build_dir'], "modulefiles")

def check_env():
    try:
        print("Project directory = " + os.environ["BT_HOME"])
    except:
        print("Ensure benchtool module is loaded before continuing.")
        sys.exit(1)

# Check benchtool is installed
def is_installed(path):
    if not path:
        print("$BT_HOME not set, is the benchtool module loaded?")
        sys.exit(0)
    
    if not os.path.isfile(os.path.join(path, ".installed")):
        print("Benchtool is not installed in $BT_HOME")
        sys.exit(0)

# Delete project directories for uninstall
def remove_dirs(path_list):
    global path_dict
    for path in path_list:
        print("Deleting " + path_dict[path] + "...")
        if os.path.isdir(path_dict[path]):
            shutil.rmtree(path_dict[path])

# Rewrite package config files into $BT_HOME
def overwrite():
    global src_dir
    root_src_dir = os.path.join(src_dir, "data")
    root_dst_dir = os.path.expandvars("$BT_HOME")

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                # in case of the src and dst are the same file
                if os.path.samefile(src_file, dst_file):
                    continue
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)

# Run installer
def install(settings):

    read_ini(settings)
    check_status()
    install_files()
    update_settings()
#    update_module()
    update_bash()
    copy_key()
    success()
    ml()

    print()
    print("Done.")
    print("Now run:")
    print("source ~/.bashrc")
    print("ml benchtool")

# Run uninstaller
def uninstall():

    home_path = os.path.expandvars("$BT_HOME")
    is_installed(home_path)

    print("\033[0;31m!!!DELETING ALL APPLICATIONS, RESULTS AND CONFIG DATA!!!\033[0m")
    print("Coninuing in 5 seconds...")
    time.sleep(5)

    is_installed(home_path)
    check_env()
    read_ini(os.path.join(home_path, "settings.ini"))
    remove_dirs(list(path_dict.keys()))

# Overwrite config files from package
def update():
    read_ini(False)
    check_env()
    remove_dirs(['home_dir'])
    update_files()
    update_settings()
    copy_key()
    success()
    print("Done.")
