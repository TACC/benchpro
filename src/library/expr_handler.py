# System Imports
import re
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob
        self.search_dicts = []

    # Return True if operators are found in string
    def has_arithmatic(self, expr):
        matching_ops = ['\+', '\-', '\*', '\/', '\**']
        if any(op in str(expr) for op in matching_ops):
            return True
        else:
            return False

    # Evaulate arithamtic in string 
    def evaluate_arithmatic(self, expr):
        try:
            return int(eval(expr.replace("\\", "")))
        except:
            self.glob.lib.msg.error("failed to evaulate artimatic expression '" + expr + "'")

    # Find matching key in dict and return value, or return False 
    def replace_var(self, var, search_dict):
        # Check if var matches key in dict
        if var in search_dict.keys():
            return True, search_dict[var]
        # No match
        else:
            return False, ""

    # Look for key in multiple dicts, return value or error
    def look_for_replacement(self, var):
        # For each dict in list
        for search_dict in self.search_dicts:
            # Look for key in dict
            matched, new_val = self.replace_var(var, search_dict)
            if matched:
                return new_val
        self.glob.lib.msg.error("Unable to resolve variable '" + var + "' in config file")

    # Replace variables
    def resolve_vars(self, dict_value):
        # Get list of {variables}
        var_list = re.findall('\{([^}]+)',str(dict_value))
        # Replace all vars in each dict value
        for var in var_list:
            dict_value = dict_value.replace("{"+var+"}", str(self.look_for_replacement(var)))

        return dict_value

    # Check dict for vars, resolve them and then evaluate for arithmatic
    def eval_dict(self, cfg_dict):

        # Building application
        if self.glob.args.build:
            self.search_dicts = [self.glob.config['general'], self.glob.config['config'], self.glob.system]
        # Running bench
        else:
            self.search_dicts = [self.glob.config['requirements'], self.glob.config['runtime'], self.glob.config['config'], self.glob.config['result'], self.glob.system]

        for key in cfg_dict:
            # Resolve variables
            cfg_dict[key] = self.resolve_vars(cfg_dict[key])
            
            # If operators are present
            if self.has_arithmatic(cfg_dict[key]):
                cfg_dict[key] = str(self.evaluate_arithmatic(cfg_dict[key]))

