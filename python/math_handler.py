# System Imports
import re
import sys

# Local Imports
import exception

glob = None
dicts_to_search = []

class init(object):
    def __init__(self, glob):
        self.glob = glob

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
            exception.error_and_quit(self.glob.log, "failed to evaulate artimatic expression '" + expr + "'")

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
        for search_dict in dicts_to_search:
            # Look for key in dict
            matched, new_val = self.replace_var(var, search_dict)
            if matched:
                return new_val
        exception.error_and_quit(self.glob.log, "Unable to resolve variable '" + var + "' in config file")

    # Check dict for vars, resolve them and then evaluate for arithmatic
    def eval_dict(self, cfg_dict):
        global dicts_to_search 
        dicts_to_search = [self.glob.code['runtime'], self.glob.code['config'], self.glob.system]


        for key in cfg_dict:
            # Get list of {variables}
            var_list = re.findall('\{([^}]+)',str(cfg_dict[key]))
            # Replace all vars in each dict value
            for var in var_list:
                new_val = self.look_for_replacement(var)
                cfg_dict[key] = cfg_dict[key].replace("{"+var+"}", str(new_val))
            # Evaluate dict key expressions
            if self.has_arithmatic(cfg_dict[key]):
                cfg_dict[key] = self.evaluate_arithmatic(cfg_dict[key])

