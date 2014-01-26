#!/usr/bin/env python
# encoding: utf-8

# ================================================================================
# download-logicprox-content.py
#
# This script downloads the content packages for Logic Pro X. It also arranges
# them in subdirectories the same way as displayed in the Logic Pro first run window.
#
# Example usage:
#       $ ./download-logicprox-content.py "~/Downloads/Logic Pro Content"
#
# Hannes Juutilainen <hjuutilainen@mac.com>
# https://github.com/hjuutilainen/adminscripts
#
# Version history:
# ----------------
# 2014-01-26, Hannes Juutilainen
# - First version
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

base_url = "http://audiocontentdownload.apple.com/lp10_ms3_content_2013/"
version = "1005"
logicpro_plist_name = "logicpro%s_en.plist" % version


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
    except HTTPError, e:
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
    except BaseException as e:
        raise ProcessorError("Can't download %s: %s" % (base_url, e))

    info_plist = plistlib.readPlistFromString(plist_data)
    return info_plist


def process_package_download(download_url, save_path, download_size):
    """
    Downloads the URL if it doesn't already exist 
    """
    download_size_string = human_readable_size(download_size)
    if os.path.exists(save_path):
        # Check the local file size and download if it's smaller.
        # TODO: Get a better way for this. The 'DownloadSize' key in logicpro_plist
        # seems to be wrong for a number of packages.
        if os.path.getsize(save_path) < download_size:
            print "Remote file is larger. Downloading %s from %s" % (download_size_string, download_url)
            download_package_as(download_url, save_path)
        else:
            print "Skipping already downloaded package %s" % download_url
    else:
        print "Downloading %s from %s" % (download_size_string, download_url)
        download_package_as(download_url, save_path)
    
    pass


def process_content_item(content_item, parent_items):
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
            process_content_item(subcontent_item, new_parent_items)
    
    # We don't have any subcontent so get the package references and download
    else:
        package_name = content_item.get('Packages', None)
        if not os.path.exists(relative_path):
            #print "Creating dir %s" % relative_path
            os.makedirs(relative_path)
        
        if isinstance(package_name, str):
            package_dict = packages.get(package_name, {})
            download_name = package_dict.get('DownloadName', None)
            download_size = package_dict.get('DownloadSize', None)
            save_path = "".join([relative_path, '/', download_name])
            download_url = ''.join([base_url, download_name])
            process_package_download(download_url, save_path, download_size)
            
        
        if isinstance(package_name, list):
            for i in package_name:
                package_dict = packages.get(i, {})
                download_name = package_dict.get('DownloadName', None)
                download_size = package_dict.get('DownloadSize', None)
                save_path = "".join([relative_path, '/', download_name])
                download_url = ''.join([base_url, download_name])
                process_package_download(download_url, save_path, download_size)
        
    

def main(argv=None):
    # ================
    # Parse arguments
    # ================
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=str, help="Download location. For example '~/Downloads'", nargs=1)
    args = vars(parser.parse_args())
    
    global download_directory
    if args['output']:
        download_directory = os.path.abspath(args['output'][0])
    else:
        home = os.path.expanduser('~')
        download_directory = os.path.join(home, 'Downloads')
    
    # =================================================================
    # Download the property list which contains the package references
    # =================================================================
    logicpro_plist = download_logicpro_plist()
    
    # =====================================
    # Parse the property list for packages
    # =====================================
    global packages
    packages = logicpro_plist['Packages']
    content = logicpro_plist['Content']
    for content_item in content:
        process_content_item(content_item, None)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
