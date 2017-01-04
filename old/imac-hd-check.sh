#!/bin/sh

# ================================================================================
# imac-hd-check.sh
# Hannes Juutilainen <hjuutilainen@mac.com>
#
# This script checks if the __current__ machine is part of Apple's iMac 1TB Seagate
# Hard Drive Replacement Program <http://www.apple.com/support/imac-harddrive/>.
# The script is ready to be copy/pasted to Apple Remote Desktop or some other
# remote management system.
#
# The script is adapted from iMac_Warranty_Check.rb by Riley Shott
# https://github.com/Ginja/Admin_Scripts/blob/master/iMac_Warranty_Check.rb
#
#
# Version history:
# 2012-11-06, Hannes Juutilainen
# - First version
# ================================================================================

# ================================================================================
# Exit codes, customize if needed.
# For example, ARD outputs a green task status with 0 and red task status with 1
# ================================================================================
HARD_DRIVE_REPLACEMENT_NEEDED=1
HARD_DRIVE_REPLACEMENT_NOT_NEEDED=0
NOT_APPLICABLE_FOR_THIS_MODEL=0

# ================================================================================
# First of all, we need to be running on an iMac
# ================================================================================
MODEL=$(system_profiler SPHardwareDataType | sed -n -e 's/[ \t][ \t]*Model Name: \(.*\)/\1/g p')
if [[ $MODEL != "iMac" ]]; then
    echo "Not applicable for this model: $MODEL"
    exit $NOT_APPLICABLE_FOR_THIS_MODEL
fi

# ================================================================================
# Get the hostname and serial number
# ================================================================================
HOSTNAME=$(hostname)
SERIAL=$(system_profiler SPHardwareDataType | awk '/Serial Number/ {print $4}')

# ================================================================================
# Construct the curl command
# ================================================================================
CHECK_URL="https://supportform.apple.com/201107/SerialNumberEligibilityAction.do?cb=iMacHDCheck.response&sn=${SERIAL}"
CURL="curl --silent --max-time 30"

# ================================================================================
# Check if this machine is part of the replacement program
# ================================================================================
VALID_SN_STRING="Valid iMac SN has Seagate HDD - covered by program"
WARRANTYSTATUS=$($CURL "${CHECK_URL}" | grep "${VALID_SN_STRING}")
if [[ $? == 0 ]]; then
    echo "Host $HOSTNAME with serial number $SERIAL needs a replacement disk"
    exit $HARD_DRIVE_REPLACEMENT_NEEDED
fi

exit $HARD_DRIVE_REPLACEMENT_NOT_NEEDED
