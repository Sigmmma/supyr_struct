from supyr_struct.defs.tag_def import *


def get():
    return TgaDef

class TgaDef(TagDef):

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

    
    ext = ".tga"

    def_id = "tga"

    endian = "<"
    
    descriptor = { TYPE:Container, NAME:"tga_image",
                    0:{ TYPE:Struct, NAME:"header", SIZE:18,
                        0:{ TYPE:UInt8, NAME:"image_id_length"},
                        1:{ TYPE:Enum8, NAME:"has_color_map",
                            0:"no",
                            1:"yes"
                            },
                        2:{ TYPE:BitStruct, NAME:"image_type",
                            0:{ TYPE:BitUEnum, NAME:"format", SIZE:2,
                                0:"bw_1_bit",
                                1:"color_mapped_rgb",
                                2:"unmapped_rgb"
                                },
                            1:{ TYPE:Pad, SIZE:1 },
                            2:{ TYPE:Bit, NAME:"rle_compressed" }
                            },
                        3:{ TYPE:UInt16, NAME:"color_map_origin" },
                        4:{ TYPE:UInt16, NAME:"color_map_length" },
                        5:{ TYPE:UInt8,  NAME:"color_map_depth" },
                        6:{ TYPE:UInt16, NAME:"image_origin_x" },
                        7:{ TYPE:UInt16, NAME:"image_origin_y" },
                        8:{ TYPE:UInt16, NAME:"width" },
                        9:{ TYPE:UInt16, NAME:"height" },
                        10:{ TYPE:UInt8, NAME:"bpp" },
                        11:{ TYPE:BitStruct, NAME:"image_descriptor",
                             0:{ TYPE:BitUInt, NAME:"alpha_bit_count", SIZE:4},
                             1:{ TYPE:Pad, SIZE:1 },
                             2:{ TYPE:BitUEnum, NAME:"screen_origin", SIZE:1,
                                 0:"lower_left",
                                 1:"upper_left"
                                 },
                             3:{ TYPE:BitUEnum, NAME:"interleaving", SIZE:2,
                                 0:"none",
                                 1:"two_way",
                                 2:"four_way",
                                 }
                            }
                        },
                        1:{ TYPE:BytesRaw, NAME:'image_id',
                            SIZE:'.header.image_id_length' },
                        2:{ TYPE:BytesRaw, NAME:'color_table',
                            SIZE:tga_color_table_size },
                        3:{ TYPE:BytesRaw, NAME:'pixel_data',
                            SIZE:tga_pixel_bytes_size },
                        4:remaining_data
                        }

    '''
    descriptor = Container("tga_image",
                     Struct("header",
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
                                 )
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
                     BytesRaw('remaining_data', SIZE=remaining_data_length )
                     )
    '''
