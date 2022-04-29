#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label: x.y.z"
    exit 1
fi

# Update version in setup.py
sed -i "/version=/c\    version=\'${1}\'," ./setup.py

# Update site.sh
sed -i "/set BP_VERSION/c\set BP_VERSION \"${1}\"" ./site.sh

# Update version in user repo
echo "benchpro v${1}" > $HOME/benchpro/.version
date >> $HOME/benchpro/.version

echo "Push user repo before reinstalling"
echo "--------------"
echo "git -C $HOME/benchpro add ."
echo "git -C $HOME/benchpro commit -m 'updated version info'"
echo "git -C $HOME/benchpro push "
echo
echo "Version updated"
