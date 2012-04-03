#!/bin/sh

# ================================================================================
# check-for-osx-flashback.K.sh
#
# Script to check system for any signs of OSX/Flashback.K trojan
# Checks are based on information from F-Secure's website:
# http://www.f-secure.com/v-descs/trojan-downloader_osx_flashback_k.shtml
#
# Hannes Juutilainen, hjuutilainen@mac.com
#
# History:
# - 2012-04-03, Hannes Juutilainen, first version
# ================================================================================

# Check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 2>&1
    exit 1
fi

# ================================================================================
echo "Checking /Applications/Safari.app/Contents/Info.plist for LSEnvironment key"
# ================================================================================
defaults read /Applications/Safari.app/Contents/Info LSEnvironment > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
	printf "%b\n\n" "===> WARNING: Found LSEnvironment in Safari Info.plist"
else
	printf "%b\n\n" "---> Not found"
fi


# ================================================================================
echo "Checking if /Users/Shared/.libgmalloc.dylib exists"
# ================================================================================
if [[ -f /Users/Shared/.libgmalloc.dylib ]]; then
	printf "%b\n\n" "===> WARNING: Found /Users/Shared/.libgmalloc.dylib"
else
	printf "%b\n\n" "---> Not found"
fi


# ================================================================================
echo "Checking /Users/*/.MacOSX/environment"
# ================================================================================
shopt -s nullglob
USER_HOMES=/Users/*
for f in $USER_HOMES
do
	echo "---> Checking $f/.MacOSX/environment.plist"
	if [[ -f $f/.MacOSX/environment.plist ]]; then
		defaults read $f/.MacOSX/environment DYLD_INSERT_LIBRARIES > /dev/null 2>&1
		if [[ $? -eq 0 ]]; then
			printf "%b\n" "===> WARNING: Found DYLD_INSERT_LIBRARIES key in $f/.MacOSX/environment"
		fi
	fi
done
shopt -u nullglob
printf "%b\n\n" "---> Done"

exit 0
