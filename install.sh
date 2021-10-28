#!/bin/bash

quit() {
    printf "$1"
    exit 1
}

WORKING_DIR=`pwd`

# Source site variables
SOURCE_FILE="$WORKING_DIR/site.sh"
printf "Reading ${SOURCE_FILE}...\n"
source $SOURCE_FILE
if [ $? != 0 ]; then quit "\nCan't source ${SOURCE_FILE}, quitting.\n\n"; fi

# Get path to SSH key - not stored in repo
SSH_KEY=""
if [ "$1" = "" ]; then
    printf "Enter path to SSH key:\n"
    read SSH_KEY
    if [ $? != 0 ]; then quit "\nProvided SSH key not found.\nQuitting.\n\n"; fi
else
    SSH_KEY=$1    
fi

# Clean up env & build/install directories
${WORKING_DIR}/dev/clean.sh
rm -rf ${BT_SITE}/python/lib/python${PY_VERSION}/site-packages/benchtool-${BT_VERSION}*
rm -f ${BT_SITE}/modulefiles/benchtool/*.lua
rm -f ${BT_SITE}/package
rm -f ${BT_SITE}/python/lib/python${PY_VERSION}/site-packages/benchtool-latest

# Setup
mkdir -p ${BT_SITE}/logs
mkdir -p ${BT_SITE}/repo
mkdir -p ${BT_SITE}/collection
mkdir -p ${BT_SITE}/python/lib/python${PY_VERSION}/site-packages
mkdir -p ${BT_SITE}/modulefiles/benchtool

printf "\nCleaned up...\n\n"

# Copy  and contextualize module file
cp ${WORKING_DIR}/data/modulefiles/benchtool.lua                        ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_site/c\local bt_site = \"${BT_SITE}\""                ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_repo/c\local bt_repo = \"${BT_REPO}\""                ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local tacc_scratch/c\local tacc_scratch = \"${TACC_SCRATCH}\"" ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_home/c\local bt_home = \"${BT_HOME}\""                ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_apps/c\local bt_apps = \"${BT_APPS}\""                ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_results/c\local bt_results = \"${BT_RESULTS}\""       ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local bt_version/c\local bt_version = \"${BT_VERSION}\""       ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua
sed -i "/local py_version/c\local py_version = \"${PY_VERSION}\""       ${BT_SITE}/modulefiles/benchtool/${BT_VERSION}.lua

ml use ${BT_SITE}/modulefiles
ml benchtool
if [ $? != 0 ]; then quit "\nCan't load module, quitting.\n\n"; fi

printf "\nModule loaded...\n\n"

# Install python package
python3 setup.py install --prefix=${BT_SITE}/python/ > /dev/null
if [ $? != 0 ]; then quit "\nPackage installation failed, quitting.\n\n"; fi

printf "\nPackage installed...\n\n"

# Change group permissions
chmod -R g+X ${BT_SITE}
chmod -R g+r ${BT_SITE}
chmod g+x ${BT_SITE}/python/bin/benchtool
chmod -R g+w ${BT_SITE}/collection

# Update symlink
ln -s python/lib/python${PY_VERSION}/site-packages/benchtool-latest/ ${BT_SITE}/package 
ln -s benchtool-${BT_VERSION}-py${PY_VERSION}.egg/ ${BT_SITE}/python/lib/python${PY_VERSION}/site-packages/benchtool-latest

# Install user files 
YOUR_BT=$(eval echo $BT_HOME)

if [ ! -d $YOUR_BT ]; then
    git clone git@github.com:TACC/benchtool.git $YOUR_BT
else
    git -C $YOUR_BT pull 
fi

if [ $? != 0 ]; then quit "\nUser files install failed, quitting.\n\n"; fi

benchtool --validate
if [ $? != 0 ]; then quit "\nValidation failed, quitting.\n\n"; fi

printf "\nValidation complete...\n\n"

# Check version
benchtool --version
if [ $? != 0 ]; then quit "\nVersion check failed, quitting.\n\n"; fi

# Clean build files
${WORKING_DIR}/dev/clean.sh

# Check SSH connection
ssh -i ${SSH_KEY} ${DB_USER}@${DB_HOST} -t "echo 'Connection test'" > /dev/null 2>&1
if [ $? != 0 ]; then quit "\nSSH connection failed, quitting.\n\n"; fi

echo
echo "------------------------------------------------"
echo "Benchtool successfully installed into $BT_SITE"
echo "User files installed into $BT_HOME for testing"
echo "To use, load site module with:"
echo "ml use $BT_SITE/modulefiles"
echo "ml benchtool"
echo
echo "------------------------------------------------"
echo "Add the following lines to your crontab:"
echo "* /5 * * * * /bin/rsync --remove-source-files -av -e \"ssh -i $SSH_KEY\" $BT_SITE/collection/* $DB_USER@$DB_HOST:$REMOTE_PATH/ | tee -a $BT_SITE/logs/collect_\`date +\\%Y\\-%m-%d\`.log"
echo "0 0 * * * /bin/rsync -av /home1/06280/mcawood/work2/repo_backup/ $BT_SITE/repo/ | tee -a $BT_SITE/logs/repo_\`date +\\%Y\\-%m-%d\`.log"
echo 

