#!/usr/bin/env python
# encoding: utf-8
"""
wrap-dmg.py

Created by Hannes Juutilainen on 2010-10-18.
"""

import sys
import os
import getopt
import subprocess
import tempfile
import shutil
import plistlib

# ===================================================
# Options for creating the disk image
# ===================================================
dmg_format = 'UDZO'  # UDIF zlib-compressed
# dmg_format = 'UDRO'    # UDIF read-only image

# Formats that make sense in this context:
# UDRO - UDIF read-only image
# UDCO - UDIF ADC-compressed image
# UDZO - UDIF zlib-compressed image
# UDBZ - UDIF bzip2-compressed image (OS X 10.4+ only)
# UFBI - UDIF entire image with MD5 checksum
# UDTO - DVD/CD-R master for export

dmg_uid = '99'  # Who ever is mounting
dmg_gid = '99'  # Who ever is mounting
dmg_mode = '555'  # Read-only
dmg_fs = 'HFS+' # Filesystem

# ===================================================
# Globals
# ===================================================
input_item = ""
input_item_name = ""
input_item_type = ""
use_contents = False
hdiutil_output_name = ""
hdiutil_volume_name = ""
hdiutil_output_path = ""
input_parent = ""
item_name = ""
verbose = False
quiet = False
auto = False

