# System Imports
import os
import shutil as su
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Check inputs for module creation
    def check_for_existing_module(self, mod_path, mod_file):

        # Check if module already exists
        if os.path.isfile(os.path.join(mod_path, mod_file)):

            if self.glob.stg['overwrite']:
                self.glob.lib.msg.warning("Deleting old module in " + self.glob.lib.rel_path(mod_path) + 
                                                " because 'overwrite=True' in settings.ini")
                su.rmtree(mod_path)
                os.makedirs(mod_path)

            else:
                self.glob.lib.msg.error("Module path already exists.")
    
    # Copy template to target dir
    def copy_mod_template(self, module_template):

        mod_obj = []

        # Add custom module path if set in cfg
        if self.glob.config['general']['module_use']:

            # Handle env vars in module path
            if self.glob.config['general']['module_use'].startswith(self.glob.stg['topdir_env_var']):

                topdir = self.glob.stg['topdir_env_var'].strip("$")

                mod_obj.append("local " + topdir + " = os.getenv(\"" + topdir + "\") or \"\"\n")
                mod_obj.append("prepend_path(\"MODULEPATH\", pathJoin(" + topdir + ", \"" + self.glob.config['general']['module_use'][len(topdir)+2:] + "\"))\n")

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

        pop_dict = {**mod, **self.glob.config['metadata'], **self.glob.config['general'], **self.glob.config['config']}

        for key in pop_dict:
            self.glob.log.debug("replace " + "<<<" + key + ">>> with " + str(pop_dict[key]))
            mod_obj = [line.replace("<<<" + str(key) + ">>>", str(pop_dict[key])) for line in mod_obj]
        
        return mod_obj

    # Write module to file
    def write_mod_file(self, module, tmp_mod_file):
        with open(tmp_mod_file, "w") as f:
            for line in mod_obj:
                f.write(line)

    # Make module for compiled appliation
    def make_mod(self):

        self.glob.log.debug("Creating module file for " + self.glob.config['general']['code'])

        # Get module file path
        mod_path = os.path.join(self.glob.stg['module_path'], self.glob.config['general']['system'], self.glob.config['config']['arch'], self.glob.lib.get_module_label(self.glob.config['modules']['compiler']), \
                                self.glob.lib.get_module_label(self.glob.config['modules']['mpi']), self.glob.config['general']['code'], str(self.glob.config['general']['version']))

        mod_file = self.glob.config['config']['build_label'] + ".lua"
    
        self.check_for_existing_module(mod_path, mod_file)
    
        template_filename = self.glob.config['general']['code'] + "_" + str(self.glob.config['general']['version']) + ".module" 
        module_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir'], template_filename)

        # Use generic module template if not found for this application
        if not os.path.isfile(module_template):
            self.glob.lib.msg.low([self.glob.warning, 
                                "Module template '" + template_filename + "' not found, generating a generic module."])
            module_template = os.path.join(self.glob.stg['template_path'], self.glob.stg['build_tmpl_dir'], "generic.module")

        self.glob.log.debug("Using module template file: " + module_template)

        # Copy base module template to 
        mod_obj = self.copy_mod_template(module_template)

        # Populuate template with config params
        mod_obj = self.populate_mod_template(mod_obj)
        # Test module template
        tmp_mod_file = "tmp." + mod_file
        self.glob.lib.test_template(tmp_mod_file, mod_obj)
        # Write module template to file
        self.glob.lib.write_list_to_file(mod_obj, tmp_mod_file)

        return mod_path, tmp_mod_file
