#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# check-mavericks-compatibility.py
#
# This script checks if the current system is compatible with OS X 10.9 Mavericks.
# These checks are based on the installCheckScript and volCheckScript in
# /Applications/Install OS X Mavericks.app/Contents/SharedSupport/OSInstall.mpkg/Distribution
#
# The checks used in this script are:
# - Machine has a specific supported board-id or is a virtual machine
# - 64 bit capable CPU
# - At least 2 GB of memory
# - Current system version is less than 10.9
# - Current system version is at least 10.6.6 or newer
#
# Exit codes:
# 0 = Mavericks is supported
# 1 = Mavericks is not supported
#
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Version history:
# ----------------
# 2013-10-25, Hannes Juutilainen
# - Minor refactoring
# 2013-10-20, Hannes Juutilainen
# - Updated for Mavericks GM
# 2013-09-06, Hannes Juutilainen
# - First version
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
# Set this to True if you want to add "mavericks_supported" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
updateMunkiConditionalItems = False
# ================================================================================
# End configuration
# ================================================================================


def logger(message, status, info):
    if verbose:
        print "%14s: %-40s [%s]" % (message, status, info)
    pass


def conditional_items_path():
    # <http://code.google.com/p/munki/wiki/ConditionalItems>
    # Read the location of the ManagedInstallDir from ManagedInstall.plist
    bundle_id = 'ManagedInstalls'
    pref_name = 'ManagedInstallDir'
    managed_installs_dir = CFPreferencesCopyAppValue(pref_name, bundle_id)
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
    if StrictVersion(product_version) >= StrictVersion('10.9'):
        logger("System",
               "%s %s" % (product_name, product_version),
               "Failed")
        return False
    elif StrictVersion(product_version) >= StrictVersion('10.6.6'):
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


