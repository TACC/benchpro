#!/bin/bash

source sourceme

APP=lammps
BENCH=ljmelt

# Remove existing installation
benchtool --delApp $APP		> /dev/null

echo "EXIT CODES:"

benchtool --help           > /dev/null
echo     "--help          $?"

benchtool --version           > /dev/null
echo     "--version       $?"

benchtool --validate           > /dev/null
echo     "--validate      $?"

benchtool --avail			> /dev/null
echo     "--avail         $?"

benchtool --build $APP --overload dry_run=True	> /dev/null
echo     "--build         $?"

benchtool --listApps		> /dev/null
echo     "--listApps      $?"

benchtool --queryApp $APP	> /dev/null
echo     "--queryApp      $?"

benchtool --bench $BENCH --overload dry_run=True > /dev/null
echo     "--bench         $?"

benchtool --last           > /dev/null
echo     "--last          $?"

output=$(benchtool --listResults pending | tail -n 3 | head -n 1)
benchtool --queryResult $output > /dev/null
echo     "--queryResult   $?"

benchtool --delApp $APP  	> /dev/null
echo     "--delApp        $?"

benchtool --capture         > /dev/null
echo     "--capture       $?"

benchtool --listResults all > /dev/null
echo     "--listResults   $?"

benchtool --dbResult dataset=$BENCH --export    > /dev/null
echo     "--dbResult      $?"

benchtool --dbApp code=$APP   > /dev/null
echo     "--dbApp         $?"

benchtool --build all_apps --overload dry_run=True > /dev/null
echo     "--suite         $?"

benchtool --history           > /dev/null
echo     "--history       $?"

benchtool --clean           > /dev/null
echo     "--clean         $?"

