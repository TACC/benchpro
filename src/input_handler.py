import glob
import os
import time
import shutil as su

sl                  = "/"

def find_matching_files(search_dict):
    file_list=[]
    for search in search_dict:
        file_list += glob.glob(search)
    return file_list   

# Delete matching files
def clean_matching_files(file_list):
    tally=0
    for f in file_list:
        try:
            os.remove(f)
            tally +=1
        except:
            print("Error cleaning the file", f)
    return tally

# Delete appliation and module file 
def delete_dir(code_dict):
    top_dir = str(os.getcwd())
    if not code_dict[0] == "build":
        top_dir += sl + "build"

    app_dir = ""
    for d in code_dict:
        app_dir = app_dir + sl + d 

    mod_dir = top_dir + sl + "modulefiles" + sl.join(app_dir.split(sl)[:-1])
    app_dir = top_dir + app_dir

    if os.path.isdir(app_dir):
        print("Removing application installed in "+app_dir)
        print("Continuing in 10 seconds...")
        time.sleep(10)
        su.rmtree(app_dir)
        print("")
        print("Application removed.")

        try:
            su.rmtree(mod_dir)
            print("Module removed.")

        except:
            print("Warning, no module file located in "+mod_dir+". Skipping.")

    else:
        print("No application found in "+app_dir)

def clean_temp_files():
    print("Cleaning up temp files...")
    search_dict = ['*.o*',
                   '*.e*',
                   '*.log'
                  ]

    file_list = find_matching_files(search_dict)

    if file_list:
        print("Found the following files to delete:")
        for f in file_list:
            print(f)

        print("Continuing in 10 seconds...")
        time.sleep(10)
        print("No going back now...")
        deleted = clean_matching_files(file_list)
        print("Done, ", str(deleted), " files successfuly cleaned.")

    else:
        print("No temp files found.")

def remove_app(code_str):
    code_dict=code_str.split("/")
    delete_dir(code_dict)

def get_subdirs(base):
    return [name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))]

def recurse_down(app_dir):
    for d in get_subdirs(app_dir):
        if d != 'modulefiles':
            new_dir = app_dir + sl + d
            if d[0].isdigit():
                print("    "+sl.join(new_dir.split(sl, 2)[2:]))
            else:
                recurse_down(new_dir)

def show_installed():
    print("Currently installed applications:")
    print("---------------------------------")
    app_dir = "."+sl+"build" 
    recurse_down(app_dir)

def show_available():
    print("Available application profiles:")
    print("---------------------------------")
    app_dir = "."+sl+"config"+sl+"codes"+sl
    temp_files = glob.glob(app_dir+"*.cfg")    
    for f in temp_files:
        code = f.split('/')[-1]
        if not code == "default.cfg":
            print("    "+code[:-4])
 
