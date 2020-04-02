#!/bin/bash

# SETUP
DATE=`date +"%Y-%m-%d_%H-%M"`

HOST="$(hostname -s).${TACC_SYSTEM:-unknown_sys}"
EXE_PATH="./tools"
CHECK_EXE="lshw"
OUT_DIR="hw_report-${HOST}-${DATE}"
mkdir -p $OUT_DIR
LOG="$OUT_DIR/hw_info.log"

echo "Collecting HW info:" > $LOG
echo "Host: $HOST" >> $LOG
echo "Date: $DATE" >> $LOG

# CHECK FILE EXISTS AND OWNED BY ROOT
if [[ ! -f $EXE_PATH/$CHECK_EXE ]]
then
  echo "$EXE_PATH/$CHECK_EXE executable not found, somethings not right..." >> $LOG
  exit 1
elif [[ ! $(stat -c '%U' $EXE_PATH/$CHECK_EXE) -eq "root" ]]
then
  echo "Insufficient privileges, run change_permissions.sh as root. Quitting for now..." >> $LOG
  exit 1
else 
  echo "Checks passed, proceeding." >> $LOG
fi

# ARR OF TASK LABELS
declare -a label=("cpuid.all.raw"
                "cpuid.core0"
                "lshw"
                "TACC_HWP_set"
                "lspci"
                "rdmsr_all"
                "rpm"
                "lscpu"
                )

# ARR OF CORRESPONDING CMDs 
declare -a cmd=("$EXE_PATH/cpuid -r"
                "taskset -c 0 $EXE_PATH/cpuid -1"
                "$EXE_PATH/lshw"
                "$EXE_PATH/TACC_HWP_set -v -s"
                "$EXE_PATH/lspci -xxx"
                "$EXE_PATH/rdmsr_all"
                "rpm -qa"
                "lscpu"
                )

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
