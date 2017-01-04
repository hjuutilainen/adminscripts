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
# 2012-04-10, Hannes Juutilainen
# - Added support for checking multiple browsers
# - Changes in output formatting 
# 2012-04-03, Hannes Juutilainen
# - First version
# ================================================================================

# ================================================================================
# Apps that need to be checked for the LSEnvironment key
# If you need to check additional paths, add them here
# ================================================================================
APPLICATIONS_TO_CHECK=(
"/Applications/Safari.app"
"/Applications/Firefox.app"
"/Applications/Google Chrome.app"
"/Applications/Opera.app"
)

SCAN_RESULTS=0

# ================================================================================
# Check for root
# ================================================================================
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 2>&1
    exit 1
fi


# ================================================================================
echo "Checking for LSEnvironment key in application bundles"
# ================================================================================
for APPLICATION in "${APPLICATIONS_TO_CHECK[@]}"
do
	if [[ -e "$APPLICATION/Contents/Info.plist" ]]; then
		defaults read "$APPLICATION/Contents/Info" LSEnvironment > /dev/null 2>&1
		if [[ $? -eq 0 ]]; then
			printf "%b\n" "===> WARNING: Found LSEnvironment in $APPLICATION/Contents/Info.plist"
			SCAN_RESULTS=1
		else
			printf "%b\n" "---> Key not found: $APPLICATION/Contents/Info.plist"
		fi
	#else
		#printf "%b\n" "---> File doesn't exist: $APPLICATION/Contents/Info.plist"
	fi
done


# ================================================================================
printf "\n%b\n" "Checking for /Users/Shared/.libgmalloc.dylib"
# ================================================================================
if [[ -e /Users/Shared/.libgmalloc.dylib ]]; then
	printf "%b\n" "===> WARNING: Found /Users/Shared/.libgmalloc.dylib"
	SCAN_RESULTS=1
else
	printf "%b\n" "---> File doesn't exist"
fi


# ================================================================================
printf "\n%b\n" "Checking for DYLD_INSERT_LIBRARIES key in /Users/*/.MacOSX/environment.plist"
# ================================================================================
shopt -s nullglob
USER_HOMES=/Users/*
for f in $USER_HOMES
do
	if [[ -f $f/.MacOSX/environment.plist ]]; then
		defaults read $f/.MacOSX/environment DYLD_INSERT_LIBRARIES > /dev/null 2>&1
		if [[ $? -eq 0 ]]; then
			printf "%b\n" "===> WARNING: Found DYLD_INSERT_LIBRARIES key in $f/.MacOSX/environment"
			SCAN_RESULTS=1
		fi
	else
		printf "%b\n" "---> File doesn't exist in $f/.MacOSX/environment.plist"
	fi
done
shopt -u nullglob
printf "%b\n" "---> Done"


# ================================================================================
printf "\n%b" "Results: "
# ================================================================================
if [[ $SCAN_RESULTS -ne 0 ]]; then
    printf "%b\n\n" "WARNING: System tested positive on at least one of the tests."
else
	printf "%b\n\n" "System is clean."
fi

exit 0
