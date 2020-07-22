#!/usr/bin/env python3

import configparser as cp

def get_prolog_operations():
    
    cfg_file = "prolog.cfg"
    prolog_parser = cp.ConfigParser()
    prolog_parser.optionxform=str
    prolog_parser.read(cfg_file)

    prolog_dict = {}    

    for section in prolog_parser.sections():
        prolog_dict[section] = {}
        for value in prolog_parser.options(section):
            prolog_dict[section][value] = prolog_parser.get(section, value)

    return prolog_dict


def write_prolog_script(prolog_dict):

    script_file = "prolog.sh"


    with open(script_file, 'w') as out:

        out.write("#!/bin/bash \n \n")

        out.write("function warn { \n")
        out.write("    echo warn \n")

        out.write("} \n \n")

        for section in prolog_dict:
            out.write("# " + section + "\n")

            out.write("test=$("+prolog_dict[section]['test_statement'].replace('$file', prolog_dict[section]['test_file'])+") \n")

            out.write("if [ $test " + prolog_dict[section]['test_condition'] + " ]; then \n")
            out.write("    " + prolog_dict[section]['test_result'] + " \n")
            out.write("fi \n")

prolog_dict = get_prolog_operations()
write_prolog_script(prolog_dict)

