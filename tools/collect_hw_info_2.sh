#!/bin/bash

EXE_PATH="./"
LOG="hw_info.log"
DATE=`date +"%Y-%m-%d_%H-%M"`
HOST=`hostname -s`

declare -a label=("cpuid.all.raw"
		"cpuid.core0"
		"lshw"
                "TACC_HWP_set"
                "lspci"
                "rdmsr_all"
		"rpm"
		"lscpu"
                )

declare -a cmd=("${EXE_PATH}cpuid -r"
		"taskset -c 0 ${EXE_PATH}cpuid -1"
		"${EXE_PATH}lshw"
                "${EXE_PATH}TACC_HWP_set -v -s"
                "${EXE_PATH}lspci -xxx"
                "${EXE_PATH}rdmsr_all"
		"rpm -qa"
		"lscpu"
                )

echo "Starting data capture..." > $LOG

len=${#label[@]}
for (( i=0; i<$len; i++ ))
do 
    if [[ -f $EXE ]]
    then
        if [[ stat -c '%U' ${label[$i]} -eq "root" ]]
        then
            echo "Collecting ${label[$i]} info..." >> $LOG
            ${cmd[$i]} > $HOST-$DATE.${label[$i]}.txt
            echo "Done." >> $LOG
        else
            echo "Insufficient privileges, run change_ownership.sh as root. Skipping for now..." >> $LOG
        fi
    else
        echo "$EXE executable not found, skipping..." >> $LOG
    fi
done

