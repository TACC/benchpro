# System Imports
import os
import shutil as su
import subprocess
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob
        self.sanitize_modulepath()

    # Execute an LMOD command
    def lmod_query(self, args):

        # Cast to list
        if not type(args) == list:
            args = [args]

        try:
            proc = subprocess.Popen(([os.path.join(os.environ.get('LMOD_DIR'),'lmod')] + args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status         = proc.returncode
            stdout, stderr = proc.communicate()
            err_out        = sys.stderr
            if (os.environ.get('LMOD_REDIRECT','@redirect@') != 'no'):
                err_out=sys.stdout
        except subprocess.CalledProcessError as e:
            self.glob.lib.msg.error(["unable to execute \"lmod " + ' '.join(args) + "\'", e])

        return stderr.decode()

    # Remove BenchPRO references in MODULEPATH (to avoid module search finding benchpro modules)
    def sanitize_modulepath(self):
        paths = os.environ["MODULEPATH"].split(":")
        [paths.remove(path) for path in paths if "benchpro" in path]
        os.environ["MODULEPATH"] = ":".join(paths)

    # Get list of default modules
    def set_default_module_list(self, module_use):

        if os.path.isdir(self.glob.stg['user_mod_path']):
            module_use += [self.glob.stg['user_mod_path']] 

        # Append 'module use' elements to MODULEPATH, support comma delimited list of paths
        if module_use:
            for module in module_use.split(","):
                module_path = module.strip()
                if not os.path.isdir(module_path):
                    self.glob.lib.msg.warning("ml use path not found: " + module_path)

                os.environ["MODULEPATH"] = module_use + ":" + os.environ["MODULEPATH"]


        self.glob.default_module_list = self.lmod_query(['-t', '-d', 'av']).split("\n")


    # Gets full module name of default module, eg: 'intel' -> 'intel/18.0.2'
    def get_full_mod_name(self, module):

        # No slashes and no digits = short form module
        if (not '/' in module) or all(not char.isdigit() for char in module):
            # Get default module version from lmod
            for default in self.glob.default_module_list:
                if module+"/" in default:
                    return default
            else:
                self.glob.lib.msg.error("module '" + module + "': format error.")
        else:
            return module

    # Check if module is available on the system
    def check_module_exists(self, key, value):

        # Module check enabled
        if self.glob.stg['check_modules']:

            # If module is non Null
            if value:
                # Module exists
                if self.lmod_query(['show', value]):
                    # Return full module name
                    return self.get_full_mod_name(value) 
        else: 
            return value
           

    # Check inputs for module creation
    def check_for_previous_module(self, mod_path, mod_file):

        # Check if module already exists
        if os.path.isfile(os.path.join(mod_path, mod_file)):

            if self.glob.stg['overwrite']:
                self.glob.lib.msg.warning("Deleting old module in " + self.glob.lib.rel_path(mod_path) +
                                                " because 'overwrite=True' in $BP_HOME/settings.ini")
                su.rmtree(mod_path)
                os.makedirs(mod_path)

            else:
                self.glob.lib.msg.error("Module path already exists: " + mod_path)

    # Convert module name to usable directory name, Eg: intel/18.0.2 -> intel18
    def get_label(self, module):
        label = module
        if module.count(self.glob.stg['sl']) > 0:
            comp_ver = module.split(self.glob.stg['sl'])
            label = comp_ver[0] + comp_ver[1].split(".")[0]
        return label

    # Copy template to target dir
    def copy_mod_template(self, module_template):

        mod_obj = []

        for path in self.glob.paths:
            mod_obj.append("prepend_path(\"PATH\",     \"" + path + "\")\n")

        # Add custom module path if set in cfg
        if self.glob.config['general']['module_use']:

            # Handle env vars in module path
            if self.glob.config['general']['module_use'].startswith(self.glob.stg['home_env']):

                project = self.glob.stg['home_env'].strip("$")

                mod_obj.append("local " + project + " = os.getenv(\"" + project + "\") or \"\"\n")
                mod_obj.append("prepend_path(\"MODULEPATH\", pathJoin(" + project + ", \"" + self.glob.config['general']['module_use'][len(project)+2:] + "\"))\n")

            else:
                mod_obj.append("prepend_path( \"MODULEPATH\" , \"" + self.glob.config['general']['module_use'] + "\") \n")

        with open(module_template, 'r') as inp:
            mod_obj.extend(inp.readlines())

        return mod_obj

    # Replace <<<>>> vars in copied template
    def populate_mod_template(self, mod_obj):
        # Get comma delimited list of non-Null build modules
        mod_list = []
        for key in self.glob.config['modules']:
            if self.glob.config['modules'][key]:
                mod_list.append(self.glob.config['modules'][key])

        mod = {}
        mod['mods'] = ', '.join('"{}"'.format(m) for m in mod_list)
        # Get capitalized code name for env var
        mod['caps_code'] = self.glob.config['general']['code'].upper().replace("-", "_")

        pop_dict = {**mod, **self.glob.config['metadata'], **self.glob.config['general'], **self.glob.config['config'], **self.glob.ev}

        for key in pop_dict:
            self.glob.lib.msg.log("replace " + "<<<" + key + ">>> with " + str(pop_dict[key]))
            mod_obj = [line.replace("<<<" + str(key) + ">>>", str(pop_dict[key])) for line in mod_obj]
        
        return mod_obj

    # Write module to file
    def write_mod_file(self, module, tmp_mod_file):
        with open(tmp_mod_file, "w") as f:
            for line in mod_obj:
                f.write(line)


    # Make module for compiled appliation
    def make_mod(self):

        self.glob.lib.msg.log("Creating module file for " + self.glob.config['general']['code'])

        # Get module file path
        mod_path = os.path.join(    self.glob.stg['module_path'], 
                                    self.glob.config['general']['system'], 
                                    self.glob.config['config']['arch'], 
                                    self.glob.modules['compiler']['safe'], 
                                    self.glob.modules['mpi']['safe'], 
                                    self.glob.config['general']['code'], 
                                    str(self.glob.config['general']['version']))

        mod_file = self.glob.config['config']['build_label'] + ".lua"
    
        self.check_for_previous_module(mod_path, mod_file)
    
        template_filename = self.glob.config['general']['code'] + "_" + str(self.glob.config['general']['version']) + ".module" 
        module_template = os.path.join(self.glob.stg['sys_tmpl_path'], template_filename)

        # Use generic module template if not found for this application
        if not os.path.isfile(module_template):
            self.glob.lib.msg.low("Module template '" + template_filename + "' not found, generating a generic module.")
            module_template = os.path.join(self.glob.stg['sys_tmpl_path'], "generic.module")

        self.glob.lib.msg.log("Using module template file: " + module_template)

        # Copy base module template to 
        if self.glob.config['config']['bin_dir']:
            self.glob.paths += [os.path.join(self.glob.config['metadata']['install_path'], self.glob.config['config']['bin_dir'])]
        else:
            self.glob.paths += [self.glob.config['metadata']['install_path']]

        mod_obj = self.copy_mod_template(module_template)

        # Populuate template with config params
        mod_obj = self.populate_mod_template(mod_obj)
        # Test module template
        tmp_mod_file = os.path.join(self.glob.ev['BP_HOME'], "tmp." + mod_file)
        self.glob.lib.template.test_template(tmp_mod_file, mod_obj)
        # Write module template to file
        self.glob.lib.files.write_list_to_file(mod_obj, tmp_mod_file)

        return mod_path, tmp_mod_file
