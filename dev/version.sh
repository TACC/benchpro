#!/bin/bash

if [ -z ${1} ]; then
    echo "Provide version label: x.y.z"
    exit 1
fi

# Update version in setup.py
sed -i "/version=/c\    version=\'${1}\'," ./setup.py

# Update site.sh
sed -i "/set BPS_VERSION /c\set BPS_VERSION \"${1}\"" ./site.sh

echo
echo "Version updated"
