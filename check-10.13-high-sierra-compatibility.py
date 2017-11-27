#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-1013-sierra-compatibility.py
#
# This script checks if the current system is compatible with macOS 10.13 High
# Sierra.
# These checks are based on the information provided by Apple.
#
# The checks done by this script are (in order):
# - Machine is a virtual machine or has a specific supported board-id
# - Machine model is not in a list of unsupported models
# - Current system version is less than 10.12 and at least 10.7.5
#
# Exit codes:
# 0 = High Sierra is supported
# 1 = High Sierra is not supported
#
#
# Ported to Python for High Sierra by Tom Cinbis
# https://github.com/tcinbis/adminscripts
#
# Original script by Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Checker shell script created by Laurent Pertois
# https://github.com/laurentpertois/High-Sierra-Compatibility-Checker
#
# ================================================================================

import os
import platform
import plistlib
import re
import subprocess
import sys

# ================================================================================
# Start configuration
# ================================================================================

# Set this to False if you don't want any output, just the exit codes

verbose = True

# Set this to True if you want to add "high_sierra_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = True


# ================================================================================
# End configuration
# ================================================================================

def conditional_items_path():
    # <https://github.com/munki/munki/wiki/Conditional-Items>
    # Read the location of the ManagedInstallDir from ManagedInstall.plist

    cmd = [
        "/usr/bin/defaults",
        "read",
        "/Library/Preferences/ManagedInstalls",
        "ManagedInstallDir"
    ]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    managed_installs_dir = results.strip()

    # Make sure we're outputting our information to "ConditionalItems.plist"
    if managed_installs_dir:
        conItemsPath = os.path.join(managed_installs_dir.decode('ascii'), 'ConditionalItems.plist')
        return conItemsPath
    else:
        # Munki default
        return "/Library/Managed Installs/ConditionalItems.plist"


def munki_installed():
    cmd = ["pkgutil", "--pkg-info", "com.googlecode.munki.core"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode == 0:
        return True
    else:
        return False


def run_script():
    version = platform.mac_ver()[0]
    majorVersion = int(str(version).split('.')[1])
    minorVersion = int(str(version).split('.')[2])

    supported = False

    if (majorVersion >= 8 and minorVersion < 13) or (majorVersion == 7 and minorVersion == 5):
        ramCmd = ['/usr/sbin/sysctl', '-n', 'hw.memsize']
        ram = int(subprocess.run(ramCmd, stdout=subprocess.PIPE).stdout.decode('ascii')) / 1024 / 1024 / 1024

        minimumRam = 2
        minimumSpace = 9

        freeSpaceCmd = [
            '/usr/sbin/diskutil info / | awk -F\'[()]\' \'/Free Space|Available Space/ {print $2}\'| sed -e \'s/\ Bytes//\'']
        freeSpace = int(int(subprocess.run(freeSpaceCmd, stdout=subprocess.PIPE, shell=True).stdout.decode(
            'ascii')) / 1024 / 1024 / 1024)

        modelIdentifierCmd = ['/usr/sbin/sysctl -n hw.model']
        modelIdentifier = str(
            subprocess.run(modelIdentifierCmd, stdout=subprocess.PIPE, shell=True).stdout.decode('ascii')).replace('\n',
                                                                                                                   '')
        modelnameCmd = 'echo \"' + modelIdentifier + '\" | sed s/[^0-9,]//g | awk -F, \'{print $1}\''
        modelname = re.sub(r'[0-9,]', '', modelIdentifier)
        modelVersion = int(re.sub(r',.*', '', re.sub(r'[^0-9,]', '', modelIdentifier)))

        if modelname == "iMac" and modelVersion >= 10 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True
        elif modelname == "Macmini" and modelVersion >= 4 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True
        elif modelname == "MacPro" and modelVersion >= 5 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True
        elif modelname == "MacBook" and modelVersion >= 6 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True
        elif modelname == "MacBookAir" and modelVersion >= 3 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True
        elif modelname == "MacBookPro" and modelVersion >= 7 and ram >= minimumRam and freeSpace >= minimumSpace:
            supported = True

    return supported


def append_conditional_items(dictionary):
    current_conditional_items_path = conditional_items_path()
    if os.path.exists(current_conditional_items_path):
        existing_dict = plistlib.readPlist(current_conditional_items_path)
        output_dict = dict(existing_dict.items() + dictionary.items())
    else:
        output_dict = dictionary
    plistlib.writePlist(output_dict, current_conditional_items_path)


def main(argv=None):
    high_sierra_supported_dict = {}

    # Run the checks
    high_sierra_supported = run_script()
    if high_sierra_supported:
        high_sierra_supported_dict = {'high_sierra_supported': True}
    else:
        high_sierra_supported_dict = {'high_sierra_supported': False}

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and update_munki_conditional_items:
        append_conditional_items(high_sierra_supported_dict)

    # Exit codes:
    # 0 = High Sierra is supported
    # 1 = High Sierra is not supported
    return high_sierra_supported


if __name__ == '__main__':
    sys.exit(main())
