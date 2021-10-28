#!/bin/bash

ml python3

set() {
    echo "$1=$2"
    export $1=$2
}

# SETUP
set BT_SYSTEM $TACC_SYSTEM
set BT_VERSION "1.2.6"
set PY_VERSION "3.`python3 --version | cut -d '.' -f 2`"
set BT_HOME '$HOME/benchtool'
set BT_APPS '$SCRATCH/benchtool/apps'
set BT_RESULTS '$SCRATCH/benchtool/results'

# DB access
set DB_USER "bench_user"
set DB_HOST "tacc-stats03.tacc.utexas.edu"
set REMOTE_PATH "/home/mcawood/benchdb/data_store"

# SYSTEM SPECIFIC
if [ $BT_SYSTEM = "frontera" ]; then
    set TACC_SCRATCH "/scratch1"
    set BT_SITE "${TACC_SCRATCH}/hpc_tools/benchtool"
    set BT_REPO "${BT_SITE}/repo"

elif [ $BT_SYSTEM = "ls6" ]; then
    set TACC_SCRATCH "/scratch"
    set BT_SITE "${TACC_SCRATCH}/06280/mcawood/benchtool"
    set BT_REPO "${BT_SITE}/repo"

elif [ $BT_SYSTEM = "stampede2" ]; then
    set TACC_SCRATCH "/scratch"
    set BT_SITE "${TACC_SCRATCH}/hpc_tools/benchtool"
    set BT_REPO "${BT_REPO}/repo"
fi
echo 
return 0

