#!/bin/bash

# Set dry_run=True
sed -i "/dry_run                 =/c\dry_run                 = False" ${BP_HOME}/settings.ini

# Disable debug output
sed -i "/debug                   =/c\debug                   = True" ${BP_HOME}/settings.ini

# Set Timeout
sed -i "/timeout                 =/c\timeout                 = 1" ${BP_HOME}/settings.ini

# Set clean_on_fail
sed -i "/clean_on_fail           =/c\clean_on_fail           = False" ${BP_HOME}/settings.ini
