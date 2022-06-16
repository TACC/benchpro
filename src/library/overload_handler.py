# System Imports
import copy
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob
        # init seach_space AFTER dicts are populated to avoid stale refs
        self.search_space = []

    # Select which dicts are searchable when applying overloads
    def set_search_space(self):
        self.search_space = [self.glob.stg,
                            self.glob.config['general'],
                            self.glob.config['config'],
                            self.glob.config['requirements'],
                            self.glob.config['runtime'],
                            self.glob.config['result'],
                            self.glob.sched['sched'],
                            self.glob.system
                            ]

    # Replace dict values with overloaded values
    def update(self, overload_key, search_dict):
        # If found matching key
        if overload_key in search_dict:

            self.glob.lib.msg.log("Overload key '" + overload_key + "' found in dict!")
            old = search_dict[overload_key]

            # If cfg value is a list, skip datatype check
            if "," in self.glob.overload_dict[overload_key]:
                search_dict[overload_key] = self.glob.overload_dict[overload_key]

            else:
                datatype = type(search_dict[overload_key])
                try:
                    # Convert datatypes
                    if datatype is str:
                        search_dict[overload_key] = str(self.glob.overload_dict[overload_key])
                    elif datatype is int:
                        search_dict[overload_key] = int(self.glob.overload_dict[overload_key])
                    elif datatype is bool:
                        search_dict[overload_key] = self.glob.overload_dict[overload_key] == 'True'
                except:
                    self.glob.lib.msg.error("datatype mismatch for '" + overload_key +"', expected=" + str(datatype) +\
                                                ", provided=" + str(type(overload_key)))

            self.glob.lib.msg.high("Overloading " + overload_key + ": '" + str(old) + "' -> '" + \
                                        str(search_dict[overload_key]) + "'")
            # Add to list of overloaded keys
            self.glob.overloaded += [overload_key]
            # Remove key from overload dict
            self.glob.overload_dict.pop(overload_key)
            # Match found
            return True
        
        else:
            # No match found
            return False

    # Scan searchable dicts for matching key to overload
    def replace(self):

        # Init dicts to search
        self.set_search_space()

        # For each overload key
        for overload_key in list(self.glob.overload_dict):
            self.glob.lib.msg.log("Overloading key " + overload_key + "...")            
            # Search for match in searchable dicts
            for search_dict in self.search_space:
                # Attempt to replace matching key
                if self.update(overload_key, search_dict):
                    # Replaced - next overload key
                    break

    # Generate dict from commandline params
    def setup_dict(self):

        user_input = self.glob.args.overload

        # Check if input is a file?
        overload_file = self.glob.lib.files.find_in([self.glob.stg['config_path']], user_input[0]+"*", False) 
        if overload_file:
            # Remove first element (filename)
            user_input.pop(0)
            # Add file values to param list
            with open(overload_file, 'r') as f:
                user_input.extend(f.readlines())

        # Read key-values into dict
        for setting in user_input:
            pair = setting.split('=')
            # Test key-value pair
            if not len(pair) == 2:
                print("Invalid overload [key]=[value] pair detected: ", setting)
                sys.exit(1)
            self.glob.overload_dict[pair[0].strip()] = pair[1].strip()

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
    def check_for_unused(self):

        # Last chance to make replacements
        self.replace()

        # First check for overloaded params that are incompatible with exec mode
        self.catch_incompatible()
        
        # Check if any params are left in overload_dict = unused
        if len(self.glob.overload_dict):
            self.glob.lib.msg.high("The following --overload argument does not match existing params:")
            # Print unmatched key-values
            for key in self.glob.overload_dict:
                self.glob.lib.msg.high("  " + key + "=" + self.glob.overload_dict[key])
            self.glob.lib.msg.error("Invalid input arguments.")

