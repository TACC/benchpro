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
    def cleanup(self, clean_list):
        
        # Clean default *.tmp files
        if not clean_list:
            clean_list = gb.glob(os.path.join(self.glob.basedir, 'tmp.*'))

        if clean_list:
            for f in clean_list:
                try:
                    # Files
                    if os.path.isfile(f):
                        os.remove(f)
                    # Clean dir trees
                    elif os.path.isdir(f):
                        self.prune_tree(f)

                    self.glob.log.debug("Successfully removed tmp object " + self.glob.lib.rel_path(f))
                except Exception as e :
                    self.glob.log.debug("Failed to remove tmp object " + self.glob.lib.rel_path(f))

    # Remove created files if we are crashing
    def rollback(self):
        # Clean tmp files
        self.cleanup([])
        # Clean 
        self.cleanup(self.glob.cleanup)

    # Find file in directory
    def find_exact(self, filename, path):
        # Check file doesn't exist already
        if os.path.isfile(filename):
            return filename

        # Search recursively for file
        files = gb.glob(path+'/**/'+filename, recursive = True)

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

    # Looks for file in paths
    def look(self, paths, filename):
        for path in paths:
            results = gb.glob(os.path.join(path, filename))
            if len(results) == 1:
                return results[0]
            
        return False

    # Accepts list of paths and filename, returns file path to file if found, or errors 
    def find_in(self, paths, filename, error_if_missing):

        # Add some default locations to the search path list
        paths.extend(["", self.glob.basedir, self.glob.cwd, self.glob.home])
        found = self.look(paths, filename) 

        if found:
            return found

        # Error if not found?
        if error_if_missing:
            self.glob.lib.msg.error(["Unable to locate file '" + filename + "' in any of these locations:"].extends(\
                                    [self.glob.lib.rel_path(locations)]))

        return False

    # Find *file* in directory
    def find_partial(self, filename, path):
        # Check file doesn't exist already
        if os.path.isfile(filename):
            return filename
        # Search provided path for file
        for root, dirs, files in os.walk(path):
            match = next((s for s in files if filename in s), None)
            if match:
                return os.path.join(root, match)
        # File not found
        return None

    # Get owner of file
    def file_owner(self, filename):
        return pwd.getpwuid(os.stat(filename).st_uid).pw_name

    # Check write permissions to a directory
    def write_permission(self, path):
        if os.access(path, os.W_OK | os.X_OK):
            return True
        return False

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

    # Prune dir tree until not unique
    def prune_tree(self, path):
        path_elems  = path.split(self.glob.stg['sl'])
        parent_path = self.glob.stg['sl'].join(path.split(self.glob.stg['sl'])[:-1])
        parent_dir  = path_elems[-2]

        # If parent dir is root ('build' or 'modulefile') or if it contains more than this subdir, delete this subdir
        if (parent_dir == self.glob.stg['build_dir']) or \
           (parent_dir == self.glob.stg['module_dir']) or \
           (len(gb.glob(os.path.join(parent_path,"*"))) > 1):

            su.rmtree(path)
        # Else resurse with parent
        else:
            self.prune_tree(parent_path)

    # Create directories if needed
    def create_dir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                self.glob.lib.msg.error(
                    "Failed to create directory " + path)

        # Add to cleanup list
        self.glob.cleanup.append(path)

    # Get list of files in search path
    def get_files_in_path(self, search_path):
        return gb.glob(os.path.join(search_path, "*.cfg"))

    # Check if path exists, if so append .dup
    def check_dup_path(self, path):
        if os.path.isdir(path):
            return self.check_dup_path(path + ".dup")
        return path

    # Copy tmp files to directory
    def copy(self, dest, src, new_name, clean):

        # Get file name
        if not new_name:
            new_name = src
            if self.glob.stg['sl'] in new_name:
                new_name = new_name.split(self.glob.stg['sl'])[-1]

            # Strip tmp prefix from file for new filename
            if 'tmp.' in new_name:
                new_name = new_name[4:]

        try:
            su.copyfile(src, os.path.join(dest, new_name))
            self.glob.log.debug("Copied file " + src + " into " + dest)
        except IOError as e:
            self.glob.lib.msg.high(e)
            self.glob.lib.msg.error(
                "Failed to move " + src + " to " + os.path.join(dest, new_name))

        # Remove tmp files after copy
        if clean:
            os.remove(src)

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

            if self.glob.stg['sync_staging']:
                self.glob.lib.msg.low("Downloading " + src + "...")
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

            # Absolute path or in local repo
            src_path = os.path.expandvars(src)
            if not os.path.isfile(src_path) and not os.path.isdir(src_path):
                src_path = os.path.join(self.glob.stg['local_repo'], src)

            # Check presence
            if not os.path.isfile(src_path) and not os.path.isdir(src_path):
                self.glob.lib.msg.error("Input file '" + src + "' not found in repo " + \
                                        self.glob.lib.rel_path(self.glob.stg['local_repo']))

            # Copy files
            if self.glob.stg['sync_staging']:
                self.glob.lib.msg.low("Copying " + src_path + "...")
                # Copy file
                if os.path.isfile(src_path):
                    su.copy(src_path, self.glob.config['metadata']['dest_path'])

                # Copy dir
                else:
                    dest = src_path.split(self.glob.stg['sl'])[-1]
                    su.copytree(src_path, os.path.join(self.glob.config['metadata']['dest_path'], dest))


    # Ensure input files exist
    def stage(self):
       
        # Check section exists
        if 'files' in self.glob.config.keys():

            self.glob.lib.msg.low("Staging input files...")
            if self.glob.stg['sync_staging']:
                # Create build dir
                self.create_dir(self.glob.config['metadata']['dest_path'])
            else:
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

    # Read version number from file
    def read_version(self):
        with open(os.path.join(self.glob.basedir, ".version"), 'r') as f:
            return f.readline().split(" ")[-1][1:].strip()

    # Write module to file
    def write_list_to_file(self, list_obj, output_file):
        with open(output_file, "w") as f:
            for line in list_obj:
                f.write(line)

