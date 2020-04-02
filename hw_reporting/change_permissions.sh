#!/bin/bash

PREFIX="./tools"

if [ $USER != "root" ]
then
	echo "Run as root."
	exit 1
fi

declare -a exe=("ibnetdiscover"
		"lshw"
                "lspci"
                "rdmsr_all"
                "TACC_HWP_set"
		)

for i in "${exe[@]}"
do
  chown root.root $PREFIX/$i
  chmod 4755 $PREFIX/$i
done
 
