#!/bin/bash

if [ -z $1 ]; then
    echo "Provide version label"
    exit 1
fi

echo "benchtool v$1" > ../.version
date >> ../.version

echo "Version file updated."
