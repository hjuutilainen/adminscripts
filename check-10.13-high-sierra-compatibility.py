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
# Modified for High Sierra by Tom Cinbis
# https://github.com/tcinbis/adminscripts
#
# Original script by Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Checker created by Laurent Pertois @Jamf
# https://github.com/laurentpertois/High-Sierra-Compatibility-Checker
#
# ================================================================================

import sys
import subprocess
import os
import re
import plistlib
from distutils.version import StrictVersion
from Foundation import CFPreferencesCopyAppValue


# ================================================================================
# Start configuration
# ================================================================================

# Set this to False if you don't want any output, just the exit codes
verbose = True

# Set this to True if you want to add "high_sierra_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = False

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
        return os.path.join(managed_installs_dir, 'ConditionalItems.plist')
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
    cmd = ["/bin/sh", "High_Sierra_Compatibility_Checker.sh"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for result in results.split():
        if result == "True":
            print("System is compatible")
            return True
    return False


def append_conditional_items(dictionary):
    current_conditional_items_path = conditional_items_path()
    if os.path.exists(current_conditional_items_path):
        existing_dict = plistlib.readPlist(current_conditional_items_path)
        output_dict = dict(existing_dict.items() + dictionary.items())
    else:
        output_dict = dictionary
    plistlib.writePlist(output_dict, current_conditional_items_path)
    pass


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
