#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath $BASH_SOURCE)")
ml use "$SCRIPT_PATH/build/modulefiles"
ml builder
