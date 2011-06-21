import os

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

class GetDevice():
	def __init__(self, device):
		self.device = device

		import platform
		platform = platform.system()
		if platform == 'Linux':
			import LinuxCDROM
			self.__class__ = LinuxCDROM.LinuxCDROM
		else:
			raise PlatformNotSupportedException(platform)

if __name__ == "__main__":
	import sys
	cd = GetDevice(sys.argv[1])
	if cd.is_ready():
		print "Device is ready to read disc"
	elif cd.tray_open():
		print "Tray is open"
	elif cd.no_media():
		print "Device is empty"
	else:
		print "Device is not ready"
