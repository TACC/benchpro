#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label: x.y.z"
    exit 1
fi

# Update version in setup.py
sed -i "/version=/c\    version=\'${1}\'," ./setup.py

# Update site.sh
sed -i "/set BT_VERSION/c\set BT_VERSION \"${1}\"" ./site.sh

# Update version in user repo
echo "benchtool v${1}" > ./benchtool/.version
date >> ./benchtool/.version

echo "Push user repo before reinstalling"
echo "--------------"
echo "git -C benchtool add ."
echo "git -C benchtool commit -m 'updated version info'"
echo "git -C benchtool push "
echo
echo "Version updated"
