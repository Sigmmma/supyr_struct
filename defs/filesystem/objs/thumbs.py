'''
This module provides a Tag class for a Windows thumbs.db file as well
as several structs and BlockDefs for parsing the images contained within.

Most of the documentation on the jfif format was taken from here:
    https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format

See here for information on specific jfif marker types and their usage:
    https://en.wikipedia.org/wiki/JPEG#JPEG_files
'''
from .olecf import *
from supyr_struct.defs.block_def import *
from supyr_struct.defs.constants import *

# ##################################
#          Jfif constants          #
# ##################################
SOI = b'\xFF\xD8'  # jfif 'start of image' marker
SOS = b'\xFF\xDA'  # jfif 'start of scan' marker
EOI = b'\xFF\xD9'  # jfif 'end of image' marker


def catalog_name_size(node=None, parent=None, attr_index=None,
                      rawdata=None, new_value=None, **kwargs):
    '''Size getter/setter for the size of a catalog entry name string.'''
    if parent is None:
        return 0
    if new_value is None:
        return parent.record_len - 16
    else:
        parent.record_len = new_value + 16


def has_next_jfif_stream(node=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, **kwargs):
    '''WhileArray decider to determine if another jfif stream is upcoming.'''
    if rawdata is None:
        return False
    try:
        data = rawdata.peek(2)
        return len(data) and (data != EOI)
    except Exception:
        pass


def jfif_stream_size(node=None, parent=None, attr_index=None,
                     rawdata=None, new_value=None, **kwargs):
    '''Size getter/setter for the size of a jfif data stream.'''
    if parent is None:
        return 0
    if new_value is None:
        return parent.stream_len - 2
    else:
        parent.stream_len = new_value + 2


jfif_stream = Container('jfif_stream',
    BytesRaw('segment_mark', SIZE=2),
    UInt16('stream_len', ENDIAN='>'),  # length of the upcoming data stream
    #                                     plus the size of this field
    BytesRaw('data_stream', SIZE=jfif_stream_size)
    )

jfif_image = Container('jfif_image',
    BytesRaw('image_start',  # marks the start of a jfif image
        SIZE=2, DEFAULT=SOI),
    WhileArray('jfif_streams',
        CASE=has_next_jfif_stream, SUB_STRUCT=jfif_stream),
    BytesRaw('image_end', SIZE=2, DEFAULT=EOI)
    )

thumb_stream_header = QuickStruct('header',
    UInt32('header_len', DEFAULT=12),
    UInt32('unknown'),  # seems to always be 1
    UInt32('stream_len'),
    )

thumb_stream_def = BlockDef('thumb_stream',
    thumb_stream_header,
    jfif_image
    )

# a variant structure which doesnt attempt to parse the
# jfif image stream, but rather just treats it as a
# bytes object with a length defined in the header.
fast_thumb_stream_def = BlockDef('fast_thumb_stream',
    thumb_stream_header,
    BytesRaw('data_stream', SIZE='.header.stream_len')
    )

# The directory in a thumbnails file seems to consist of a
# specific pattern of directory entries. This is the pattern:
#     Root Entry
#     1
#     Catalog
#     N
# where N is the reversed thumb_id of each thumbnail. This means
# that the thumb_id(when converted to a unicode string and having
# the order of the characters in the string reversed) has to
# match the storage name entry in the storage directory entry.

catalog_entry = Container('catalog_entry',
    UInt32('record_len'),  # the number of bytes of this entry
    UInt32('thumb_id'),    # begins at 1 for the first thumbnail and
    #                         increments by 1 for each subsequent thumbnail
    UInt64('timestamp'),   # timestamp in win32 standard time.
    #                        Use win32time_to_pytime to convert to a
    #                        python timestamp and pytime_to_win32time
    #                        to convert a python timestamp to a win32 one
    StrUtf16('name', SIZE=catalog_name_size)
    )

catalog_header = QuickStruct('header',
    UInt16('header_len', DEFAULT=16),
    UInt16('unknown', DEFAULT=7),  # maybe a version number?
    UInt32('catalog_len'),
    UInt32('width_max'),
    UInt32('height_max'),
    )

catalog_def = BlockDef('catalog',
    catalog_header,
    Array('catalog_array',
        SIZE='.header.catalog_len',
        SUB_STRUCT=catalog_entry
        )
    )


class ThumbsTag(OlecfTag):
    '''
    '''
    def __init__(self, **kwargs):
        OlecfTag.__init__(self, **kwargs)
        try:
            self.data.sectors
        except (AttributeError, IndexError, KeyError):
            return
        try:
            self.ministream = self.get_stream_by_index(0)
        except Exception:
            self.ministream = None
        try:
            self.contig_ministream = self.ministream.peek()
        except Exception:
            self.contig_ministream = b''
