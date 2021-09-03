# System imports
import glob as gb
import os
import pwd
import shutil as su
import tarfile
import urllib.request

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

    # Confirm file exists
    def exists(self, fileName, path):

        if self.find_exact(fileName, path):
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
                "Failed to move " + obj + " to " + os.path.join(path, new_obj_name))

        # Remove tmp files after copy
        if clean:
            os.remove(obj)

    # Extract tar file list to working dir
    def untar_files(self, file_list):
        # Iterate over file list
        for src in file_list:
            # Check file existing in repo
            if os.path.isfile(src):

                # Stage files synchronously
                if self.glob.stg['sync_staging']:
                    self.glob.lib.msg.low("Extracting " + src + "...")
                    # Extract to working dir
                    tar = tarfile.open(src)
                    tar.extractall(self.glob.config['metadata']['dest_path'])
                    tar.close()

            # File not found
            else:
                self.glob.lib.msg.error("Input file '" + src + "' not found in repo " + \
                                        self.glob.lib.rel_path(self.glob.stg['local_repo']))

    # Download URL
    def wget_files(self, file_list):
        for elem in file_list:
            src = elem.strip()
            dest = os.path.join(self.glob.config['metadata']['dest_path'], src.split("/")[-1])
            try:
                urllib.request.urlretrieve(src, dest)
            except:
                self.glob.lib.msg.error("Failed to download " + src)

            # Check if file is compressed
            if any(x in src for x in ['tar', 'tgz', 'bgz']):
                self.untar_files([os.path.join(src,dest)])

    # Copy file list to working dir
    def cp_files(self, file_list):
        for elem in file_list:
            src = elem.strip()

            # Check if directory
            src_path = os.path.expandvars(src)
            if not os.path.isfile(src_path) and not os.path.isdir(src_path):
                src_path = os.path.join(self.glob.stg['local_repo'], src)

            # Copy file
            if os.path.isfile(src_path):
                su.copy(src_path, self.glob.config['metadata']['dest_path'])

            # Copy dir
            elif os.path.isdir(src_path): 
                dest = src_path.split(self.glob.stg['sl'])[-1]
                su.copytree(src_path, os.path.join(self.glob.config['metadata']['dest_path'], dest))

            else:
                self.glob.lib.msg.error("Input file '" + src + "' not found in repo " + \
                                        self.glob.lib.rel_path(self.glob.stg['local_repo']))


    # Ensure input files exist
    def stage(self):
       
        # Check section exists
        if 'files' in self.glob.config.keys():

            if self.glob.stg['sync_staging']:
                self.glob.lib.msg.low("Staging input files...")
                # Create build dir
                self.create_dir(self.glob.config['metadata']['dest_path'])
            else:
                self.glob.lib.msg.low("Checking input files...")
                self.glob.stage = {}

            # Evaluate expressions
            self.glob.lib.expr.eval_dict(self.glob.config['config'])
            self.glob.lib.expr.eval_dict(self.glob.config['files'])

            # Parse through supported file operations
            for op in self.glob.config['files'].keys():
                if op == 'tar':
                    self.untar_files([os.path.join(self.glob.stg['local_repo'], x.strip()) for x in self.glob.config['files'][op].split(',')])

                elif op == 'wget':
                    self.wget_files(self.glob.config['files'][op].split(','))
    
                elif op == 'cp':
                    self.cp_files(self.glob.config['files'][op].split(','))

                else:
                    self.glob.lib.msg.error(["Unsupported file stage operation selected: '" + op + "'.", 
                                            "Supported operations = tar, wget, cp."])

