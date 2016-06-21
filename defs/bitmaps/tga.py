'''
    tga image file

    Structures were pieced together from various online sources
'''
from supyr_struct.defs.tag_def import *
from supyr_struct.buffer import BytearrayBuffer

def get(): return tga_def

#it isnt possible to set the size in the below functions
#because the size is derived from multiple source inputs
#and must be set manually. This is expected to happen for
#some types of structures, so rather than raise an error,
#do nothing since this is normal and the user handles it

def tga_color_table_size(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, *args, **kwargs):
    '''Used for calculating the size of the color table bytes'''
    if new_value is not None:
        return
    if parent is None:
        raise KeyError("Cannot calculate the size of tga "+
                       "color table without a supplied Block.")
    if attr_index is not None and hasattr(parent[attr_index], '__len__'):
        return len(parent[attr_index])
    header = parent.header

    if not header.has_color_map:
        return 0
    elif header.color_map_depth in (15, 16):
        return 2 * header.color_map_length
    return header.color_map_depth * header.color_map_length // 8


def tga_pixel_bytes_size(block=None, parent=None, attr_index=None,
                         rawdata=None, new_value=None, *args, **kwargs):
    '''Used for calculating the size of the pixel data bytes'''
    if new_value is not None:
        return
    if parent is None:
        raise KeyError("Cannot calculate the size of tga "+
                       "pixels without without a supplied Block.")
    if attr_index is not None and hasattr(parent[attr_index], '__len__'):
        return len(parent[attr_index])
    
    header = parent.PARENT.header
    pixels = header.width * header.height
    image_type = header.image_type

    if image_type.format == 0:
        return pixels // 8
    elif header.bpp in (15, 16):
        return 2 * pixels
    return header.bpp * pixels // 8

def read_rle_stream(parent, rawdata, root_offset=0, offset=0, **kwargs):
    if parent is None:
        raise KeyError("Cannot calculate the size of tga "+
                       "pixels without without a supplied Block.")
    
    header = parent.PARENT.header
    pixels_count = header.width * header.height
    image_type   = header.image_type

    bpp = header.bpp // 8
    if header.bpp == 15:
        bpp = 2
        
    start = root_offset+offset
    bytes_count = pixels_count * bpp

    if image_type.rle_compressed:
        pixels = BytearrayBuffer([0]*bytes_count)

        comp_bytes_count = curr_pixel = 0
        rawdata.seek(start)
        
        while curr_pixel < pixels_count:
            packet_header = rawdata.read(1)[0]
            if packet_header&128:
                #this packet is compressed with RLE
                pixels.write(rawdata.read(bpp)*(packet_header-127))
                comp_bytes_count += 1 + bpp
                curr_pixel += packet_header-127
            else:
                #it's a raw packet
                pixels.write(rawdata.read((packet_header+1)*bpp))
                comp_bytes_count += 1 + (packet_header+1)*bpp
                curr_pixel += packet_header+1
        
        return pixels, comp_bytes_count
    else:
        return BytearrayBuffer(rawdata[start:start+bytes_count]), bytes_count


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
            "bw_8_bit",
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
    BytesRaw('image_id',    SIZE='.header.image_id_length'),
    BytesRaw('color_table', SIZE=tga_color_table_size ),
    StreamAdapter('pixels_wrapper',
        SUB_STRUCT=BytesRaw('pixels', SIZE=tga_pixel_bytes_size ),
        DECODER=read_rle_stream ),
    BytesRaw('remaining_data', SIZE=remaining_data_length ),

    NAME='tga_image',
    def_id="tga", ext=".tga"
    )
