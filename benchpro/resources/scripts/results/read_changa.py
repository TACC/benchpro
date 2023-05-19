#!/usr/bin/env python3
import sys
time = 0
with open(sys.argv[1]) as fp:
    lines = fp.readlines()
    for line in lines:
        if line.startswith('Big step'):
            time += float(line.split(" ")[4])
print(time)
