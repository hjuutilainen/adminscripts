#!/bin/bash

# ==================================================
# reposado-removeDeprecatedProducts.sh
#
# Script to remove deprecated products from a branch
# ==================================================

REPOUTIL="/var/git/reposado/code/repoutil"

function usage () {
	echo "Usage: $0 <branch-name>"
	exit
}

# We need a branch.
if [ -z $1 ]; then
	echo "Missing branch"
	usage
	exit 1
fi

# Print the products to be removed
echo "Getting a list of deprecated products..."
IFS="
"
deprecatedProductsFull=(`$REPOUTIL --list-branch=${1} | grep Deprecated`)
if [[ ${#deprecatedProductsFull[@]} -eq 0 ]]; then
	echo "No deprecated products"
	exit 0
fi
for (( i=0; i<${#deprecatedProductsFull[@]}; i++ )); do
	echo ${deprecatedProductsFull[$i]}
done
unset IFS
echo ""

# Ask for confirmation
while true; do
    read -p "Remove products from catalog $1? [y]n: " yn
    case $yn in
        [Yy]* ) 
	    deprecatedProductIDs=( `$REPOUTIL --list-branch=${1} | grep Deprecated | awk '{print $1}'`)
	    echo "$REPOUTIL --remove-product ${deprecatedProductIDs[@]} $1"
	    $REPOUTIL --remove-product ${deprecatedProductIDs[@]} $1
	    break;;
        [Nn]* )
	    exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
