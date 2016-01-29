"""
This module contains generic structures that fit various needs.

These structures are not meant to be used as is, (except Void_Desc)
and need to be included in a descriptor before it is sanitized.
Critical keys will be missing if they aren't sanitized.
"""

from supyr_struct.fields import *
from supyr_struct.defs.constants import *

Void_Desc = { TYPE:Void, NAME:'Voided', GUI_NAME:'Voided' }

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
remaining_data = { TYPE:BytearrayRaw, NAME:"Remaining_Data",
                   SIZE:remaining_data_length }

#compressed normals
'''These compressed normals are found in 3D models used
on console video games. Their usage is highly memory
efficient and the compression loss is beyond negligable'''
Compressed_Normal_32 = { TYPE:BitStruct, SIZE:4,
                         0:{ TYPE:Bit1SInt, NAME:"X", SIZE:11},
                         1:{ TYPE:Bit1SInt, NAME:"Y", SIZE:11},
                         2:{ TYPE:Bit1SInt, NAME:"Z", SIZE:10},
                         }
Compressed_Normal_16 = { TYPE:BitStruct, SIZE:2, 
                         0:{TYPE:Bit1SInt, GUI_NAME:"X", SIZE:5},
                         1:{TYPE:Bit1SInt, GUI_NAME:"Y", SIZE:6},
                         2:{TYPE:Bit1SInt, GUI_NAME:"Z", SIZE:5}
                         }


#colors
A_R_G_B_Float = { TYPE:Struct,
                  0:{ TYPE:Float, NAME:"A" },
                  1:{ TYPE:Float, NAME:"R" },
                  2:{ TYPE:Float, NAME:"G" },
                  3:{ TYPE:Float, NAME:"B" }
                  }
A_R_G_B_Byte = { TYPE:Struct, 
                 0:{ TYPE:UInt8, NAME:"A" },
                 1:{ TYPE:UInt8, NAME:"R" },
                 2:{ TYPE:UInt8, NAME:"G" },
                 3:{ TYPE:UInt8, NAME:"B" }
                 }
#rotations
I_J_K_W_Float = { TYPE:Struct,
                  0:{ TYPE:Float, NAME:"I" },
                  1:{ TYPE:Float, NAME:"J" },
                  2:{ TYPE:Float, NAME:"K" },
                  3:{ TYPE:Float, NAME:"W" }
                  }

#colors
R_G_B_Float = { TYPE:Struct, 
                0:{ TYPE:Float, NAME:"R" },
                1:{ TYPE:Float, NAME:"G" },
                2:{ TYPE:Float, NAME:"B" }
                }
R_G_B_Byte = { TYPE:Struct, 
               0:{ TYPE:UInt8, NAME:"R" },
               1:{ TYPE:UInt8, NAME:"G" },
               2:{ TYPE:UInt8, NAME:"B" }
               }

#coordinates
X_Y_Z_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"X" },
                1:{ TYPE:Float, NAME:"Y" },
                2:{ TYPE:Float, NAME:"Z" }
                }
X_Y_Z_Short = { TYPE:Struct,
                0:{ TYPE:SInt16, NAME:"X" },
                1:{ TYPE:SInt16, NAME:"Y" },
                2:{ TYPE:SInt16, NAME:"Z" }
                }
X_Y_Z_Byte = { TYPE:Struct,
               0:{ TYPE:SInt8, NAME:"X" },
               1:{ TYPE:SInt8, NAME:"Y" },
               2:{ TYPE:SInt8, NAME:"Z" }
               }
#rotations
I_J_K_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"I" },
                1:{ TYPE:Float, NAME:"J" },
                2:{ TYPE:Float, NAME:"K" }
                }
#yaw, pitch, roll
Y_P_R_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"Y" },
                1:{ TYPE:Float, NAME:"P" },
                2:{ TYPE:Float, NAME:"R" }
                }



#distance, time, anything measurable really
Range_Float = { TYPE:Struct,
                0:{ TYPE:Float, NAME:"Start"},
                1:{ TYPE:Float, NAME:"End"}
                }

#coordinates
X_Y_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"X" },
              1:{ TYPE:Float, NAME:"Y" }
              }
X_Y_Short = { TYPE:Struct,
              0:{ TYPE:SInt16, NAME:"X" },
              1:{ TYPE:SInt16, NAME:"Y" }
              }
U_V_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"U" },
              1:{ TYPE:Float, NAME:"V" }
              }
U_V_Short = { TYPE:Struct,
              0:{ TYPE:SInt16, NAME:"U" },
              1:{ TYPE:SInt16, NAME:"V" }
              }
U_V_Byte = { TYPE:Struct,
              0:{ TYPE:SInt8, NAME:"U" },
              1:{ TYPE:SInt8, NAME:"V" }
              }

#yaw pitch
Y_P_Float = { TYPE:Struct,
              0:{ TYPE:Float, NAME:"Y" },
              1:{ TYPE:Float, NAME:"P" }
              }
