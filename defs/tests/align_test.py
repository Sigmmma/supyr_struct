from supyr_struct.defs.tag_def import *

def get():
    return TestDef

class TestDef(TagDef):
    '''
    This definition is a test of the auto-alignment feature
    '''

    ext = ".test"

    def_id = "test"

    endian = ">"

    align = ALIGN_AUTO

    descriptor = {TYPE:Struct, GUI_NAME:"data",#size should be 80
                  0:{ TYPE:UInt8, NAME:"uint8" },#0
                  1:{ TYPE:UInt16, NAME:"uint16" },#2
                  2:{ TYPE:Pad, SIZE:1 },
                  3:{ TYPE:UInt32, NAME:"uint32" },#8
                  4:{ TYPE:Pad, SIZE:2 },
                  5:{ TYPE:Float, NAME:"float" },#16
                  6:{ TYPE:Double, NAME:"double" },#24
                  7:{ TYPE:StrRawUtf8,  NAME:"str1", SIZE:3 },#32
                  8:{ TYPE:StrRawUtf16, NAME:"str2", SIZE:10 },#36
                  9:{ TYPE:StrRawUtf32, NAME:"str3", SIZE:4 },#48
                  10:{ TYPE:Pad, SIZE:1 },
                  11:{ TYPE:Pointer64, NAME:"pointer1" },#56
                  12:{ TYPE:Pad, SIZE:1 },
                  13:{ TYPE:Pointer32, NAME:"pointer2" },#68
                  14:{ TYPE:Pad, SIZE:1 }
                  }
