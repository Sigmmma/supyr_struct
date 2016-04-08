'''
    tga image file

    Structures were pieced together from various online sources
'''
from supyr_struct.defs.tag_def import *


def get(): return tga_def

def tga_color_table_size(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, *args, **kwargs):
    if new_value is not None:
        #it isnt possible to set the size because the size is
        #derived from multiple source inputs and must be set
        #manually. This is expected to happen for some types
        #of structures, so rather than raise an error, just do
        #nothing since this is normal and the user handles it
        return
    
    '''Used for calculating the size of the color table bytes'''
    if parent is None:
        raise KeyError("Cannot calculate the size of TGA "+
                       "Color Table without a supplied Block.")
    header = parent.header

    if not header.has_color_map:
        return 0
    elif header.color_map_depth in (15, 16):
        return 2 * header.color_map_length
    return header.color_map_depth * header.color_map_length // 8


def tga_pixel_bytes_size(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, *args, **kwargs):
    if new_value is not None:
        #it isnt possible to set the size because the size is
        #derived from multiple source inputs and must be set
        #manually. This is expected to happen for some types
        #of structures, so rather than raise an error, just do
        #nothing since this is normal and the user handles it
        return
    
    '''Used for calculating the size of the pixel data bytes'''
    if parent is None:
        raise KeyError("Cannot calculate the size of TGA "+
                       "Pixels without without a supplied Block.")
    
    header = parent.header
    pixels     = header.width * header.height
    image_type = header.image_type

    if image_type.rle_compressed:
        raise NotImplementedError("RLE Compressed TGA files are not able "+
                                  "to be opened. \nOpening requires "+
                                  "decompressing until Width*Height "+
                                  "pixels have been decompressed.")
    elif image_type.format == 0:
        return pixels // 8
    elif header.bpp in (15, 16):
        return 2 * pixels
    return header.bpp * pixels // 8

tga_header = Struct("header",
    UInt8("image_id_length"),
    UEnum8("has_color_map",
        "no",
        "yes"
        ),
    LBitStruct("image_type",
        BitUEnum("format",
            "bw_1_bit",
            "color_mapped_rgb",
            "unmapped_rgb",
            SIZE=2
            ),
        Pad(1),
        Bit("rle_compressed"),
        Pad(4),
        ),
    LUInt16("color_map_origin"),
    LUInt16("color_map_length"),
    UInt8("color_map_depth"),
    LUInt16("image_origin_x"),
    LUInt16("image_origin_y"),
    LUInt16("width"),
    LUInt16("height"),
    UInt8("bpp"),
    LBitStruct("image_descriptor",
        BitUInt("alpha_bit_count", SIZE=4),
        Pad(1),
        BitUEnum("screen_origin",
            "lower_left",
            "upper_left",
            SIZE=1
            ),
        BitUEnum("interleaving",
            "none",
            "two_way",
            "four_way",
            SIZE=2
            )
        )
    )

#create the definition that builds tga files
tga_def = TagDef(
    tga_header,
    BytesRaw('image_id',       SIZE='.header.image_id_length'),
    BytesRaw('color_table',    SIZE=tga_color_table_size ),
    BytesRaw('pixel_data',     SIZE=tga_pixel_bytes_size ),
    BytesRaw('remaining_data', SIZE=remaining_data_length ),

    NAME='tga_image',
    def_id="tga", ext=".tga"
    )
