'''
This definition is a test of the auto-alignment feature
'''
from supyr_struct.defs.tag_def import *

def get(): return test_def

test_def = TagDef(
    Struct('align_test',
        UInt8("uint8"),#0
        UInt16("uint16"),#2
        Pad(1),
        UInt32("uint32"),#8
        Pad(2),
        Float("float"),#16
        Double("double"),#24
        StrRawUtf8("str1",  SIZE=3),#32
        StrRawUtf16("str2", SIZE=10),#36
        StrRawUtf32("str3", SIZE=4),#48
        Pad(1),
        Pointer64("pointer1"),#56
        Pad(1),
        Pointer32("pointer2"),#68
        Pad(1)
        ),
                   
    #size should be 80 bytes when alignment does its thing
    ext=".test", def_id="test", align=ALIGN_AUTO
    )
