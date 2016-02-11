"""
This module contains generic structures that fit various needs.

These structures are not meant to be used as is, (except void_desc)
and need to be included in a descriptor before it is sanitized.
Critical keys will be missing if they aren't sanitized.
"""

from supyr_struct.fields import *
from supyr_struct.defs.constants import *

void_desc = { TYPE:Void, NAME:'voided', GUI_NAME:'voided' }

def remaining_data_length(**kwargs):
    if kwargs.get("new_value") is not None:
        return
    raw_data = kwargs.get("raw_data")
    parent = kwargs.get("parent")
    if raw_data is not None:
        #the data is being initially read
        return (len(raw_data) - kwargs.get('offset', 0) +
                kwargs.get('root_offset', 0))
    elif parent is not None:
        #the data already exists, so just return its length
        remainder = parent[kwargs.get('attr_index', None)]
        try:
            return len(remainder)
        except Exception:
            return 0
    else:
        return 0


#used when you just want to read the rest of the data into a bytes object
remaining_data = { TYPE:BytearrayRaw, NAME:"remaining_data",
                   SIZE:remaining_data_length }

#compressed normals
'''These compressed normals are found in 3D models used
on console video games. Their usage is highly memory
efficient and the compression loss is beyond negligable'''
Compressed_Normal_32 = { TYPE:BitStruct, SIZE:4,
                         0:{ TYPE:Bit1SInt, NAME:"x", SIZE:11},
                         1:{ TYPE:Bit1SInt, NAME:"y", SIZE:11},
                         2:{ TYPE:Bit1SInt, NAME:"z", SIZE:10},
                         }
Compressed_Normal_16 = { TYPE:BitStruct, SIZE:2, 
                         0:{TYPE:Bit1SInt, GUI_NAME:"x", SIZE:5},
                         1:{TYPE:Bit1SInt, GUI_NAME:"y", SIZE:6},
                         2:{TYPE:Bit1SInt, GUI_NAME:"z", SIZE:5}
                         }


#colors
A_R_G_B_Float = { TYPE:Struct,
                  0:{ TYPE:Float, NAME:"a" },
                  1:{ TYPE:Float, NAME:"r" },
                  2:{ TYPE:Float, NAME:"g" },
                  3:{ TYPE:Float, NAME:"b" }
                  }
A_R_G_B_Byte = { TYPE:Struct, 
                 0:{ TYPE:UInt8, NAME:"a" },
                 1:{ TYPE:UInt8, NAME:"r" },
                 2:{ TYPE:UInt8, NAME:"g" },
                 3:{ TYPE:UInt8, NAME:"b" }
                 }
#rotations
I_J_K_W_Float = { TYPE:Struct,
                  0:{ TYPE:Float, NAME:"i" },
                  1:{ TYPE:Float, NAME:"j" },
                  2:{ TYPE:Float, NAME:"k" },
                  3:{ TYPE:Float, NAME:"w" }
                  }

#colors
R_G_B_Float = { TYPE:Struct, 
                0:{ TYPE:Float, NAME:"r" },
                1:{ TYPE:Float, NAME:"g" },
                2:{ TYPE:Float, NAME:"b" }
                }
R_G_B_Byte = { TYPE:Struct, 
               0:{ TYPE:UInt8, NAME:"r" },
               1:{ TYPE:UInt8, NAME:"g" },
               2:{ TYPE:UInt8, NAME:"b" }
               }

#coordinates
X_Y_Z_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"x" },
                1:{ TYPE:Float, NAME:"y" },
                2:{ TYPE:Float, NAME:"z" }
                }
X_Y_Z_Short = { TYPE:Struct,
                0:{ TYPE:SInt16, NAME:"x" },
                1:{ TYPE:SInt16, NAME:"y" },
                2:{ TYPE:SInt16, NAME:"z" }
                }
X_Y_Z_Byte = { TYPE:Struct,
               0:{ TYPE:SInt8, NAME:"x" },
               1:{ TYPE:SInt8, NAME:"y" },
               2:{ TYPE:SInt8, NAME:"z" }
               }
#rotations
I_J_K_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"i" },
                1:{ TYPE:Float, NAME:"j" },
                2:{ TYPE:Float, NAME:"k" }
                }
#yaw, pitch, roll
Y_P_R_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"y" },
                1:{ TYPE:Float, NAME:"p" },
                2:{ TYPE:Float, NAME:"r" }
                }



#distance, time, anything measurable really
Range_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"start"},
                1:{ TYPE:Float, NAME:"end"}
                }

#coordinates
X_Y_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"x" },
              1:{ TYPE:Float, NAME:"y" }
              }
X_Y_Short = { TYPE:Struct,
              0:{ TYPE:SInt16, NAME:"x" },
              1:{ TYPE:SInt16, NAME:"y" }
              }
U_V_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"u" },
              1:{ TYPE:Float, NAME:"v" }
              }
U_V_Short = { TYPE:Struct,
              0:{ TYPE:SInt16, NAME:"u" },
              1:{ TYPE:SInt16, NAME:"v" }
              }
U_V_Byte = { TYPE:Struct,
              0:{ TYPE:SInt8, NAME:"u" },
              1:{ TYPE:SInt8, NAME:"v" }
              }

#yaw pitch
Y_P_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"y" },
              1:{ TYPE:Float, NAME:"p" }
              }
