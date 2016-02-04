from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.defs.tag_def import *
from supyr_struct.field_methods import *

com = combine

def LZW_Reader(self, desc, parent, raw_data=None, attr_index=None,
               root_offset=0, offset=0, **kwargs):
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'Data' Field."
    
    if raw_data is not None:
        #first byte is irrelevant to deducing the size, so add 1 to the offset
        start = root_offset + offset
        raw_data.seek(start + 1)
        blocksize = int.from_bytes(raw_data.read(1), byteorder='little')
        size = blocksize + 2
        
        #if length % char_size is not zero, it means the location lies
        #between individual characters. Try again from this spot + 1
        while blocksize > 0:
            raw_data.seek(start+size)
            blocksize = raw_data.read(1)
            if not blocksize:
                break
            blocksize = int.from_bytes(blocksize, byteorder='little')
            size += blocksize + 1
        
        raw_data.seek(start)
        #read and store the variable
        parent[attr_index] = self.decoder(raw_data.read(size),parent,attr_index)
        return offset + size
    else:
        parent[attr_index] = self.default()
        return offset
    

Bytearray_LZW = Field( name="Bytearray_LZW", default=bytearray(),
                       raw=True, endian='=', sizecalc=len_sizecalc,
                       reader=LZW_Reader, writer=bytes_writer)

def get():
    return GifDef

