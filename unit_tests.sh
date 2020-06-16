#!/bin/bash

source ld_env.sh

APP=lammps

# Remove existing installation
benchtool --remove $APP  > /dev/null

echo "EXIT CODES:"

benchtool --avail          > /dev/null
echo     "--avail     $?"

benchtool --install $APP > /dev/null
echo     "--install   $?"

benchtool --installed      > /dev/null
echo     "--installed $?"

benchtool --query $APP   > /dev/null
echo     "--query     $?"

benchtool --bench $APP     > /dev/null
echo     "--bench     $?"

benchtool --remove $APP  > /dev/null
echo     "--remove    $?"

benchtool --clean          > /dev/null
echo     "--clean     $?"
