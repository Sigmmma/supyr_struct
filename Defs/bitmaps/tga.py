from supyr_struct.Defs.Tag_Def import *


def Construct():
    return TGA_Def

class TGA_Def(Tag_Def):

    def TGA_Color_Table_Size(*args, **kwargs):
        if kwargs.get("New_Value"):
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return None
        
        '''Used for calculating the size of the color table bytes'''
        if "Tag" not in kwargs:
            raise KeyError("Cannot calculate the size of TGA "+
                           "Color Table without Tag reference.")

        Tag_Data = kwargs["Tag"].Tag_Data
        
        if not Tag_Data.Has_Color_Map:
            return 0
        else:
            Depth = Tag_Data.Color_Map_Depth
            if Depth == 15: Depth = 16
            
            return (Depth//8) * Tag_Data.Color_Map_Length


    def TGA_Pixel_Bytes_Size(*args, **kwargs):
        if kwargs.get("New_Value"):
            #it isnt possible to set the size because the size is
            #derived from multiple source inputs and must be set
            #manually. This is expected to happen for some types
            #of structures, so rather than raise an error, just do
            #nothing since this is normal and the user handles it
            return None
        
        '''Used for calculating the size of the pixel data bytes'''
        if "Tag" not in kwargs:
            raise KeyError("Cannot calculate the size of TGA "+
                           "Pixels without Tag reference.")
        
        Tag_Data = kwargs["Tag"].Tag_Data

        Pixels = Tag_Data.Width * Tag_Data.Height
        Image_Type = Tag_Data.Image_Type

        if Image_Type.RLE_Compressed:
            raise NotImplementedError("RLE Compressed TGA files are not able "+
                                      "to be opened. \nOpening requires "+
                                      "decompressing them until Width*Height "+
                                      "pixels have been decompressed.")
        else:
            BPP = Tag_Data.BPP
            if BPP == 15: BPP = 16
            
            if Image_Type.Format == 0:
                return Pixels//8
            
            return (BPP * Pixels) // 8

    
    Ext = ".tga"

    Cls_ID = "tga"

    Endianness = "<"
    
    Tag_Structure = {TYPE:Struct, GUI_NAME:"TGA Image",
                      0:{ TYPE:UInt8, GUI_NAME:"Image ID Length"},
                      1:{ TYPE:UInt8, GUI_NAME:"Has Color Map",
                          ELEMENTS:{0:{NAME:"No"},
                                    1:{NAME:"Yes"}
                                    }
                          },
                      2:{ TYPE:Bit_Struct, GUI_NAME:"Image Type",
                           0:{TYPE:Bit_UInt, GUI_NAME:"Format", SIZE:2,
                              ELEMENTS:{0:{GUI_NAME:"BW 1 Bit"},
                                        1:{GUI_NAME:"Color Mapped RGB"},
                                        2:{GUI_NAME:"Unmapped RGB"},
                                        }
                              },
                           1:{ PAD:1 },
                           2:{TYPE:Bit_UInt, GUI_NAME:"RLE Compressed", SIZE:1,
                              ELEMENTS:{0:{NAME:"No"}, 1:{NAME:"Yes"} }
                              }
                          },
                      3:{ TYPE:UInt16, GUI_NAME:"Color Map Origin" },
                      4:{ TYPE:UInt16, GUI_NAME:"Color Map Length" },
                      5:{ TYPE:UInt8, GUI_NAME:"Color Map Depth" },
                      6:{ TYPE:Struct, GUI_NAME:"Image Origin",
                          0:{ TYPE:UInt16, NAME:"X" },
                          1:{ TYPE:UInt16, NAME:"Y" },
                          },
                      7:{ TYPE:UInt16, NAME:"Width" },
                      8:{ TYPE:UInt16, NAME:"Height" },
                      9:{ TYPE:UInt8, NAME:"BPP" },
                      10:{ TYPE:Bit_Struct, GUI_NAME:"Image Descriptor",
                           0:{TYPE:Bit_UInt, GUI_NAME:"Alpha Bit Count", SIZE:4},
                           1:{ PAD:1 },
                           2:{TYPE:Bit_UInt, GUI_NAME:"Screen Origin", SIZE:1,
                              ELEMENTS:{0:{GUI_NAME:"Lower Left"},
                                        1:{GUI_NAME:"Upper Left"}
                                        },
                              },
                           3:{TYPE:Bit_UInt, GUI_NAME:"Interleaving", SIZE:2,
                              ELEMENTS:{0:{GUI_NAME:"None"},
                                        1:{GUI_NAME:"Two Way"},
                                        2:{GUI_NAME:"Four Way"},
                                        }
                              }
                          },
                     CHILD:{ TYPE:Container, NAME:"Image_Data",
                         0:{TYPE:Bytearray_Raw, GUI_NAME:'Image ID',
                            SIZE:'..Image_ID_Length'},
                         1:{TYPE:Bytearray_Raw, GUI_NAME:'Color Table',
                            SIZE:TGA_Color_Table_Size},
                         2:{TYPE:Bytearray_Raw, GUI_NAME:'Pixel Data',
                            SIZE:TGA_Pixel_Bytes_Size}
                         },
                 }
