#!/bin/bash

PREFIX="`pwd`/hw_utils"

if [ $USER != "root" ]
then
	echo "Run as root."
	exit 1
fi

declare -a exe=("cpuid"
				"ibnetdiscover"
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

echo "Done."
exit 0 
