#!/usr/bin/env bash

set() {
    echo "$1=$2"
    export $1="$2"
}

# SETUP
set BPS_SYSTEM      $TACC_SYSTEM
set BPS_VERSION "1.8.10"
[[ -z $BP_DEV ]] && set BP_DEV 1
set BUILD_HASH `echo $RANDOM | md5sum | head -c 8`

set BUILD_DATE      "$(date +'%Y-%m-%d %H:%m:%S')"
set BPS_VERSION_STR "${BPS_VERSION}-${BUILD_HASH}"
set PY_VERSION      "3.`python3 --version | head -n 1 | cut -d '.' -f 2`"
set PY_LIB          $TACC_PYTHON_LIB
set PY_MODULE       "python3"

# USER VARIABLES [dynamic]
set BP_HOME         '$HOME/benchpro'
set BP_REPO         '$SCRATCH/benchpro/repo'
set BP_APPS         '$SCRATCH/benchpro/apps'
set BP_RESULTS      '$SCRATCH/benchpro/results'

# DB access
set DB_USER         "benchpro"
set DB_HOST         "benchpro.tacc.utexas.edu"
set REMOTE_PATH     "/home/benchpro/benchdb/data_store"

SSH_KEY=$HOME/.ssh/id_rsa

# SYSTEM SPECIFIC
if [[ $BPS_SYSTEM = "frontera" ]]; then
    set TACC_SCRATCH    "/scratch1"
    SITE="${TACC_SCRATCH}/hpc_tools/benchpro"
    ml python3

elif [[ $BPS_SYSTEM = "vista" ]]; then
    set TACC_SCRATCH    "/scratch"
    SITE="${TACC_SCRATCH}/projects/benchpro"
    SSH_KEY=$HOME/.ssh/id_ed25519

elif [[ $BPS_SYSTEM = "ls6" ]]; then
    set TACC_SCRATCH    "/scratch"
    SITE="${TACC_SCRATCH}/projects/benchpro"

elif [[ $BPS_SYSTEM = "stampede3" ]]; then
    set TACC_SCRATCH    "/scratch"
    SITE="${TACC_SCRATCH}/projects/benchpro"
    set PY_MODULE       "python"
#    set PY_ENV "1"
fi

#BP_DEV=0

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

# SITE VARIABLES [static]
set BPS_HOME        "${SITE}"
set BPS_COLLECT     "${BPS_HOME}/collection"
set BPS_INC         "${BPS_HOME}/package/benchpro"
set BPS_MODULES     "${BPS_HOME}/modulefiles"
set BPS_BIN         "${BPS_HOME}/python/bin"

today=`date +%Y-%m-%d_%H-%M-%S`
set BPS_LOG         "${BPS_HOME}/logs/build_${today}.log"

return 0

