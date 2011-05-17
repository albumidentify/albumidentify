# Return Codes
#
# Do not depend on any optional codes
# 
DEV_EMPTY = -2		# Device is empty (optional)
DEV_TRAY_OPEN = -1	# Tray is open (optional)
DEV_NOT_READY = 0	# Device is not ready
DEV_READY = 1		# Device is ready to read disc

class PlatformNotSupportedException(Exception):
	def __init__(self,platform):
		self.platform = platform
	def __str__(self):
		return "Platform %s not Supported" % self.platform

class DeviceNotSupportedException(Exception):
	def __init__(self,device,operation):
		self.operation = operation
		self.device = device
	def __str__(self):
		return "%s is not supported by device %s" % (self.operation,self.device)


def status(device):
	import platform
	platform = platform.system()
	if platform == 'Linux':
		return Unix_CDROM_status(device)
	else:
		raise PlatformNotSupportedException(platform)

def eject(device):
	import platform
	platform = platform.system()
	if platform == 'Linux':
		Unix_CDROM_eject(device)
	else:
		raise PlatformNotSupportedException(platform)

def Unix_CDROM_status(device):
	import fcntl
	import CDROM as CD
	import os
	
	fd = os.fdopen(os.open(device, os.O_RDONLY | os.O_NONBLOCK))
	
	res = fcntl.ioctl(fd, CD.CDROM_DRIVE_STATUS)
	
	if res == CD.CDS_DISC_OK:
		return DEV_READY
	elif res == CD.CDS_DRIVE_NOT_READY:
		return DEV_NOT_READY
	elif res == CD.CDS_TRAY_OPEN:
		return DEV_TRAY_OPEN
	elif res == CD.CDS_NO_DISC:
		return DEV_EMPTY
	elif res == CD.CDS_NO_INFO:
		raise DeviceNotSupportedException(device, "Status Check")
	
	fd.close()

def Unix_CDROM_eject(device):
	import fcntl
	import CDROM as CD
	import os
	
	fd = os.fdopen(os.open(device, os.O_RDONLY | os.O_NONBLOCK))
	
	fcntl.ioctl(fd, CD.CDROMEJECT)

	fd.close()

if __name__ == "__main__":
	import sys
	res = status(sys.argv[1])
	if res == DEV_NOT_READY:
		print "Device is not ready"
	if res == DEV_READY:
		print "Device is ready to read disc"
	if res == DEV_EMPTY:
		print "Device is empty"
	if res == DEV_TRAY_OPEN:
		print "Tray is open"
