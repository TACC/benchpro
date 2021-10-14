#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label"
    exit 1
fi

# Update module filename
mv ./data/modulefiles/benchtool/*.lua ./data/modulefiles/benchtool/${1}.lua
sed -i "/local version/c\local version         = \"${1}\"" ./data/modulefiles/benchtool/${1}.lua

# Update version in setup.py
sed -i "/version=/c\    version=\'${1}\'," ./setup.py

# Update install.sh
sed -i "/VERSION=/c\VERSION=\"${1}\"" ./install.sh

# Update version in user repo
echo "benchtool v${1}" > ./benchtool/.version
date >> ./benchtool/.version


echo "Push user repo"
echo "--------------"
echo "git -C benchtool add ."
echo "git -C benchtool commit -m 'updated version info'"
echo "git -C benchtool push "
echo
echo "Version updated"
