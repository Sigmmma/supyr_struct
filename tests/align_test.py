'''
Unit test module meant to test the alignment modes in BlockDefs
'''
from supyr_struct.defs.block_def import BlockDef
from supyr_struct.field_types import Struct, Array, Pad, Pointer32, Pointer64,\
     UInt32, UInt16, UInt8, Float, Double, StrRawUtf8, StrRawUtf16, StrRawUtf32
from supyr_struct.defs.constants import SIZE, ALIGN_AUTO, ALIGN_NONE

__all__ = ['auto_align_test', 'no_align_test', 'pass_fail']


pass_fail = {'pass': 0, 'fail': 0, 'test_count': 2}

align_test_struct = Struct('align_test',
    UInt8("uint8"),    # auto aligns to 0
    UInt16("uint16"),  # auto aligns to 2
    Pad(1),
    UInt32("uint32"),  # auto aligns to 8
    Pad(2),
    Float("float"),    # auto aligns to 16
    Double("double"),  # auto aligns to 24
    StrRawUtf8("str1",  SIZE=3),   # auto aligns to 32
    StrRawUtf16("str2", SIZE=10),  # auto aligns to 36
    StrRawUtf32("str3", SIZE=4),   # auto aligns to 48
    Pad(1),
    Pointer64("pointer1"),  # auto aligns to 56
    Pad(1),
    Pointer32("pointer2"),  # auto aligns to 68
    Pad(1)
    )

# a definition to test automatic structure alignment
auto_align_test_def = BlockDef('auto_align_test',
    align_test_struct,
    # size should pad to 80 bytes when auto alignment happens
    align_mode=ALIGN_AUTO
    )

no_align_test_def = BlockDef('no_align_test',
    align_test_struct,
    # size should pad to 54 bytes
    align_mode=ALIGN_NONE
    )


def auto_align_test():
    # test the align test and make sure the automatic alignment works
    if auto_align_test_def.descriptor[0][SIZE] == 80:
        print("Passed 'auto_align' test.")
        pass_fail['pass'] += 1
    else:
        print("Failed 'auto_align' test.")
        pass_fail['fail'] += 1


def no_align_test():
    # test the align test and make sure the automatic alignment works
    if no_align_test_def.descriptor[0][SIZE] == 54:
        print("Passed 'no_align' test.")
        pass_fail['pass'] += 1
    else:
        print("Failed 'no_align' test.")
        pass_fail['fail'] += 1


# run some tests
if __name__ == '__main__':
    pass_fail['fail'] = pass_fail['pass'] = 0
    auto_align_test()
    no_align_test()
    print('%s passed, %s failed. %s%% passed.' % (
        pass_fail['pass'], pass_fail['fail'],
        str(pass_fail['pass'] * 100 / pass_fail['test_count']).split('.')[0]))
    input()
