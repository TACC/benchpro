#!/bin/bash

APP_LIST="lammps code=namd,build_label=x86 wrf openfoam milc gromacs code=amber,version=22,build_label=x86 code=swift,build_label=dmo qe"
APP="lammps"
BENCH_LIST="ljmelt namd_apoa1 new_conus12km SimpleBenchMarkLarge milc_18 gromacs_PEP STMV_NVE EAGLE_DMO_12 AUSURF112"
BENCH="ljmelt"

OUT="regress.out"


benchset slurm_account=A-ccsc
benchset dry_run=True

result(){
    op=`echo $2 | cut -d " " -f1`
    printf "%-20s" "$op"
    if [ $1 -ne 0 ]; then
        printf ": FAILED ($1)"
        printf "\n"
        exit 1
    else
        printf ": PASSED"
        printf "\n"
    fi
}

# Remove existing installation
benchpro --delApp $APP		> $OUT

declare cases=( "help"
            "version" 
            "validate"
            "avail"
            "build $APP"
            "listApps"
            "queryApp $APP"
            "bench $BENCH"
            "last"
            "delApp $APP "
            "capture"
            "listResults all"
            "dbResult dataset=$BENCH --export"
            "dbApp code=$APP"
            "history"
            "clean"
            ) 

for c in "${cases[@]}"; do
    benchpro --$c >> $OUT 
    result $? $c
done

#benchpro --build all_apps --overload dry_run=True > /dev/null
#echo     "--suite         $?"

echo "Done"
