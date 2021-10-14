#!/bin/bash
WORKING_DIR=`pwd`
VERSION="1.2.5"
PY_VER="3.`python3 --version | cut -d '.' -f 2`"
SITE_PATH="/scratch1/hpc_tools/benchtool"
USER_PATH="$HOME/benchtool"

SSH_KEY=""
DB_USER="bench_user"
DB_HOST="tacc-stats03.tacc.utexas.edu"
REMOTE_PATH="/home/mcawood/benchdb/data_store"

printf "uno momento por favor...\n"

# Get path to SSH key - not stored in repo
if [ "$1" = "" ]; then
    printf "Enter path to SSH key:\n"
    read SSH_KEY
else
    SSH_KEY=$1    
fi

if [ ! -f $SSH_KEY ]; then
    printf "\nProvided SSH key not found.\nQuitting.\n\n"
    exit 1
fi

# Clean up env & build/install directories
ml unload benchtool
${WORKING_DIR}/dev/clean.sh
rm -rf ${SITE_PATH}/python/lib/python${PY_VER}/site-packages/benchtool-${VERSION}*
rm -f ${SITE_PATH}/modulefiles/benchtool/${VERSION}.lua
rm -f ${SITE_PATH}/package
rm -f ${SITE_PATH}/python/lib/python${PY_VER}/site-packages/benchtool-latest

# Setup
mkdir -p ${SITE_PATH}/logs
mkdir -p ${SITE_PATH}/repo
mkdir -p ${SITE_PATH}/collection
mkdir -p ${SITE_PATH}/python/lib/python${PY_VER}/site-packages
mkdir -p ${SITE_PATH}/modulefiles/benchtool

printf "\nCleaned up...\n\n"

# Copy module file
cp ${WORKING_DIR}/data/modulefiles/benchtool/*.lua ${SITE_PATH}/modulefiles/benchtool/
sed -i "/local site_dir/c\local site_dir = \"${SITE_PATH}\"" ${SITE_PATH}/modulefiles/benchtool/*.lua

ml use ${SITE_PATH}/modulefiles
ml benchtool

if [ $? != 0 ]; then
    printf "\nCan't load module, quitting.\n\n"
    exit 1
fi

printf "\nModule loaded...\n\n"

# Install python package
python3 setup.py install --prefix=${SITE_PATH}/python/ > /dev/null

if [ $? != 0 ]; then
    printf "\nPackage installation failed, quitting.\n\n"
    exit 1
fi

printf "\nPackage installed...\n\n"

# Change group permissions
chmod -R g+X ${SITE_PATH}
chmod -R g+r ${SITE_PATH}
chmod g+x ${SITE_PATH}/python/bin/benchtool
chmod -R g+w ${SITE_PATH}/collection

# Update symlink
ln -s python/lib/python${PY_VER}/site-packages/benchtool-latest/ ${BT_SITE}/package 
ln -s benchtool-${BT_VERSION}-py${PY_VER}.egg/ ${BT_SITE}/python/lib/python${PY_VER}/site-packages/benchtool-latest

# Install user files 

if [ ! -d $USER_PATH ]; then
    git clone git@github.com:TACC/benchtool.git $USER_PATH
    printf "\nUser files installed...\n\n"
else
    
    git -C $USER_PATH pull 
    printf "\nUser files updated...\n\n"
fi

if [ $? != 0 ]; then
    printf "\nUser files install failed, quitting.\n\n"
    exit 1
fi

benchtool --validate

if [ $? != 0 ]; then
    printf "\nValidation failed, quitting.\n\n"
    exit 1
fi

printf "\nValidation complete...\n\n"

# Check version
benchtool --version

if [ $? != 0 ]; then
    printf "\nVersion check failed, quitting.\n\n"
    exit 1
fi

# Clean build files
$WORKING_DIR/dev/clean.sh

# Check SSH connection
ssh -i $SSH_KEY $DB_USER@$DB_HOST -t "echo 'Connection test'" > /dev/null 2>&1

if [ $? != 0 ]; then
    printf "SSH connection failed, quitting.\n"
    exit 1
fi

echo
echo "------------------------------------------------"
echo "Benchtool successfully installed into $SITE_PATH"
echo "User files installed into $BT_HOME for testing"
echo "To use, load site module with:"
echo "ml use $SITE_PATH/modulefiles"
echo "ml benchtool"
echo
echo "------------------------------------------------"
echo "Add the following lines to your crontab:"
echo "* /5 * * * * /bin/rsync --remove-source-files -av -e \"ssh -i $SSH_KEY\" $BT_SITE/collection/* $DB_USER@$DB_HOST:$REMOTE_PATH/ | tee -a $SITE_PATH/logs/collect_\`date +\\%Y\\-%m-%d\`.log"
echo "0 0 * * * /bin/rsync -av /home1/06280/mcawood/work2/repo_backup/ $SITE_PATH/repo/ | tee -a $SITE_PATH/logs/repo_\`date +\\%Y\\-%m-%d\`.log"
echo 

