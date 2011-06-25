#
# tag_flac.py
#
# ctypes wrapper around libflac for reading vorbis comments
# and picture metadata.
#
# (c) 2011 albumidentify
#

from ctypes import *
from ctypes.util import find_library

__libflac = CDLL(find_library("FLAC"))

class _StreamMetadata_VorbisComment_Entry(Structure):
        _fields_ = [ ("length", c_uint),
                     ("entry", c_char_p) ]

class _StreamMetadata_StreamInfo(Structure):
        pass

class _StreamMetadata_Padding(Structure):
        pass

class _StreamMetadata_Application(Structure):
        pass

class _StreamMetadata_SeekTable(Structure):
        pass

class _StreamMetadata_CueSheet(Structure):
        pass

class _StreamMetadata_Picture(Structure):
        _fields_ = [ ("type", c_uint),
                     ("mime_type", c_char_p),
                     ("description", c_char_p),
                     ("width", c_uint),
                     ("height", c_uint),
                     ("depth", c_uint),
                     ("colors", c_uint),
                     ("data_length", c_uint),
                     ("data", POINTER(c_ubyte)) ]

class _StreamMetadata_Unknown(Structure):
        pass

class _StreamMetadata_VorbisComment(Structure):
        _fields_ = [ ("vendor_string", _StreamMetadata_VorbisComment_Entry),
                       ("num_comments", c_uint),
                       ("comments", POINTER(_StreamMetadata_VorbisComment_Entry)) ]

class _StreamMetadata_Data(Union):
        _fields_ = [ 
                        ("stream_info", _StreamMetadata_StreamInfo),
                        ("padding", _StreamMetadata_Padding),
                        ("application", _StreamMetadata_Application),
                        ("seek_table", _StreamMetadata_SeekTable),
                        ("vorbis_comment", _StreamMetadata_VorbisComment),
                        ("cue_sheet", _StreamMetadata_CueSheet),
                        ("picture", _StreamMetadata_Picture),
                        ("unknown", _StreamMetadata_Unknown)
                        ]

class _StreamMetadata(Structure):
        _fields_ = [ ("type", c_uint),
                       ("is_last", c_uint),
                       ("length", c_uint),
                       ("data", _StreamMetadata_Data) ]

def get_vorbis_comments(filename):
        """ Return the contents of the Vorbis Comments metadata block.

            Returns a dictionary mapping keys to lists of values.
        """
        pi = POINTER(_StreamMetadata)()

        if not __libflac.FLAC__metadata_get_tags(filename, byref(pi)):
                return {}

        comment = pi[0].data.vorbis_comment
        tags = {}

        for i in xrange(comment.num_comments):
                c = comment.comments[i].entry
                parts = c.split("=", 1)
                if tags.has_key(parts[0]):
                        tags[parts[0]].append(parts[1])
                else:
                        tags[parts[0]] = [ parts[1] ]

        __libflac.FLAC__metadata_object_delete(pi)

        return tags

def get_pictures(filename):
        """ Return the picture metadata embedded in the file.

            Returns a list of pictures as dictionaries:
                [ { 'mime' : 'mime/type', 'data' : <buffer> }, ... ]

            XXX: Only ever returns the first picture at this point.
            TODO: Move to libFLAC's level 1 metadata iterator API.
        """
        pi = POINTER(_StreamMetadata)()

        if not __libflac.FLAC__metadata_get_picture(filename, byref(pi), -1, None, None, -1, -1, -1, -1):
                return {}

        picture = pi[0].data.picture

        pic =  { 
                 "mime" : picture.mime_type,
                 "desc" : picture.description,
                 "pictype" : picture.type,
                 "imagedata" : buffer(string_at(picture.data, picture.data_length),0, picture.data_length)
        }

        __libflac.FLAC__metadata_object_delete(pi)

        return [ pic ]
