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
rm -rf ${BP_SITE}/python/lib/python${PY_VERSION}/site-packages/benchpro-${BP_VERSION}*
rm -f ${BP_SITE}/modulefiles/benchpro/*.lua
rm -f ${BP_SITE}/package
rm -f ${BP_SITE}/python/lib/python${PY_VERSION}/site-packages/benchpro-latest

# Setup
mkdir -p ${BP_SITE}/logs
mkdir -p ${BP_SITE}/repo
mkdir -p ${BP_SITE}/collection
mkdir -p ${BP_SITE}/python/lib/python${PY_VERSION}/site-packages
mkdir -p ${BP_SITE}/modulefiles/benchpro

printf "\nCleaned up...\n\n"

# Copy  and contextualize module file
cp ${WORKING_DIR}/data/modulefiles/benchpro.lua                        ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_site/c\local bp_site = \"${BP_SITE}\""                ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_repo/c\local bp_repo = \"${BP_REPO}\""                ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local tacc_scratch/c\local tacc_scratch = \"${TACC_SCRATCH}\"" ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_home/c\local bp_home = \"${BP_HOME}\""                ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_apps/c\local bp_apps = \"${BP_APPS}\""                ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_results/c\local bp_results = \"${BP_RESULTS}\""       ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local bp_version/c\local bp_version = \"${BP_VERSION}\""       ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua
sed -i "/local py_version/c\local py_version = \"${PY_VERSION}\""       ${BP_SITE}/modulefiles/benchpro/${BP_VERSION}.lua

ml use ${BP_SITE}/modulefiles
ml benchpro
if [ $? != 0 ]; then quit "\nCan't load module, quitting.\n\n"; fi

printf "\nModule loaded...\n\n"

# Install python package
python3 setup.py install --prefix=${BP_SITE}/python/ > /dev/null
if [ $? != 0 ]; then quit "\nPackage installation failed, quitting.\n\n"; fi

printf "\nPackage installed...\n\n"

# Change group permissions
chmod -R g+X ${BP_SITE}
chmod -R g+r ${BP_SITE}
chmod g+x ${BP_SITE}/python/bin/benchpro
chmod -R g+w ${BP_SITE}/collection

# Update symlink
ln -s python/lib/python${PY_VERSION}/site-packages/benchpro-latest/ ${BP_SITE}/package 
ln -s benchpro-${BP_VERSION}-py${PY_VERSION}.egg/ ${BP_SITE}/python/lib/python${PY_VERSION}/site-packages/benchpro-latest

# Install user files 
YOUR_BP=$(eval echo $BP_HOME)

if [ ! -d $YOUR_BP ]; then
    git clone git@github.com:TACC/benchpro.git $YOUR_BP
else
    git -C $YOUR_BP pull 
fi

if [ $? != 0 ]; then quit "\nUser files install failed, quitting.\n\n"; fi

benchpro --validate
if [ $? != 0 ]; then quit "\nValidation failed, quitting.\n\n"; fi

printf "\nValidation complete...\n\n"

# Check version
benchpro --version
if [ $? != 0 ]; then quit "\nVersion check failed, quitting.\n\n"; fi

# Clean build files
${WORKING_DIR}/dev/clean.sh

# Check SSH connection
ssh -i ${SSH_KEY} ${DB_USER}@${DB_HOST} -t "echo 'Connection test'" > /dev/null 2>&1
if [ $? != 0 ]; then quit "\nSSH connection failed, quitting.\n\n"; fi

echo
echo "------------------------------------------------"
echo "Benchtool successfully installed into $BP_SITE"
echo "User files installed into $BP_HOME for testing"
echo "To use, load site module with:"
echo "ml use $BP_SITE/modulefiles"
echo "ml benchpro"
echo
echo "------------------------------------------------"
echo "Add the following lines to your crontab:"
echo "* /5 * * * * /bin/rsync --remove-source-files -av -e \"ssh -i $SSH_KEY\" $BP_SITE/collection/* $DB_USER@$DB_HOST:$REMOTE_PATH/ | tee -a $BP_SITE/logs/collect_\`date +\\%Y\\-%m-%d\`.log"
echo "0 0 * * * /bin/rsync -av /home1/06280/mcawood/work2/repo_backup/ $BP_SITE/repo/ | tee -a $BP_SITE/logs/repo_\`date +\\%Y\\-%m-%d\`.log"
echo 

