"""
This module contains generic structures that fit various needs.

These structures are not meant to be used as is, (except void_desc)
and need to be included in a descriptor before it is sanitized.
Critical keys will be missing if they aren't sanitized.
"""

from supyr_struct.defs.constants import *
from supyr_struct.fields import *

void_desc = Void('voided')

def remaining_data_length(block=None, parent=None, attr_index=None,
                          rawdata=None, new_value=None, *args, **kwargs):
    if new_value is not None:
        return
    
    if rawdata is not None:
        #the data is being initially read
        return (len(rawdata) - kwargs.get('offset', 0) +
                kwargs.get('root_offset', 0))
    elif parent is not None:
        #the data already exists, so just return its length
        remainder = parent[attr_index]
        try:
            return len(remainder)
        except Exception:
            pass
    return 0


#used when you just want to read the rest of the data into a bytes object
remaining_data = BytearrayRaw("remaining_data", SIZE=remaining_data_length)

#compressed normals
'''These compressed normals are found in 3D models used
on console video games. Their usage is highly memory
efficient and the compression loss is beyond negligable'''
Compressed_Normal_32 = LBitStruct('compressed_norm32',
    Bit1SInt("x", SIZE=11),
    Bit1SInt("y", SIZE=11),
    Bit1SInt("z", SIZE=10)
    )
Compressed_Normal_16 = LBitStruct('compressed_norm16',
    Bit1SInt("x", SIZE=5),
    Bit1SInt("y", SIZE=6),
    Bit1SInt("z", SIZE=5)
    )


#colors
A_R_G_B_Float = Struct('argb_float',
    LFloat("a"),
    LFloat("r"),
    LFloat("g"),
    LFloat("b")
    )
A_R_G_B_Byte = Struct('argb_uint8',
    UInt8("a"),
    UInt8("r"),
    UInt8("g"),
    UInt8("b")
    )
#rotations
I_J_K_W_Float = Struct('ijkw_float',
    LFloat("i"),
    LFloat("j"),
    LFloat("k"),
    LFloat("w")
    )

#colors
R_G_B_Float = Struct('rgb_float',
    LFloat("r"),
    LFloat("g"),
    LFloat("b")
    )
R_G_B_Byte = Struct('rgb_uint8',
    UInt8("r"),
    UInt8("g"),
    UInt8("b")
    )

#coordinates
X_Y_Z_Float = Struct('xyz_float',
    Float("x"),
    Float("y"),
    Float("z")
    )
X_Y_Z_Short = Struct('xyz_sint16',
    LSInt16("x"),
    LSInt16("y"),
    LSInt16("z")
    )
X_Y_Z_Byte = Struct('xyz_sint8',
    SInt8("x"),
    SInt8("y"),
    SInt8("z")
    )
#rotations
I_J_K_Float = Struct('ijk_float',
    LFloat("i"),
    LFloat("j"),
    LFloat("k")
    )
#yaw, pitch, roll
Y_P_R_Float = Struct('ypr_float',
    LFloat("y"),
    LFloat("p"),
    LFloat("r")
    )



#distance, time, anything measurable really
Range_Float = Struct('range_float',
    LFloat("start"),
    LFloat("end")
    )

#coordinates
X_Y_Float = Struct('xy_float',
    LFloat("x"),
    LFloat("y")
    )
X_Y_Short = Struct('xy_sint16',
    LSInt16("x"),
    LSInt16("y")
    )
U_V_Float = Struct('uv_float',
    LFloat("u"),
    LFloat("v")
    )
U_V_Short = Struct('uv_sint16',
    LSInt16("u"),
    LSInt16("v")
    )
U_V_Byte = Struct('uv_sint8',
    SInt8("u"),
    SInt8("v")
    )

#yaw pitch
Y_P_Float = Struct('yp_float',
    LFloat("y"),
    LFloat("p")
    )
