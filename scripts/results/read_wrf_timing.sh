#!/bin/bash
tally=0.0
first=0
while read line; do
  if [[ $line == "Timing for main:"* ]]; then
  	# skip first line
  	if [[ $first -eq 0 ]]; then
		first=1
		continue 
	fi

    result=$(echo $line | cut -d ':' -f 5 | cut -d ' ' -f 2)
    tally=$(echo $tally + $result | bc)
  fi
done < $1
echo $tally
