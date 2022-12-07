# System Imports

import copy
import os
import sys

class init(object):

    def __init__(self, glob):
        self.glob = glob
        # init seach_space AFTER dicts are populated to avoid stale refs
        self.search_space = []

    # Select which dicts are searchable when applying overloads
    def set_search_space(self):
        self.search_space = [   self.glob.stg,
                                self.glob.ev,
                                self.glob.config['general'],
                                self.glob.config['config'],
                                self.glob.config['files'],
                                self.glob.config['modules'],
                                self.glob.config['requirements'],
                                self.glob.config['runtime'],
                                self.glob.config['result'],
                                self.glob.sched['sched'],
                                self.glob.system]

    def set_valid_keys(self):
        key_list = self.glob.lib.files.read(os.path.join(self.glob.stg['site_sys_cfg_path'], self.glob.stg['key_cfg_file']))
        self.glob.valid_keys = [key_list.remove(k) if k[0] == "#" else k.strip() for k in key_list]

    # Replace dict values with overloaded_dict values
    def update(self, overload_key, search_dict):


        for pre_dict in list(self.glob.overloaded_dict.keys()):
            if overload_key in pre_dict:
                self.glob.lib.msg.high("Skipping duplicate overload key: " + overload_key + "=" + str(self.glob.overloaded_dict[overload_key]))
#                print("", overload_key)
                self.glob.overload_dict.pop(overload_key)
                return False

        # Looking for provided key in search_dict
        # Match found
        if overload_key in search_dict.keys():

            val = search_dict[overload_key]
            if not val:
                val = "None"


            self.glob.lib.msg.log("Overload key '" + str(overload_key) + "=" + str(val) + "' found in dict!")

            old_val = search_dict[overload_key]



            # If cfg value is a list, skip datatype check
            if "," in str(self.glob.overload_dict[overload_key]):
                self.glob.lib.msg.log("Skip overload datatype check for list '" + + "'")
                search_dict[overload_key] = self.glob.overload_dict[overload_key]

            # Not list type
            else:
                # Assign new value
                search_dict[overload_key] = self.glob.lib.cast_to(self.glob.overload_dict[overload_key], type(old_val))

            # Only print overloads from CLI
            if overload_key not in self.glob.defs_overload_dict.keys():
                self.glob.lib.msg.high("Overloading " + overload_key + ": '" + str(old_val) + "' -> '" + \
                                            str(search_dict[overload_key]) + "'")
          
            self.glob.overloaded_dict[overload_key] = self.glob.overload_dict[overload_key]
            # Remove key from overload dict
            self.glob.overload_dict.pop(overload_key)
            # Match found
            return True
        
        # No matching key found in this search_dict
        else:
            return False

    # Scan searchable dicts for matching key to overload
    def replace(self, search_space):

        # Init dicts to search
        if not search_space:
            self.set_search_space()
        else:
            self.search_space = [search_space]
       
       # For each overload key
        for overload_key in list(self.glob.overload_dict):

            # Check valid key in $BPS_INC/system/config/valid_keys.cfg
            if not overload_key in self.glob.valid_keys:
                self.glob.lib.msg.error([key for key in self.glob.valid_keys] + ["Invalid setting: '" + overload_key + "'"])

            self.glob.lib.msg.log("Attempting to overload key " + overload_key + "...")            
            # Search for match in searchable dicts
            for search_dict in self.search_space:
                # Attempt to replace matching key
                if self.update(overload_key, search_dict):
                    # Replaced or dropped dupe - next overload key
                    break

            self.glob.lib.msg.log("No match for '" + overload_key + "' found on this pass.")

    # Generate dict from commandline params
    def init_overload_dict(self):

        self.glob.lib.msg.log(["OVERLOAD DICT CREATION", 
                               "----------------------"])

        for overload_src in [self.glob.args.overload, self.glob.defs_overload_list]:

            # If overload list is not empty
            if overload_src:
                # Iterate overload list
                for overload in overload_src:

                    self.glob.lib.msg.log("Adding '" + overload + "' to overload dict")
                    if not isinstance(overload, str):
                        continue
                    # Split string into str by '='
                    kv = overload.split('=')
                    # Test key-value (kv)
                    if not len(kv) == 2:
                        print("Invalid overload [key]=[value] detected: \"" + str(overload) + "\"")
                        sys.exit(1)
                    # Passed format test
                    
                    # Check key not already present:
                    if not kv[0] in self.glob.overload_dict.keys():
                        self.glob.overload_dict[kv[0].strip()] = self.glob.lib.destr(kv[1].strip())


        self.glob.lib.msg.log("----------------------")

    # Catch overload keys that are incompatible with local exec mode before checking for missed keys
    def catch_incompatible(self):
        # Runtime overload only works with sched exec_mode
        bad_keys = ["runtime"]
        # Iterate over overload dict
        for key in copy.deepcopy(self.glob.overload_dict):
            # Pop incompatible (unmatchable) keys 
            if key in bad_keys:
                self.glob.lib.msg.low("Ignoring bad overload key '" + key +  "' - incompatible with current exec_mode")
                self.glob.overload_dict.pop(key)

    # Print warning if overload dict not empty (unmatched keys)
    def check_for_unused_overloads(self):

        # Last chance to make replacements
        self.replace(None)

        # First check for overloaded_dict params that are incompatible with exec mode
        self.catch_incompatible()
        
        # Check if any params are left in overload_dict = unused
        if len(self.glob.overload_dict):
            self.glob.lib.msg.high("The following --overload argument(s) did not match existing params:")
            # Print unmatched key-values
            for key in self.glob.overload_dict:
                self.glob.lib.msg.high("  " + key + "=" + str(self.glob.overload_dict[key]))
            self.glob.lib.msg.error("Invalid input arguments.")

    # Confirm all required overloads are present in settings.ini
    def check_for_required_overloads(self):


        for required_key in self.glob.required_overload_keys:
            # No value defined - error
            try:
                if self.glob.overload_dict[required_key]:
                    pass
            except:
                self.glob.lib.msg.error(["Missing required setting '" + required_key + "'",
                                         "Please set with:",
                                         "bps " + required_key + "=[val]"])

 
