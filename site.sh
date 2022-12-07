#!/usr/bin/env bash

ml python3

set() {
    echo "$1=$2"
    export $1="$2"
}

# SETUP
set BPS_SYSTEM $TACC_SYSTEM
set BPS_VERSION "1.7.1"
[[ -z BP_DEV ]] && set BP_DEV 1
set BUILD_HASH `echo $RANDOM | md5sum | head -c 8`

# Enforce client re-validate with higher number
set VALIDATOR_VER "2"

set BUILD_DATE "$(date +'%Y-%m-%d %H:%m:%S')"
set BPS_VERSION_STR "${BPS_VERSION}-${BUILD_HASH}.${VALIDATOR_VER}"
set PY_VERSION "3.`python3 --version | head -n 1 | cut -d '.' -f 2`"
set BP_HOME '$HOME/benchpro'
set BP_APPS '$SCRATCH/benchpro/apps'
set BP_RESULTS '$SCRATCH/benchpro/results'

# DB access
set DB_USER "benchpro"
set DB_HOST "benchpro.tacc.utexas.edu"
set REMOTE_PATH "/home/benchpro/benchdb/data_store"

# SYSTEM SPECIFIC
if [[ $BPS_SYSTEM = "frontera" ]]; then
    set TACC_SCRATCH "/scratch1"
    SITE="${TACC_SCRATCH}/hpc_tools/benchpro"

elif [[ $BPS_SYSTEM = "ls6" ]]; then
    set TACC_SCRATCH "/scratch"
    SITE="${TACC_SCRATCH}/projects/benchpro"

elif [[ $BPS_SYSTEM = "stampede2" ]]; then
    set TACC_SCRATCH "/scratch"
    SITE="${TACC_SCRATCH}/hpc_tools/benchpro"
fi

#BP_DEV=0

set BP_REPO "${SITE}/repo"

# PRODUCTION INSTALL
if [[ $BP_DEV == 0 ]]; then
    printf "\n\033[0;31m!!!YOU ARE ABOUT TO REDEPLOY THE PRODUCTION SITE PACKAGE!!!\033[0m \n\n"
    sleep 5
# DEV INSTALL
else
    SITE="${SITE}-dev"
    printf "\n\033[0;32mDEPLOYING SITE PACKAGE IN DEV MODE [BP_DEV=1]\033[0m\n\n"
    sleep 2
fi


set BPS_HOME "${SITE}"
set BPS_COLLECT "${BPS_HOME}/collection"
set BPS_INC "${BPS_HOME}/package/benchpro"
set BPS_MODULES "${BPS_HOME}/modulefiles"
set BPS_BIN "${BPS_HOME}/python/bin"

today=`date +%Y-%m-%d_%H-%M-%S`
set BP_LOG "${BPS_HOME}/logs/build_${today}.log"

return 0

