#!/bin/bash

APP="lammps"
BENCH="ljmelt"

result(){
    op=`echo $2 | cut -d " " -f1`
    printf "%-20s" "$op"
    if [ $1 -ne 0 ]; then
        printf ": FAILED"
        printf "\n"
        exit 1
    else
        printf ": PASSED"
        printf "\n"
    fi
}

# Remove existing installation
benchpro --delApp $APP		> /dev/null

declare cases=( "help"
            "version" 
            "validate"
            "avail"
            "build $APP --overload dry_run=True build_label=test"
            "listApps"
            "queryApp $APP"
            "bench $BENCH --overload dry_run=True build_label=test"
            "last"
            "delApp $APP/test "
            "capture"
            "listResults all"
            "dbResult dataset=$BENCH --export"
            "dbApp code=$APP"
            "history"
            "clean"
            ) 

for c in "${cases[@]}"; do
    benchpro --$c > /dev/null 2>&1
    result $? $c
done

#benchpro --build all_apps --overload dry_run=True > /dev/null
#echo     "--suite         $?"

echo "Done"
