# System Imports
import re
import sys

class init(object):
    def __init__(self, glob):
        self.glob = glob
        self.search_space = []

    # Sets the dicts to search for matching keys, depending on build/bench operation
    def set_search_space(self):

        if self.glob.args.build:
            self.search_space = [       self.glob.config['general'], 
                                        self.glob.config['config'], 
                                        self.glob.sched['sched'], 
                                        self.glob.system, 
                                        self.glob.stg]
        # Running bench
        elif self.glob.args.bench:
            self.search_space = [       self.glob.config['requirements'], 
                                        self.glob.config['runtime'],
                                        self.glob.config['config'], 
                                        self.glob.config['result'], 
                                        self.glob.sched['sched'], 
                                        self.glob.system]

    # Return True if operators are found in string
    def has_arithmatic(self, expr):
        matching_ops = ['\+', '\-', '\*', '\/', '\**']
        if any(op in str(expr) for op in matching_ops):
            return True
        else:
            return False

    # Evaulate arithamtic in string 
    def evaluate_arithmatic(self, expr):

        self.glob.lib.msg.log("Evaluating arithmatic: " + str(expr) )
        try:
            return int(eval(expr.replace("\\", "")))
        except:
            self.glob.lib.msg.error("failed to evaulate artimatic expression '" + expr + "'")

    # Find matching key in dict and return value, or return False 
    def find_key(self, key, search_dict):
        # Check if var matches key in dict
        if key in search_dict.keys():
            return True, search_dict[key]
        # No match
        else:
            return False, ""

    # Look for key in multiple dicts, return value or error
    def get_dict_value(self, key):

        # For each dict in list
        for search_dict in self.search_space:
            if search_dict:
                # Look for key in dict
                matched, value = self.find_key(key, search_dict)
                if matched:
                    # Cast to int
                    try:
                        return int(value)
                    # Return str
                    except:
                        return value 

        # No match found in search space
        self.glob.lib.msg.error("Unable to resolve variable '" + key + "'")

    # Replace variables
    def resolve_vars(self, dict_value, runtime_keys):
        # Get list of <<<variables>>>
        var_list = re.findall('\<<<([^>>>]+)',str(dict_value))

        # For each found variable
        for var in var_list:

            # Skip runtime keys for now
            if runtime_keys and (var in runtime_keys):
                break 

            new_value = str(self.get_dict_value(var))
            dict_value = dict_value.replace("<<<" + var + ">>>", new_value)
            self.glob.lib.msg.log("Replacing <<<" + var + ">>> with " + new_value)

        return dict_value

    # Check dict for vars, resolve them and then evaluate for arithmatic
    def eval_dict(self, cfg_dict, eval_runtime_vars):

        self.set_search_space()

        runtime_keys = None
        if eval_runtime_vars:
            print("HERE", self.glob.config['runtime'])
            runtime_keys = self.glob.config['runtime'].keys()

        for key in cfg_dict:
            # Resolve variables
            cfg_dict[key] = self.resolve_vars(cfg_dict[key], runtime_keys) 
            
            # If operators are present
            if self.has_arithmatic(cfg_dict[key]):
                cfg_dict[key] = str(self.evaluate_arithmatic(cfg_dict[key]))

    # Get key from string
    def extract_key(self, expr):
        return re.search("\[(.*?)\]", expr).group(1)

    # Replace [key] with value
    def replace_key(self, expr, key, value):
        return expr.replace("["+key+"]", str(value))

    # Get value from string
    def get_value(self, expr):
       return expr.split("=")[1].strip()

    # Evaluate logical expression
    def eval_logic_expr(self, expr):

        self.glob.lib.msg.log("Evaluating logical " +  str(expr))
        try:
            return eval(expr)
        except:
            self.glob.lib.msg.error("Unable to eval " + expr)

    # Replace variable in condition with existing value from search space, then evaluate expression
    def eval_cond(self, cond):
        key = self.extract_key(cond)
        return self.eval_logic_expr(self.replace_key(cond, key, self.get_dict_value(key)))

    # Update dict value with rule value
    def apply_rule(self, action):
        key = self.extract_key(action)
        value = action.split("=")[1].strip().replace('"', '').replace("'", "")
   
        # If this value has already been overloaded - don't change it a 2nd time (rules < user_overload)
        if key in self.glob.overloaded:
            self.glob.lib.msg.low("Skipping conflicting system rule: " + key + "='" + value + "'")
            return

        # Search dicts for matching key
        for search_dict in self.search_space:
            if key in search_dict.keys():
                self.glob.lib.msg.low("Applying system rule: " + key + " '" + search_dict[key] + "' > '" + value + "'")
                search_dict[key] = value
                return
        # No existing key found
        self.glob.lib.msg.error("No existing parameter found matching '" + key + "' from rules file.")

    # Evaluate a rule's condition, apply updates 
    def eval_rule(self, rule):

        self.glob.lib.msg.log("Evaluating rule: " + str(rule))

        rule = rule.replace("AND", "and")
        rule = rule.replace("OR", "or")
        condition = rule.split(":")[0].replace('"', '\'')
        action = rule.split(":")[1].replace('"', '\'')

        # Badly formatted rule
        if not condition or not action:
            self.glob.lib.msg.error("Rule formatting error in '" + rule + "'")

        conditions = []
        #check for AND
        if "and" in condition:
            conditions.extend(condition.split(" and "))
        #check for OR
        elif "or" in condition:
            conditions.extend(condition.split(" or "))
        else:
            conditions = [condition]

        # Evaluate each condition
        for cond in conditions:
            condition = condition.replace(cond, str(self.eval_cond(cond)))

        # Evaluate whole expression 
        if self.eval_logic_expr(condition):
            self.apply_rule(action)

    # Apply system rules
    def apply_system_rules(self):

        # Skip applying system rules
        if not self.glob.stg['apply_system_rules']:
            return

        # Rules file for this system
        rules_file = self.glob.lib.files.find_in([self.glob.stg['rules_path']], self.glob.system['system']+".cfg", False)
        # System rules file exists
        if rules_file:

            # Set variable search space
            self.set_search_space()
            
            # Read rules from file
            rules = self.glob.lib.files.read(rules_file)  

            # Evaluate each rule
            for line in rules:
                self.eval_rule(line)

