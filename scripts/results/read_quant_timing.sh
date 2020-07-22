#!/bin/bash

result_str=$(grep 'PWSCF        :' $1 | cut -d ' ' -f 21)
mins=$(echo $result_str | cut -d 'm' -f 1)
secs=$(echo $result_str | cut -d 'm' -f 2 | cut -d 's' -f 1)

result=$(echo $(echo $mins \* 60 | bc) + $secs | bc)

echo $result
