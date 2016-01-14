from supyr_struct.Defs.Tag_Def import *


def Construct():
    return TGA_Def

class TGA_Def(Tag_Def):

    def TGA_Color_Table_Size(*args, **kwargs):
        if kwargs.get("New_Value") is not None:
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return
        
        '''Used for calculating the size of the color table bytes'''
        if "Parent" not in kwargs:
            raise KeyError("Cannot calculate the size of TGA "+
                           "Color Table without a supplied Tag_Block.")

        Header = kwargs["Parent"].Header
        
        if not Header.Has_Color_Map:
            return 0
        else:
            Depth = Header.Color_Map_Depth
            if Depth == 15:
                Depth = 16
            
            return (Depth//8) * Header.Color_Map_Length


    def TGA_Pixel_Bytes_Size(*args, **kwargs):
        if kwargs.get("New_Value") is not None:
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return
        
        '''Used for calculating the size of the pixel data bytes'''
        if "Parent" not in kwargs:
            raise KeyError("Cannot calculate the size of TGA "+
                           "Pixels without without a supplied Tag_Block.")
        
        Header = kwargs["Parent"].Header

        Pixels = Header.Width * Header.Height
        Image_Type = Header.Image_Type

        if Image_Type.Flags.RLE_Compressed:
            raise NotImplementedError("RLE Compressed TGA files are not able "+
                                      "to be opened. \nOpening requires "+
                                      "decompressing until Width*Height "+
                                      "pixels have been decompressed.")
        elif Image_Type.Format == 0:
            return Pixels//8
        else:
            BPP = Header.BPP
            if BPP == 15:
                BPP = 16
            
            return (BPP * Pixels) // 8

    
    Ext = ".tga"

    Cls_ID = "tga"

    Endian = "<"
    
    Tag_Structure = { TYPE:Container, NAME:"TGA_Image",
                        0:{ TYPE:Struct, NAME:"Header",
                            0:{ TYPE:UInt8, NAME:"Image_ID_Length"},
                            1:{ TYPE:Enum8, NAME:"Has_Color_Map",
                                0:{ NAME:"No" },
                                1:{ NAME:"Yes" }
                                },
                            2:{ TYPE:Bit_Struct, NAME:"Image_Type",
                                 0:{TYPE:Bit_Enum, NAME:"Format", SIZE:2,
                                    0:{NAME:"BW_1_Bit"},
                                    1:{NAME:"Color_Mapped_RGB"},
                                    2:{NAME:"Unmapped_RGB"}
                                    },
                                 1:{TYPE:Bit_Bool, NAME:"Flags", SIZE:2,
                                    0:{ NAME:"RLE_Compressed" , VALUE:2}
                                    }
                                },
                            3:{ TYPE:UInt16, NAME:"Color_Map_Origin" },
                            4:{ TYPE:UInt16, NAME:"Color_Map_Length" },
                            5:{ TYPE:UInt8,  NAME:"Color_Map_Depth" },
                            6:{ TYPE:UInt16, NAME:"Image_Origin_X" },
                            7:{ TYPE:UInt16, NAME:"Image_Origin_Y" },
                            8:{ TYPE:UInt16, NAME:"Width" },
                            9:{ TYPE:UInt16, NAME:"Height" },
                            10:{ TYPE:UInt8, NAME:"BPP" },
                            11:{ TYPE:Bit_Struct, NAME:"Image_Descriptor",
                                 0:{TYPE:Bit_UInt, NAME:"Alpha_Bit_Count", SIZE:4},
                                 1:{ TYPE:Pad, SIZE:1 },
                                 2:{TYPE:Bit_Enum, NAME:"Screen_Origin", SIZE:1,
                                    0:{NAME:"Lower_Left"},
                                    1:{NAME:"Upper_Left"}
                                    },
                                 3:{TYPE:Bit_Enum, NAME:"Interleaving", SIZE:2,
                                    0:{NAME:"None"},
                                    1:{NAME:"Two_Way"},
                                    2:{NAME:"Four_Way"},
                                    }
                                }
                            },
                            1:{ TYPE:Bytes_Raw, NAME:'Image_ID',
                                SIZE:'.Header.Image_ID_Length' },
                            2:{ TYPE:Bytes_Raw, NAME:'Color_Table',
                                SIZE:TGA_Color_Table_Size },
                            3:{ TYPE:Bytes_Raw, NAME:'Pixel_Data',
                                SIZE:TGA_Pixel_Bytes_Size },
                            4:Remaining_Data
                            }