help_message = '''
Usage: wrap-dmg.py <options>

Options:
  -h | --help            Display this message
  -i | --input <path>    Path to file/folder to process
  -n | --name <name>     Optional, custom name for the disk image
  -v | --verbose         Show operation details
  -a | --auto            Don't ask any question, just use the defaults

'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def create_disk_image():
    """Wrap the temp directory in a disk image"""
    if verbose:
        print "\nCreating disk image with properties:"
        print "---> %-20s%-20s" % ("Filename:", os.path.split(hdiutil_output_path)[1])
        print "---> %-20s%-20s" % ("Output path:", hdiutil_output_path)
    else:
        if not quiet: print "\nCreating disk image from %s" % input_item

    hdiutil_process = ['/usr/bin/hdiutil',
                       'create',
                       '-srcFolder', temp_dir,
                       '-format', dmg_format,
                       '-fs', dmg_fs,
                       '-volname', hdiutil_volume_name,
                       '-uid', dmg_uid,
                       '-gid', dmg_gid,
                       '-mode', dmg_mode,
                       '-noscrub',
                       # '-verbose',
                       hdiutil_output_path]
    if not os.path.exists(hdiutil_output_path):
        p = subprocess.Popen(hdiutil_process,
                             bufsize=1,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (plist, err) = p.communicate()
        if err:
            print >> sys.stderr, "%s" % (err)
        if not quiet: print "---> Done"
        if p.returncode == 0:
            return True
        else:
            return False
    else:
        if not quiet: print "---> %s exists." % hdiutil_output_path
        return False


def copy_item():
    """Copy target item(s) to temporary directory"""
    if verbose: print "\nCopying target to temp directory"
    global use_contents
    src = input_item
    (file_name, file_extension) = os.path.splitext(input_item_name)
    if os.path.isdir(input_item):
        if file_extension == ".app" or file_extension == ".pkg" or file_extension == ".mpkg":
            dst = os.path.join(temp_dir, os.path.split(input_item)[1])
        elif not use_contents:
            dst = os.path.join(temp_dir, os.path.split(input_item)[1])
        else:
            dst = temp_dir
    else:
        dst = os.path.join(temp_dir, os.path.split(input_item)[1])
    if os.path.exists(temp_dir):
        if verbose: print "---> %-20s%-20s" % ("Source:", src)
        if verbose: print "---> %-20s%-20s" % ("Destination:", dst)
        return_code = 1
        if os.path.isfile(input_item):
            if verbose: print "---> %-20s%-20s" % ("Source type:", "File")
            return_code = subprocess.call(["/bin/cp", src, dst])
        elif os.path.isdir(input_item):
            if verbose: print "---> %-20s%-20s" % ("Source type:", "Directory")
            return_code = subprocess.call(["/usr/bin/ditto", src, dst])
        if return_code == 0:
            if verbose: print "---> Done"
            clear_quarantine(dst)
            return True
        else:
            return False


def create_temp_dir():
    """Create a secure temp directory"""
    if verbose: print "\nCreating a temp directory"
    global temp_dir
    temp_dir = tempfile.mkdtemp()
    if os.path.exists(temp_dir):
        if verbose: print "---> %s" % temp_dir
        if verbose: print "---> Done"
        return True
    else:
        return False


def clear_temp_dir():
    """Remove the temp directory"""
    if verbose: print "\nRemoving temp directory"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        if not os.path.exists(temp_dir):
            if verbose: print "---> Removed %s" % temp_dir
            if verbose: print "---> Done"
            return True
        else:
            return False


def create_link(destination):
    """ Create a symbolic link in disk image"""
    ln_source = destination
    ln_destination = os.path.join(temp_dir, os.path.split(ln_source)[1])
    subprocess.call(["/bin/ln", "-s", ln_source, ln_destination])


def defaults_read(key_name, file_name):
    """Read the specified key from specified file"""
    defaults_process = ["/usr/bin/defaults", "read", file_name, key_name]
    p = subprocess.Popen(defaults_process, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    return results.strip()


def new_title_for_app_bundle(bundle_path):
    """Given a path, tries to create a versioned title by reading from [path]/Contents/Info.plist"""
    original_name = os.path.split(bundle_path)[1]
    (original_name, file_extension) = os.path.splitext(original_name)
    info_plist_path_for_defaults = os.path.realpath(os.path.join(bundle_path, 'Contents/Info'))
    bundle_short_version_string = ""
    bundle_version = ""
    bundle_short_version_string = defaults_read('CFBundleShortVersionString', info_plist_path_for_defaults)
    bundle_version = defaults_read('CFBundleVersion', info_plist_path_for_defaults)
    if bundle_short_version_string != "" and not original_name.endswith(bundle_short_version_string):
        if verbose: print "---> %-20s%-20s" % ("Version:", bundle_short_version_string)
        return "-".join([original_name, bundle_short_version_string])
    elif bundle_version != "" and not original_name.endswith(bundle_version):
        if verbose: print "---> %-20s%-20s" % ("Version:", bundle_version)
        return "-".join([original_name, bundle_version])
    else:
        return original_name


def clear_quarantine(file_path):
    """Check and clear com.apple.quarantine"""
    if verbose: print "\nClearing quarantine attributes on %s" % input_item_name
    xattr_process = ["/usr/bin/xattr", file_path]
    xattr_process = ["/usr/bin/xattr", "-r", "-d", "com.apple.quarantine", file_path]
    p = subprocess.Popen(xattr_process, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results, err) = p.communicate()
    if verbose: print "---> Done"
    pass


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            long_args = ["help", "input=", "name=", "verbose", "auto"]
            opts, args = getopt.getopt(argv[1:], "hi:n:va", long_args)
        except getopt.error, msg:
            raise Usage(msg)

        # ===================================================
        # option processing
        # ===================================================
        for option, value in opts:
            if option in ("-v", "--verbose"):
                global verbose
                verbose = True
            if option in ("-q", "--quiet"):
                global quiet
                quiet = True
            if option in ("-a", "--auto"):
                global auto
                auto = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-i", "--input"):
                global input_item
                input_item = os.path.abspath(value)
                global use_contents
                if value.endswith("/") and not input_item.endswith("/"):
                    use_contents = True
                else:
                    use_contents = False
                global input_parent
                input_parent = os.path.split(input_item)[0]
            if option in ("-n", "--name"):
                global item_name
                item_name = value

        # ===================================================
        # We need at least input_item to process
        # ===================================================
        if not input_item:
            raise Usage(help_message)

        # ===================================================
        # Construct the needed names and paths
        # ===================================================
        else:
            global input_item_name
            global hdiutil_output_name
            global hdiutil_volume_name
            global hdiutil_output_path
            global input_item_type

            # ===================================================
            # Get filename and extension
            # ===================================================
            if verbose: print "\nAnalyzing %s" % input_item
            input_item_name = os.path.split(input_item)[1]
            (file_name, file_extension) = os.path.splitext(input_item_name)

            # ===================================================
            # Try to get a good name based on input file type
            # ===================================================
            if file_extension == ".app":
                if verbose: print "---> %-20s%-20s" % ("Type:", "Application")
                input_item_type = "Application"
                file_name = new_title_for_app_bundle(input_item)
            elif file_extension == ".pkg" or file_extension == ".mpkg":
                input_item_type = "Installer package"
                if os.path.isdir(input_item):
                    if verbose: print "---> %-20s%-20s" % ("Type:", "Installer package")
                    file_name = new_title_for_app_bundle(input_item)
            else:
                if verbose: print "---> %-20s%-20s" % ("Type:", "Generic")
                input_item_type = "Generic"
                file_name = new_title_for_app_bundle(input_item)

            # ===================================================
            # Replace whitespace with dashes
            # ===================================================
            file_name = file_name.replace(" ", "-")

            if verbose: print "---> %-20s%-20s" % ("Basename:", file_name)
            if not item_name:
                hdiutil_output_name = ".".join([file_name, "dmg"])
                hdiutil_volume_name = file_name
            else:
                hdiutil_output_name = ".".join([item_name, "dmg"])
                hdiutil_volume_name = item_name

            # ===================================================
            # If the input file is not within the user home dir,
            # point the output path to ~/Downloads
            # ===================================================
            home_directory = os.path.expanduser('~')
            if not input_parent.startswith(home_directory):
                hdiutil_output_path = os.path.join(home_directory, 'Downloads', hdiutil_output_name)
            else:
                hdiutil_output_path = os.path.join(input_parent, hdiutil_output_name)
            if verbose: print "---> %-20s%-20s" % ("Volume name:", hdiutil_volume_name)
            if verbose: print "---> %-20s%-20s" % ("Output path:", hdiutil_output_path)

            if not auto:
                print "\nPlease provide some additional details for the disk image:"

                # ===================================================
                # Ask for volume name
                # ===================================================
                question = "---> Name of the volume?  [%s]: " % hdiutil_volume_name
                answer = raw_input(question)
                if answer:
                    hdiutil_volume_name = answer
                    hdiutil_output_name = ".".join([hdiutil_volume_name, "dmg"])

                # ===================================================
                # Ask for filename
                # ===================================================
                question = "---> Filename for the disk image?  [%s]: " % hdiutil_output_name
                answer = raw_input(question)
                if answer:
                    hdiutil_output_name = answer

                # ===================================================
                # Ask for save path
                # ===================================================
                question = "---> Output directory?  [%s]: " % os.path.split(hdiutil_output_path)[0]
                answer = raw_input(question)
                if answer:
                    hdiutil_output_path = os.path.join(answer, hdiutil_output_name)
                else:
                    hdiutil_output_path = os.path.join(os.path.split(hdiutil_output_path)[0], hdiutil_output_name)

            # ===================================================
            # Start working
            # ===================================================
            # clear_quarantine(input_item)

            if not create_temp_dir():
                print >> sys.stderr, "Error. Creating a temp directory failed"
                return 2
            if not copy_item():
                print >> sys.stderr, "Error. Copying items to temp directory failed"
                clear_temp_dir()
                return 2
            if input_item_type == "Application":
                create_link("/Applications")
                create_link("/Applications/Utilities")
            if not create_disk_image():
                print >> sys.stderr, "Error. Creating the disk image failed"
                clear_temp_dir()
                return 2
            if not clear_temp_dir():
                print >> sys.stderr, "Error. Cleaning the temp directory failed"
                return 2
            if not quiet: print ""

            return 0

    except Usage, err:
        print >> sys.stderr, str(err.msg)
        return 2


if __name__ == "__main__":
    sys.exit(main())