def is_64bit_capable():
    cmd = ["/usr/sbin/sysctl", "-n", "hw.cpu64bit_capable"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


def has_required_amount_of_memory():
    minimum_memory = int(2048 * 1024 * 1024)
    cmd = ["/usr/sbin/sysctl", "-n", "hw.memsize"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    actual_memory = int(results)
    actual_memory_gigabytes = actual_memory / 1024 / 1024 / 1024
    if actual_memory >= minimum_memory:
        logger("Memory",
               "%i GB physical memory installed" % actual_memory_gigabytes,
               "OK")
        return True
    else:
        logger("Memory",
               "%i GB installed, 2 GB required" % actual_memory_gigabytes,
               "Failed")
        return False


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


def is_supported_board_id():
    if is_virtual_machine():
        return True
    platform_support_values = [
        "Mac-00BE6ED71E35EB86",
        "Mac-031AEE4D24BFF0B1",
        "Mac-031B6874CF7F642A",
        "Mac-27ADBB7B4CEE8E61",
        "Mac-2E6FAB96566FE58C",
        "Mac-35C1E88140C3E6CF",
        "Mac-4B7AC7E43945597E",
        "Mac-4BC72D62AD45599E",
        "Mac-50619A408DB004DA",
        "Mac-66F35F19FE2A0D05",
        "Mac-6F01561E16C75D06",
        "Mac-742912EFDBEE19B3",
        "Mac-77EB7D7DAF985301",
        "Mac-7BA5B2794B2CDB12",
        "Mac-7DF21CB3ED6977E5",
        "Mac-7DF2A3B5E5D671ED",
        "Mac-8ED6AF5B48C039E1",
        "Mac-942452F5819B1C1B",
        "Mac-942459F5819B171B",
        "Mac-94245A3940C91C80",
        "Mac-94245B3640C91C81",
        "Mac-942B59F58194171B",
        "Mac-942B5BF58194151B",
        "Mac-942C5DF58193131B",
        "Mac-AFD8A9D944EA4843",
        "Mac-C08A6BB70A942AC2",
        "Mac-C3EC7CD22292981F",
        "Mac-F2208EC8",
        "Mac-F2218EA9",
        "Mac-F2218EC8"
        "Mac-F2218FA9",
        "Mac-F2218FC8",
        "Mac-F221BEC8",
        "Mac-F221DCC8",
        "Mac-F222BEC8",
        "Mac-F2238AC8",
        "Mac-F2238BAE",
        "Mac-F223BEC8",
        "Mac-F22586C8",
        "Mac-F22587A1",
        "Mac-F22587C8",
        "Mac-F22589C8",
        "Mac-F2268AC8",
        "Mac-F2268CC8",
        "Mac-F2268DAE",
        "Mac-F2268DC8",
        "Mac-F2268EC8",
        "Mac-F226BEC8",
        "Mac-F22788AA",
        "Mac-F227BEC8",
        "Mac-F22C86C8",
        "Mac-F22C89C8",
        "Mac-F22C8AC8",
        "Mac-F42386C8",
        "Mac-F42388C8",
        "Mac-F4238BC8",
        "Mac-F4238CC8",
        "Mac-F42C86C8",
        "Mac-F42C88C8",
        "Mac-F42C89C8",
        "Mac-F42D86A9",
        "Mac-F42D86C8",
        "Mac-F42D88C8",
        "Mac-F42D89A9",
        "Mac-F42D89C8",
        "Mac-F65AE981FFA204ED",
        "Mac-FC02E91DDD3FA6A4"]
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


def check_firmware_version():
    """docstring for check_firmware_version"""
    cmd = ["/usr/sbin/ioreg", "-p", "IOService",
           "-n", "AppleAHCIDiskDriver",
           "-r",
           "-l",
           "-d", "1",
           "-w", "0"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    disk_dict = {}
    for line in results.splitlines():
        m = re.match(r"^\s*\"(?P<key>.*)\" = \"(?P<value>.*)\"$", line)
        if m:
            disk_dict[m.group('key')] = m.group('value').strip()
    model = disk_dict.get('Model', '')
    revision = disk_dict.get('Revision', '')
    return model, revision


def hardware_model():
    cmd = ["/usr/sbin/sysctl", "-n", "hw.model"]
    p = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    return results.strip()


def is_firmware_compatible():
    """docstring for needs_ssd_fw_update"""
    if is_virtual_machine():
        return True
    if hardware_model() not in ['MacBookAir5,1', 'MacBookAir5,2']:
        return True
    
    revisions = ['TPSABBF0', 'TPVABBF0']
    models = ['TS064E', 'TS128E']
    
    model, revision = check_firmware_version()
    if any(mod in model for mod in models) and any(rev in revision for rev in revisions):
        logger("SSD Model",
               model,
               "OK")
        logger("SSD Revision",
               revision,
               "Failed")
        return False
    else:
        logger("SSD Model",
               model,
               "OK")
        logger("SSD Revision",
               revision,
               "OK")
        return True


def main(argv=None):
    mavericks_supported_dict = {}
    mavericks_needs_fw_update_dict = {}

    # Run the checks
    board_id_passed = is_supported_board_id()
    firmware_passed = is_firmware_compatible()
    memory_passed = has_required_amount_of_memory()
    cpu_passed = is_64bit_capable()
    system_version_passed = is_system_version_supported()

    if board_id_passed and memory_passed and cpu_passed and system_version_passed and firmware_passed:
        mavericks_supported = 0
        mavericks_needs_fw_update = 0
        mavericks_supported_dict = {'mavericks_supported': True}
        mavericks_needs_fw_update_dict = {'mavericks_needs_fw_update': False}
    elif board_id_passed and memory_passed and cpu_passed and system_version_passed and not firmware_passed:
        mavericks_supported = 0
        mavericks_needs_fw_update = 1
        mavericks_supported_dict = {'mavericks_supported': True}
        mavericks_needs_fw_update_dict = {'mavericks_needs_fw_update': True}
    else:
        mavericks_supported = 1
        mavericks_needs_fw_update = 1
        mavericks_supported_dict = {'mavericks_supported': False}
        mavericks_needs_fw_update_dict = {'mavericks_needs_fw_update': False}

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and updateMunkiConditionalItems:
        append_conditional_items(mavericks_supported_dict)
        append_conditional_items(mavericks_needs_fw_update_dict)

    # Exit codes:
    # 0 = Mavericks is supported
    # 1 = Mavericks is not supported
    return mavericks_supported and mavericks_needs_fw_update


if __name__ == '__main__':
    sys.exit(main())
