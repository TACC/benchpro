import configparser as cp
import fileinput
import os
import shutil
import sys

# Package dir containing install files
src_dir = os.path.join("/", *os.path.dirname(os.path.abspath(__file__)).split("/")[:-1], "src")
path_dict = {}

def read_ini():

    # Read install.ini file
    ini_parser    = cp.ConfigParser()
    ini_parser.optionxform=str

    ini_parser.read(os.path.join(src_dir, "data", "install.ini"))

    # Check paths are defined
    for key in ['install_dir', 'build_dir', 'bench_dir']:
        if not ini_parser.has_option('paths', key):
            print("install.ini file missing required key '" + key + "'")
            sys.exit(1)

    print("Checking installation paths...")

    # Parse install paths
    ini = {section: dict(ini_parser.items(section)) for section in ini_parser.sections()}
    for path in list(ini["paths"].keys()):
        path_dict[path] = os.path.expandvars(ini["paths"][path])
        # Check envvars are resolved 
        if "$" in path_dict[path]:
            print("Unable to resolve variable in " + path_dict[path])
            sys.exit(1)

        #Set envvar for resolving other paths
        os.environ[path] = path_dict[path]

def check_status():

    # Check if installed already
    if os.path.isdir(path_dict['install_dir']):
        print("Existing installation located in " + path_dict["install_dir"])
        print("Please clean up before installing.")
        sys.exit(1)

    # Make install directory
    try:
        os.makedirs(path_dict['install_dir'])
    except OSError as e:
        print("Failed to create directory")
        print(e)

def update_settings():
    # Update settings.ini keys with install.ini paths
    setting_parser    = cp.ConfigParser()
    setting_parser.optionxform=str
    setting_parser.read(os.path.join(src_dir, "data", "settings.ini"))

    print("Updating settings.ini...")

    # Check each section
    for section in setting_parser.sections():
        # For matching key
        for key in path_dict.keys():
            if setting_parser.has_option(section, key):
                setting_parser.set(section, key, path_dict[key])

    # Write updates
    setting_parser.write(open(os.path.join(src_dir, "data", "settings.ini"), 'w'))

def update_paths():

    print("Updating project paths...")

    # Update benchtool with project path
    with fileinput.FileInput(os.path.join(src_dir, "benchtool"), inplace=True) as fp:
        for line in fp:
            if "basedir =" in line:
                print("    basedir = \"" + path_dict['install_dir'] + "\"", end = '\n')

            else:
                print(line, end ='')

    # Update module file with project paths
    with fileinput.FileInput(os.path.join(src_dir, "data", "modulefiles", "benchtool.lua"), inplace=True) as fp:
        for line in fp:
            if "local install_dir" in line:
                print("local install_dir    = \"" + path_dict['install_dir'] + "\"", end = '\n')
            elif "local build_dir" in line:
                print("local build_dir      = \"" + path_dict['build_dir'] + "\"", end = '\n')
            else:
                print(line, end ='')



    # Update sourceme script with build path
    with fileinput.FileInput(os.path.join(src_dir, "data", "sourceme"), inplace=True) as fp:
        for line in fp:
            if "BUILD=" in line:
                print("BUILD=\"" + path_dict['build_dir'] + "\"", end = '\n')

            else:
                print(line, end ='')

def copy_files():

    # Files/dirs to install
    install_dict = {path_dict['install_dir']:  [".version",
                                                "settings.ini",
                                                "install.ini",
                                                "README.md",
                                                "config/",
                                                "templates/",
                                                "resources/",
                                                "sourceme"],
                    path_dict['build_dir']:   ["modulefiles/"]
                    }

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
            fp.write("# Load benchtool environment \n")
            fp.write("source " + os.path.join(path_dict['install_dir'], "sourceme") + "\n" )
            fp.write("#### \n")

# Run installer
def run():

    read_ini()
    check_status()
    update_settings()
    update_paths()
    copy_files()
    update_bash()

    print("Done.")
    print("Run 'ml benchtool' in a new shell.")


