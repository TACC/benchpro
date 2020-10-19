#!/bin/bash
if [ `whoami` != "root" ]
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

path=$(dirname $0)

for i in "${exe[@]}"
do
  chown root.root $path/$i
  chmod 4755 $path/$i
done

echo "Done."
exit 0 
