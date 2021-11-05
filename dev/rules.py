import re
import sys

options = {"nodes": 4, "queue": "someQueue"}

# Get key from string
def get_key(expr):
    return re.search("\[(.*?)\]", expr).group(1)

# Replace [key] with value
def replace_key(expr, key):
    return expr.replace("["+key+"]", str(options[key]))

# Get value from string
def get_value(expr):
   return expr.split("=")[1].strip() 

# Evaluate logical expression
def eval_expr(expr):
    try:
        return eval(expr)
    except:
        print("Unable to eval " + expr)
        sys.exit(1)

# Evaluate variable condition
def eval_cond(cond):
    key = get_key(cond)
    # Key exists 
    if key in options.keys():
        return eval_expr(replace_key(cond, key))
    # Key doesn't exist
    else:
        print("Key not found")
        sys.exit(1)

# Break condition by logicals, evaluate and update result
def parse_line(line):

    line = line.replace("AND", "and")
    line = line.replace("OR", "or")

    condition = line.split(":")[0]
    result = line.split(":")[1]

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
        condition = condition.replace(cond, str(eval_cond(cond)))

    # Evaluate whole expression
    test = eval_expr(condition)

    if test:
        print("System rule applied, " + get_key(result) + " '" + options[get_key(result)] + "' > '" + get_value(result).strip('"') + "'")


with open("benchtool/config/rules/frontera.cfg") as f:

    print("nodes = ", options['nodes'])

    lines = f.readlines()
    for line in lines:
        print("Condition: " + line.strip())
        parse_line(line.strip())
        print()
