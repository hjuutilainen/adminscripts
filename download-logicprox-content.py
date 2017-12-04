#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# download-logicprox-content.py
#
# This script downloads the content packages for Logic Pro X. It also arranges
# them in subdirectories the same way as displayed in the Logic Pro first run window.
#
# Logic Pro X Version: 10.3.2
#
# List package URLs:
#       $ ./download-logicprox-content.py list
#
# Download packages:
#       $ ./download-logicprox-content.py download -o ~/Downloads/LogicProContent
#
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
import urllib2
import shutil
import argparse
import objc

# Logic Pro X 10.1 update changed the remote plist file format to binary.
# Since plistlib is not able to deal with binary property lists, we're
# using FoundationPlist from Munki instead.
if not os.path.exists('/usr/local/munki/munkilib'):
    print >> sys.stderr, ("ERROR: munkilib not found")
    sys.exit(1)
else:
    sys.path.append('/usr/local/munki/munkilib')
    try:
        from munkilib import FoundationPlist as plistlib
    except ImportError:
        try:
            import FoundationPlist as plistlib
        except ImportError:
            # maybe we're not on an OS X machine...
            print >> sys.stderr, ("ERROR: FoundationPlist is not available")
            sys.exit(1)


# The URL and the plist file name can be found with the strings command. For example:
#
#     $ cd "/Applications/Logic Pro X.app/Contents/MacOS"
#     $ strings "Logic Pro X" | egrep -B 100 -A 10 ContentBaseURL | egrep 'plist|http'
#
base_url = "http://audiocontentdownload.apple.com/lp10_ms3_content_2016/"
base_url_2013 = "http://audiocontentdownload.apple.com/lp10_ms3_content_2013/"
version = "1032"
logicpro_plist_name = "logicpro%s.plist" % version


download_urls_temp = {}

def human_readable_size(bytes):
    """
    Converts bytes to human readable string
    """
    for x in ['bytes','KB','MB','GB']:
        if bytes < 1024.0:
            return "%3.1f %s" % (bytes, x)
        bytes /= 1000.0 # This seems to be the Apple default
    return "%3.1f %s" % (bytes, 'TB')


def download_package_as(url, output_file):
    """
    Downloads an URL to the specified file path
    """
    if not url or not output_file:
        return False
    
    try:
        req = urllib2.urlopen(url)
        with open(output_file, 'wb') as fp:
            shutil.copyfileobj(req, fp)
    except urllib2.HTTPError as e:
        print "HTTP Error:", e.code, url
    
    return True


def download_logicpro_plist():
    """
    Downloads the Logic Pro Content property list and
    returns a dictionary
    """
    plist_url = ''.join([base_url, logicpro_plist_name])
    try:
        f = urllib2.urlopen(plist_url)
        plist_data = f.read()
        f.close()
    except urllib2.HTTPError as e:
        print "HTTP Error:", e.code, url

    info_plist = plistlib.readPlistFromString(plist_data)
    return info_plist


def process_package_download(download_url, save_path, download_size, download_name):
    """
    Downloads the URL if it doesn't already exist 
    """
    global download_urls_temp
    existing_item = download_urls_temp.get(download_url, None)
    if existing_item:
        existing_item["savepaths"].append(save_path)
    else:
        download_urls_temp[download_url] = {"savepaths": [save_path], "download_name": download_name, "download_size": download_size}
    
    pass

def process_package_dict(package_dict):
    """
    Processes information from a single package dictionary.
    Returns the download URL, file name and size
    """
    download_name = package_dict.get('DownloadName', None)
    download_size = package_dict.get('DownloadSize', None)
    if not download_name.startswith('../'):
        download_url = ''.join([base_url, download_name])
    else:
        download_name = os.path.basename(download_name)
        download_url = ''.join([base_url_2013, download_name])
    return (download_url, download_name, download_size)


