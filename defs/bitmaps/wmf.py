'''
Windows meta file

Structure definitions written using documentation on these websites:
http://wvware.sourceforge.net/caolan/ora-wmf.html
http://www.rpi.edu/dept/acm/packages/gimp/gimp-1.2.3/plug-ins/common/wmf.c
'''

from supyr_struct.defs.tag_def import *
from supyr_struct.defs.constants import *


def get(): return wmf_def


WMF_PLACEABLE_HEADER_SIZE = 22
WMF_PLACEABLE_HEADER_MAGIC = b'\xD7\xCD\xC6\x9A'
BITBLT_FUNC_NUM = b'\x22\x09'
DIB_BITBLT_FUNC_NUM = b'\x40\x09'


def record_param_count(parent=None, new_value=None, **kwargs):
    '''Size getter/setter for the record parameters array element count.'''
    if parent is None:
        raise KeyError("Cannot get/set the size of record parameter " +
                       "array without a supplied parent.")

    if new_value is None:
        return (parent.size - 3)*2
    assert not new_value % 2, 'record byte sizes must be a multiple of 2.'
    parent.size = 3 + new_value//2


def get_has_placeable_header(rawdata=None, **kwargs):
    '''Returns whether or not a wmf placeable header is in the rawdata.'''
    if hasattr(rawdata, 'peek'):
        return rawdata.peek(4) == WMF_PLACEABLE_HEADER_MAGIC
    return False


def get_has_next_record(rawdata=None, **kwargs):
    '''Returns whether or not more wmf records exist in the rawdata.'''
    try:
        return len(rawdata.peek(6)) >= 6
    except Exception:
        return False


def get_set_wmf_eof(parent=None, new_value=None, **kwargs):
    '''Size getter/setter for the length of a wmf file.'''
    if parent is None:
        raise KeyError("Cannot get or set the size of the" +
                       "wmf file without a supplied parent.")
    if new_value is None:
        return parent.header.filesize * 2 + parent.placeable_header.binsize
    parent.header.filesize = (new_value - parent.placeable_header.binsize) // 2


def get_record_type(rawdata=None, **kwargs):
    '''Returns the type of upcoming wmf record.'''
    try:
        return rawdata.peek(6)[4:]
    except Exception:
        return


def get_bitmap_size(**kwargs):
    '''
    Size getter for the number of bytes of pixel data
    in a dib_bitblt_record or bitblt_record bitmap.
    '''
    # This function is currently a placeholder since I havent
    # done enough research to figure out how it should work.
    return 0


