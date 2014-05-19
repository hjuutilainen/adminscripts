#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# office-2011-installed-language.py
#
# Exit codes:
# 0 = Office is installed
# 1 = Office is not installed at all
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# ================================================================================

import sys
import subprocess
import os
import re
import plistlib
import datetime
from distutils.version import StrictVersion
from operator import itemgetter, attrgetter
from Foundation import CFPreferencesCopyAppValue

# ================================================================================
# Start configuration
# ================================================================================
# Set this to False if you don't want any output, just the exit codes
verbose = True
# Set this to True if you want to add "office_2011_language" custom conditional to
# /Library/Managed Installs/ConditionalItems.plist
update_munki_conditional_items = False
# ================================================================================
# End configuration
# ================================================================================

def info_for_package_identifier(identifier):
    """
    Returns an info dictionary for a given package identifier
    by running /usr/sbin/pkgutil --pkg-info-plist <identifier>
    """
    if not identifier:
        return None
    
    cmd = ["/usr/sbin/pkgutil", "--pkg-info-plist", identifier]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    if p.returncode != 0:
        return None
    
    package_info_dict = {}
    package_info_dict = plistlib.readPlistFromString(results)
    return package_info_dict


def installed_core_resource_packages():
    """
    Returns a list of installed Office core resource packages
    
    These packages have the following identifier format:
    com.microsoft.office.<language>.core_resources.pkg.<version>
    """
    cmd = ["/usr/sbin/pkgutil", "--pkgs-plist"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    if p.returncode != 0:
        return []
    all_package_identifiers = plistlib.readPlistFromString(results)
    re_core_resource = re.compile(r'^com\.microsoft\.office\.(?P<language_code>.*)\.core_resources\.pkg\.(?P<version>[0-9\.]+)(.update$|$)')
    matching_packages = []
    for identifier in all_package_identifiers:
        m = re.match(re_core_resource, identifier)
        if m and m.group('language_code'):
            item_info = info_for_package_identifier(identifier)
            item_info['language'] = m.group('language_code')
            matching_packages.append(item_info)
    return matching_packages


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
    # Get all Office core resource packages
    packages = installed_core_resource_packages()
    
    if len(packages) == 0:
        # Office is not installed
        return 1
    
    # Sort the packages by install time
    packages_sorted = sorted(packages, key=attrgetter('install-time', 'pkg-version'), reverse=True)
    
    # Installed language is the language of the latest package
    latest_package_info = packages_sorted[0]
    latest_lang = latest_package_info.get('language', None)
    
    if verbose:
        if latest_lang:
            print latest_lang
        else:
            print "Could not determine installed language"

    # Update "ConditionalItems.plist" if munki is installed
    if munki_installed() and update_munki_conditional_items and latest_lang:
        append_conditional_items({'office_2011_language': latest_lang})

    
    return 0


if __name__ == '__main__':
    sys.exit(main())
