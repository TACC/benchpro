#!/bin/bash

[[ $# -ne 2 ]] && echo "arg1 = match, arg2 = replace" && exit 1

old="$(<<< "$1" sed -e 's`[][\\/.*^$]`\\&`g')"
new="$(<<< "$2" sed -e 's`[][\\/.*^$]`\\&`g')"

printf "\n"
printf "Find:    $1\n"
printf "Replace: $2\n\n"
printf "Continue (y/n):"

read -n 1 k <&1

if [[ $k != "y" ]] ; then
    printf "\nQuitting\n"
    exit 1
fi

printf "\n\n"

#file_list=("site.sh")
#file_list=("src/global_settings.py")
file_list=("INSTALL" "README.md" "site.sh" "src/"* "src/library/"* "benchpro/defaults.ini" "doc/source/"*)
#file_list=("test.txt")



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
        sed -i "s/${old}/${new}/g" ${file}
        matches ${file}
        printf "  After   $old_matches | $new_matches = $((old_matches + new_matches))\n"
        printf "\n"
    else
        grep -r "${old}" ${file} 
    fi
done
printf "Done.\n"