def process_content_item(content_item, parent_items, list_only=False):
    """
    Extracts and processes information from a single Content item
    """
    # Get the _LOCALIZABLE_ key which contains the human readable name
    localizable_items = content_item.get('_LOCALIZABLE_', [])
    display_name = localizable_items[0].get('DisplayName')
    new_parent_items = None
    
    # Check if this item is a child of another Content item
    if parent_items:
        display_names = []
        for parent_item in parent_items:
            localizable_parent_items = parent_item.get('_LOCALIZABLE_', [])
            parent_display_name = localizable_parent_items[0].get('DisplayName')
            display_names.append(parent_display_name)
        display_names.append(display_name)
        display_names.insert(0, download_directory)
        relative_path = os.path.join(*display_names)
        new_parent_items = list(parent_items)
        new_parent_items.append(content_item)
    else:
        relative_path = os.path.join(download_directory, display_name)
        new_parent_items = list([content_item])
    
    # Check if this item contains child Content items and process them
    subcontent = content_item.get('SubContent', None)    
    if subcontent:
        for subcontent_item in subcontent:
            process_content_item(subcontent_item, new_parent_items, list_only)
    
    # We don't have any subcontent so get the package references and download
    else:
        package_name = content_item.get('Packages', None)
        if not os.path.exists(relative_path) and not list_only:
            #print "Creating dir %s" % relative_path
            os.makedirs(relative_path)
        
        # There can be only one package defined as a string
        # or an array of packages
        
        if type(package_name) == objc.pyobjc_unicode:
            package_dict = packages.get(package_name, {})
            (download_url, download_name, download_size) = process_package_dict(package_dict)
            save_path = "".join([relative_path, '/', download_name])
            process_package_download(download_url, save_path, download_size, download_name)
            
        else:
            for i in package_name:
                package_dict = packages.get(i, {})
                (download_url, download_name, download_size) = process_package_dict(package_dict)
                save_path = "".join([relative_path, '/', download_name])
                process_package_download(download_url, save_path, download_size, download_name)


def main(argv=None):
    # ================
    # Arguments
    # ================
    
    # Create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands', dest='subparser_name')
    
    # List
    parser_install = subparsers.add_parser('list', help='List package URLs')
    
    # Raw
    parser_install = subparsers.add_parser('raw', help='Print the full update property list')
    
    # Download
    parser_activate = subparsers.add_parser('download', help='Download packages')
    parser_activate.add_argument('-o', '--output', nargs=1, required=True, help='Download location. For example ~/Downloads/LogicProContent')
    
    # Parse arguments
    args = vars(parser.parse_args())
    
    # =================================================================
    # Download the property list which contains the package references
    # =================================================================
    logicpro_plist = download_logicpro_plist()
    
    # Raw requested, just print the property list and exit
    if args['subparser_name'] == 'raw':
        print logicpro_plist
        return 0
    
    global download_directory
    if args.get('output', None):
        download_directory = os.path.abspath(args['output'][0])
    else:
        home = os.path.expanduser('~')
        download_directory = os.path.join(home, 'Downloads/LogicProContent')    
    
    # =====================================
    # Parse the property list for packages
    # =====================================
    global packages
    packages = logicpro_plist['Packages']
    content_dict = logicpro_plist['Content']
    content = content_dict.get('en', [])
    for content_item in content:
        if args['subparser_name'] == 'list':
            process_content_item(content_item, None, list_only=True)
        else:
            process_content_item(content_item, None, list_only=False)
    
    # ======================================
    # Download and link the items
    # ======================================
    temp_download_dir = os.path.join(download_directory, "__Downloaded Items")
    if not os.path.exists(temp_download_dir) and not args['subparser_name'] == 'list':
        os.makedirs(temp_download_dir)
    for key in sorted(download_urls_temp):
        value = download_urls_temp[key]
        download_url = key
        if args['subparser_name'] == 'list':
            print download_url
            continue
        save_path = os.path.join(temp_download_dir, value["download_name"])
        
        # Since Logic Pro X 10.2.3, the download size can be either an integer
        # or a string ("123.456.789"). The following is only an assumption
        # how to parse the latter...
        download_size = value.get("download_size", 0)
        download_size_int = 0
        if type(download_size) == objc.pyobjc_unicode:
            # Strip anything that isn't a digit
            download_size_string = re.sub(r"\D", "", download_size)
            download_size_int = int(download_size_string)
        else:
            download_size_int = int(download_size)
        
        # Now convert the bytes to a human readable string
        download_size_string = human_readable_size(download_size_int)
        
        if os.path.exists(save_path):
            # Check the local file size and download if it's smaller.
            # TODO: Get a better way for this. The 'DownloadSize' key in logicpro_plist
            # seems to be wrong for a number of packages.
            if os.path.getsize(save_path) < download_size_int:
                print "Remote file is larger. Downloading %s from %s" % (download_size_string, download_url)
                download_package_as(download_url, save_path)
            else:
                print "Skipping already downloaded package %s" % download_url
        else:
            print "Downloading %s" % (download_url)
            download_package_as(download_url, save_path)
        
        for item in value["savepaths"]:
            if os.path.exists(item):
                os.unlink(item)
            os.link(save_path, item)
            print "---> Linked %s" % item
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
