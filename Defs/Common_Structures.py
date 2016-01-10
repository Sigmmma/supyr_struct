"""
This module contains generic structures that fit various needs.

These structures are not meant to be used as is, (except Void_Desc)
and need to be included in a descriptor before it is sanitized.
Critical keys will be missing if they aren't sanitized.
"""

from supyr_struct.Field_Types import *
from supyr_struct.Defs.Constants import *

Void_Desc = { TYPE:Void, NAME:'Voided', GUI_NAME:'Voided' }

def Remaining_Data_Length(**kwargs):
    if "New_Value" in kwargs:
        return
    if "Raw_Data" in kwargs:
        #the data is being initially read
        return (len(kwargs.get('Raw_Data', bytes())) -
                kwargs.get('Offset', 0) +
                kwargs.get('Root_Offset', 0))
    elif "Parent" in kwargs:
        #the data already exists, so just return its length
        return len(kwargs.get('Parent')[kwargs.get('Attr_Index', 0)])
    else:
        raise KeyError('Insufficient information to calculate size.')

#used when you just want to read the rest of the data into a bytes object
Remaining_Data = { TYPE:Container, NAME:"Remaining_Data",
                   0:{ TYPE:Bytearray_Raw, NAME:"Data",
                       SIZE:Remaining_Data_Length }
                   }

#compressed normals
'''These compressed normals are found in 3D models used
on console video games. Their usage is highly memory
efficient and the compression loss is beyond negligable'''
Compressed_Normal_32 = { TYPE:Bit_Struct, SIZE:4,
                         0:{ TYPE:Bit_sInt, NAME:"X", SIZE:11},
                         1:{ TYPE:Bit_sInt, NAME:"Y", SIZE:11},
                         2:{ TYPE:Bit_sInt, NAME:"Z", SIZE:10},
                         }
Compressed_Normal_16 = { TYPE:Bit_Struct, SIZE:2, 
                         0:{TYPE:Bit_sInt, GUI_NAME:"X", SIZE:5},
                         1:{TYPE:Bit_sInt, GUI_NAME:"Y", SIZE:6},
                         2:{TYPE:Bit_sInt, GUI_NAME:"Z", SIZE:5}
                         }


#colors
A_R_G_B_Float = { TYPE:Struct,
                  0:{ TYPE:Float, NAME:"A" },
                  1:{ TYPE:Float, NAME:"R" },
                  2:{ TYPE:Float, NAME:"G" },
                  3:{ TYPE:Float, NAME:"B" }
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
