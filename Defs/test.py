from .Common_Structures import *
from supyr_struct.Defs.Tag_Def import Tag_Def

def Construct():
    return Test_Definition

class Test_Definition(Tag_Def):
    '''
    This definition is a test of the auto-alignment feature
    '''

    Ext = ".test"

    Cls_ID = "test"

    Endianness = ">"

    Tag_Structure = { TYPE:Struct, GUI_NAME:"Data",#size should be 72
                      0:{ TYPE:UInt8, NAME:"uint8" },#0
                      1:{ TYPE:UInt16, NAME:"uint16" },#2
                      2:{ PAD:1 },
                      3:{ TYPE:UInt32, NAME:"uint32" },#8
                      4:{ PAD:2 },
                      5:{ TYPE:Float, NAME:"float" },#16
                      6:{ TYPE:Double, NAME:"double" },#20
                      7:{ TYPE:Str_Raw_UTF8,  NAME:"str1", SIZE:3 },#32
                      8:{ TYPE:Str_Raw_UTF16, NAME:"str2", SIZE:10 },#36
                      9:{ TYPE:Str_Raw_UTF32, NAME:"str3", SIZE:4 },#48
                      10:{ PAD:1 },
                      11:{ TYPE:Pointer64, NAME:"pointer1" },#56
                      12:{ PAD:1 },
                      13:{ TYPE:Pointer32, NAME:"pointer2" },#60
                      14:{ PAD:1 },
                      }
