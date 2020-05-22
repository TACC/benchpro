#!/bin/bash

source ld_env.sh

# Remove existing installation
benchtool --remove lammps  > /dev/null

echo "EXIT CODES:"

benchtool --avail          > /dev/null
echo     "--avail     $?"

benchtool --install lammps > /dev/null
echo     "--install   $?"

benchtool --installed      > /dev/null
echo     "--installed $?"

benchtool --query lammps   > /dev/null
echo     "--query     $?"

benchtool --run lammps     > /dev/null
echo     "--run       $?"

benchtool --remove lammps  > /dev/null
echo     "--remove    $?"

benchtool --clean          > /dev/null
echo     "--clean     $?"
