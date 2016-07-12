'''
Definition for the thumbs.db system file that is generated for
quick image preview in various Windows operating systems.
'''
from .olecf import *

def get(): return thumbs_def


# ##################################
#          Directory names         #
# ##################################
CATALOG_STR = 'Catalog'


thumb_data = Container('thumb_data',
    POINTER=None
    )

thumb_header = Container('thumbnail',
    LUInt32('UNKNOWN1'),  # seems to be a fairly low value
    LUInt32('thumb_id'),  # begins at 1 for the first thumbnail and
    #                       increments by 1 for each subsequent thumbnail
    BytesRaw('UNKNOWN2', SIZE=8),  # maybe a hash of the original image?
    LCStrUtf16('name'),

    ALIGN=4,  # the alignment seems to be 4 byte aligned *shrug*
    )

# The directory in a thumbnails file seems to consist of a
# specific pattern of directory entries. This is the pattern:
#     Root Entry
#     1
#     Catalog
#     N
# where N is the thumb_id of each thumbnail. This means that
# the thumb_id(when converted to a unicode string) has to
# match the storage name entry in the storage directory entry.

thumbs_catalog = Struct('thumbs_catalog',
    LUInt16('UNKNOWN1', DEFAULT=16),
    LUInt16('UNKNOWN2', DEFAULT=7),
    LUInt32('thumb_count'),
    LUInt32('width_max'),
    LUInt32('height_max'),
    )

thumbs = Container('thumbs',
    thumbs_catalog,
    Array('thumbnails',
        SIZE='.thumbs_catalog.thumb_count',
        SUB_STRUCT=thumb_header),
    )

thumbs_def = TagDef("thumbs",
    olecf_header,
    BytesRaw('header_padding', SIZE=olecf_header_pad_size),
    SectorArray('sectors', SUB_STRUCT=sector_switch),
    ext=".db", endian="<", tag_cls=OlecfTag
    )
