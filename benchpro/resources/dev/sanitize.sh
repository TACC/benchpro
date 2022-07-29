#!/bin/bash

# Set dry_run=True
sed -i "/dry_run                 =/c\dry_run                 = True" ${BP_HOME}/settings.ini

# Disable debug output
sed -i "/debug                   =/c\debug                   = False" ${BP_HOME}/settings.ini

# Set Timeout
sed -i "/timeout                 =/c\timeout                 = 5" ${BP_HOME}/settings.ini

# Set clean_on_fail
sed -i "/clean_on_fail           =/c\clean_on_fail           = True" ${BP_HOME}/settings.ini
