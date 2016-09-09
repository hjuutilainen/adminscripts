#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-mountainlion-compatibility.py
#
# This script checks if the current system is compatible with OS X Mountain Lion.
# These checks are based on the installCheckScript and volCheckScript in
# InstallESD.dmg -> ./Packages/OSInstall.mpkg/Distribution
#
# The checks are:
# - Machine has a specific board-id or is a virtual machine
# - 64 bit capable CPU
# - At least 2GB of memory
# - System version earlier than 10.8 but at least 10.6.6
#
# Exit codes:
# 0 = Mountain Lion is supported
# 1 = Mountain Lion is not supported
#
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Version history:
# ----------------
# 2012-10-10, Hannes Juutilainen
# - First version
#
# ================================================================================

import sys
import subprocess
import os
import re
import plistlib
import platform
from distutils.version import StrictVersion
from Foundation import CFPreferencesCopyAppValue

# ================================================================================
# Start configuration
# ================================================================================
# Set this to False if you don't want any output, just the exit codes
verbose = True
# Set this to True if you want to add "mountainlion_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
updateMunkiConditionalItems = False
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


def isSystemVersionSupported():
    systemVersionPlist = plistlib.readPlist("/System/Library/CoreServices/SystemVersion.plist")
    productName = systemVersionPlist['ProductName']
    productVersion = systemVersionPlist['ProductVersion']
    if StrictVersion(productVersion) > StrictVersion('10.8'):
        logger("System",
                "%s %s" % (productName, productVersion),
                "Failed")
        return False
    elif StrictVersion(productVersion) >= StrictVersion('10.6.6'):
        logger("System",
                "%s %s" % (productName, productVersion),
                "OK")
        return True
    else:
        logger("System",
                "%s %s" % (productName, productVersion),
                "Failed")
        return False


def getBoardID():
    ioregProcess = [ "/usr/sbin/ioreg",
                     "-p", "IODeviceTree",
                     "-r",
                     "-n", "/",
                     "-d", "1" ]
    p1 = subprocess.Popen(ioregProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["/usr/bin/grep", "board-id"], stdin=p1.stdout, stdout=subprocess.PIPE)
    (results, err) = p2.communicate()
    boardID = re.sub(r"^\s*\"board-id\" = <\"(.*)\">$", r"\1", results)
    boardID = boardID.strip()
    if boardID.startswith('Mac'):
        return boardID
    else:
        return None


def is64BitCapable():
    sysctlProcess = [ "sysctl", "-n", "hw.cpu64bit_capable" ]
    p = subprocess.Popen(sysctlProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    if bool(results):
        logger("CPU",
                "64 bit capable",
                "OK")
        return True
    else:
        logger("CPU",
                "not 64 bit capable",
                "Failed")
        return False


def hasRequiredAmountOfRAM():
    minimumRam = int(2048 * 1024 * 1024)
    sysctlProcess = [ "sysctl", "-n", "hw.memsize" ]
    p = subprocess.Popen(sysctlProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    actualRAM = int(results)
    actualRAMGigabytes = actualRAM / 1024 / 1024 / 1024
    if actualRAM >= minimumRam:
        logger("Memory",
                "%i GB physical memory installed" % (actualRAMGigabytes),
                "OK")
        return True
    else:
        logger("Memory",
                "%i GB installed, 2 GB required" % (actualRAMGigabytes),
                "Failed")
        return False


def isVirtualMachine():
    sysctlProcess = [ "sysctl", "-n", "machdep.cpu.features" ]
    p = subprocess.Popen(sysctlProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for aFeature in results.split():
        if aFeature == "VMM":
            logger("Board ID",
                    "Virtual machine",
                    "OK")
            return True
    return False


def isSupportedBoardID():
    if isVirtualMachine():
        return True
    platformSupportValues = [
        "Mac-F42D88C8",
        "Mac-F2218EA9",
        "Mac-F42D86A9",
        "Mac-F22C8AC8",
        "Mac-942B59F58194171B",
        "Mac-F226BEC8",
        "Mac-F2268DC8",
        "Mac-2E6FAB96566FE58C",
        "Mac-7BA5B2794B2CDB12",
        "Mac-4B7AC7E43945597E",
        "Mac-F22C89C8",
        "Mac-942459F5819B171B",
        "Mac-F42388C8",
        "Mac-F223BEC8",
        "Mac-F4238CC8",
        "Mac-F222BEC8",
        "Mac-F227BEC8",
        "Mac-F2208EC8",
        "Mac-66F35F19FE2A0D05",
        "Mac-F4238BC8",
        "Mac-F221BEC8",
        "Mac-C08A6BB70A942AC2",
        "Mac-8ED6AF5B48C039E1",
        "Mac-F2238AC8",
        "Mac-F22586C8",
        "Mac-6F01561E16C75D06",
        "Mac-F2268EC8",
        "Mac-F22589C8",
        "Mac-F22587A1",
        "Mac-F22788AA",
        "Mac-F42C86C8",
        "Mac-942C5DF58193131B",
        "Mac-F2238BAE",
        "Mac-F22C86C8",
        "Mac-F2268CC8",
        "Mac-F2218FC8",
        "Mac-742912EFDBEE19B3",
        "Mac-F42D89C8",
        "Mac-F22587C8",
        "Mac-F42D89A9",
        "Mac-F2268AC8",
        "Mac-F42C89C8",
        "Mac-942452F5819B1C1B",
        "Mac-F2218FA9",
        "Mac-F221DCC8",
        "Mac-94245B3640C91C81",
        "Mac-F42D86C8",
        "Mac-4BC72D62AD45599E",
        "Mac-F2268DAE",
        "Mac-F42C88C8",
        "Mac-94245A3940C91C80",
        "Mac-F42386C8",
        "Mac-C3EC7CD22292981F",
        "Mac-942B5BF58194151B",
        "Mac-F2218EC8" ]
    boardID = getBoardID()
    if boardID in platformSupportValues:
        logger("Board ID",
                boardID,
                "OK")
        return True
    else:
        logger("Board ID",
                "\"%s\" is not supported" % boardID,
                "Failed")
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
    mountainlion_supported_dict = {}

    # Run the checks
    boardIDPassed = isSupportedBoardID()
    memoryPassed = hasRequiredAmountOfRAM()
    cpuPassed = is64BitCapable()
    systemVersionPassed = isSystemVersionSupported()

    if ( boardIDPassed and memoryPassed and cpuPassed and systemVersionPassed ):
        mountainLionSupported = 0
        mountainlion_supported_dict = { 'mountainlion_supported': True }
    else:
        mountainLionSupported = 1
        mountainlion_supported_dict = { 'mountainlion_supported': False }

    # Update "ConditionalItems.plist" if munki is installed
    if ( munkiInstalled() and updateMunkiConditionalItems ):
        appendConditionalItems(mountainlion_supported_dict)

    # Exit codes:
    # 0 = Mountain Lion is supported
    # 1 = Mountain Lion is not supported
    return mountainLionSupported


if __name__ == '__main__':
    sys.exit(main())
