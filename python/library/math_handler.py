# System Imports
import re
import sys

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
        for search_dict in [self.glob.code['requirements'], self.glob.code['runtime'], self.glob.code['config'], self.glob.system]:
            # Look for key in dict
            matched, new_val = self.replace_var(var, search_dict)
            if matched:
                return new_val
        self.glob.lib.msg.error("Unable to resolve variable '" + var + "' in config file")


    # Get left hand side of expr, in form ['misc', [op]]
    def eval_lhs(self, op):
        try:
            # Check if op is a variable
            if op[-1] == "}":
                # Find loc of other bracket
                open_brac = op.rfind('{')
                # Pass content of bracket for replacement
                replace_var = str(self.look_for_replacement(op[open_brac+1:-1])[0])
                # Return evaluated string
                return [op[:open_brac], replace_var]
            # Op must be int
            else :
               int_op = ""
               # Keep converting to ints until they aren't
               while op[-1].isdigit() and len(op) > 0:
                   int_op += op[-1]
                   op = op[:-1]
               return [op, int_op]

        except:
            self.glob.lib.msg.error("Unable to evaluate operand '" + str(op) + "'")

    def eval_rhs(self, op):
        try:
            if op[0] == "{":
                close_brac = op.find('}')
                replace_var = str(self.look_for_replacement(op[1:close_brac])[0]) 
                return [replace_var, op[close_brac+1:]]
            else:
                int_op = ""
                while op[0].isdigit() and len(op) > 0:
                    int_op += op[0]
                    op = op[1:]
                return [int_op, op]

        except:
            self.glob.lib.msg.error("Unable to evaluate operand '" + str(op) + "'")

    # Find operator, lhs, rhs then do math
    def handle_operator(self, dict_value):

        matching_ops = ['\+', '\-', '\*', '\/', '\**']

        # ignore plain digits
        if not isinstance(dict_value, int):

            # Look for each operator
            for op in matching_ops:

                # For each occurance of op
                for loc in re.finditer(re.escape(op), dict_value):

                    lhs = None
                    rhs = None
                    op = dict_value[loc.start():loc.end()]

                    if loc.start() > 0:
                        lhs = self.eval_lhs(dict_value[:loc.start()])

                    if loc.end() < len(dict_value): 
                        rhs = self.eval_rhs(dict_value[loc.end():])
                
                    # Eval expression and return reassembled string
                    return lhs[0] + str(self.evaluate_arithmatic(lhs[1] + op[1:] + rhs[0])) + rhs[1]

        return dict_value


    # Check dict for vars, resolve them and then evaluate for arithmatic
    def eval_dict(self, cfg_dict):

        for key in cfg_dict:
    
            # First handle any operators
            cfg_dict[key] = self.handle_operator(cfg_dict[key])

            # Get list of {variables}
            var_list = re.findall('\{([^}]+)',str(cfg_dict[key]))

            # Replace all vars in each dict value
            for var in var_list:
                new_val = self.look_for_replacement(var)
                cfg_dict[key] = cfg_dict[key].replace("{"+var+"}", str(new_val))

