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
python3 setup.py install

# Install user files
benchtool --install
benchtool --validate

# Copy SSH key
cp ~/scratch1/benchtool.old5/auth/id_rsa.bench_user $BENCHTOOL/auth/
benchtool --validate

# Check version
benchtool --version
