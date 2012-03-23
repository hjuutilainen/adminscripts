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
dmgFormat	= 'UDZO'	# UDIF zlib-compressed
dmgUid		= '99'		# Who ever is mounting
dmgGid		= '99'		# Who ever is mounting
dmgMode		= '555'		# Read-only

# ===================================================
# Globals
# ===================================================
inputItem 			= ""
inputItemName		= ""
inputItemType		= ""
useContents			= False
hdiutilOutputName	= ""
hdiutilVolumeName	= ""
hdiutilOutputPath	= ""
inputParent 		= ""
itemName 			= ""
hdiutilOutputPath 	= ""
verbose				= False
quiet				= False
auto				= False

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


def createDiskImage():
	"""Wrap the temp directory in a disk image"""
	if verbose:
		print "\nCreating disk image with properties:"
		print "---> %-20s%-20s" % ("Filename:", os.path.split(hdiutilOutputPath)[1])
		print "---> %-20s%-20s" % ("Output path:", hdiutilOutputPath)
	else:
		if not quiet: print "\nCreating disk image from %s" % inputItem
		
	hdiutilProcess = ['/usr/bin/hdiutil',
						'create',
						'-srcFolder', 	tempDir,
						'-format', 		dmgFormat,
						'-volname', 	hdiutilVolumeName,
						'-uid', 		dmgUid,
						'-gid',			dmgGid,
						'-mode', 		dmgMode,
						'-noscrub',
						#'-verbose',
						hdiutilOutputPath]
	if not os.path.exists(hdiutilOutputPath):
		p = subprocess.Popen(hdiutilProcess,
							bufsize=1,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE)
		(plist, err) = p.communicate()
		if err:
			print >>sys.stderr, "%s" % (err)
		if not quiet: print "---> Done"
		if p.returncode == 0:
			return True
		else:
			return False
	else:
		if not quiet: print "---> %s exists." % hdiutilOutputPath
		return False


def copyItem():
	"""Copy target item(s) to temporary directory"""
	if verbose: print "\nCopying target to temp directory"
	global useContents
	src = inputItem
	(fileBaseName, fileExtension) = os.path.splitext(inputItemName)
	if os.path.isdir(inputItem):
		if fileExtension == ".app" or fileExtension == ".pkg" or fileExtension == ".mpkg":
			dst = os.path.join(tempDir, os.path.split(inputItem)[1])
		elif not useContents:
			dst = os.path.join(tempDir, os.path.split(inputItem)[1])
		else:
			dst = tempDir
	else:
		dst = os.path.join(tempDir, os.path.split(inputItem)[1])
	if os.path.exists(tempDir):
		if verbose: print "---> %-20s%-20s" % ("Source:", src)
		if verbose: print "---> %-20s%-20s" % ("Destination:", dst)
		retcode = 1
		if os.path.isfile(inputItem):
			if verbose: print "---> %-20s%-20s" % ("Source type:", "File")
			retcode = subprocess.call(["/bin/cp", src, dst])
		elif os.path.isdir(inputItem):
			if verbose: print "---> %-20s%-20s" % ("Source type:", "Directory")
			retcode = subprocess.call(["/usr/bin/ditto", src, dst])
		if retcode == 0:
			if verbose: print "---> Done"
			clearQuarantine(dst)
			return True
		else:
			return False


def createTempDir():
	"""Create a secure temp directory"""
	if verbose: print "\nCreating a temp directory"
	global tempDir
	tempDir = tempfile.mkdtemp()
	if os.path.exists(tempDir):
		if verbose: print "---> %s" % tempDir
		if verbose: print "---> Done"
		return True
	else:
		return False


def clearTempDir():
	"""Remove the temp directory"""
	if verbose: print "\nRemoving temp directory"
	if os.path.exists(tempDir):
		shutil.rmtree(tempDir)
		if not os.path.exists(tempDir):
			if verbose: print "---> Removed %s" % tempDir
			if verbose: print "---> Done"
			return True
		else:
			return False


def createLink(destination):
	""" Create a symbolic link in disk image"""
	lnSource = destination
	lnDst = os.path.join(tempDir, os.path.split(lnSource)[1])
	subprocess.call(["/bin/ln", "-s", lnSource, lnDst])


