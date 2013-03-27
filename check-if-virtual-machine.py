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
updateMunkiConditionalItems = True
# ================================================================================
# End configuration
# ================================================================================

def logger(message, status, info):
    if verbose:
        print "%10s: %-40s [%s]" % (message, status, info)
    pass

def conditionalItemsPath():
    # <http://code.google.com/p/munki/wiki/ConditionalItems>
    # Read the location of the ManagedInstallDir from ManagedInstall.plist
    BUNDLE_ID = 'ManagedInstalls'
    pref_name = 'ManagedInstallDir'
    managedinstalldir = CFPreferencesCopyAppValue(pref_name, BUNDLE_ID)
    # Make sure we're outputting our information to "ConditionalItems.plist"
    if managedinstalldir:
        return os.path.join(managedinstalldir, 'ConditionalItems.plist')
    else:
        # Munki default
        return "/Library/Managed Installs/ConditionalItems.plist"


def munkiInstalled():
    pkgutilProcess = [ "pkgutil", "--pkg-info", "com.googlecode.munki.core" ]
    p = subprocess.Popen(pkgutilProcess, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    if p.returncode == 0:
        return True
    else:
        return False

def isVirtualMachine():
    sysctlProcess = [ "sysctl", "-n", "machdep.cpu.features" ]
    p = subprocess.Popen(sysctlProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for aFeature in results.split():
        if aFeature == "VMM":
            return True
    return False



def appendConditionalItems(aDict):
    conditionalitemspath = conditionalItemsPath()
    if os.path.exists(conditionalItemsPath()):
        existing_dict = plistlib.readPlist(conditionalitemspath)
        output_dict = dict(existing_dict.items() + aDict.items())
    else:
        output_dict = aDict
    plistlib.writePlist(output_dict, conditionalitemspath)
    pass

def main(argv=None):
    newConditionalItemsDict = {}

    if isVirtualMachine():
        print "This system is virtual"
        machineType = 0
        newConditionalItemsDict = { 'virtual_machine': True }
    else:
        print "This system is not virtual"
        machineType = 1
        newConditionalItemsDict = { 'virtual_machine': False }

    # Update "ConditionalItems.plist" if munki is installed
    if ( munkiInstalled() and updateMunkiConditionalItems ):
        appendConditionalItems(newConditionalItemsDict)

    # Exit codes:
    # 0 = This machine is virtual
    # 1 = This machine is not virtual
    return machineType


if __name__ == '__main__':
    sys.exit(main())












