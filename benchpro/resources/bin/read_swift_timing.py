#!/usr/bin/env python3

import sys
time_tally = 0.
cut_start = 0
cut_end = 0

with open(sys.argv[1]) as fp:
        line = fp.readline()
        results = False
        while line:
            if results:
                time = line[cut_start:cut_end]
                try:
                    time_tally += float(time.strip())
                except:
                    pass

            if "#   Step" in line:
                cut_start = line.find("Wall-clock")
                cut_end = line.find("Props")
                results = True
            line = fp.readline()

if time_tally:
        print(round(time_tally/1000, 1))

