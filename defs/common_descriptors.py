'''
This module contains generic structures that fit various needs.

These structures are not meant to be used as is(except void_desc)
and need to be included in a descriptor before it is sanitized.

Critical keys will be missing if they aren't sanitized.
'''

from supyr_struct.defs.constants import *
from supyr_struct.fields import *

void_desc = Void('voided')


def remaining_data_length(block=None, parent=None, attr_index=None,
                          rawdata=None, new_value=None, *args, **kwargs):
    '''
    Size getter for the amount of data left in the rawdata
    starting at kwargs['offset'] + kwargs['root_offset']

    If not provided, offset and root_offset default to 0.
    '''
    if new_value is not None:
        # there is no size to set for an open ended data stream
        return

    if rawdata is not None:
        # the data is being initially read
        return (len(rawdata) - kwargs.get('offset', 0) +
                kwargs.get('root_offset', 0))
    elif parent is not None:
        # the data already exists, so just return its length
        remainder = parent[attr_index]
        try:
            return len(remainder)
        except Exception:
            pass
    return 0


# used when you just want to read the rest of the rawdata into a bytes object
remaining_data = BytearrayRaw("remaining_data", SIZE=remaining_data_length)


# These compressed normals are found in 3D models used on console video games.
# Their use is very memory efficient and the compression loss is very low.
compressed_normal_32 = LBitStruct('compressed_norm32',
    Bit1SInt("x", SIZE=11),
    Bit1SInt("y", SIZE=11),
    Bit1SInt("z", SIZE=10)
    )
compressed_normal_16 = LBitStruct('compressed_norm16',
    Bit1SInt("x", SIZE=5),
    Bit1SInt("y", SIZE=5),
    Bit1SInt("z", SIZE=5),
    Pad(1),
    )


# colors
argb_float = Struct('argb_float',
    LFloat("a"),
    LFloat("r"),
    LFloat("g"),
    LFloat("b")
    )
argb_byte = Struct('argb_uint8',
    UInt8("a"),
    UInt8("r"),
    UInt8("g"),
    UInt8("b")
    )
# rotations
ijkw_float = Struct('ijkw_float',
    LFloat("i"),
    LFloat("j"),
    LFloat("k"),
    LFloat("w")
    )

# colors
rgb_float = Struct('rgb_float',
    LFloat("r"),
    LFloat("g"),
    LFloat("b")
    )
rgb_byte = Struct('rgb_uint8',
    UInt8("r"),
    UInt8("g"),
    UInt8("b")
    )

# coordinates
xyz_float = Struct('xyz_float',
    Float("x"),
    Float("y"),
    Float("z")
    )
xyz_short = Struct('xyz_sint16',
    LSInt16("x"),
    LSInt16("y"),
    LSInt16("z")
    )
xyz_byte = Struct('xyz_sint8',
    SInt8("x"),
    SInt8("y"),
    SInt8("z")
    )
# rotations
ijk_float = Struct('ijk_float',
    LFloat("i"),
    LFloat("j"),
    LFloat("k")
    )
# yaw, pitch, roll
ypr_float = Struct('ypr_float',
    LFloat("y"),
    LFloat("p"),
    LFloat("r")
    )


# distance, time, anything measurable really
range_float = Struct('range_float',
    LFloat("start"),
    LFloat("end")
    )

# coordinates
xy_float = Struct('xy_float',
    LFloat("x"),
    LFloat("y")
    )
xy_short = Struct('xy_sint16',
    LSInt16("x"),
    LSInt16("y")
    )
uv_float = Struct('uv_float',
    LFloat("u"),
    LFloat("v")
    )
uv_short = Struct('uv_sint16',
    LSInt16("u"),
    LSInt16("v")
    )
uv_byte = Struct('uv_sint8',
    SInt8("u"),
    SInt8("v")
    )

# yaw pitch
yp_float = Struct('yp_float',
    LFloat("y"),
    LFloat("p")
    )
