#!/bin/bash

# Clean build files
rm -rf benchtool.egg-info
rm -rf build
rm -rf dist

# Install python package
python3 setup.py install

# Install user files
benchtool --update

# Check version
benchtool --version
