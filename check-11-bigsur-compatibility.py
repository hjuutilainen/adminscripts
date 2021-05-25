#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-11-bigsur-compatibility.py
#
# This script checks if the current system is compatible with macOS 11 Big Sur.
# These checks are based on the installCheckScript and volCheckScript in
# distribution file of OSInstall.mpkg installer package.

# The OSInstall.mpkg can be found in the Packages directory of InstallESD disk image:
#   /Applications/Install macOS Catalina.app/Contents/SharedSupport/InstallESD.dmg
#       -> /Volumes/InstallESD/Packages/OSInstall.mpkg
#
# The checks done by this script are (in order):
# - Machine is a virtual machine or has a specific supported board-id
# - Machine model is not in a list of unsupported models
# - Current system version is less than 10.15 and at least 10.9
#
# Exit codes:
# 0 = Big Sur is supported
# 1 = Big Sur is not supported
#
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Thanks to Ralph Cyranka, Ed Bobak and @tcinbis
#
# ================================================================================

import sys
import subprocess
import os
import re
import plistlib
from distutils.version import StrictVersion


# ================================================================================
# Start configuration
# ================================================================================

# Set this to False if you don't want any output, just the exit codes
verbose = True

# Set this to True if you want to add "catalina_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = False

# ================================================================================
# End configuration
# ================================================================================


def logger(message, status, info):
    if verbose:
        print "%14s: %-40s [%s]" % (message, status, info)
    pass


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


def is_system_version_supported():
    system_version_plist = plistlib.readPlist("/System/Library/CoreServices/SystemVersion.plist")
    product_name = system_version_plist['ProductName']
    product_version = system_version_plist['ProductVersion']
    if StrictVersion(product_version) >= StrictVersion('11.0'):
        logger("System",
               "%s %s" % (product_name, product_version),
               "Failed")
        return False
    elif StrictVersion(product_version) >= StrictVersion('10.9'):
        logger("System",
               "%s %s" % (product_name, product_version),
               "OK")
        return True
    else:
        logger("System",
               "%s %s" % (product_name, product_version),
               "Failed")
        return False


def get_board_id():
    cmd = ["/usr/sbin/ioreg",
           "-p", "IODeviceTree",
           "-r",
           "-n", "/",
           "-d", "1"]
    p1 = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["/usr/bin/grep", "board-id"], stdin=p1.stdout, stdout=subprocess.PIPE)
    (results, err) = p2.communicate()
    board_id = re.sub(r"^\s*\"board-id\" = <\"(.*)\">$", r"\1", results)
    board_id = board_id.strip()
    if board_id.startswith('Mac'):
        return board_id
    else:
        return None


