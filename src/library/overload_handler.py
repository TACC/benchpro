# System Imports
import copy
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Overload dict keys with overload key
    def update(self, overload_key, param_dict):
        # If found matching key
            if overload_key in param_dict:
                old = param_dict[overload_key]

                # If cfg value is a list, skip datatype check
                if "," in self.glob.overload_dict[overload_key]:
                    param_dict[overload_key] = self.glob.overload_dict[overload_key]

                else:
                    datatype = type(param_dict[overload_key])

                    try:
                        # Convert datatypes
                        if datatype is str:
                            param_dict[overload_key] = str(self.glob.overload_dict[overload_key])
                        elif datatype is int:
                            param_dict[overload_key] = int(self.glob.overload_dict[overload_key])
                        elif datatype is bool:
                            param_dict[overload_key] = self.glob.overload_dict[overload_key] == 'True'
                    except:
                        self.glob.lib.msg.error("datatype mismatch for '" + overload_key +"', expected=" + str(datatype) +\
                                                ", provided=" + str(type(overload_key)))

                self.glob.lib.msg.high("Overloading " + overload_key + ": '" + str(old) + "' -> '" + \
                                        str(param_dict[overload_key]) + "'")
                # Remove key from overload dict
                self.glob.overload_dict.pop(overload_key)


    # Replace cfg params with cmd line inputs
    def replace(self, search_dict):
        for overload_key in list(self.glob.overload_dict):
            # If dealing with code/sched/compiler cfg, descend another level
            if list(search_dict)[0] == "metadata":
                for section_dict in search_dict:
                    self.update(overload_key, search_dict[section_dict])
            else:
                self.update(overload_key, search_dict)

    # Generate dict fom colon-delimited params
    def setup_dict(self, user_input):

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
                print("Invalid overload key-value pair detected: ", setting)
                sys.exit(1)
            self.glob.overload_dict[pair[0].strip()] = pair[1].strip()

    # Catch overload keys that are incompatible with local exec mode before checking for missed keys
    def catch_incompatible(self):

        # Runtime overload only works with sched exec_mode
        bad_keys = ["runtime"]

        for key in copy.deepcopy(self.glob.overload_dict):
            if key in bad_keys:
                self.glob.lib.msg.low("Ignoring bad overload key '" + key +  "' - incompatible with current exec_mode")
                self.glob.overload_dict.pop(key)

    # Print warning if cmd line params dict not empty
    def check_for_unused(self):

        # First check for overloaded params that are incompatible with exec mode
        self.catch_incompatible()
        
        # Check if any params are left in overload_dict = unused
        if len(self.glob.overload_dict):
            self.glob.lib.msg.high("The following --overload argument does not match existing params:")
            for key in self.glob.overload_dict:
                self.glob.lib.msg.high("  " + key + "=" + self.glob.overload_dict[key])
            self.glob.lib.msg.error("Invalid input arguments.")

