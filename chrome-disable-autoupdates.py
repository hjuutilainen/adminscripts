#!/usr/bin/env python
# encoding: utf-8
"""
chrome-disable-autoupdates.py

This script disables system wide automatic updates for Google Chrome. It can 
optionally remove the whole Keystone and its ticket store too. It should work 
for Chrome versions 18 and later.

Created by Hannes Juutilainen, hjuutilainen@mac.com

History:
2012-05-30, Hannes Juutilainen
- First version

"""

import sys
import os
import getopt
import subprocess

# =========================================
# Set this to 'True'
# to automatically remove the whole Keystone
# =========================================
remove_keystone = False

google_software_update_bundle = "/Library/Google/GoogleSoftwareUpdate/GoogleSoftwareUpdate.bundle"
chrome_bundle_id = "com.google.Chrome"


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def keystone_installed():
    """Check if Keystone is installed"""
    if os.path.exists(google_software_update_bundle):
        return True
    else:
        return False


def keystone_nuke():
    """Nuke the installed Keystone"""
    agent_path = os.path.join(
        google_software_update_bundle,
        "Contents/Resources/GoogleSoftwareUpdateAgent.app/Contents/Resources"
    )
    install_script = os.path.join(agent_path, "install.py")
    if os.path.exists(install_script):
        p = subprocess.Popen(
            [install_script, "--nuke"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
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
        print >> sys.stderr, "Error: KeystoneRegistration.framework not found"
        return False


def remove_chrome_from_keystone():
    """Removes Chrome from Keystone. Only return False if ksadmin fails."""
    ksadmin = os.path.join(google_software_update_bundle, "Contents/MacOS/ksadmin")
    if os.path.exists(ksadmin):
        ksadmin_process = [
            ksadmin,
            '--delete',
            '--productid',
            chrome_bundle_id
        ]
        p = subprocess.Popen(
            ksadmin_process,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        (results, error) = p.communicate()
        if error:
            print >> sys.stderr, "%s" % error
        if results:
            print results
        if p.returncode == 0:
            print "Removed Chrome from Keystone"
        else:
            print >> sys.stderr, "Warning: ksadmin exited with code %i" % p.returncode

    else:
        print >> sys.stderr, "Warning: %s not found" % ksadmin
        if not os.path.exists("/Library/Google/GoogleSoftwareUpdate/TicketStore/"):
            print >> sys.stderr, "Warning: No ticket store either."


def print_usage():
    print "Options: "
    print "  [ -c | --chromeonly   ]      Only remove Chrome ticket (default)"
    print "  [ -k | --keystoneNuke ]      Remove the whole Keystone"
    print "  [ -h | --help         ]      Print this message"


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            long_args = ["help", "keystoneNuke", "chromeonly"]
            opts, args = getopt.getopt(argv[1:], "hkc", long_args)
        except getopt.error, msg:
            print_usage()
            return 1
        
        global remove_keystone
        for option, value in opts:
            if option in ("-c", "--chromeonly"):
                remove_keystone = False
            if option in ("-k", "--keystoneNuke"):
                remove_keystone = True
            if option in ("-h", "--help"):
                print_usage()
                return 1
        
        # Check for root
        if os.geteuid() != 0:
            print >> sys.stderr, "This script must be run as root"
            return 1
        
        # Check if Keystone is actually installed
        if not keystone_installed():
            print "Nothing to do. Keystone is not installed on this computer"
            return 0
        
        if remove_keystone:
            if keystone_nuke():
                print "Keystone removed"
                return 0
            else:
                print >> sys.stderr, "Error: Keystone nuke failed"
                return 0
        else:
            remove_chrome_from_keystone()
            return 0
    
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
