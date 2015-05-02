#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-if-virtual-machine.py
#
# This script checks if the current system is running virtualized. This is done
# by checking if machdep.cpu.features from sysctl contains VMM. OS X Mountain
# Lion installer performs this same check when determining if it can be installed.
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Version history:
# ----------------
# 2013-03-27, Hannes Juutilainen
# - First version
#
# ================================================================================

import sys
import os
import subprocess
import plistlib
from Foundation import CFPreferencesCopyAppValue

# ================================================================================
# Start configuration
# ================================================================================
# Set this to False if you don't want any output, just the exit codes
verbose = True
# Set this to True if you want to add "virtual_machine" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = True
# ================================================================================
# End configuration
# ================================================================================

def logger(message, status, info):
    if verbose:
        print "%10s: %-40s [%s]" % (message, status, info)
    pass


def conditional_items_path():
    # <http://code.google.com/p/munki/wiki/ConditionalItems>
    # Read the location of the ManagedInstallDir from ManagedInstall.plist
    BUNDLE_ID = 'ManagedInstalls'
    pref_name = 'ManagedInstallDir'
    managed_installs_dir = CFPreferencesCopyAppValue(pref_name, BUNDLE_ID)
    # Make sure we're outputting our information to "ConditionalItems.plist"
    if managed_installs_dir:
        return os.path.join(managed_installs_dir, 'ConditionalItems.plist')
    else:
        # Munki default
        return "/Library/Managed Installs/ConditionalItems.plist"


def munki_installed():
    pkgutil_process = ["pkgutil", "--pkg-info", "com.googlecode.munki.core"]
    p = subprocess.Popen(pkgutil_process, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode == 0:
        return True
    else:
        return False


def is_virtual_machine():
    sysctl_process = ["sysctl", "-n", "machdep.cpu.features"]
    p = subprocess.Popen(sysctl_process, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for feature in results.split():
        if feature == "VMM":
            return True
    return False


def append_conditional_items(conditionals_dict):
    conditionals_path = conditional_items_path()
    if os.path.exists(conditionals_path):
        existing_dict = plistlib.readPlist(conditionals_path)
        output_dict = dict(existing_dict.items() + conditionals_dict.items())
    else:
        output_dict = conditionals_dict
    plistlib.writePlist(output_dict, conditionals_path)
    pass


def main(argv=None):
    new_conditional_items = {}

    if is_virtual_machine():
        print "This system is virtual"
        machine_type = 0
        new_conditional_items = {'virtual_machine': True}
    else:
        print "This system is not virtual"
        machine_type = 1
        new_conditional_items = {'virtual_machine': False}

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and update_munki_conditional_items:
        append_conditional_items(new_conditional_items)

    # Exit codes:
    # 0 = This machine is virtual
    # 1 = This machine is not virtual
    return machine_type


if __name__ == '__main__':
    sys.exit(main())












