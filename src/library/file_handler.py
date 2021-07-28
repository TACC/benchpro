# System imports
import glob as gb
import os
import pwd
import shutil as su

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Delete tmp build files if installation fails
    def remove_tmp_files(self):
        file_list = gb.glob(os.path.join(self.glob.basedir, 'tmp.*'))
        if file_list:
            for f in file_list:
                try:
                    os.remove(f)
                    self.glob.log.debug("Successfully removed tmp file "+f)
                except:
                    self.glob.log.debug("Failed to remove tmp file ", f)

    # Find file in directory
    def find_exact(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name

        # Search recursively for file
        files = gb.glob(path+'/**/'+file_name, recursive = True)

        if files:
            return files[0]
        else:
            return None

    # Confirm application exe is available
    def exists(self, fileName, code_path):

        if self.find_exact(fileName, code_path):
            return True
        else:
            return False

    # Find *file* in directory
    def find_partial(self, file_name, path):
        # Check file doesn't exist already
        if os.path.isfile(file_name):
            return file_name
        # Search provided path for file
        for root, dirs, files in os.walk(path):
            match = next((s for s in files if file_name in s), None)
            if match:
                return os.path.join(root, match)
        # File not found
        return None

    # Get owner of file
    def file_owner(self, file_name):
        return pwd.getpwuid(os.stat(file_name).st_uid).pw_name

    # Get a list of sub-directories, called by 'search_tree'
    def get_subdirs(self, base):
        return [name for name in os.listdir(base)
            if os.path.isdir(os.path.join(base, name))]

    # Recursive function to scan app directory, called by 'get_installed'
    def search_tree(self, installed_list, app_dir, start_depth, current_depth, max_depth):
        for d in self.get_subdirs(app_dir):
            if d != self.glob.stg['module_dir']:
                new_dir = os.path.join(app_dir, d)
                # Once tree hits max search depth, append path to list
                if current_depth == max_depth:
                    installed_list.append(self.glob.stg['sl'].join(new_dir.split(self.glob.stg['sl'])[start_depth + 1:]))
                # Else continue to search tree
                else:
                    self.search_tree(installed_list, new_dir, start_depth,current_depth + 1, max_depth)

    # Create directories if needed
    def create_dir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                self.glob.lib.msg.error(
                    "Failed to create directory " + path)

    # Get list of files in search path
    def get_files_in_path(self, search_path):
        return gb.glob(os.path.join(search_path, "*.cfg"))

    # Check if path exists, if so append .dup
    def check_dup_path(self, path):
        if os.path.isdir(path):
            return self.check_dup_path(path + ".dup")
        return path

    # Copy tmp files to directory
    def install(self, path, obj, new_obj_name, clean):

        # Get file name
        if not new_obj_name:
            new_obj_name = obj
            if self.glob.stg['sl'] in new_obj_name:
                new_obj_name = new_obj_name.split(self.glob.stg['sl'])[-1]

            # Strip tmp prefix from file for new filename
            if 'tmp.' in new_obj_name:
                new_obj_name = new_obj_name[4:]

        try:
            su.copyfile(obj, os.path.join(path, new_obj_name))
            self.glob.log.debug("Copied file " + obj + " into " + path)
        except IOError as e:
            self.glob.lib.msg.high(e)
            self.glob.lib.msg.error(
                "Failed to move " + obj + " to " + path + self.glob.stg['sl'] + new_obj_name)

        # Remove tmp files after copy
        if clean:
            os.remove(obj)

