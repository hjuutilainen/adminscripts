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
import plistlib

# =========================================
# Set this to 'True'
# to automatically remove the whole Keystone
# =========================================
removeKeystone = False

googleSoftwareUpdate = "/Library/Google/GoogleSoftwareUpdate/GoogleSoftwareUpdate.bundle"
chromeBundleID = "com.google.Chrome"


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def keystoneIsInstalled():
    """Check if Keystone is installed"""
    if os.path.exists(googleSoftwareUpdate):
        return True
    else:
        return False


def keystoneNuke():
    """Nuke the installed Keystone"""
    agentPath = os.path.join(googleSoftwareUpdate, "Contents/Resources/GoogleSoftwareUpdateAgent.app/Contents/Resources")
    installScript = os.path.join(agentPath, "install.py")
    if os.path.exists(installScript):
        retcode = subprocess.call([installScript, "--nuke"])
        if retcode == 0:
            return True
        else:
            return False
    else:
        print >> sys.stderr, "Error: KeystoneRegistration.framework not found"
        return False


def removeChromeFromKeystone():
    """Removes Chrome from Keystone. Only return False if ksadmin fails."""
    ksadmin = os.path.join(googleSoftwareUpdate, "Contents/MacOS/ksadmin")
    if os.path.exists(ksadmin):
        ksadminProcess = [  ksadmin, '--delete', '--productid',  chromeBundleID]
        retcode = subprocess.call(ksadminProcess)
        if retcode != 0:
            print >> sys.stderr, "Warning: ksadmin exited with code %i" % retcode
        else:
            print "Removed Chrome from Keystone"
    else:
        print >> sys.stderr, "Warning: %s not found" % ksadmin
        if not os.path.exists("/Library/Google/GoogleSoftwareUpdate/TicketStore/"):
            print >> sys.stderr, "Warning: No ticket store either."


def printUsage():
    print "Options: "
    print "  [ -c | --chromeonly   ]      Only remove Chrome ticket (default)"
    print "  [ -k | --keystoneNuke ]      Remove the whole Keystone"
    print "  [ -h | --help         ]      Print this message"


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            longArgs = ["help", "keystoneNuke", "chromeonly"]
            opts, args = getopt.getopt(argv[1:], "hkc", longArgs)
        except getopt.error, msg:
            printUsage()
            return 1
        
        global removeKeystone
        for option, value in opts:
            if option in ("-c", "--chromeonly"):
                removeKeystone = False
            if option in ("-k", "--keystoneNuke"):
                removeKeystone = True
            if option in ("-h", "--help"):
                printUsage()
                return 1
        
        # Check for root
        if os.geteuid() != 0:
            print >> sys.stderr, "This script must be run as root"
            return 1
        
        # Check if Keystone is actually installed
        if not keystoneIsInstalled():
            print "Nothing to do. Keystone is not installed on this computer"
            return 0
        
        if removeKeystone:
            if keystoneNuke():
                print "Keystone removed"
                return 0
            else:
                print >> sys.stderr, "Error: Keystone nuke failed"
                return 0
        else:
            removeChromeFromKeystone()
            return 0
    
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
