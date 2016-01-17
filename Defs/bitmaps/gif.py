from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.Defs.Tag_Def import *
from supyr_struct.Re_Wr_De_En import Bytes_Writer

BytesToInt = int.from_bytes

Com = Combine

def LZW_Reader(self, Desc, Parent, Raw_Data=None, Attr_Index=None,
                   Root_Offset=0, Offset=0, **kwargs):
    assert Parent is not None and Attr_Index is not None,\
           "'Parent' and 'Attr_Index' must be provided and "+\
           "not None when reading a 'Data' Field_Type."
    
    if Raw_Data is not None:
        #first byte is irrelevant to deducing the size, so add 1 to the offset
        Start = Root_Offset + Offset
        Raw_Data.seek(Start + 1)
        Blocksize = BytesToInt(Raw_Data.read(1), byteorder='little')
        Size = Blocksize + 2
        
        #if length % char_size is not zero, it means the location lies
        #between individual characters. Try again from this spot + 1
        while Blocksize > 0:
            Raw_Data.seek(Start+Size)
            Blocksize = Raw_Data.read(1)
            if not Blocksize:
                break
            Blocksize = BytesToInt(Blocksize, byteorder='little')
            Size += Blocksize + 1
        
        Raw_Data.seek(Start)
        #read and store the variable
        Parent[Attr_Index] = self.Decoder(Raw_Data.read(Size), Parent, Attr_Index)
        return Offset + Size
    else:
        Parent[Attr_Index] = self.Default()
        return Offset
    

Bytearray_LZW = Field_Type(Name="Bytearray_LZW", Default=bytearray(),
                           Raw=True, Endian='=', Size_Calc=Len_Size_Calc,
                           Reader=LZW_Reader, Writer=Bytes_Writer)

def Construct():
    return GIF_Def

