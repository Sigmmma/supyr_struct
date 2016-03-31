from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.defs.tag_def import *
from supyr_struct.field_methods import bytes_writer

BytesToInt = int.from_bytes

com = combine

DIB_HEADER_MIN_LEN = 12
BMP_HEADER_SIZE = 14
DIB_HEADER_DEFAULT_SIZE = 124

def get():
    return BmpDef

class BmpDef(TagDef):

    ext = ".bmp"

    def_id = "bmp"

    endian = "<"

    def bmp_color_table_size(*args, **kwargs):
        '''Used for calculating the size of the color table bytes'''
        if kwargs.get("new_value") is not None:
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return
        
        if "parent" not in kwargs:
            return 0

        header = kwargs["parent"].dib_header

        entry_size = 4
        depth = header.bpp
        if header.header_size == DIB_HEADER_MIN_LEN:
            entry_size = 3
        
        if depth >= 16:
            return 0
        
        return (2**depth)*entry_size


    def bmp_unspecified_color_table_size(*args, **kwargs):
        '''Used for calculating the size of the color table bytes'''
        if kwargs.get("new_value") is not None:
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return
        
        if "parent" not in kwargs:
            return 0
        
        bmp_image = kwargs["parent"]
        header_size = bmp_image.dib_header.header_size
        size = (bmp_image.pixels_pointer - (len(bmp_image.color_table)
                                            + header_size + BMP_HEADER_SIZE))
        if size > 0:
            return size
        return 0

    def get_dib_header(*args, **kwargs):
        raw_data = kwargs.get('raw_data')
        
        if hasattr(raw_data, 'peek'):
            return BytesToInt(raw_data.peek(4), byteorder='little')
        else:
            return DIB_HEADER_DEFAULT_SIZE
            #raise KeyError("Cannot determine bmp dib header "+
            #               "version without supplying raw_data.")


    def dib_header_remainder(*args, **kwargs):
        parent = kwargs.get('parent')
        
        if parent is None:
            raise KeyError("Cannot calculate or set the size of bmp"+
                           "dib header without a supplied block.")

        new_value = kwargs.get('new_value')
        
        if new_value is None:
            return parent.header_size - DIB_HEADER_MIN_LEN
        parent.header_size = DIB_HEADER_MIN_LEN + new_value
        


    bitmap_core_header = { TYPE:Struct, NAME:"bitmap_core_header",
                           0:{ TYPE:UInt32, NAME:"header_size",
                               DEFAULT:DIB_HEADER_MIN_LEN },
                           1:{ TYPE:UInt16, NAME:"image_width" },
                           2:{ TYPE:UInt16, NAME:"image_height" },
                           3:{ TYPE:UInt16, NAME:"color_planes", DEFAULT:1 },
                           4:{ TYPE:UInt16, NAME:"bpp" }
                           }

    unknown_dib_header = com({ NAME:"unknown_dib_header",
                               CHILD:{ TYPE:BytesRaw, NAME:"unknown_data",
                                       SIZE:dib_header_remainder }
                               }, bitmap_core_header )

    bitmap_info_header = com({ NAME:"bitmap_info_header",
                               0:{ DEFAULT:40 },
                               1:{ TYPE:SInt32 },
                               2:{ TYPE:SInt32 },
                               5:{ TYPE:Enum32, NAME:"compression_method",
                                   0:{ NAME:"RGB",            VALUE:0 },
                                   1:{ NAME:"RLE8",           VALUE:1 },
                                   2:{ NAME:"RLE4",           VALUE:2 },
                                   3:{ NAME:"BITFIELDS",      VALUE:3 },
                                   4:{ NAME:"JPEG",           VALUE:4 },
                                   5:{ NAME:"PNG",            VALUE:5 },
                                   6:{ NAME:"ALPHABITFIELDS", VALUE:6 },
                                   7:{ NAME:"CMYK",           VALUE:11 },
                                   8:{ NAME:"CMYKRLE8",       VALUE:12 },
                                   9:{ NAME:"CMYKRLE4",       VALUE:13 }
                                   },
                               6:{ TYPE:UInt32, NAME:"image_size" },
                               7:{ TYPE:SInt32, NAME:"h_res" },#pixels per meter
                               8:{ TYPE:SInt32, NAME:"v_res" },#pixels per meter
                               9:{ TYPE:UInt32, NAME:"palette_count" },
                               10:{ TYPE:UInt32, NAME:"palette_colors_used" }
                               }, bitmap_core_header )

    bitmap_v2_header = com({ NAME:"bitmap_v2_header",
                             0:{ DEFAULT:52 },
                             11:{ TYPE:UInt32, NAME:"red_mask" },
                             12:{ TYPE:UInt32, NAME:"green_mask" },
                             13:{ TYPE:UInt32, NAME:"blue_mask" },
                             }, bitmap_info_header )

    bitmap_v3_header = com({ NAME:"bitmap_v3_header",
                             0:{ DEFAULT:56 },
                             14:{ TYPE:UInt32, NAME:"alpha_mask" }
                             }, bitmap_v2_header )

    bitmap_v4_header = com({ NAME:"bitmap_v4_header",
                             0:{ DEFAULT:108 },
                             15:{ TYPE:Enum32, NAME:"color_space_type",
                                  0:{ NAME:"CALIBRATED_RGB", VALUE:0 }
                                  },
                             16:{ TYPE:Struct, NAME:"endpoints",
                                  #Each of these colors is actually a set of
                                  #3 fixed point numbers with 2 bits for the
                                  #integer part and 30 bits for the fraction.
                                  #Since such a Field is not implemented,
                                  #they will just be read as raw bytes for now.
                                  0:{ TYPE:BytesRaw, NAME:"cie_xyz_red",   SIZE:12 },
                                  1:{ TYPE:BytesRaw, NAME:"cie_xyz_green", SIZE:12 },
                                  2:{ TYPE:BytesRaw, NAME:"cie_xyz_blue",  SIZE:12 }
                                  },
                             #each of these gamma attributes is a fixed point
                             #number with 16 bits for the integer part and
                             #16 bits for the fractional part. Since such a
                             #Field is not implemented, they will just
                             #be read as raw bytes for now.
                             17:{ TYPE:BytesRaw, NAME:"gamma_red",   SIZE:4 },
                             18:{ TYPE:BytesRaw, NAME:"gamma_green", SIZE:4 },
                             19:{ TYPE:BytesRaw, NAME:"gamma_blue",  SIZE:4 },
                             }, bitmap_v3_header )

    bitmap_v5_header = com({ NAME:"bitmap_v5_header",
                             0:{ DEFAULT:124 },
                             15:{ 0:{ NAME:"CALIBRATED_RGB", VALUE:0 },
                                  1:{ NAME:"sRGB",     VALUE:'sRGB' },
                                  2:{ NAME:"WINDOWS",  VALUE:'Win ' },
                                  3:{ NAME:"LINKED",   VALUE:'LINK' },
                                  4:{ NAME:"EMBEDDED", VALUE:'MBED' }
                                  },
                             20:{ TYPE:Enum32, NAME:"intent",
                                  0:{ NAME:"None",     VALUE:0 },
                                  1:{ NAME:"BUSINESS", VALUE:1 },
                                  2:{ NAME:"GRAPHICS", VALUE:2 },
                                  3:{ NAME:"IMAGES",   VALUE:4 },
                                  4:{ NAME:"ABS_COLORIMETRIC", VALUE:8 }
                                  },
                             21:{ TYPE:Pointer32, NAME:"profile_data_pointer" },
                             22:{ TYPE:UInt32,    NAME:"profile_size" },
                             23:{ TYPE:UInt32,    NAME:"reserved" }
                             }, bitmap_v4_header )

    dib_header = { TYPE:Switch, NAME:"dib_header",
                   DEFAULT:unknown_dib_header,
                   CASE:get_dib_header,
                   CASES:{ 12:bitmap_core_header,
                           40:bitmap_info_header,
                           52:bitmap_v2_header,
                           56:bitmap_v3_header,
                           108:bitmap_v4_header,
                           124:bitmap_v5_header,
                           }
                   }
    
    descriptor = { TYPE:Container, NAME:"bmp_image",
                      0:{ TYPE:Enum16, NAME:"bmp_type",
                          DEFAULT:'MB',
                          0:{ NAME:"bitmap",        VALUE:'MB' },
                          1:{ NAME:"bitmap_array",  VALUE:'AB' },
                          2:{ NAME:"color_icon",    VALUE:'IC' },
                          3:{ NAME:"color_pointer", VALUE:'PC' },
                          4:{ NAME:"icon",          VALUE:'CI' },
                          5:{ NAME:"pointer",       VALUE:'TP' }
                          },
                      1:{ TYPE:UInt32, NAME:"filelength" },
                      2:{ TYPE:UInt32, NAME:"reserved" },
                      3:{ TYPE:Pointer32, NAME:"pixels_pointer" },
                      4:dib_header,
                      5:{ TYPE:BytesRaw, NAME:'color_table',
                          SIZE:bmp_color_table_size },
                      6:{ TYPE:BytesRaw, NAME:'unspecified_color_table',
                          SIZE:bmp_unspecified_color_table_size },
                      7:{ TYPE:BytesRaw, NAME:"pixels",
                          #rather than try to compute the size based on
                          #the various different compression methods and
                          #versions, it is easier to just read the rest
                          #of the file into a bytes object and let the
                          #user decide what to do with any extra data.
                          SIZE:remaining_data_length,
                          POINTER:'.pixels_pointer' },
                      8:{ TYPE:Void, NAME:"eof", POINTER:'.filelength' }
                 }
