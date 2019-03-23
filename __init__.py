from supyr_struct import field_type_methods, blocks, tag, buffer

# ##############
#   metadata   #
# ##############
__author__ = "Devin Bobadilla"
#           YYYY.MM.DD
__date__ = "2019.03.21"
__version__ = (1, 2, 0)



# give tag a reference to blocks
tag.blocks = blocks

# give blocks a reference to tag
blocks.block.tag = tag

# field_types needs to directly access the attributes of field_type_methods
# and blocks, so we dont worry about setting up its dependencies
# since it imports its dependencies by itself.
# Other modules need a reference to it though, so import it.
from supyr_struct import field_types

# tag_def, block_def, and common_descs
# need to be given references to other modules
from supyr_struct.defs import tag_def, block_def, common_descs

# give blocks and field_types references to the
# block_def, tag_def, and field_type_methods modules
block_def.blocks = tag_def.blocks = field_type_methods.blocks = blocks
block_def.field_types = tag_def.field_types =\
                        field_type_methods.field_types = field_types
tag_def.TagDef.tag_cls = tag.Tag

# give a common_descs reference to field_type_methods
field_type_methods.common_descs = common_descs


# not for export
del tag_def
del block_def
del common_descs


# import all the things to export when importing supyr_struct

from supyr_struct.field_types import *
from supyr_struct.defs.block_def import BlockDef
from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.util import fcc


# expose the most useful classes and objects
__all__ = [
    'buffer', 'field_types', 'field_type_methods', 'tag', 'blocks', 'defs',

    'BlockDef', 'TagDef', 'fcc',
    # hierarchy and structure
    'Container', 'Array', 'WhileArray', 'Struct', 'QuickStruct', 'QStruct',
    'BBitStruct', 'LBitStruct', 'Union', 'Switch', 'StreamAdapter',
    # special FieldTypes
    'BPointer32', 'LPointer32', 'BPointer64', 'LPointer64',
    'Void', 'Pad', 'Computed', 'WritableComputed',
    # integers and floats
    'BUIntBig', 'BSIntBig', 'BS1IntBig',
    'LUIntBig', 'LSIntBig', 'LS1IntBig',
    'UBitInt',  'SBitInt',  'S1BitInt',
    'Bit', 'UInt8', 'SInt8',
    'BUInt16', 'BUInt24', 'BUInt32', 'BUInt64', 'BFloat',
    'BSInt16', 'BSInt24', 'BSInt32', 'BSInt64', 'BDouble',
    'LUInt16', 'LUInt24', 'LUInt32', 'LUInt64', 'LFloat',
    'LSInt16', 'LSInt24', 'LSInt32', 'LSInt64', 'LDouble',
    'BUDecimal', 'BSDecimal', 'LUDecimal', 'LSDecimal',
    # float and long int timestamps
    'BFloatTimestamp',  'LFloatTimestamp',  'BTimestamp32', 'LTimestamp32',
    'BDoubleTimestamp', 'LDoubleTimestamp', 'BTimestamp64', 'LTimestamp64',
    # enumerators and booleans
    'UBitEnum',  'SBitEnum',  'BitBool',
    'LUEnumBig', 'LSEnumBig', 'LBoolBig',
    'BUEnumBig', 'BSEnumBig', 'BBoolBig',
    'UEnum8',   'SEnum8',   'Bool8',
    'BUEnum16', 'BUEnum24', 'BUEnum32', 'BUEnum64',
    'LUEnum16', 'LUEnum24', 'LUEnum32', 'LUEnum64',
    'BSEnum16', 'BSEnum24', 'BSEnum32', 'BSEnum64',
    'LSEnum16', 'LSEnum24', 'LSEnum32', 'LSEnum64',
    'BBool16', 'BBool24', 'BBool32', 'BBool64',
    'LBool16', 'LBool24', 'LBool32', 'LBool64',
    # integers and float arrays
    'UInt8Array',   'SInt8Array', 'BytesRaw', 'BytearrayRaw', 'BytesRawEnum',
    'BUInt16Array', 'BSInt16Array', 'LUInt16Array', 'LSInt16Array',
    'BUInt32Array', 'BSInt32Array', 'LUInt32Array', 'LSInt32Array',
    'BUInt64Array', 'BSInt64Array', 'LUInt64Array', 'LSInt64Array',
    'BFloatArray',  'BDoubleArray', 'LFloatArray',  'LDoubleArray',
    # strings
    'StrLatin1',  'StrNntLatin1',  'CStrLatin1',  'StrRawLatin1',
    'StrAscii',   'StrNntAscii',   'CStrAscii',   'StrRawAscii',
    'StrUtf8',    'StrNntUtf8',    'CStrUtf8',    'StrRawUtf8',
    'BStrUtf16',  'BStrNntUtf16',  'BCStrUtf16',  'BStrRawUtf16',
    'BStrUtf32',  'BStrNntUtf32',  'BCStrUtf32',  'BStrRawUtf32',
    'LStrUtf16',  'LStrNntUtf16',  'LCStrUtf16',  'LStrRawUtf16',
    'LStrUtf32',  'LStrNntUtf32',  'LCStrUtf32',  'LStrRawUtf32',
    'StrHex',

    # #########################################################
    # short hand names that use the endianness of the system  #
    # #########################################################
    'BitStruct', 'Pointer32', 'Pointer64',
    # integers and floats
    'UIntBig', 'SIntBig', 'S1IntBig',
    'UInt16', 'UInt24', 'UInt32', 'UInt64', 'Float',
    'SInt16', 'SInt24', 'SInt32', 'SInt64', 'Double',
    'UDecimal', 'SDecimal',
    # float and long int timestamps
    'FloatTimestamp', 'DoubleTimestamp', 'Timestamp32', 'Timestamp64',
    # enumerators and booleans
    'UEnumBig', 'SEnumBig', 'BoolBig', 'StrAsciiEnum',
    'UEnum16', 'UEnum24', 'UEnum32', 'UEnum64', 'Bool16', 'Bool24',
    'SEnum16', 'SEnum24', 'SEnum32', 'SEnum64', 'Bool32', 'Bool64',
    # integers and float arrays
    'UInt16Array', 'SInt16Array', 'UInt32Array', 'SInt32Array',
    'UInt64Array', 'SInt64Array', 'FloatArray',  'DoubleArray',
    # strings
    'StrUtf16', 'StrNntUtf16', 'CStrUtf16', 'StrRawUtf16',
    'StrUtf32', 'StrNntUtf32', 'CStrUtf32', 'StrRawUtf32'
    ]
