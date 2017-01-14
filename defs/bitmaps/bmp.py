'''
BMP image file definitions

Structures were pieced together from various online sources
'''
from supyr_struct.defs.tag_def import *

bytes_to_int = int.from_bytes

BMP_HEADER_SIZE = 14
DIB_HEADER_MIN_LEN = 12
DIB_HEADER_DEFAULT_SIZE = 124


def get(): return bmp_def


def bmp_color_table_size(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, **kwargs):
    '''
    Size getter/setter the byte size of the color_table data in a bmp file.
    '''
    if new_value is not None:
        # it isnt possible to set the size because the size is
        # derived from multiple source inputs and must be set
        # manually. This is expected to happen for some types
        # of structures, so rather than raise an error, just do
        # nothing since this is normal and the user handles it
        return

    if parent is None:
        return 0

    header = parent.dib_header

    entry_size = 4
    depth = header.bpp
    if header.header_size == DIB_HEADER_MIN_LEN:
        entry_size = 3

    if depth >= 16:
        return 0

    return (2**depth)*entry_size


def bmp_unspec_ct_size(block=None, parent=None, attr_index=None,
                       rawdata=None, new_value=None, **kwargs):
    '''
    Size getter/setter for the byte size of the extra
    undefined data after the color_table in a bmp file.
    '''
    if new_value is not None or parent is None:
        # it isnt possible to set the size because the size is
        # derived from multiple source inputs and must be set
        # manually. This is expected to happen for some types
        # of structures, so rather than raise an error, just do
        # nothing since this is normal and the user handles it
        return 0

    header_size = parent.dib_header.header_size
    size = (parent.header.pixels_pointer - len(parent.color_table) -
            header_size - BMP_HEADER_SIZE)
    if size > 0:
        return size
    return 0


def get_dib_header(block=None, parent=None, attr_index=None,
                   rawdata=None, new_value=None, **kwargs):
    '''
    Returns the size of the upcoming dib header.
    '''
    try:
        return bytes_to_int(rawdata.peek(4), byteorder='little')
    except AttributeError:
        return DIB_HEADER_DEFAULT_SIZE
        # raise KeyError("Cannot determine bmp dib header "+
        #                "version without supplying rawdata.")


def dib_header_remainder(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, **kwargs):
    '''
    Size getter/setter for the number of bytes left over
    after parsing all of the known attributes of a dib header.
    '''
    if parent is None:
        raise KeyError("Cannot calculate or set the size of bmp " +
                       "dib header without a supplied block.")
    if new_value is None:
        return max(parent.header_size - DIB_HEADER_DEFAULT_SIZE, 0)
    parent.header_size = parent.binsize


compression_method = LUEnum32("compression_method",
    ("rgb",  0),
    ("rle8", 1),
    ("rle4", 2),
    ("bitfields", 3),
    ("jpeg",      4),
    ("png",       5),
    ("alphabitfields", 6),
    ("cmyk",     11),
    ("cmykrle8", 12),
    ("cmykrle4", 13)
    )

endpoints = Struct("endpoints",
    # Each of these colors is actually a set of
    # 3 fixed point numbers with 2 bits for the
    # integer part and 30 bits for the fraction.
    # Since such a FieldType is not implemented,
    # they will just be parsed as raw bytes for now.
    BytesRaw("cie_xyz_red",   SIZE=12),
    BytesRaw("cie_xyz_green", SIZE=12),
    BytesRaw("cie_xyz_blue",  SIZE=12)
    )


color_space_type = LUEnum32("color_space_type",
    ("calibrated_rgb", 0),
    ("srgb",     'BGRs'),
    ("windows",  ' niW'),
    ("linked",   'KNIL'),
    ("embedded", 'DEBM')
    )

intent = LUEnum32("intent",
    ("None",     0),
    ("business", 1),
    ("graphics", 2),
    ("images",   4),
    ("abs_colorimetric", 8)
    )


bitmap_core_header = Struct("bitmap_core_header",
    LUInt32("header_size", DEFAULT=DIB_HEADER_MIN_LEN),
    LUInt16("image_width"),
    LUInt16("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp")
    )

bitmap_info_header = Struct("bitmap_info_header",
    LUInt32("header_size", DEFAULT=40),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used")
    )

