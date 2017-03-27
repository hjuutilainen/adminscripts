#!/bin/bash

# ==================================================
# reposado-remove-deprecated-products.sh
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
DEPRECATED_PRODUCTS=( $("${REPOUTIL}" --list-branch=${1} | grep Deprecated) )
if [[ ${#DEPRECATED_PRODUCTS[@]} -eq 0 ]]; then
	echo "No deprecated products"
	exit 0
fi
for (( i=0; i<${#DEPRECATED_PRODUCTS[@]}; i++ )); do
	echo ${DEPRECATED_PRODUCTS[$i]}
done
unset IFS
echo ""

# Ask for confirmation
while true; do
    read -p "Remove products from catalog $1? [y]n: " yn
    case $yn in
        [Yy]* ) 
	    DEPRECATED_PRODUCT_IDS=( $("${REPOUTIL}" --list-branch=${1} | grep Deprecated | awk '{print $1}') )
	    echo "${REPOUTIL} --remove-product ${DEPRECATED_PRODUCT_IDS[@]} $1"
	    #"${REPOUTIL}" --remove-product ${DEPRECATED_PRODUCT_IDS[@]} $1
	    break;;
        [Nn]* )
	    exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
