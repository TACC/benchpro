#!/bin/bash

# Clean user files
benchtool --uninstall

# Remove python package
pip uninstall -y benchtool

# Clean build files
rm -rf benchtool.egg-info
rm -rf build
rm -rf dist

# Install python package
python3 setup.py install --prefix=/scratch1/hpc_tools/benchtool/python/
chgrp -R G-25072 /scratch1/hpc_tools/benchtool/python/
chmod -R g+X /scratch1/hpc_tools/benchtool/python/
chmod -R g+r /scratch1/hpc_tools/benchtool/python/
chmod g+x /scratch1/hpc_tools/benchtool/python/bin/benchtool


# Install user files
benchtool --install
benchtool --validate

# Check version
benchtool --version
