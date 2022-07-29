#!/bin/bash

if [ -z "$1" ]; then
    echo "Provide ouput file as argument."
    exit 1

fi

result_str=$(grep 'PWSCF        :' $1 | rev | cut -d 'W' -f 2 | cut -d 'U' -f 1 | rev )
mins=$(echo $result_str | cut -d 'm' -f 1)
secs=$(echo $result_str | cut -d 'm' -f 2 | cut -d 's' -f 1)

result=$(echo $(echo $mins \* 60 | bc) + $secs | bc)

echo $result
