from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.Defs.Tag_Def import *
from supyr_struct.Re_Wr_De_En import Bytes_Writer

BytesToInt = int.from_bytes

Com = Combine

DIB_HEADER_MIN_LEN = 12

def Construct():
    return GIF_Def

class GIF_Def(Tag_Def):

    Ext = ".bmp"

    Cls_ID = "bmp"

    Endian = "<"

    def Get_DIB_Header(*args, **kwargs):
        Raw_Data = kwargs.get('Raw_Data')
        
        if hasattr(Raw_Data, 'peek'):
            return BytesToInt(Raw_Data.peek(4), byteorder='little')
        else:
            raise KeyError("Cannot determine BMP DIB Header "+
                           "version without supplying Raw_Data.")


    def DIB_Header_Remainder(*args, **kwargs):
        Parent = kwargs.get('Parent')
        
        if Parent is None:
            raise KeyError("Cannot calculate or set the size of BMP"+
                           "DIB Header without a supplied Block.")

        New_Value = kwargs.get('New_Value')
        
        if New_Value is None:
            return Parent.Header_Size - DIB_HEADER_MIN_LEN
        Parent.Header_Size = DIB_HEADER_MIN_LEN + New_Value
        


    Bitmap_Core_Header = { TYPE:Struct, NAME:"Bitmap_Core_Header",
                           0:{ TYPE:UInt32, NAME:"Header_Size",
                               DEFAULT:DIB_HEADER_MIN_LEN },
                           1:{ TYPE:UInt16, NAME:"Image_Width" },
                           2:{ TYPE:UInt16, NAME:"Image_Height" },
                           3:{ TYPE:UInt16, NAME:"Color_Planes", DEFAULT:1 },
                           4:{ TYPE:UInt16, NAME:"BPP" }
                           }

    Unknown_DIB_Header = Com({ NAME:"Unknown_DIB_Header",
                               CHILD:{ TYPE:Bytes_Raw, NAME:"Unknown_Data",
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
                                  #Since such a Field_Type is not implemented,
                                  #they will just be read as raw bytes for now.
                                  0:{ TYPE:Bytes_Raw, NAME:"CIE_XYZ_Red",   SIZE:12 },
                                  1:{ TYPE:Bytes_Raw, NAME:"CIE_XYZ_Green", SIZE:12 },
                                  2:{ TYPE:Bytes_Raw, NAME:"CIE_XYZ_Blue",  SIZE:12 }
                                  },
                             #each of these gamma attributes is a fixed point
                             #number with 16 bits for the integer part and
                             #16 bits for the fractional part. Since such a
                             #Field_Type is not implemented, they will just
                             #be read as raw bytes for now.
                             17:{ TYPE:Bytes_Raw, NAME:"Gamma_Red",   SIZE:4 },
                             18:{ TYPE:Bytes_Raw, NAME:"Gamma_Green", SIZE:4 },
                             19:{ TYPE:Bytes_Raw, NAME:"Gamma_Blue",  SIZE:4 },
                             }, Bitmap_V3_Header )

    Bitmap_V5_Header = Com({ NAME:"Bitmap_V5_Header",
                             0:{ DEFAULT:124 },
                             15:{ 0:{ NAME:"CALIBRATED_RGB", VALUE:0 },
                                  1:{ NAME:"sRGB",     VALUE:StrToInt('sRGB', '>')},
                                  2:{ NAME:"WINDOWS",  VALUE:StrToInt('Win ', '>')},
                                  3:{ NAME:"LINKED",   VALUE:StrToInt('LINK', '>')},
                                  4:{ NAME:"EMBEDDED", VALUE:StrToInt('MBED', '>')}
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
                             23:{ PAD:4 }
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
    
    Tag_Structure = { TYPE:Container, NAME:"BMP_Image",
                      0:{ TYPE:Enum16, NAME:"BMP_Type",
                          DEFAULT:StrToInt('BM'),
                          0:{ NAME:"Bitmap",        VALUE:StrToInt('BM') },
                          1:{ NAME:"Bitmap_Array",  VALUE:StrToInt('BA') },
                          2:{ NAME:"Color_Icon",    VALUE:StrToInt('CI') },
                          3:{ NAME:"Color_Pointer", VALUE:StrToInt('CP') },
                          4:{ NAME:"Icon",          VALUE:StrToInt('IC') },
                          5:{ NAME:"Pointer",       VALUE:StrToInt('PT') }
                          },
                      1:{ TYPE:UInt32, NAME:"File_Length" },
                      2:{ TYPE:UInt32, NAME:"Reserved" },
                      3:{ TYPE:Pointer32, NAME:"Pixel_Data_Pointer" },
                      4:DIB_Header,
                      5:Remaining_Data
                 }
