#!/bin/bash

# ================================================================================
# export-macos-man-pages.sh
#
# This script exports all available man pages to a folder in ~/Desktop
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# ================================================================================

set -o pipefail

# Get OS version and build
PRODUCT_VERSION=$(defaults read /System/Library/CoreServices/SystemVersion.plist ProductVersion)
PRODUCT_BUILD_VERSION=$(defaults read /System/Library/CoreServices/SystemVersion.plist ProductBuildVersion)
NOW=$(date +"%Y%m%d%H%M%S")

# This directory will contain all of the created files
WORK_DIR=$(mktemp -d "${HOME}/Desktop/man-${PRODUCT_VERSION}-${PRODUCT_BUILD_VERSION}-${NOW}.XXXXXX")
echo "Working in ${WORK_DIR}"

for SECTION_NUMBER in {1..8}; do
    OUTPUT_DIR="${WORK_DIR}/${SECTION_NUMBER}"
    mkdir -p "${OUTPUT_DIR}"
    for j in $(man -aWS ${SECTION_NUMBER} \* | xargs basename | sed 's/\.[^.]*$//' | sort -u); do
        COMMAND_NAME=$(basename $j)
        echo "Getting section ${SECTION_NUMBER} manual page for ${COMMAND_NAME}"
        man "${COMMAND_NAME}" 2> /dev/null | col -bx > "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
        sed -e '1d' -e '$d' -i '' "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
        sed -e :a -e '/./,$!d;/^\n*$/{$d;N;};/\n$/ba' -i '' "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
    done
done


OUTPUT_DIR="${WORK_DIR}/compgen"
mkdir -p "${OUTPUT_DIR}"
for COMMAND_NAME in $(compgen -c); do
    man "${COMMAND_NAME}" 2> /dev/null | col -bx > "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
    sed -e '1d' -e '$d' -i '' "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
    sed -e :a -e '/./,$!d;/^\n*$/{$d;N;};/\n$/ba' -i '' "${OUTPUT_DIR}/${COMMAND_NAME}.txt"
done


open "${WORK_DIR}"

