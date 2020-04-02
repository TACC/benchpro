#!/bin/bash

# Setup
LOG="hw_info.log"
DATE=`date +"%Y-%m-%d_%H-%M"`
HOST=`hostname -s`
echo "Collecting HW info:" > $LOG
echo "Host: `hostname`" >> $LOG
echo "Date: `date`" >> $LOG

# CPUID
EXE="cpuid"
if [[ -f $EXE ]]
then
  echo "Collecting cpuid info..." >> $LOG
  ./$EXE -r > $HOST-$DATE.$EXE.all.raw
  taskset -c 0 ./$EXE -1 > $HOST-$DATE.$EXE.core0.txt
  echo "Done." >> $LOG
else
  echo "$EXE executable not found, skipping..." >> $LOG
fi

# LSHW
EXE="lshw"
if [[ -f $EXE ]]
then
  if [[ stat -c '%U' $EXE -eq "root" ]]
  then 
    echo "Collecting $EXE info..." >> $LOG
    ./$EXE > $HOST-$DATE.$EXE
    echo "Done." >> $LOG
  else
    echo "Insufficient privileges, run change_ownership.sh as root. Skipping for now..." >> $LOG
  fi
else
  echo "$EXE executable not found, skipping..." >> $LOG
fi

# TACC_HWP_set
EXE="TACC_HWP_set"
if [[ -f $EXE ]]
then
  if [[ stat -c '%U' $EXE -eq "root" ]]
  then
    echo "Collecting $EXE info..." >> $LOG
    ./$EXE -v -s > $HOST-$DATE.$EXE.txt
    echo "Done." >> $LOG
  else
    echo "Insufficient privileges, run change_ownership.sh as root. Skipping for now..." >> $LOG
  fi
else
  echo "$EXE executable not found, skipping..." >> $LOG
fi


# LSPCI
EXE="lspci"
if [[ -f $EXE ]]
then
  if [[ stat -c '%U' $EXE -eq "root" ]]
  then
    echo "Collecting $EXE info..." >> $LOG
    ./$EXE -xxx > $HOST-$DATE.$EXE.txt
    echo "Done." >> $LOG
  else
    echo "Insufficient privileges, run change_ownership.sh as root. Skipping for now..." >> $LOG
  fi
else
  echo "$EXE executable not found, skipping..." >> $LOG
fi


# MSRs
EXE="rdmsr_all"
if [[ -f "cpuid" ]]
then

fi

# LSCPU
if [[ -f "cpuid" ]]
then

fi



