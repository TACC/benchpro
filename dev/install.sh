#!/bin/bash

# Clean build files
./dev/clean.sh

# Remove python package
python3 -m pip uninstall -y benchtool

# Install package
INSTALL_DIR=/scratch1/hpc_tools/benchtool

mkdir -p $INSTALL_DIR/python
mkdir -p $INSTALL_DIR/modulefiles/benchtool

# Copy module file
cp src/data/modulefiles/benchtool/*.lua $INSTALL_DIR/modulefiles/benchtool/

ml use $INSTALL_DIR/modulefiles
ml benchtool

# Install python package
python3 setup.py install --prefix=$INSTALL_DIR/python/
chmod -R g+X $INSTALL_DIR/python/
chmod -R g+r $INSTALL_DIR/python/
chmod g+x $INSTALL_DIR/python/bin/benchtool

rm $BT_SITE/python/lib/python3.7/site-packages/benchtool-latest
ln -s benchtool-$BT_VERSION-py3.7.egg/ $BT_SITE/python/lib/python3.7/site-packages/benchtool-latest

# Install user files
benchtool --update

# Check version
benchtool --version

# Clean build files
./dev/clean.sh
