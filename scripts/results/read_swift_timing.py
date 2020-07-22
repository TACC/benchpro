#!/usr/bin/env python3

import sys
time_tally = 0.
with open(sys.argv[1]) as fp:
	line = fp.readline()
	results = False
	while line:
		if results:
			time = line[-20:-3]
			try:
				time_tally += float(time.strip())
			except:
				pass

		if "#   Step" in line: results = True
		line = fp.readline()

if time_tally:
	print(round(time_tally/1000, 1))

