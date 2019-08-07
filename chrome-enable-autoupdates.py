#!/usr/bin/env python
# encoding: utf-8
"""
chrome-enable-autoupdates.py

This script enables system wide automatic updates for Google Chrome.
It should work for Chrome versions 18 and later. No configuration needed
as this is originally intended as a munki postinstall script.

Created by Hannes Juutilainen, hjuutilainen@mac.com

History:
--------
2019-08-05, Andy Duss
- Fix keystone_registration_framework_path to point to correct directory

2017-09-01, Hannes Juutilainen
- Ignore errors when installing keystone

2015-09-25, Niklas Blomdalen
- Modifications to include old KeystoneRegistration installation (python version)

2014-11-20, Hannes Juutilainen
- Modifications for Chrome 39

2012-08-31, Hannes Juutilainen
- Added --force flag to keystone install as suggested by Riley Shott

2012-05-29, Hannes Juutilainen
- Added more error checking

2012-05-25, Hannes Juutilainen
- Added some error checking in main

2012-05-24, Hannes Juutilainen
- First version

"""

import sys
import os
import subprocess
import plistlib
from distutils.version import LooseVersion

chrome_path = "/Applications/Google Chrome.app"
info_plist_path = os.path.realpath(os.path.join(chrome_path, 'Contents/Info.plist'))
brand_path = "/Library/Google/Google Chrome Brand.plist"
brand_key = "KSBrandID"
tag_path = info_plist_path
tag_key = "KSChannelID"
version_path = info_plist_path
version_key = "KSVersion"


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def chrome_installed():
    """Check if Chrome is installed"""
    if os.path.exists(chrome_path):
        return True
    else:
        return False


def chrome_version():
    """Returns Chrome version"""
    info_plist = plistlib.readPlist(info_plist_path)
    bundle_short_version = info_plist["CFBundleShortVersionString"]
    return bundle_short_version


def chrome_update_url():
    """Returns KSUpdateURL from Chrome Info.plist"""
    info_plist = plistlib.readPlist(info_plist_path)
    update_url = info_plist["KSUpdateURL"]
    return update_url


def chrome_product_id():
    """Returns KSProductID from Chrome Info.plist"""
    info_plist = plistlib.readPlist(info_plist_path)
    product_id = info_plist["KSProductID"]
    return product_id


def keystone_registration_framework_path():
    """Returns KeystoneRegistration.framework path"""
    if LooseVersion(chrome_version()) >= LooseVersion("76"):
        keystone_registration = os.path.join(chrome_path, 'Contents', 'Frameworks')
        keystone_registration = os.path.join(keystone_registration, 'Google Chrome Framework.framework')
        keystone_registration = os.path.join(keystone_registration, 'Frameworks', 'KeystoneRegistration.framework')
        keystone_registration = os.path.join(keystone_registration, 'Versions', 'Current')
    elif LooseVersion(chrome_version()) >= LooseVersion("75") and LooseVersion(chrome_version()) < LooseVersion("76"):
        keystone_registration = os.path.join(chrome_path, 'Contents/Frameworks/')
        keystone_registration = os.path.join(keystone_registration, 'Google Chrome Framework.framework/Versions')
        keystone_registration = os.path.join(keystone_registration, chrome_version())
        keystone_registration = os.path.join(keystone_registration, 'Frameworks/KeystoneRegistration.framework')
    else:
        keystone_registration = os.path.join(chrome_path, 'Contents/Versions')
        keystone_registration = os.path.join(keystone_registration, chrome_version())
        keystone_registration = os.path.join(keystone_registration, 'Google Chrome Framework.framework')
        keystone_registration = os.path.join(keystone_registration, 'Frameworks/KeystoneRegistration.framework')
    return keystone_registration


def keystone_install():
    """Install the current Keystone"""
    install_script = os.path.join(keystone_registration_framework_path(), 'Resources/ksinstall')
    if not os.path.exists(install_script):
        install_script = os.path.join(keystone_registration_framework_path(), 'Resources/install.py')
    keystone_payload = os.path.join(keystone_registration_framework_path(), 'Resources/Keystone.tbz')
    if os.path.exists(install_script) and os.path.exists(keystone_payload):
        ksinstall_process = [
            install_script,
            '--install', keystone_payload,
            '--force'
        ]
        p = subprocess.Popen(ksinstall_process, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (results, error) = p.communicate()
        if results:
            print results
        if p.returncode != 0:
            if error:
                print >> sys.stderr, "%s" % error
            print >> sys.stderr, "Keystone install exited with code %i" % p.returncode

        # Since we used --force argument, succeed no matter what the exit code was.
        return True
    else:
        print >> sys.stderr, "Error: KeystoneRegistration.framework not found"
        return False


def register_chrome_with_keystone():
    """Registers Chrome with Keystone"""
    ksadmin = "/Library/Google/GoogleSoftwareUpdate/GoogleSoftwareUpdate.bundle/Contents/MacOS/ksadmin"
    if os.path.exists(ksadmin):
        ksadmin_process = [
            ksadmin,
            '--register',
            '--productid', chrome_product_id(),
            '--version', chrome_version(),
            '--xcpath', chrome_path,
            '--url', chrome_update_url(),
            '--tag-path', tag_path,
            '--tag-key', tag_key,
            '--brand-path', brand_path,
            '--brand-key', brand_key,
            '--version-path', version_path,
            '--version-key', version_key
        ]
        p = subprocess.Popen(ksadmin_process, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (results, error) = p.communicate()
        if error:
            print >> sys.stderr, "%s" % error
        if results:
            print results
        if p.returncode == 0:
            return True
        else:
            return False
    else:
        print >> sys.stderr, "Error: %s doesn't exist" % ksadmin
        return False


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        # Check for root
        if os.geteuid() != 0:
            print >> sys.stderr, "This script must be run as root"
            return 1

        if not chrome_installed():
            print >> sys.stderr, "Error: Chrome is not installed on this computer"
            return 1
        if keystone_install():
            print "Keystone installed"
        else:
            print >> sys.stderr, "Error: Keystone install failed"
            return 1
        if register_chrome_with_keystone():
            print "Registered Chrome with Keystone"
            return 0
        else:
            print >> sys.stderr, "Error: Failed to register Chrome with Keystone"
            return 1

    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
