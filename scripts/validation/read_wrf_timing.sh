#!/bin/bash
tally=0.0
while read line; do
  if [[ $line == "Timing for main:"* ]]; then
    result=$(echo $line | cut -d ':' -f 5 | cut -d ' ' -f 2)
    tally=$(echo $tally + $result | bc)
  fi
done < $1
echo $tally