def defaultsRead(aKey, fromFile):
	"""Read the specified key from specified file"""
	defaultsReadProcess = ["/usr/bin/defaults", "read", fromFile, aKey]
	p = subprocess.Popen(defaultsReadProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(results, err) = p.communicate()
	return results.strip()


def newTitleForAppBundle(fullPath):
	"""Given a path, tries to create a versioned title by reading from [path]/Contents/Info.plist"""
	originalName = os.path.split(fullPath)[1]
	(originalName, fileExtension) = os.path.splitext(originalName)
	infoPlistPath = os.path.realpath(os.path.join(fullPath, 'Contents/Info.plist'))
	infoPlistPathForDefaults = os.path.realpath(os.path.join(fullPath, 'Contents/Info'))
	bundleShortVersion = ""
	bundleVersion = ""
	bundleShortVersion = defaultsRead('CFBundleShortVersionString', infoPlistPathForDefaults)
	bundleVersion = defaultsRead('CFBundleVersion', infoPlistPathForDefaults)
	if bundleShortVersion != "" and not originalName.endswith(bundleShortVersion):
		if verbose: print "---> %-20s%-20s" % ("Version:", bundleShortVersion)
		return "-".join([originalName, bundleShortVersion])
	elif bundleVersion != "" and not originalName.endswith(bundleVersion):
		if verbose: print "---> %-20s%-20s" % ("Version:", bundleVersion)
		return "-".join([originalName, bundleVersion])
	else:
		return originalName


def clearQuarantine(fullPath):
	"""Check and clear com.apple.quarantine"""
	if verbose: print "\nClearing quarantine attributes on %s" % inputItemName
	xattrListProcess = ["/usr/bin/xattr", fullPath]
	xattrListProcess = ["/usr/bin/xattr", "-r", "-d", "com.apple.quarantine", fullPath]
	p = subprocess.Popen(xattrListProcess, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(results, err) = p.communicate()
	if verbose: print "---> Done"
	pass


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			longArgs = ["help", "input=", "name=", "verbose", "auto"]
			opts, args = getopt.getopt(argv[1:], "hi:n:va", longArgs)
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
				global inputItem
				inputItem = os.path.abspath(value)
				global useContents
				if value.endswith("/") and not inputItem.endswith("/"):
					useContents = True
				else:
					useContents = False
				global inputParent
				inputParent = os.path.split(inputItem)[0]
			if option in ("-n", "--name"):
				global itemName
				itemName = value
		
		# ===================================================
		# We need at least inputItem to process
		# ===================================================
		if not inputItem:
			raise Usage(help_message)
		
		# ===================================================
		# Construct the needed names and paths
		# ===================================================
		else:
			global inputItemName
			global hdiutilOutputName
			global hdiutilVolumeName
			global hdiutilOutputPath
			global inputItemType
			
			# ===================================================
			# Get filename and extension
			# ===================================================
			if verbose: print "\nAnalyzing %s" % inputItem
			inputItemName = os.path.split(inputItem)[1]
			(fileBaseName, fileExtension) = os.path.splitext(inputItemName)
			
			# ===================================================
			# Try to get a good name based on input file type
			# ===================================================
			if fileExtension == ".app":
				if verbose: print "---> %-20s%-20s" % ("Type:", "Application")
				inputItemType = "Application"
				fileBaseName = newTitleForAppBundle(inputItem)
			elif fileExtension == ".pkg" or fileExtension == ".mpkg":
				inputItemType = "Installer package"
				if os.path.isdir(inputItem):
					if verbose: print "---> %-20s%-20s" % ("Type:", "Installer package")
					fileBaseName = newTitleForAppBundle(inputItem)
			else:
				if verbose: print "---> %-20s%-20s" % ("Type:", "Generic")
				inputItemType = "Generic"
				fileBaseName = newTitleForAppBundle(inputItem)
			
			# ===================================================
			# Replace whitespace with dashes
			# ===================================================
			fileBaseName = fileBaseName.replace(" ", "-")
			
			if verbose: print "---> %-20s%-20s" % ("Basename:", fileBaseName)
			if not itemName:
				hdiutilOutputName = ".".join([fileBaseName, "dmg"])
				hdiutilVolumeName = fileBaseName
			else:
				hdiutilOutputName = ".".join([itemName, "dmg"])
				hdiutilVolumeName = itemName
			
			# ===================================================
			# If the input file is not within the user home dir,
			# point the output path to ~/Downloads
			# ===================================================
			homedir = os.path.expanduser('~')
			if not inputParent.startswith(homedir):
				hdiutilOutputPath = os.path.join(homedir, 'Downloads', hdiutilOutputName)
			else:
				hdiutilOutputPath = os.path.join(inputParent, hdiutilOutputName)
			if verbose: print "---> %-20s%-20s" % ("Volume name:", hdiutilVolumeName)
			if verbose: print "---> %-20s%-20s" % ("Output path:", hdiutilOutputPath)
			
			
			if not auto:
				print "\nPlease provide some additional details for the disk image:"
				
				# ===================================================
				# Ask for volume name
				# ===================================================
				questionString = "---> Name of the volume?  [%s]: " % hdiutilVolumeName
				answer = raw_input(questionString)
				if answer:
					hdiutilVolumeName = answer
					hdiutilOutputName = ".".join([hdiutilVolumeName, "dmg"])
				
				# ===================================================
				# Ask for filename
				# ===================================================
				questionString = "---> Filename for the disk image?  [%s]: " % hdiutilOutputName
				answer = raw_input(questionString)
				if answer:
					hdiutilOutputName = answer
				
				# ===================================================
				# Ask for save path
				# ===================================================
				questionString = "---> Output directory?  [%s]: " % os.path.split(hdiutilOutputPath)[0]
				answer = raw_input(questionString)
				if answer:
					hdiutilOutputPath = os.path.join(answer, hdiutilOutputName)
				else:
					hdiutilOutputPath = os.path.join(os.path.split(hdiutilOutputPath)[0], hdiutilOutputName)
			
			# ===================================================
			# Start working
			# ===================================================
			#clearQuarantine(inputItem)
			
			if not createTempDir():
				print >> sys.stderr, "Error. Creating a temp directory failed"
				return 2
			if not copyItem():
				print >> sys.stderr, "Error. Copying items to temp directory failed"
				clearTempDir()
				return 2
			if inputItemType == "Application":
				createLink("/Applications")
				createLink("/Applications/Utilities")
			if not createDiskImage():
				print >> sys.stderr, "Error. Creating the disk image failed"
				clearTempDir()
				return 2
			if not clearTempDir():
				print >> sys.stderr, "Error. Cleaning the temp directory failed"
				return 2
			if not quiet: print ""
			
			return 0
	
	except Usage, err:
		print >> sys.stderr, str(err.msg)
		return 2


if __name__ == "__main__":
	sys.exit(main())
