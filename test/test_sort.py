import unittest
import os
import sys
srcdir = os.path.join(os.path.abspath(os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),"..")), "src")
if os.path.exists(srcdir):
	        sys.path.insert(0, srcdir)
from renamealbum import sort

class SortTest(unittest.TestCase):
	def testNumberSpace(self):
		""" A number, a space, then text """
		start = ["1 track", "3 trackthree", "2 tracktwo", "10 track10"]
		expected = ["1 track", "2 tracktwo", "3 trackthree", "10 track10"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testNumberDotSpace(self):
		""" A number, a dot, then text """
		start = ["1. track", "3. trackthree", "2. tracktwo", "10. track10"]
		expected = ["1. track", "2. tracktwo", "3. trackthree", "10. track10"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testDash(self):
		""" A number, a dash, then text """
		start = ["1-track", "3-trackthree", "2-tracktwo", "10-track10"]
		expected = ["1-track", "2-tracktwo", "3-trackthree", "10-track10"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testFlacNaming(self):
		""" syntax used by ripcd/2flac """
		start = ["track01", "track03", "track02", "track10"]
		expected = ["track01", "track02", "track03", "track10"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testLeadingZero(self):
		""" Nicely done already """
		start = ["02 - ArtistTrack", "04 - ArtistTrack", "03 - ArtistTrack", "01 - ArtistTrack"]
		expected = ["01 - ArtistTrack", "02 - ArtistTrack", "03 - ArtistTrack", "04 - ArtistTrack"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testCommonTextThenNumber(self):
		""" Common text then a number """
		start = ["Artist 3 - Something", "Artist 12 - Else", "Artist 1 - One"]
		expected = ["Artist 1 - One", "Artist 3 - Something", "Artist 12 - Else"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testCommonTextThenLeadingZeroNumber(self):
		""" Common text then a (nice) number """
		start = ["Artist 03 - Something", "Artist 12 - Else", "Artist 01 - One"]
		expected = ["Artist 01 - One", "Artist 03 - Something", "Artist 12 - Else"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testDirectoryWithCommonNumber(self):
		""" Part of a directory with a common year in it """
		start = ["/artist 2005 album/Artist 3 - Something", "/artist 2005 album/Artist 12 - Else", "/artist 2005 album/Artist 1 - One"]
		expected = ["/artist 2005 album/Artist 1 - One", "/artist 2005 album/Artist 3 - Something", "/artist 2005 album/Artist 12 - Else"]
		self.assertEqual(sort.sorted_list(start), expected)

	def testLeadingZeroNonLeadingMix(self):
		""" Mix of nice numbers and normal numbers """
		start = ["12 twelve", "3 three", "02 two"]
		expected = ["02 two", "3 three", "12 twelve"]
		self.assertEqual(sort.sorted_list(start), expected)

# FIXME: commented out below tests as they now attempt to sort by tag which needs local file data to test
#
#	def testNumberInName(self):
#		""" Stupid artists who put numbers in their name """
#		start = ["2Pac - 02 - track2", "2Pac - 01 - track1"]
#		expected = ["2Pac - 01 - track1", "2Pac - 02 - track2"]
#		self.assertEqual(sort.sorted_list(start), expected)
#
#	def testNoNumber(self):
#		""" A something with no numbers gives up """
#		start = ["Hello 02 foo", "NoNumbersHere"]
#		expected = ["Hello 02 foo", "NoNumbersHere"]
#		self.assertEqual(sort.sorted_list(start), expected)
#
#	def testNonCommonPrefix(self):
#		""" A non-common prefix gives up """
#		start = ["Hello 02 foo", "There 01 bar"]
#		expected = ["Hello 02 foo", "There 01 bar"]
#		self.assertEqual(sort.sorted_list(start), expected)

if __name__ == '__main__':
	unittest.main()
