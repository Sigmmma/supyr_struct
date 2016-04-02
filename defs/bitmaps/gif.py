from math import log
from struct import unpack
from pprint import pprint

from supyr_struct.defs.tag_def import *
from supyr_struct.field_methods import *

com = combine

def get(): return gif_def

def lzw_reader(self, desc, parent, raw_data=None, attr_index=None,
               root_offset=0, offset=0, **kwargs):
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'data' Field."
    
    if raw_data is not None:
        #first byte is irrelevant to deducing the size, so add 1 to the offset
        start = root_offset + offset
        raw_data.seek(start + 1)
        blocksize = int.from_bytes(raw_data.read(1), byteorder='little')
        size = blocksize + 2
        
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
        if not flags.color_table:
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

BytearrayLZW = Field( name="BytearrayLZW", default=bytearray(), endian='=',
                       raw=True, oe_size=True, sizecalc=len_sizecalc,
                       reader=lzw_reader, writer=bytes_writer)
    
block_delim = { TYPE:UInt8, NAME:"block_delimiter",
                VISIBLE:False, EDITABLE:False, MIN:0, MAX:0}

base_extension = { TYPE:Container, NAME:"extension",
                   0:{ TYPE:UInt8, NAME:"sentinel",
                       EDITABLE:False, DEFAULT:33 },
                   1:{ TYPE:Enum8, NAME:"label", EDITABLE:False,
                       0:{ NAME:'plaintext_extension',   VALUE:1 },
                       1:{ NAME:'gfx_control_extension', VALUE:249 },
                       2:{ NAME:'comment_extension',     VALUE:254 },
                       3:{ NAME:'application_extension', VALUE:255 }
                       },
                   2:{ TYPE:UInt8, NAME:"byte_size", EDITABLE:False }
                   }

unknown_extension = com({ NAME:"unknown_extension",
                          3:{ TYPE:BytesRaw, NAME:"unknown_body",
                              SIZE:".byte_size" },
                          4:block_delim }, base_extension )


gfx_extension = com({ NAME:"gfx_control_extension",
                      1:{ DEFAULT:249 },
                      3:{ TYPE:BitStruct, NAME:"flags",
                          0:{ TYPE:Bit,     NAME:'transparent' },
                          1:{ TYPE:Bit,     NAME:'user_input' },
                          2:{ TYPE:BitUInt, NAME:'disposal_method', SIZE:3 }
                          },
                      4:{ TYPE:UInt16, NAME:"delay_time" },
                      5:{ TYPE:UInt8, NAME:"transparent_color_index" },
                      6:block_delim }, base_extension )

comment_extension = com({ NAME:"comment_extension",
                          1:{ DEFAULT:254 },
                          3:{ TYPE:StrRawAscii, NAME:"comment_string",
                              SIZE:'.byte_size' },
                          4:block_delim }, base_extension )

plaintext_extension = com({ NAME:"plaintext_extension",
                            1:{ DEFAULT:1 },
                            2:{ DEFAULT:12 },
                            3:{ TYPE:UInt16, NAME:"text_grid_left" },
                            4:{ TYPE:UInt16, NAME:"text_grid_top" },
                            5:{ TYPE:UInt16, NAME:"text_grid_width" },
                            6:{ TYPE:UInt16, NAME:"ttext_grid_height" },
                            7:{ TYPE:UInt8, NAME:"char_cell_width" },
                            8:{ TYPE:UInt8, NAME:"char_cell_height" },
                            9:{ TYPE:UInt8, NAME:"fg_color_index" },
                            10:{ TYPE:UInt8, NAME:"bg_color_index" },
                            11:{ TYPE:UInt8, NAME:"string_length"},
                            12:{ TYPE:StrRawAscii, NAME:"plaintext_string",
                                 SIZE:'.string_length' },
                            13:block_delim }, base_extension )

app_extension = com({ NAME:"application_extension",
                      1:{ DEFAULT:255 },
                      2:{ DEFAULT:11 },
                      3:{ TYPE:StrRawAscii, NAME:"application_id",
                          SIZE:'.byte_size' },
                      4:{ TYPE:UInt8,    NAME:"data_length"},
                      5:{ TYPE:BytesRaw, NAME:"application_data",
                          SIZE:'.data_length' },
                      6:block_delim }, base_extension )

image_block = { TYPE:Container, NAME:"image_block",
                0:{ TYPE:UInt8,  NAME:'sentinel',
                    EDITABLE:False, DEFAULT:44 },
                1:{ TYPE:UInt16, NAME:"left" },
                2:{ TYPE:UInt16, NAME:"top" },
                3:{ TYPE:UInt16, NAME:"width" },
                4:{ TYPE:UInt16, NAME:"height" },
                5:{ TYPE:BitStruct, NAME:"flags",
                    0:{ TYPE:BitUInt, NAME:"color_table_size", SIZE:3 },
                    1:{ TYPE:Pad, SIZE:2 },
                    2:{ TYPE:Bit, NAME:"sort" },
                    3:{ TYPE:Bit, NAME:"interlace" },
                    4:{ TYPE:Bit, NAME:"color_table" }
                    },
                6:{ TYPE:BytearrayRaw, NAME:"local_color_table",
                    SIZE:color_table_size },
                7:{ TYPE:BytearrayLZW, NAME:"image_data" }
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

gif_header = { TYPE:Struct, NAME:"gif_header",
               0:{ TYPE:UInt24, NAME:"gif_sig", DEFAULT:'GIF' },
               1:{ TYPE:Enum24, NAME:"version", DEFAULT:'a98',
                  0:{ NAME:"Ver_87a", VALUE:'a78' },
                  1:{ NAME:"Ver_89a", VALUE:'a98' }
                  }
               }

gif_logical_screen = { TYPE:Container, NAME:"gif_logical_screen",
                       0:{ TYPE:UInt16, NAME:"canvas_width" },
                       1:{ TYPE:UInt16, NAME:"canvas_height" },
                       2:{ TYPE:BitStruct, NAME:"flags",
                           0:{ TYPE:BitUInt, NAME:"color_table_size", SIZE:3 },
                           1:{ TYPE:Bit,     NAME:"sort" },
                           2:{ TYPE:BitUInt, NAME:"color_resolution", SIZE:3 },
                           3:{ TYPE:Bit,     NAME:"color_table" }
                           },
                       3:{ TYPE:UInt8, NAME:"bg_color_index" },
                       4:{ TYPE:UInt8, NAME:"aspect_ratio" },
                       5:{ TYPE:BytearrayRaw, NAME:"global_color_table",
                           SIZE:color_table_size }
                       }

gif_desc = { TYPE:Container, NAME:"gif_image",
             0:gif_header,
             1:gif_logical_screen,
             2:{ TYPE:WhileArray, NAME:"data_blocks",
                 SUB_STRUCT:data_block,
                 CASE:has_next_data_block },
             3:{ TYPE:UInt8, NAME:"trailer", MIN:59, MAX:59,
                 DEFAULT:';', EDITABLE:False, VISIBLE:False }
             }

gif_def = TagDef( ext=".gif", def_id="gif", endian="<", descriptor=gif_desc )
