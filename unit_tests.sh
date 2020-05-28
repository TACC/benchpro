#!/bin/bash

source ld_env.sh

APP=swift

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

benchtool --run $APP     > /dev/null
echo     "--run       $?"

benchtool --remove $APP  > /dev/null
echo     "--remove    $?"

benchtool --clean          > /dev/null
echo     "--clean     $?"
