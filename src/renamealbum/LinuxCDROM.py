import os
import fcntl
import CDROM

class LinuxCDROM():
	def __init__(self, device):
		self.device = device

	def _status(self):
		fd = os.fdopen(os.open(self.device, os.O_RDONLY | os.O_NONBLOCK))
		res = fcntl.ioctl(fd, CDROM.CDROM_DRIVE_STATUS)
		fd.close()

		if res == CDROM.CDS_NO_INFO:
			raise DeviceNotSupportedException(device, "Status Check")
		else:
			return res

	def is_ready(self):
		if self._status() == CDROM.CDS_DISC_OK:
			return True
		else:
			return False

	def tray_open(self): # not supported by all devices
		if self._status() == CDROM.CDS_TRAY_OPEN:
			return True
		else:
			return False

	def no_media(self): # not supported by all devices
		if self._status() == CDROM.CDS_NO_DISC:
			return True
		else:
			return False

	def eject(self):
		fd = os.fdopen(os.open(self.device, os.O_RDONLY | os.O_NONBLOCK))
		fcntl.ioctl(fd, CDROM.CDROMEJECT)
		fd.close()