class GIF_Def(Tag_Def):

    Ext = ".gif"

    Cls_ID = "gif"

    Endian = "<"

    def Color_Table_Size(*args, **kwargs):        
        '''Used for calculating the size of the color table bytes'''
        Parent = kwargs.get('Parent')
        
        if Parent is not None:
            Flags = Parent.Flags
        else:
            raise KeyError("Cannot calculate or set the size of GIF "+
                           "Color Table without a supplied Parent.")

        New_Value = kwargs.get('New_Value')
        
        if New_Value is None:
            if not Flags.Color_Table_Flag:
                return 0
            return 3*(2**(1 + Flags.Color_Table_Size))
        
        if New_Value > 3:
            Flags.Color_Table_Size = int(log((New_Value//3),2)-1)
            return
        Flags.Color_Table_Size = 0

    def Has_Next_Data_Block(*args, **kwargs):
        Raw_Data = kwargs.get('Raw_Data')
        
        if hasattr(Raw_Data, 'peek'):
            return Raw_Data.peek(1) != b';'
        return False

    def Get_Data_Block(*args, **kwargs):
        Raw_Data = kwargs.get('Raw_Data')
        if hasattr(Raw_Data, 'peek'):
            data = Raw_Data.peek(1)
            if len(data):
                return int.from_bytes(data, byteorder='little')
            return None

    def Get_Block_Extension(*args, **kwargs):
        Raw_Data = kwargs.get('Raw_Data')
        
        if hasattr(Raw_Data, 'peek'):
            data = Raw_Data.peek(2)
            if len(data) < 2:
                return None
            return int.from_bytes(data[1:2], byteorder='little')
        return None
    
    Block_Delim = { TYPE:UInt8, NAME:"Block_Delimiter",
                    VISIBLE:False, EDITABLE:False, MIN:0, MAX:0}
    
    Base_Extension = { TYPE:Container, NAME:"Extension",
                       0:{ TYPE:UInt8, NAME:"Sentinel",
                           EDITABLE:False, DEFAULT:33 },
                       1:{ TYPE:Enum8, NAME:"Label", EDITABLE:False,
                           0:{ NAME:'Plaintext_Extension',   VALUE:1 },
                           1:{ NAME:'GFX_Control_Extension', VALUE:249 },
                           2:{ NAME:'Comment_Extension',     VALUE:254 },
                           3:{ NAME:'Application_Extension', VALUE:255 }
                           },
                       2:{ TYPE:UInt8, NAME:"Byte_Size", EDITABLE:False }
                       }
    
    Unknown_Extension = Com({ NAME:"Unknown_Extension",
                              3:{ TYPE:Bytes_Raw, NAME:"Unknown_Body",
                                  SIZE:".Byte_Size" },
                              4:Block_Delim }, Base_Extension )

    
    GFX_Extension = Com({ NAME:"GFX_Control_Extension",
                          1:{ DEFAULT:249 },
                          3:{ TYPE:Bit_Struct, NAME:"Flags",
                              0:{ TYPE:Bit_UInt, NAME:'Transparent',     SIZE:1 },
                              1:{ TYPE:Bit_UInt, NAME:'User_Input',      SIZE:1 },
                              2:{ TYPE:Bit_UInt, NAME:'Disposal_Method', SIZE:3 }
                              },
                          4:{ TYPE:UInt16, NAME:"Delay_Time" },
                          5:{ TYPE:UInt8, NAME:"Transparent_Color_Index" },
                          6:Block_Delim }, Base_Extension )

    Comment_Extension = Com({ NAME:"Comment_Extension",
                              1:{ DEFAULT:254 },
                              3:{ TYPE:Str_Raw_ASCII, NAME:"Comment_String",
                                  SIZE:'.Byte_Size' },
                              4:Block_Delim }, Base_Extension )
    
    Plaintext_Extension = Com({ NAME:"Plaintext_Extension",
                                1:{ DEFAULT:1 },
                                2:{ DEFAULT:12 },
                                3:{ TYPE:UInt16, NAME:"Text_Grid_Left" },
                                4:{ TYPE:UInt16, NAME:"Text_Grid_Top" },
                                5:{ TYPE:UInt16, NAME:"Text_Grid_Width" },
                                6:{ TYPE:UInt16, NAME:"Text_Grid_Height" },
                                7:{ TYPE:UInt8, NAME:"Char_Cell_Width" },
                                8:{ TYPE:UInt8, NAME:"Char_Cell_Height" },
                                9:{ TYPE:UInt8, NAME:"Foreground_Color_Index" },
                                10:{ TYPE:UInt8, NAME:"Background_Color_Index" },
                                11:{ TYPE:UInt8, NAME:"String_Length"},
                                12:{ TYPE:Str_Raw_ASCII, NAME:"Plaintext_String",
                                     SIZE:'.String_Length' },
                                13:Block_Delim }, Base_Extension )

    App_Extension = Com({ NAME:"Application_Extension",
                          1:{ DEFAULT:255 },
                          2:{ DEFAULT:11 },
                          3:{ TYPE:Str_Raw_ASCII, NAME:"Application_ID",
                              SIZE:'.Byte_Size' },
                          4:{ TYPE:UInt8, NAME:"Data_Length"},
                          5:{ TYPE:Bytes_Raw, NAME:"Application_Data",
                              SIZE:'.Data_Length' },
                          6:Block_Delim }, Base_Extension )

    Image_Block = { TYPE:Container, NAME:"Image_Block",
                    0:{ TYPE:UInt8,  NAME:'Sentinel',
                        EDITABLE:False, DEFAULT:44 },
                    1:{ TYPE:UInt16, NAME:"Left" },
                    2:{ TYPE:UInt16, NAME:"Top" },
                    3:{ TYPE:UInt16, NAME:"Width" },
                    4:{ TYPE:UInt16, NAME:"Height" },
                    5:{ TYPE:Bit_Struct, NAME:"Flags",
                        0:{ TYPE:Bit_UInt, NAME:"Color_Table_Size", SIZE:3 },
                        1:{ TYPE:Pad, SIZE:2 },
                        2:{ TYPE:Bit_UInt, NAME:"Sort_Flag", SIZE:1 },
                        3:{ TYPE:Bit_UInt, NAME:"Interlace", SIZE:1 },
                        4:{ TYPE:Bit_UInt, NAME:"Color_Table_Flag", SIZE:1 }
                        },
                    6:{ TYPE:Bytearray_Raw, NAME:"Local_Color_Table",
                        SIZE:Color_Table_Size },
                    7:{ TYPE:Bytearray_LZW, NAME:"Image_Data" }
                    }

    Block_Extension = { TYPE:Switch, NAME:"Block_Extension",
                        DEFAULT:Unknown_Extension,
                        CASE:Get_Block_Extension,
                        CASES:{ 0:Unknown_Extension,
                                1:Plaintext_Extension,
                                249:GFX_Extension,
                                254:Comment_Extension,
                                255:App_Extension
                                }
                        }
    

    Data_Block = { TYPE:Switch, NAME:"Data_Block",
                   DEFAULT:Unknown_Extension,
                   CASE:Get_Data_Block,
                   CASES:{ 33:Block_Extension,
                           44:Image_Block }
                   }
    
    Tag_Structure = { TYPE:Container, NAME:"GIF_Image",
                      0:{ TYPE:UInt24, NAME:"GIF_Sig", DEFAULT:'GIF' },
                      1:{ TYPE:Enum24, NAME:"Version", DEFAULT:'a98',
                          0:{ NAME:"Ver_87a", VALUE:'a78' },
                          1:{ NAME:"Ver_89a", VALUE:'a98' }
                          },
                      2:{ TYPE:UInt16, NAME:"Canvas_Width" },
                      3:{ TYPE:UInt16, NAME:"Canvas_Height" },
                      4:{ TYPE:Bit_Struct, NAME:"Flags",
                          0:{ TYPE:Bit_UInt, NAME:"Color_Table_Size", SIZE:3 },
                          1:{ TYPE:Bit_UInt, NAME:"Sort_Flag", SIZE:1 },
                          2:{ TYPE:Bit_UInt, NAME:"Color_Resolution", SIZE:3 },
                          3:{ TYPE:Bit_UInt, NAME:"Color_Table_Flag", SIZE:1 }
                          },
                      5:{ TYPE:UInt8, NAME:"Background_Color_Index" },
                      6:{ TYPE:UInt8, NAME:"Pixel_Aspect_Ratio" },
                      7:{ TYPE:Bytearray_Raw, NAME:"Global_Color_Table",
                          SIZE:Color_Table_Size },
                      8:{ TYPE:While_Array, NAME:"Data_Blocks",
                          SUB_STRUCT:Data_Block,
                          CASE:Has_Next_Data_Block },
                      9:{ TYPE:UInt8, NAME:"Trailer", MIN:59, MAX:59,
                          DEFAULT:';', EDITABLE:False, VISIBLE:False }
                 }
