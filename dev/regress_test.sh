#!/bin/bash

APP_LIST="lammps code=namd,build_label=x86 wrf openfoam milc gromacs code=amber,build_label=x86 code=swift,build_label=dmo qe"
APP="lammps"
BENCH_LIST="ljmelt namd_apoa1 new_conus12km SimpleBenchMarkLarge milc_18 gromacs_PEP STMV_NVE EAGLE_DMO_12 AUSURF112"
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
            "build $APP_LIST --overload dry_run=True"
            "listApps"
            "queryApp $APP"
            "bench $BENCH_LIST --overload dry_run=True"
            "last"
            "delApp $APP_LIST "
            "capture"
            "listResults all"
            "dbResult dataset=$BENCH --export"
            "dbApp code=$APP"
            "history"
            "clean"
            ) 

for c in "${cases[@]}"; do
    benchpro --$c > /dev/null 
    result $? $c
done

#benchpro --build all_apps --overload dry_run=True > /dev/null
#echo     "--suite         $?"

echo "Done"
