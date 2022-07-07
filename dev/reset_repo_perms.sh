#!/usr/bin/env bash

if [[ "$USER" != "root" ]]; then
    echo "Run as root."
    exit 1
fi

if [[ -z $BP_REPO ]]; then
    echo "\$BP_REPO not set."
    exit 1
fi

chmod 644 $BP_REPO/*

