from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.defs.tag_def import *
from supyr_struct.field_methods import bytes_writer

BytesToInt = int.from_bytes

Com = combine

DIB_HEADER_MIN_LEN = 12
BMP_HEADER_SIZE = 14
DIB_HEADER_DEFAULT_SIZE = 124

def get():
    return BmpDef

class BmpDef(TagDef):

    ext = ".bmp"

    tag_id = "bmp"

    endian = "<"

    def BMP_Color_Table_Size(*args, **kwargs):
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

        Header = kwargs["parent"].DIB_Header

        Entry_Size = 4
        Depth = Header.BPP
        if Header.Header_Size == DIB_HEADER_MIN_LEN:
            Entry_Size = 3
        
        if Depth >= 16:
            return 0
        
        return (2**Depth)*Entry_Size


    def BMP_Unspecified_Color_Table_Size(*args, **kwargs):
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
        
        BMP_Image = kwargs["parent"]
        Header_Size = BMP_Image.DIB_Header.Header_Size
        size = (BMP_Image.Pixels_Pointer - (len(BMP_Image.Color_Table)
                                            + Header_Size + BMP_HEADER_SIZE))
        if size > 0:
            return size
        return 0

    def Get_DIB_Header(*args, **kwargs):
        raw_data = kwargs.get('raw_data')
        
        if hasattr(raw_data, 'peek'):
            return BytesToInt(raw_data.peek(4), byteorder='little')
        else:
            return DIB_HEADER_DEFAULT_SIZE
            #raise KeyError("Cannot determine BMP DIB Header "+
            #               "version without supplying raw_data.")


    def DIB_Header_Remainder(*args, **kwargs):
        parent = kwargs.get('parent')
        
        if parent is None:
            raise KeyError("Cannot calculate or set the size of BMP"+
                           "DIB Header without a supplied block.")

        new_value = kwargs.get('new_value')
        
        if new_value is None:
            return parent.Header_Size - DIB_HEADER_MIN_LEN
        parent.Header_Size = DIB_HEADER_MIN_LEN + new_value
        


    Bitmap_Core_Header = { TYPE:Struct, NAME:"Bitmap_Core_Header",
                           0:{ TYPE:UInt32, NAME:"Header_Size",
                               DEFAULT:DIB_HEADER_MIN_LEN },
                           1:{ TYPE:UInt16, NAME:"Image_Width" },
                           2:{ TYPE:UInt16, NAME:"Image_Height" },
                           3:{ TYPE:UInt16, NAME:"Color_Planes", DEFAULT:1 },
                           4:{ TYPE:UInt16, NAME:"BPP" }
                           }

    Unknown_DIB_Header = Com({ NAME:"Unknown_DIB_Header",
                               CHILD:{ TYPE:BytesRaw, NAME:"Unknown_Data",
                                       SIZE:DIB_Header_Remainder }
                               }, Bitmap_Core_Header )

    Bitmap_Info_Header = Com({ NAME:"Bitmap_Info_Header",
                               0:{ DEFAULT:40 },
                               1:{ TYPE:SInt32 },
                               2:{ TYPE:SInt32 },
                               5:{ TYPE:Enum32, NAME:"Compression_Method",
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
                               6:{ TYPE:UInt32, NAME:"Image_Size" },
                               7:{ TYPE:SInt32, NAME:"H_Res" },#pixels per meter
                               8:{ TYPE:SInt32, NAME:"V_Res" },#pixels per meter
                               9:{ TYPE:UInt32, NAME:"Palette_Count" },
                               10:{ TYPE:UInt32, NAME:"Palette_Colors_Used" }
                               }, Bitmap_Core_Header )

    Bitmap_V2_Header = Com({ NAME:"Bitmap_V2_Header",
                             0:{ DEFAULT:52 },
                             11:{ TYPE:UInt32, NAME:"Red_Mask" },
                             12:{ TYPE:UInt32, NAME:"Green_Mask" },
                             13:{ TYPE:UInt32, NAME:"Blue_Mask" },
                             }, Bitmap_Info_Header )

    Bitmap_V3_Header = Com({ NAME:"Bitmap_V3_Header",
                             0:{ DEFAULT:56 },
                             14:{ TYPE:UInt32, NAME:"Alpha_Mask" }
                             }, Bitmap_V2_Header )

    Bitmap_V4_Header = Com({ NAME:"Bitmap_V4_Header",
                             0:{ DEFAULT:108 },
                             15:{ TYPE:Enum32, NAME:"Color_Space_Type",
                                  0:{ NAME:"CALIBRATED_RGB", VALUE:0 }
                                  },
                             16:{ TYPE:Struct, NAME:"Endpoints",
                                  #Each of these colors is actually a set of
                                  #3 fixed point numbers with 2 bits for the
                                  #integer part and 30 bits for the fraction.
                                  #Since such a Field is not implemented,
                                  #they will just be read as raw bytes for now.
                                  0:{ TYPE:BytesRaw, NAME:"CIE_XYZ_Red",   SIZE:12 },
                                  1:{ TYPE:BytesRaw, NAME:"CIE_XYZ_Green", SIZE:12 },
                                  2:{ TYPE:BytesRaw, NAME:"CIE_XYZ_Blue",  SIZE:12 }
                                  },
                             #each of these gamma attributes is a fixed point
                             #number with 16 bits for the integer part and
                             #16 bits for the fractional part. Since such a
                             #Field is not implemented, they will just
                             #be read as raw bytes for now.
                             17:{ TYPE:BytesRaw, NAME:"Gamma_Red",   SIZE:4 },
                             18:{ TYPE:BytesRaw, NAME:"Gamma_Green", SIZE:4 },
                             19:{ TYPE:BytesRaw, NAME:"Gamma_Blue",  SIZE:4 },
                             }, Bitmap_V3_Header )

    Bitmap_V5_Header = Com({ NAME:"Bitmap_V5_Header",
                             0:{ DEFAULT:124 },
                             15:{ 0:{ NAME:"CALIBRATED_RGB", VALUE:0 },
                                  1:{ NAME:"sRGB",     VALUE:'sRGB' },
                                  2:{ NAME:"WINDOWS",  VALUE:'Win ' },
                                  3:{ NAME:"LINKED",   VALUE:'LINK' },
                                  4:{ NAME:"EMBEDDED", VALUE:'MBED' }
                                  },
                             20:{ TYPE:Enum32, NAME:"Intent",
                                  0:{ NAME:"None",     VALUE:0 },
                                  1:{ NAME:"BUSINESS", VALUE:1 },
                                  2:{ NAME:"GRAPHICS", VALUE:2 },
                                  3:{ NAME:"IMAGES",   VALUE:4 },
                                  4:{ NAME:"ABS_COLORIMETRIC", VALUE:8 }
                                  },
                             21:{ TYPE:Pointer32, NAME:"Profile_Data_Pointer" },
                             22:{ TYPE:UInt32,    NAME:"Profile_Size" },
                             23:{ TYPE:UInt32,    NAME:"Reserved" }
                             }, Bitmap_V4_Header )

    DIB_Header = { TYPE:Switch, NAME:"DIB_Header",
                   DEFAULT:Unknown_DIB_Header,
                   CASE:Get_DIB_Header,
                   CASES:{ 12:Bitmap_Core_Header,
                           40:Bitmap_Info_Header,
                           52:Bitmap_V2_Header,
                           56:Bitmap_V3_Header,
                           108:Bitmap_V4_Header,
                           124:Bitmap_V5_Header,
                           }
                   }
    
    descriptor = { TYPE:Container, NAME:"BMP_Image",
                      0:{ TYPE:Enum16, NAME:"BMP_Type",
                          DEFAULT:'MB',
                          0:{ NAME:"Bitmap",        VALUE:'MB' },
                          1:{ NAME:"Bitmap_Array",  VALUE:'AB' },
                          2:{ NAME:"Color_Icon",    VALUE:'IC' },
                          3:{ NAME:"Color_Pointer", VALUE:'PC' },
                          4:{ NAME:"Icon",          VALUE:'CI' },
                          5:{ NAME:"Pointer",       VALUE:'TP' }
                          },
                      1:{ TYPE:UInt32, NAME:"File_Length" },
                      2:{ TYPE:UInt32, NAME:"Reserved" },
                      3:{ TYPE:Pointer32, NAME:"Pixels_Pointer" },
                      4:DIB_Header,
                      5:{ TYPE:BytesRaw, NAME:'Color_Table',
                          SIZE:BMP_Color_Table_Size },
                      6:{ TYPE:BytesRaw, NAME:'Unspecified_Color_Table',
                          SIZE:BMP_Unspecified_Color_Table_Size },
                      7:{ TYPE:BytesRaw, NAME:"Pixels",
                          #rather than try to compute the size based on
                          #the various different compression methods and
                          #versions, it is easier to just read the rest
                          #of the file into a bytes object and let the
                          #user decide what to do with any extra data.
                          SIZE:remaining_data_length,
                          POINTER:'.Pixels_Pointer' },
                      8:{ TYPE:Pass, NAME:"EOF", POINTER:'.File_Length' }
                 }