record_function = LSEnum16("function",
    ('EOF', 0x0000),
    ('Aldus_Header', 0x0001),
    ('CLP_Header16', 0x0002),
    ('CLP_Header32', 0x0003),
    ('Header', 0x0004),
    ('SaveDC', 0x001E),

    ('RealizePalette', 0x0035),
    ('SetPalEntries',  0x0037),

    ('StartPage', 0x004F),
    ('EndPage',   0x0050),
    ('AbortDoc',  0x0052),
    ('EndDoc',    0x005E),

    ('CreatePalette', 0x00F7),
    ('CreateBrush',   0x00F8),

    ('SetBKMode',  0x0102),
    ('SetMapMode', 0x0103),
    ('SetROP2',    0x0104),
    ('SetRelabs',  0x0105),
    ('SetPolyFillMode',   0x0106),
    ('SetStretchBltMode', 0x0107),
    ('SetTextCharExtra',  0x0108),

    ('RestoreDC',    0x0127),
    ('InvertRegion', 0x012A),
    ('PaintRegion',  0x012B),
    ('SelectClipRegion', 0x012C),
    ('SelectObject', 0x012D),
    ('SetTextAlign', 0x012E),

    ('ResizePalette', 0x0139),
    ('DibCreatePatternBrush', 0x0142),
    ('SelLayout', 0x0149),
    ('ResetDC',   0x014C),
    ('StartDoc',  0x014D),

    ('CreatePatternBrush', 0x01F9),
    ('DeleteObject',       0x01F0),

    ('SetBKColor',     0x0201),
    ('SetTextColor',   0x0209),
    ('SetTextJustification', 0x020A),
    ('SetWindowOrg',   0x020B),
    ('SetWindowExt',   0x020C),
    ('SetViewportOrg', 0x020D),
    ('SetViewportExt', 0x020E),

    ('FillRegion',     0x0228),
    ('SelectPalette',  0x0234),
    ('SetMapperFlags', 0x0231),

    ('CreateFontIndirect',   0x02FB),
    ('CreateBrushIndirect',  0x02FC),
    ('CreateBitmapIndirect', 0x02FD),

    ('OffsetWindowOrg',   0x020F),
    ('OffsetViewportOrg', 0x0211),
    ('LineTo', 0x0213),
    ('MoveTo', 0x0214),
    ('OffsetClipRgn',     0x0220),
    ('CreatePenIndirect', 0x02FA),

    ('Polygon',  0x0324),
    ('Polyline', 0x0325),

    ('ScaleWindowExt',   0x0410),
    ('ScaleViewportExt', 0x0412),

    ('ExcludeClipRect',   0x0415),
    ('IntersectClipRect', 0x0416),

    ('Ellipse',   0x0418),
    ('FloodFill', 0x0419),
    ('Rectangle', 0x041B),
    ('SetPixel',  0x041F),

    ('FrameRegion',    0x0429),
    ('AnimatePalette', 0x0436),

    ('TextOut',      0x0521),
    ('PolyPolygon',  0x0538),
    ('ExtFloodFill', 0x0548),

    ('RoundRect', 0x061C),
    ('PatBlt',    0x061D),
    ('Escape',    0x0626),
    ('DrawText',  0x062F),

    ('CreateBitmap', 0x06FE),
    ('CreateRegion', 0x06FF),

    ('Arc',   0x0817),
    ('Pie',   0x081A),
    ('Chord', 0x0830),

    ('BitBlt',    0x0922),
    ('DibBitblt', 0x0940),

    ('ExtTextOut',    0x0A32),
    ('StretchBlt',    0x0B23),
    ('DibStretchBlt', 0x0B41),
    ('SetDibToDev',   0x0D33),
    ('StretchDIB',    0x0F43),
    )

bitblt_record = Container('bitblt_record',
    LSInt32('size'),           # Total size of the record in WORDs
    record_function,           # Function number (0x0922)
    LSInt16('raster_op'),      # High-order word for the raster operation
    LSInt16('y_src_origin'),   # Y-coordinate of the source origin
    LSInt16('x_src_origin'),   # X-coordinate of the source origin
    LSInt16('y_dest'),         # Destination width
    LSInt16('x_dest'),         # Destination height
    LSInt16('y_dest_origin'),  # Y-coordinate of the destination origin
    LSInt16('x_dest_origin'),  # X-coordinate of the destination origin

    # DIB bitmap section
    LSInt32('width'),             # Width of bitmap in pixels
    LSInt32('height'),            # Height of bitmap in scan lines
    LSInt32('bytes_per_line'),    # Number of bytes in each scan line
    LSInt16('num_color_planes'),  # Number of color planes in the bitmap
    LSInt16('bpp'),               # Number of bits in each pixel

    BytearrayRaw('bitmap', SIZE=get_bitmap_size)
    )

