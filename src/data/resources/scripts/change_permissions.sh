#!/bin/bash
if [ `whoami` != "root" ]
then
    echo "Run as root."
    exit 1
fi

if [ -z "$BENCHTOOL" ]
then
    echo "\$BENCHTOOL not set, load benchtool module."
    exit 1
fi

declare -a exe=("ibnetdiscover"
		"lshw"
		"lspci"
		"rdmsr_all"
		"TACC_HWP_set"
				)

path=$BENCHTOOL/resources/hw_utils

for i in "${exe[@]}"
do
  if [ -f "${path}/$i" ]
  then
    chown root.root ${path}/$i
    chmod 4755 ${path}/$i
  fi
done

echo "Done."
exit 0 
