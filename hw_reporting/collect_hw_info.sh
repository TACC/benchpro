#!/bin/bash

# SETUP
DATE=`date +"%Y-%m-%d_%H-%M"`

HOST="$(hostname -s).${TACC_SYSTEM:-unknown_sys}"
PREFIX="./tools"
CHECK_EXE="lshw"
OUT_DIR="hw_report-${HOST}-${DATE}"
mkdir -p $OUT_DIR
LOG="$OUT_DIR/hw_info.log"

echo "Collecting HW info:" > $LOG
echo "Host: $HOST" >> $LOG
echo "Date: $DATE" >> $LOG

# CHECK FILE EXISTS AND OWNED BY ROOT
if [[ ! -f $PREFIX/$CHECK_EXE ]]
then
  echo "$PREFIX/$CHECK_EXE executable not found, somethings not right..." >> $LOG
  exit 1
elif [[ ! $(stat -c '%U' $PREFIX/$CHECK_EXE) -eq "root" ]]
then
  echo "Insufficient privileges, run change_permissions.sh as root. Quitting for now..." >> $LOG
  exit 1
else 
  echo "Checks passed, proceeding." >> $LOG
fi

# RUN LIST OF TASKS
function run_cmd() {

  local -n label=$1
  local -n cmd=$2

  # RUN LIST OF TASKS
  len=${#label[@]}
  for (( i=0; i<$len; i++ ))
  do
    LABEL=${label[$i]}
    CMD=${cmd[$i]}
    echo "Collecting $LABEL info..." >> $LOG
    $CMD > $OUT_DIR/$HOST-$DATE.$LABEL.txt
    echo "Done." >> $LOG
  done

}


# GENERIC ACCROSS ALL SYSTEMS
declare -a label=("cpuid.all.raw"
                "cpuid.core0"
                "lshw"
                "TACC_HWP_set"
                "lspci"
                "rdmsr_all"
                "rpm"
                "lscpu"
                )

declare -a cmd=("$PREFIX/cpuid -r"
                "taskset -c 0 $PREFIX/cpuid -1"
                "$PREFIX/lshw"
                "$PREFIX/TACC_HWP_set -v -s"
                "$PREFIX/lspci -xxx"
                "$PREFIX/rdmsr_all"
                "rpm -qa"
                "lscpu"
                )

  len=${#label[@]}
  for (( i=0; i<$len; i++ ))

run_cmd label cmd


# SYSTEM SPECIFIC 

if [[ $TACC_SYSTEM -eq "frontera" ]]
then

  declare -a label=("ibnetdiscover"
                )

  declare -a cmd=("$PREFIX/ibnetdiscover -p"
                )

  run_cmd

fi

