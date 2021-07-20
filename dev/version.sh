#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label"
    exit 1
fi

# Update module filename
mv src/data/modulefiles/benchtool/*.lua src/data/modulefiles/benchtool/${1}.lua

# Update version in settings.ini
sed -i "/version =/c\version = ${1}" src/data/settings.ini

# Update version file
echo "benchtool v${1}" > .version
date >> .version

echo "Version info updated."
