#!/bin/bash

[[ $# -lt 2 ]] && echo "arg1 = match, arg2 = replace" && exit 1

old="$(<<< "$1" sed -e 's`[][\\/.*^$]`\\&`g')"
new="$(<<< "$2" sed -e 's`[][\\/.*^$]`\\&`g')"

file_list=("INSTALL" "README.md" "site.sh" "src/"* "src/library/"* "benchpro/defaults.ini" "doc/source/"*)

[ ! -z "$3" ] && file_list=("$3"*)


echo "file_list $3"

dry=false
[ ! -z "$4" ] && [[ "$4" == "-d" ]] && dry=true

printf "\n"
printf "Find:    $1\n"
printf "Replace: $2\n"
printf "In:\n"
for file in "${file_list[@]}"; do
    printf "    $file\n"
done

printf "\nContinue (y/n):"

read -n 1 k <&1

if [[ $k != "y" ]] ; then
    printf "\nQuitting\n"
    exit 1
fi

printf "\n\n"

tally_before=0
tally_after=0

old_matches=0
new_matches=0

function matches() {
    old_matches=`grep -r "${old}" $1 | wc -l`
    new_matches=`grep -r "${new}" $1 | wc -l`
}

for file in "${file_list[@]}"; do

    if [[ ! -f "$file" ]]; then
        continue
    fi

    # Check theres something to replace
    matches ${file}
    
    if [[ $old_matches != 0 ]]; then
        printf "$file: \n"
        printf "          Old | New\n"
        printf "  Before  $old_matches | $new_matches = $((old_matches + new_matches))\n"
        if ($dry); then
            echo "cmd: sed -i \"s/${old}/${new}/g\" ${file}"
        else
            sed -i "s/${old}/${new}/g" ${file}
        fi
        matches ${file}
        printf "  After   $old_matches | $new_matches = $((old_matches + new_matches))\n"
        printf "\n"
    else
        grep -r "${old}" ${file} 
    fi
done
printf "Done.\n"