def is_virtual_machine():
    cmd = ["/usr/sbin/sysctl", "-n", "machdep.cpu.features"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    for feature in results.split():
        if feature == "VMM":
            logger("Board ID",
                   "Virtual machine",
                   "OK")
            return True
    return False


def get_current_model():
    cmd = ["/usr/sbin/sysctl", "-n", "hw.model"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    return results.strip()


def is_supported_model():
    supported_models = [
        'MacBookAir6,1',
        'MacBookAir6,2',
        'MacBookPro11,1',
        'MacBookPro11,2',
        'MacBookPro11,3',
        'MacBookPro12,1',
        'Macmini7,1',
        'iMac14,4',
        'iMac15,1',
        'MacBookPro13,2',
        'MacBookPro14,2',
        'MacBookPro13,3',
        'MacBookPro14,3',
        'MacPro6,1',
        'MacBook8,1',
        'MacBook9,1',
        'iMac16,2',
        'iMac17,1',
        'MacBookAir7,1',
        'MacBookAir7,2',
        'iMac16,1',
        'MacBook10,1',
        'MacBookPro13,1',
        'MacBookPro14,1',
        'MacBookPro15,2',
        'iMac18,1',
        'iMac18,2',
        'iMac18,3',
        'iMacPro1,1',
        'iMac19,1',
        'iMac19,2',
        'MacBookAir8,2',
        'MacBookAir8,1',
        'MacBookPro11,4',
        'MacBookPro11,5',
        'MacBookPro16,1',
        'MacPro7,1',
        'Macmini8,1',
        'iMac20,1',
        'iMac20,2',
        'MacBookPro15,4',
        'MacBookPro16,2',
        'MacBookPro16,4',
        'MacBookPro16,3',
        'MacBookAir9,1',
        'MacBookPro15,1',
        'MacBookPro15,3'
        ]
    current_model = get_current_model()
    if not (current_model in supported_models):
        logger("Model",
               "\"%s\" is not supported" % current_model,
               "Failed")
        return False
    else:
        logger("Model",
               current_model,
               "OK")
        return True


def is_supported_board_id():
    platform_support_values = [
        'Mac-35C1E88140C3E6CF',
        'Mac-7DF21CB3ED6977E5',
        'Mac-189A3D4F975D5FFC',
        'Mac-3CBD00234E554E41',
        'Mac-2BD1B31983FE1663',
        'Mac-E43C1C25D4880AD6',
        'Mac-35C5E08120C7EEAF',
        'Mac-81E3E92DD6088272',
        'Mac-42FD25EABCABB274',
        'Mac-FA842E06C61E91C5',
        'Mac-66E35819EE2D0D05',
        'Mac-CAD6701F7CEA0921',
        'Mac-A5C67F76ED83108C',
        'Mac-551B86E5744E2388',
        'Mac-F60DEB81FF30ACF6',
        'Mac-BE0E8AC46FE800CC',
        'Mac-F305150B0C7DEEEF',
        'Mac-9AE82516C7C6B903',
        'Mac-FFE5EF870D7BA81A',
        'Mac-DB15BD556843C820',
        'Mac-B809C3757DA9BB8D',
        'Mac-65CE76090165799A',
        'Mac-9F18E312C5C2BF0B',
        'Mac-937CB26E2E02BB01',
        'Mac-A369DDC4E67F1C45',
        'Mac-EE2EBD4B90B839A8',
        'Mac-473D31EABEB93F9B',
        'Mac-B4831CEBD52A0C4C',
        'Mac-827FB448E656EC26',
        'Mac-4B682C642B45593E',
        'Mac-77F17D7DA9285301',
        'Mac-BE088AF8C5EB4FA2',
        'Mac-7BA5B2D9E42DDD94',
        'Mac-AA95B1DDAB278B95',
        'Mac-63001698E7A34814',
        'Mac-226CB3C6A851A671',
        'Mac-827FAC58A8FDFA22',
        'Mac-06F11FD93F0323C5',
        'Mac-06F11F11946D27C5',
        'Mac-C6F71043CEAA02A6',
        'Mac-E1008331FDC96864',
        'Mac-27AD2F918AE68F61',
        'Mac-7BA5B2DFE22DDD8C',
        'Mac-CFF7D910A743CAAF',
        'Mac-AF89B6D9451A490B',
        'Mac-53FDB3D8DB8CA971',
        'Mac-5F9802EFE386AA28',
        'Mac-A61BADE1FDAD7B05',
        'Mac-E7203C0F68AA0004',
        'Mac-5A49A77366F81C72',
        'Mac-0CFF9C7C2B63DF8D',
        'Mac-937A206F2EE63C01',
        'Mac-1E7E29AD0135F9BC',
        'Mac-36B6B6DA9CFCD881',
        'Mac-112818653D3AABFC',
        'Mac-112B0A653D3AAB9C',
        'Mac-90BE64C3CB5A9AEB',
        'Mac-747B1AEFF11738BE',
        'Mac-9394BDF4BF862EE7',
        'Mac-CF21D135A7D34AA6',
        'Mac-50619A408DB004DA',
        'VMM-x86_64'
        ]
    board_id = get_board_id()
    if board_id in platform_support_values:
        logger("Board ID",
               board_id,
               "OK")
        return True
    else:
        logger("Board ID",
               "\"%s\" is not supported" % board_id,
               "Failed")
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
    catalina_supported_dict = {}

    # Run the checks
    model_passed = is_supported_model()
    board_id_passed = is_supported_board_id()
    system_version_passed = is_system_version_supported()

    if is_virtual_machine():
        catalina_supported = 0
        catalina_supported_dict = {'catalina_supported': True}
    elif model_passed and board_id_passed and system_version_passed:
        catalina_supported = 0
        catalina_supported_dict = {'catalina_supported': True}
    else:
        catalina_supported = 1
        catalina_supported_dict = {'catalina_supported': False}

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and update_munki_conditional_items:
        append_conditional_items(catalina_supported_dict)

    # Exit codes:
    # 0 = Catalina is supported
    # 1 = Catalina is not supported
    return catalina_supported


if __name__ == '__main__':
    sys.exit(main())