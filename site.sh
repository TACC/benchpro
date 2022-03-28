#!/bin/bash

ml python3

set() {
    echo "$1=$2"
    export $1=$2
}

# SETUP
set BP_SYSTEM $TACC_SYSTEM
set BP_VERSION "1.3.5"
set PY_VERSION "3.`python3 --version | head -n 1 | cut -d '.' -f 2`"
set BP_HOME '$HOME/benchpro'
set BP_APPS '$SCRATCH/benchpro/apps'
set BP_RESULTS '$SCRATCH/benchpro/results'

# DB access
set DB_USER "benchpro"
set DB_HOST "benchpro.tacc.utexas.edu"
set REMOTE_PATH "/home/benchpro/benchdb/data_store"

# SYSTEM SPECIFIC
if [ $BP_SYSTEM = "frontera" ]; then
    set TACC_SCRATCH "/scratch1"
    set BP_SITE "${TACC_SCRATCH}/hpc_tools/benchpro"
    set BP_REPO "${BP_SITE}/repo"

elif [ $BP_SYSTEM = "ls6" ]; then
    set TACC_SCRATCH "/scratch"
    set BP_SITE "${TACC_SCRATCH}/projects/benchtool"
    set BP_REPO "${BP_SITE}/repo"

elif [ $BP_SYSTEM = "stampede2" ]; then
    set TACC_SCRATCH "/scratch"
    set BP_SITE "${TACC_SCRATCH}/hpc_tools/benchpro"
    set BP_REPO "${BP_SITE}/repo"
fi

# DEV BUILD OVERWRITE
if [ ! -z $BP_DEV ]; then
    set BP_SITE "${SCRATCH}/benchpro-dev"
fi

echo 
return 0

