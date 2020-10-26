#!/bin/bash

source sourceme

APP=lammps
BENCH=ljmelt

# Remove existing installation
benchtool --remove $APP		> /dev/null

echo "EXIT CODES:"
benchtool --avail			> /dev/null
echo     "--avail       $?"

benchtool --build $APP --overload dry_run=True	> /dev/null
echo     "--build       $?"

benchtool --installed		> /dev/null
echo     "--installed   $?"

benchtool --queryApp $APP	> /dev/null
echo     "--queryApp    $?"

benchtool --bench $BENCH --overload dry_run=True > /dev/null
echo     "--bench       $?"

benchtool --remove $APP  	> /dev/null
echo     "--remove      $?"

benchtool --clean			> /dev/null
echo     "--clean       $?"

benchtool --capture         > /dev/null
echo     "--capture     $?"

benchtool --listResults all > /dev/null
echo     "--queryResult $?"

benchtool --queryDB all     > /dev/null
echo     "--queryDB     $?"