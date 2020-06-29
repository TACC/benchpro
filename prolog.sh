#!/bin/bash 
 
function warn { 
    echo Warn 
} 
 
# check-hugepages
test=$(grep 'HugePages_Total' /proc/meminfo | cut -d ':' -f 2) 
if [ $test != 0 ]; then 
    warn 
fi 
