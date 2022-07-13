#!/bin/bash

ml python3

set() {
    echo "$1=$2"
    export $1="$2"
}

# SETUP
set BP_SYSTEM $TACC_SYSTEM
set BP_SITE_VERSION "1.5.0"
[[ -z BP_DEV ]] && set BP_DEV 1
set BUILD_HASH `echo $RANDOM | md5sum | head -c 8`
set VALIDATOR_VER "1"
set BUILD_DATE "$(date +'%Y-%m-%d %H:%m:%S')"
set BP_SITE_VERSION_STR "${BP_SITE_VERSION}-${BUILD_HASH}.${VALIDATOR_VER}"
set PY_VERSION "3.`python3 --version | head -n 1 | cut -d '.' -f 2`"
set BP_HOME '$HOME/benchpro'
set BP_APPS '$SCRATCH/benchpro/apps'
set BP_RESULTS '$SCRATCH/benchpro/results'

# DB access
set DB_USER "benchpro"
set DB_HOST "benchpro.tacc.utexas.edu"
set REMOTE_PATH "/home/benchpro/benchdb/data_store"

# SYSTEM SPECIFIC
if [[ $BP_SYSTEM = "frontera" ]]; then
    set TACC_SCRATCH "/scratch1"
    SITE="${TACC_SCRATCH}/hpc_tools/benchpro"

elif [[ $BP_SYSTEM = "ls6" ]]; then
    set TACC_SCRATCH "/scratch"
    SITE="${TACC_SCRATCH}/projects/benchpro"

elif [[ $BP_SYSTEM = "stampede2" ]]; then
    set TACC_SCRATCH "/scratch"
    SITE="${TACC_SCRATCH}/hpc_tools/benchpro"
    set BP_REPO "${BP_SITE}/repo"
fi

#BP_DEV=0

# PRODUCTION INSTALL
if [[ $BP_DEV == 0 ]]; then
    printf "\n\033[0;31m!!!YOU ARE ABOUT TO REDEPLOY THE PRODUCTION SITE PACKAGE!!!\033[0m \n\n"
    sleep 5
# DEV INSTALL
else
    SITE="${SCRATCH}/benchpro-dev"
    printf "\n\033[0;32mDEPLOYING SITE PACKAGE IN DEV MODE [BP_DEV=1]\033[0m\n\n"
    sleep 2
fi

set BP_SITE "${SITE}"
set BP_REPO "${BP_SITE}/repo"
set BP_SITE_COLLECT "${BP_SITE}/collection"

today=`date +%Y-%m-%d_%H-%M-%S`
set BP_LOG "${BP_SITE}/logs/build_${today}.log"

return 0

