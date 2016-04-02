from supyr_struct.defs.tag_def import *


def get(): return tga_def

def tga_color_table_size(*args, **kwargs):
    if kwargs.get("new_value") is not None:
        #it isnt possible to set the size because the size is
        #derived from multiple source inputs and must be set
        #manually. This is expected to happen for some types
        #of structures, so rather than raise an error, just do
        #nothing since this is normal and the user handles it
        return
    
    '''Used for calculating the size of the color table bytes'''
    if "parent" not in kwargs:
        raise KeyError("Cannot calculate the size of TGA "+
                       "Color Table without a supplied Block.")

    header = kwargs["parent"].header
    
    if not header.has_color_map:
        return 0
    else:
        depth = header.color_map_depth
        if depth == 15:
            depth = 16
        
        return (depth//8) * header.color_map_length


def tga_pixel_bytes_size(*args, **kwargs):
    if kwargs.get("new_value") is not None:
        #it isnt possible to set the size because the size is
        #derived from multiple source inputs and must be set
        #manually. This is expected to happen for some types
        #of structures, so rather than raise an error, just do
        #nothing since this is normal and the user handles it
        return
    
    '''Used for calculating the size of the pixel data bytes'''
    if "parent" not in kwargs:
        raise KeyError("Cannot calculate the size of TGA "+
                       "Pixels without without a supplied Block.")
    
    header = kwargs["parent"].header

    pixels = header.width * header.height
    image_type = header.image_type

    if image_type.rle_compressed:
        raise NotImplementedError("RLE Compressed TGA files are not able "+
                                  "to be opened. \nOpening requires "+
                                  "decompressing until Width*Height "+
                                  "pixels have been decompressed.")
    elif image_type.format == 0:
        return pixels//8
    else:
        bpp = header.bpp
        if bpp == 15:
            bpp = 16
        
        return (bpp * pixels) // 8

#create the definition that builds tga files
tga_def = TagDef( Struct("header",
                      UInt8("image_id_length"),
                      Enum8("has_color_map",
                          "no",
                          "yes"
                          ),
                      BitStruct("image_type",
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
                      UInt16("color_map_origin"),
                      UInt16("color_map_length"),
                      UInt8("color_map_depth"),
                      UInt16("image_origin_x"),
                      UInt16("image_origin_y"),
                      UInt16("width"),
                      UInt16("height"),
                      UInt8("bpp"),
                      BitStruct("image_descriptor",
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
                          ),
                      SIZE=18 ),
                  BytesRaw('image_id',       SIZE='.header.image_id_length'),
                  BytesRaw('color_table',    SIZE=tga_color_table_size ),
                  BytesRaw('pixel_data',     SIZE=tga_pixel_bytes_size ),
                  BytesRaw('remaining_data', SIZE=remaining_data_length ),
                  
                  NAME='tga_image',
                  def_id="tga", ext=".tga", endian="<" )
