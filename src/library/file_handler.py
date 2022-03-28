# System imports
import cgi
import configparser as cp
import glob as gb
import os
import pwd
import shutil as su
import tarfile
from urllib.request import urlopen
from urllib.request import urlretrieve


class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Read non-cfg file into list
    def read(self, file_path):
        if not os.path.isfile(file_path):
            self.glob.lib.msg.error("File " + self.glob.lib.rel_path(file_path) + " not found.")

        with open(file_path) as f:
            return f.readlines()

    # Delete tmp build files if installation fails
    def cleanup(self, clean_list):
        
        # Clean default *.tmp files
        if not clean_list:
            clean_list = gb.glob(os.path.join(self.glob.bp_home, 'tmp.*'))

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
        paths.extend(["", self.glob.bp_home, self.glob.cwd, self.glob.home])
        file_path = self.look(paths, filename) 

        if file_path:
            return file_path

        # Error if not found?
        if error_if_missing:
            self.glob.lib.msg.error(["Unable to locate file '" + filename + "' in any of these locations:"] +\
                                    [self.glob.lib.rel_path(p) for p in paths])

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
        try:
            return [name for name in os.listdir(base)
                if os.path.isdir(os.path.join(base, name))]
        except Exception as e:
            self.glob.lib.msg.error("Directory '" + base + "' not found, did you run --validate?")

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
           (parent_dir == os.path.basename(self.glob.stg['collection_path'])) or \
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
            if os.path.isfile(src):
                su.copyfile(src, os.path.join(dest, new_name))
            else:
                su.copytree(src, os.path.join(dest, new_name))
            self.glob.log.debug("Copied file " + src + " into " + dest)
        except IOError as e:
            self.glob.lib.msg.high(e)
            self.glob.lib.msg.error(
                "Failed to move " + src + " to " + os.path.join(dest, new_name))

        # Remove tmp files after copy
        if clean:
            os.remove(src)

    # Extract tar file list to working dir
    def untar_file(self, src):

        # untar now
        if self.glob.stg['sync_staging']:
            self.glob.lib.msg.low("Extracting " + src + "...")

            # File not found
            if not os.path.isfile(src):
                self.glob.lib.msg.error("Input file '" + src + "' not found in repo " + \
                                        self.glob.lib.rel_path(self.glob.stg['local_repo']))

            # Extract to working dir
            tar = tarfile.open(src)
            tar.extractall(self.glob.config['metadata']['copy_path'])
            tar.close()

        # untar in script
        else:
            self.glob.stage_ops.append("tar -xf " + src + " -C " + self.glob.config['metadata']['copy_path'])

    # Copy file to working dir
    def cp_file(self, src):

        # Absolute path or in local repo
        src_path = os.path.expandvars(src)
        if not os.path.isfile(src_path) and not os.path.isdir(src_path):
            src_path = os.path.join(self.glob.stg['local_repo'], src)

        # Copy now
        if self.glob.stg['sync_staging']:


            # Check presence
            if not os.path.isfile(src_path) and not os.path.isdir(src_path):
                self.glob.lib.msg.error("Input file '" + src + "' not found in repo " + \
                                        self.glob.lib.rel_path(self.glob.stg['local_repo']))

            self.glob.lib.msg.low("Copying " + src_path + "...")
            # Copy file
            if os.path.isfile(src_path):
                su.copy(src_path, self.glob.config['metadata']['copy_path'])

            # Copy dir
            else:
                dest = src_path.split(self.glob.stg['sl'])[-1]
                su.copytree(src_path, os.path.join(self.glob.config['metadata']['copy_path'], dest))

        # Copy in script
        else:
           self.glob.stage_ops.append("cp -r " + src_path + " " + self.glob.config['metadata']['copy_path']) 

    # Process local file depending on type
    def stage_local(self, file_list):

        for filename in file_list:
            filename  = filename.strip()

            # Locate file
            if self.glob.stg['sync_staging']: 
                file_path = self.find_in([self.glob.stg['local_repo'], self.glob.config['metadata']['copy_path']], filename, True)
            # Assume will be in repo after download
            else:
                file_path = os.path.join(self.glob.stg['local_repo'], filename)

            # Check if compressed
            if any(x in filename for x in ['tar', 'tgz', 'bgz']):
                self.untar_file(file_path)
            else:
                self.cp_file(file_path)

    # Extract filename from URL 
    def get_url_filename(self, url):

        try:
            remotefile = urlopen(url)
            value, params = cgi.parse_header(remotefile.info()['Content-Disposition'])
            return params["filename"]

        except Exception as e:
            print(e)
            self.glob.lib.msg.error("Unable to reach URL " + url)

    # Check if file or dir is present in local repo
    def in_local_repo(self, filename):
        if os.path.isfile(os.path.join(self.glob.stg['local_repo'], filename)) \
        or os.path.isdir(os.path.join(self.glob.stg['local_repo'], filename)):
            return True
        return False

    # Download URL 
    def wget_file(self, url, filename):
        dest = None
        # Destination = working_dir or local repo
        if self.glob.stg['cache_downloads']:
            dest = os.path.join(self.glob.stg['local_repo'], filename)
        else:
            dest = os.path.join(self.glob.config['metadata']['copy_path'], filename)

        # Download now
        if self.glob.stg['sync_staging']:
            try:
                self.glob.lib.msg.low("Fetching file " + filename + "...")
                urlretrieve(url, dest)
            except Exception as e:
                self.glob.lib.msg.error("Failed to download URL '" + url + "'")
        # Download in script
        else:
            self.glob.stage_ops.append("wget -O " + dest + " " + url)

    # Download list of URLs
    def stage_urls(self, url_list):
        for url in url_list:
            local_copy = False
            # Clean up list elem
            url = url.strip()
            # Get filename from URL
            filename = self.get_url_filename(url)

            # Prefer local files & file in local repo
            if self.glob.stg['prefer_local_files'] and self.in_local_repo(filename):
                local_copy = True

            # No local copy - download
            if not local_copy:
                self.wget_file(url, filename)
            
            # Process downloaded file
            self.stage_local([filename])

    # Stage files listed in cfg under [files]
    def stage(self):
      
        # Create working dir
        self.create_dir(self.glob.config['metadata']['copy_path'])

        # Check section exists
        if 'files' in self.glob.config.keys():

            self.glob.lib.msg.high("Staging input files...")

            # Evaluate expressions in [config] and [files] sections of cfg file 
            self.glob.lib.expr.eval_dict(self.glob.config['config'])
            self.glob.lib.expr.eval_dict(self.glob.config['files'])

            # Parse through supported file operations - local, download
            for op in self.glob.config['files'].keys():

                if op == 'local':
                    self.stage_local(self.glob.config['files'][op].split(','))
                elif op == 'download':
                    self.stage_urls(self.glob.config['files'][op].split(','))
                else:
                    self.glob.lib.msg.error(["Unsupported file stage operation selected: '" + op + "'.", 
                                            "Supported operations = 'download' or 'local'"])

    # Read version number from file
    def read_version(self):
        with open(os.path.join(self.glob.bp_home, ".version"), 'r') as f:
            return f.readline().split(" ")[-1][1:].strip()

    # Write module to file
    def write_list_to_file(self, list_obj, output_file):
        with open(output_file, "w") as f:
            for line in list_obj:
                f.write(line)

    # Write command line to history file
    def write_cmd_history(self):
        history_file = os.path.join(self.glob.bp_home, ".history")
        with open(history_file, "a") as hist:
            hist.write(self.glob.cmd + "\n")

    # Get list of config files by type
    def get_cfg_list(self, cfg_type):
        # Get cfg subdir name from input
        type_dir = ""
        if cfg_type == "build":
            type_dir = self.glob.stg['build_cfg_dir']
        elif cfg_type == "bench":
            type_dir = self.glob.stg['bench_cfg_dir']
        else:
            self.glob.lib.msg.error("unknown cfg type '"+cfg_type+"'. get_cfgs() accepts either 'build' or 'bench'.")

        search_path = os.path.join(self.glob.stg['config_path'], type_dir)
        # Get list of cfg files in dir
        cfg_list = self.glob.lib.files.get_files_in_path(search_path)

        # If system subdir exists, scan that too
        if os.path.isdir(os.path.join(search_path,self.glob.system['system'])):
            cfg_list = cfg_list + self.glob.lib.files.get_files_in_path(os.path.join(search_path,self.glob.system['system']))
        return cfg_list

    # Parse cfg file into dict
    def read_cfg(self, cfg_file):
        cfg_parser = cp.ConfigParser()
        cfg_parser.optionxform=str
        cfg_parser.read(cfg_file)

        # Add file name & label to dict
        cfg_dict = {}
        cfg_dict['metadata'] ={}

        cfg_dict['metadata']['cfg_label'] = ".".join(cfg_file.split(self.glob.stg['sl'])[-1].split(".")[:-1])
        cfg_dict['metadata']['cfg_file']  = cfg_file

        # Read sections into dict
        for section in cfg_parser.sections():
            cfg_dict[section] = dict(cfg_parser.items(section))

        return cfg_dict