class GifDef(TagDef):

    ext = ".gif"

    tag_id = "gif"

    endian = "<"

    def color_table_size(*args, **kwargs):        
        '''Used for calculating the size of the color table bytes'''
        parent = kwargs.get('parent')
        
        if parent is not None:
            flags = parent.flags
        else:
            raise KeyError("Cannot calculate or set the size of GIF "+
                           "Color Table without a supplied parent.")

        new_value = kwargs.get('new_value')
        
        if new_value is None:
            if not flags.Color_Table:
                return 0
            return 3*(2**(1 + flags.color_table_size))
        
        if new_value > 3:
            flags.color_table_size = int(log((new_value//3),2)-1)
            return
        flags.color_table_size = 0

    def has_next_data_block(*args, **kwargs):
        raw_data = kwargs.get('raw_data')
        
        if hasattr(raw_data, 'peek'):
            return raw_data.peek(1) != b';'
        return False

    def get_data_block(*args, **kwargs):
        raw_data = kwargs.get('raw_data')
        if hasattr(raw_data, 'peek'):
            data = raw_data.peek(1)
            if len(data):
                return int.from_bytes(data, byteorder='little')
            return None

    def get_block_extension(*args, **kwargs):
        raw_data = kwargs.get('raw_data')
        
        if hasattr(raw_data, 'peek'):
            data = raw_data.peek(2)
            if len(data) < 2:
                return None
            return int.from_bytes(data[1:2], byteorder='little')
        return None
    
    block_delim = { TYPE:UInt8, NAME:"Block_Delimiter",
                    VISIBLE:False, EDITABLE:False, MIN:0, MAX:0}
    
    base_extension = { TYPE:Container, NAME:"Extension",
                       0:{ TYPE:UInt8, NAME:"Sentinel",
                           EDITABLE:False, DEFAULT:33 },
                       1:{ TYPE:Enum8, NAME:"Label", EDITABLE:False,
                           0:{ NAME:'plaintext_extension',   VALUE:1 },
                           1:{ NAME:'GFX_Control_Extension', VALUE:249 },
                           2:{ NAME:'comment_extension',     VALUE:254 },
                           3:{ NAME:'Application_Extension', VALUE:255 }
                           },
                       2:{ TYPE:UInt8, NAME:"Byte_Size", EDITABLE:False }
                       }
    
    unknown_extension = com({ NAME:"unknown_extension",
                              3:{ TYPE:BytesRaw, NAME:"Unknown_Body",
                                  SIZE:".Byte_Size" },
                              4:block_delim }, base_extension )

    
    gfx_extension = com({ NAME:"GFX_Control_Extension",
                          1:{ DEFAULT:249 },
                          3:{ TYPE:BitStruct, NAME:"flags",
                              0:{ TYPE:Bit,      NAME:'Transparent' },
                              1:{ TYPE:Bit,      NAME:'User_Input' },
                              2:{ TYPE:BitUInt, NAME:'Disposal_Method', SIZE:3 }
                              },
                          4:{ TYPE:UInt16, NAME:"Delay_Time" },
                          5:{ TYPE:UInt8, NAME:"Transparent_Color_Index" },
                          6:block_delim }, base_extension )

    comment_extension = com({ NAME:"comment_extension",
                              1:{ DEFAULT:254 },
                              3:{ TYPE:StrRawAscii, NAME:"Comment_String",
                                  SIZE:'.Byte_Size' },
                              4:block_delim }, base_extension )
    
    plaintext_extension = com({ NAME:"plaintext_extension",
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
                                12:{ TYPE:StrRawAscii, NAME:"Plaintext_String",
                                     SIZE:'.String_Length' },
                                13:block_delim }, base_extension )

    app_extension = com({ NAME:"Application_Extension",
                          1:{ DEFAULT:255 },
                          2:{ DEFAULT:11 },
                          3:{ TYPE:StrRawAscii, NAME:"Application_ID",
                              SIZE:'.Byte_Size' },
                          4:{ TYPE:UInt8, NAME:"Data_Length"},
                          5:{ TYPE:BytesRaw, NAME:"Application_Data",
                              SIZE:'.Data_Length' },
                          6:block_delim }, base_extension )

    image_block = { TYPE:Container, NAME:"image_block",
                    0:{ TYPE:UInt8,  NAME:'Sentinel',
                        EDITABLE:False, DEFAULT:44 },
                    1:{ TYPE:UInt16, NAME:"Left" },
                    2:{ TYPE:UInt16, NAME:"Top" },
                    3:{ TYPE:UInt16, NAME:"Width" },
                    4:{ TYPE:UInt16, NAME:"Height" },
                    5:{ TYPE:BitStruct, NAME:"flags",
                        0:{ TYPE:BitUInt, NAME:"color_table_size", SIZE:3 },
                        1:{ TYPE:Pad, SIZE:2 },
                        2:{ TYPE:Bit, NAME:"Sort" },
                        3:{ TYPE:Bit, NAME:"Interlace" },
                        4:{ TYPE:Bit, NAME:"Color_Table" }
                        },
                    6:{ TYPE:BytearrayRaw, NAME:"Local_Color_Table",
                        SIZE:color_table_size },
                    7:{ TYPE:Bytearray_LZW, NAME:"Image_Data" }
                    }

    block_extension = { TYPE:Switch, NAME:"block_extension",
                        DEFAULT:unknown_extension,
                        CASE:get_block_extension,
                        CASES:{ 0:unknown_extension,
                                1:plaintext_extension,
                                249:gfx_extension,
                                254:comment_extension,
                                255:app_extension
                                }
                        }
    

    data_block = { TYPE:Switch, NAME:"data_block",
                   DEFAULT:unknown_extension,
                   CASE:get_data_block,
                   CASES:{ 33:block_extension,
                           44:image_block }
                   }
    
    descriptor = {TYPE:Container, NAME:"GIF_Image",
                  0:{ TYPE:UInt24, NAME:"GIF_Sig", DEFAULT:'GIF' },
                  1:{ TYPE:Enum24, NAME:"Version", DEFAULT:'a98',
                      0:{ NAME:"Ver_87a", VALUE:'a78' },
                      1:{ NAME:"Ver_89a", VALUE:'a98' }
                      },
                  2:{ TYPE:UInt16, NAME:"Canvas_Width" },
                  3:{ TYPE:UInt16, NAME:"Canvas_Height" },
                  4:{ TYPE:BitStruct, NAME:"flags",
                      0:{ TYPE:BitUInt, NAME:"color_table_size", SIZE:3 },
                      1:{ TYPE:Bit,     NAME:"Sort" },
                      2:{ TYPE:BitUInt, NAME:"Color_Resolution", SIZE:3 },
                      3:{ TYPE:Bit,     NAME:"Color_Table" }
                      },
                  5:{ TYPE:UInt8, NAME:"Background_Color_Index" },
                  6:{ TYPE:UInt8, NAME:"Pixel_Aspect_Ratio" },
                  7:{ TYPE:BytearrayRaw, NAME:"Global_Color_Table",
                      SIZE:color_table_size },
                  8:{ TYPE:WhileArray, NAME:"Data_Blocks",
                      SUB_STRUCT:data_block,
                      CASE:has_next_data_block },
                  9:{ TYPE:UInt8, NAME:"Trailer", MIN:59, MAX:59,
                      DEFAULT:';', EDITABLE:False, VISIBLE:False }
             }
