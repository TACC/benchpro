import configparser as cp
import os

ini_parser    = cp.ConfigParser( strict=False )
ini_parser.optionxform=str
ini_parser.read("test.ini")

stage_dict = dict(ini_parser.items('sect'))

for op in stage_dict:
    print("This op:", op)
    for loc in stage_dict[op].split(","):
        if os.path.isfile(loc.strip()):
            print("src", loc)
        else:
            print("File not found")
            




