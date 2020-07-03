#!/bin/bash

# Simple script to get current temperature readings from processor packages and other
# devices.  Set up to deal with the most common configurations at TACC.
#
# mccalpin@tacc.utexas.edu, revised to 2020-07-03
#
# The "coretemp" kernel module sets up interfaces in /sys/class/hwmon/ to allow
# access to lots of temperature-related functionality.
# This script only looks at the labels and the current temperatures.
# /sys/class/hwmon/ contains one or more subdirectories named
#	/sys/class/hwmon/hwmon0/
#	/sys/class/hwmon/hwmon1/
#	/sys/class/hwmon/hwmon2/
#	/sys/class/hwmon/...
# There is no fixed meaning for the indices, so the script looks
# at the /sys/class/hwmon/hwmon*/name files to decide how to report
# results.
# The script current handles Intel processors (name="coretemp"),
# AMD processors (name="k10temp"), and AMD GPUs (name="amdgpu").
# Any other values report the value in the "name" file and the 
# temperature from the temp1_input file.
#
# NOTES:
# a. There can be many temp[n]_input files -- for example on Intel
#    processors there is one per core plus one for the package.
#    So far every system I have seen uses the index "1" for the
#    package-level reporting, so this script assumes that is a 
#    standard.  Caveat Emptor. YMMV.
# b. The temp[n]_input files report temperature in thousandths
#    of a degree Celcius.  The script divides by 1000 and prints the
#    results using the default awk formatting.  This will always give
#    integers with Intel processors, but may include fractional values
#    for other devices.
#
# Bugs:
# 1. For Intel processors, the script checks to see if the 
#    temp1_label file begins with "Physical" (indicating a 
#    package-level value).  If so, the result is printed.  If not,
#    the script does not look for "Physical" in the other 
#    "temp*_label" files.
# 2. For AMD processors and GPUs there is no obvious reporting 
#    of socket or slot numbers.  The script reports the results
#    in alphabetical order of /sys/class/hwmon/hwmon*/ entries.
#

REPORT=0
for LOCATION in /sys/class/hwmon/*
do
	if [ -e $LOCATION/name ]
	then
		TYPE=`cat $LOCATION/name`
		case $TYPE in
			coretemp)
				#echo "DEBUG: Intel processor found: $TYPE"
				if [ -e $LOCATION/temp1_label ]
				then
					LABEL=`cat $LOCATION/temp1_label`
					if [[ $LABEL == "Physical"* ]]
					then
						echo -n "$LABEL " | sed 's/Physical/Package/'
						cat $LOCATION/temp1_input | awk '{print "temperature",$1/1000.0,"C"}'
					fi
				fi
				REPORT=1
				;;
			k10temp)
				#echo "DEBUG: AMD processor found: $TYPE"
				REPORT=2
				;;
			amdgpu)
				#echo "DEBUG: AMD GPU found: $TYPE"
				REPORT=3
				;;
			*)
				#echo "DEBUG: some other device: $TYPE"
				REPORT=99
				;;
		esac
	fi
	#echo "DEBUG: $LOCATION $REPORT"
	if [ $REPORT -gt 1 ]
	then
		echo -n "$TYPE "
		cat $LOCATION/temp1_input | awk '{print "temperature",$1/1000.0,"C"}'
	fi
done

exit

for LOCATION in /sys/class/hwmon/*
do
	if [ -e $LOCATION/temp1_label ]
	then
		LABEL=`cat $LOCATION/temp1_label`
		if [[ $LABEL == "Physical"* ]]
		then
			echo -n "$LABEL " | sed 's/Physical/Package/'
			#cat $LOCATION/temp1_input
			cat $LOCATION/temp1_input | awk '{print "temperature",$1/1000.0,"C"}'
			#cat $LOCATION/temp1_input | awk '{printf "%.3f\n",$1/1000.0}'
		fi
	fi
done
