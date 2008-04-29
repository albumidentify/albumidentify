#
# Python ctypes bindings for libofa
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

from ctypes import *

__libofa = CDLL("libofa.so.0")

__create_print = __libofa.ofa_create_print
__create_print.argtypes = [c_char_p, c_int, c_long, c_int, c_int]
__create_print.restype = c_char_p

BYTE_ORDER_LE = 0
BYTE_ORDER_BE = 1

def create_print(samples, byteOrder, size, sRate, stereo):
	return __create_print(samples, byteOrder, size, sRate, stereo)

def get_version():
	""" Returns the libofa version number in the form:
			(major, minor, revision)
	"""
	major = c_int(0)
	minor = c_int(0)
	rev = c_int(0)
	__libofa.ofa_get_version(byref(major), byref(minor), byref(rev))
	return ((major.value, minor.value,rev.value))