bitmap_v2_header = Struct("bitmap_v2_header",
    LUInt32("header_size", DEFAULT=52),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used"),
    QStruct("bitmasks",
        LUInt32("r"), LUInt32("g"), LUInt32("b"), ORIENT='h'
        )
    )

bitmap_v3_header = Struct("bitmap_v3_header",
    LUInt32("header_size", DEFAULT=56),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used"),
    QStruct("bitmasks",
        LUInt32("r"), LUInt32("g"), LUInt32("b"), LUInt32("a"), ORIENT='h'
        )
    )

bitmap_v4_header = Struct("bitmap_v4_header",
    LUInt32("header_size", DEFAULT=108),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used"),
    QStruct("bitmasks",
        LUInt32("r"), LUInt32("g"), LUInt32("b"), LUInt32("a"), ORIENT='h'
        ),
    LUEnum32("color_space_type",
        ("calibrated_rgb", 0)
        ),
    endpoints,
    # each of these gamma attributes is a fixed point
    # number with 16 bits for the integer part and
    # 16 bits for the fractional part. Since such a
    # FieldType is not implemented, they will just
    # be parsed as raw bytes for now.
    BytesRaw("gamma_red",   SIZE=4),
    BytesRaw("gamma_green", SIZE=4),
    BytesRaw("gamma_blue",  SIZE=4),
    )

bitmap_v5_header = Struct("bitmap_v5_header",
    LUInt32("header_size", DEFAULT=DIB_HEADER_DEFAULT_SIZE),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used"),
    QStruct("bitmasks",
        LUInt32("r"), LUInt32("g"), LUInt32("b"), LUInt32("a"), ORIENT='h'
        ),
    color_space_type,
    endpoints,
    BytesRaw("gamma_red",   SIZE=4),
    BytesRaw("gamma_green", SIZE=4),
    BytesRaw("gamma_blue",  SIZE=4),
    intent,
    LPointer32("profile_data_pointer"),
    LUInt32("profile_size"),
    LUInt32("reserved")
    )

unknown_dib_header = Container("unknown_dib_header",
    LUInt32("header_size"),
    LSInt32("image_width"),
    LSInt32("image_height"),
    LUInt16("color_planes", DEFAULT=1),
    LUInt16("bpp"),
    compression_method,
    LUInt32("image_size"),
    LSInt32("h_res"),  # pixels per meter
    LSInt32("v_res"),  # pixels per meter
    LUInt32("palette_count"),
    LUInt32("palette_colors_used"),
    QStruct("bitmasks",
        LUInt32("r"), LUInt32("g"), LUInt32("b"), LUInt32("a"), ORIENT='h'
        ),
    color_space_type,
    endpoints,
    BytesRaw("gamma_red",   SIZE=4),
    BytesRaw("gamma_green", SIZE=4),
    BytesRaw("gamma_blue",  SIZE=4),
    intent,
    LPointer32("profile_data_pointer"),
    LUInt32("profile_size"),
    LUInt32("reserved"),
    BytesRaw("unknown_header_data", SIZE=dib_header_remainder)
    )

dib_header = Switch("dib_header",
    DEFAULT=unknown_dib_header,
    CASE=get_dib_header,
    CASES={12: bitmap_core_header,
           40: bitmap_info_header,
           52: bitmap_v2_header,
           56: bitmap_v3_header,
           108: bitmap_v4_header,
           124: bitmap_v5_header,
           }
    )

bmp_header = Struct('header',
    LUEnum16("bmp_type",
        ("bitmap", 'MB'),
        ("bitmap_array",  'AB'),
        ("color_icon",    'IC'),
        ("color_pointer", 'PC'),
        ("icon",          'CI'),
        ("pointer",       'TP'),
        DEFAULT='MB'
        ),
    LUInt32("filelength"),
    LUInt32("reserved"),
    LPointer32("pixels_pointer")
    )

bmp_def = TagDef("bmp",
    bmp_header,
    dib_header,
    BytesRaw('color_table', SIZE=bmp_color_table_size),
    BytesRaw('unspecified_color_table', SIZE=bmp_unspec_ct_size),
    # rather than try to compute the size based on
    # the various different compression methods and
    # versions, it is easier to just parse the rest
    # of the file into a bytes object and let the
    # user decide what to do with any extra data.
    BytesRaw("pixels", SIZE=remaining_data_length,
             POINTER='.header.pixels_pointer'),
    Void("eof", POINTER='.header.filelength'),

    ext=".bmp", endian="<"
    )