dib_bitblt_record = Container('dib_bitblt_record',
    LSInt32('size'),           # Total size of the record in WORDs
    record_function,           # Function number (0x0940)
    LSInt16('raster_op'),      # High-order word for the raster operation
    LSInt16('y_src_origin'),   # Y-coordinate of the source origin
    LSInt16('x_src_origin'),   # X-coordinate of the source origin
    LSInt16('y_dest'),         # Destination width
    LSInt16('x_dest'),         # Destination height
    LSInt16('y_dest_origin'),  # Y-coordinate of the destination origin
    LSInt16('x_dest_origin'),  # X-coordinate of the destination origin

    # DDB bitmap section
    LSInt32('width'),               # Width of bitmap in pixels
    LSInt32('height'),              # Height of bitmap in scan lines
    LSInt32('bytes_per_line'),      # Number of bytes in each scan line
    LSInt16('num_color_planes'),    # Number of color planes in the bitmap
    LSInt16('bpp'),                 # Number of bits in each pixel
    LSInt32('compression'),         # Compression type
    LSInt32('size_image'),          # Size of bitmap in bytes
    LUInt32('x_pixels_per_meter'),  # Width of image in pixels per meter
    LUInt32('y_pixels_per_meter'),  # Height of image in pixels per meter
    LSInt32('color_used'),          # Number of colors used
    LSInt32('color_important'),     # Number of important colors

    BytearrayRaw('bitmap', SIZE=get_bitmap_size)
    )

wmf_record = Container("record",
    LSInt32("size"),
    record_function,
    LUInt16Array("record_data", SIZE=record_param_count)
    )
# It's far more efficient and faster to use a UInt16Array
# rather than a ListBlock as an array with multiple UInt16s
#    Array( "record_data",
#           SUB_STRUCT = LUInt16('data'),
#           SIZE = record_param_count
#           )
#    )

wmf_record_switch = Switch('record',
    CASE=get_record_type,
    CASES={BITBLT_FUNC_NUM: bitblt_record,
        DIB_BITBLT_FUNC_NUM: dib_bitblt_record},
    DEFAULT=wmf_record
    )
# When I figure out how to properly parse the dibbitblt
# and bitblt records, this will be uncommented and used
# wmf_records = WhileArray( 'records',
#     CASE = get_has_next_record,
#     SUB_STRUCT = wmf_record_switch
#     )

wmf_records = WhileArray('records',
    CASE=get_has_next_record,
    SUB_STRUCT=wmf_record
    )

wmf_placeable_header = Struct("placeable_header",
    # Magic constant (always 0x9AC6CDD7)
    BytesRaw("key", DEFAULT=WMF_PLACEABLE_HEADER_MAGIC, SIZE=4),
    LSInt16("handle"),    # Metafile HANDLE number (always 0)
    LSInt16("left"),      # Left coordinate in metafile units
    LSInt16("top"),       # Top coordinate in metafile units
    LSInt16("right"),     # Right coordinate in metafile units
    LSInt16("bottom"),    # Bottom coordinate in metafile units
    LSInt16("inch"),      # Number of metafile units per inch
    Pad(4),
    LSInt16("checksum"),  # Checksum value for previous 10 WORDs
    SIZE=WMF_PLACEABLE_HEADER_SIZE
    )

wmf_placeable_header_switch = Switch("placeable_header",
    CASE=get_has_placeable_header,
    CASES={True: wmf_placeable_header}
    )

wmf_header = Struct('header',
    LSEnum16("filetype",
        # Type of metafile (0=memory, 1=disk)
        # some documentation says the values are
        # 0 and 1, while others say it's 1 and 2.
        # I'm going with what I've seen in example files.
        # ('memory', 1),
        # ('file',   2)
        ('memory', 0),
        ('file',   1)
        ),
    LSInt16("header_size", DEFAULT=9),  # Size of header in WORDS (always 9)
    LSInt16("version"),          # Version of Microsoft Windows used
    LSInt32("filesize"),         # Total size of the metafile in WORDs
    LSInt16("object_count"),     # Number of objects in the file
    LSInt32("max_record_size"),  # The size of largest record in WORDs
    LSInt16("num_of_params")     # Not Used (always 0)
    )


wmf_def = TagDef("wmf",
    # the first header is optional, and its
    # existance is marked by a magic number
    wmf_placeable_header_switch,
    wmf_header,
    wmf_records,

    Void("eof", POINTER=get_set_wmf_eof),

    ext='.wmf', endian="<"
)
