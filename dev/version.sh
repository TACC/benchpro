#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label"
    exit 1
fi

# Update module filename
mv src/data/modulefiles/benchtool/*.lua src/data/modulefiles/benchtool/${1}.lua
sed -i "/local version/c\local version         = \"${1}\"" src/data/modulefiles/benchtool/${1}.lua

# Update version in settings.ini
sed -i "/version =/c\version = ${1}" src/data/settings.ini

# Update version in setup.py
sed -i "/version=/c\    version=\'${1}\'," setup.py

# Update version file
echo "benchtool v${1}" > src/data/.version
date >> src/data/.version

echo "Version info updated."
