#!/bin/bash

source sourceme

APP=quantum

# Remove existing installation
benchtool --remove $APP		> /dev/null

echo "EXIT CODES:"
benchtool --avail			> /dev/null
echo     "--avail       $?"

benchtool --build $APP --setting dry_run=True	> /dev/null
echo     "--build       $?"

benchtool --installed		> /dev/null
echo     "--installed   $?"

benchtool --queryApp $APP	> /dev/null
echo     "--queryApp    $?"

benchtool --bench $APP --setting dry_run=True > /dev/null
echo     "--bench       $?"

benchtool --remove $APP  	> /dev/null
echo     "--remove      $?"

benchtool --clean			> /dev/null
echo     "--clean       $?"

benchtool --queryResult all > /dev/null
echo     "--queryResult $?"
