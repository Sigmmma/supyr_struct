from supyr_struct.Defs.Tag_Def import Tag_Def
from supyr_struct.Defs.Common_Structures import *
from supyr_struct.Field_Types import *

'''
All structure definitions within this file were written using
the work of Caustik. The information can be found on his website
http://www.caustik.com/cxbx/download/xbe.htm

Their e-mail address is:
caustik@caustik.com
'''

def Construct():
    return XBE_Def


class XBE_Def(Tag_Def):

    def Base_Rel_Pointer(*args, **kwargs):        
        '''Used for getting and setting pointers relative
        to the XBE Base Address in the XBE Image Header.'''
        
        New_Val = kwargs.get("New_Value")
        Parent  = kwargs.get("Parent")
        Path    = kwargs.get("P_Path")
        
        if Parent is None:
            raise KeyError("Cannot get or set base address relative "+
                           "pointers without the Parent block.")
        if Path == None:
            raise KeyError("Cannot get or set base address relative "+
                           "pointers without a path to the pointer.")
        
        Tag     = Parent.Get_Tag()
        Base_Addr = Tag.Tag_Data.Get_Neighbor("XBE_Image_Header.Base_Address")
        
        if New_Val is None:
            return Parent.Get_Neighbor(Path)-Base_Addr
        else:
            return Parent.Set_Neighbor(Path, New_Val+Base_Addr)


    Ext = ".xbe"
    
    Cls_ID = "xbe"

    Endian = "<"

    Incomplete = True
    
    XBE_Image_Header = {TYPE:Struct, NAME:"XBE_Image_Header",
                        0:{TYPE:Str_Raw_Latin1, NAME:"XBE_Magic",
                           SIZE:4, DEFAULT:"XBEH"},
                        1:{TYPE:Bytearray_Raw, NAME:"Digital_Signature", SIZE:256},
                        2:{TYPE:Pointer32, NAME:"Base_Address"},
                        3:{TYPE:UInt32, NAME:"Headers_Size"},
                        4:{TYPE:UInt32, NAME:"Image_Size"},
                        5:{TYPE:UInt32, NAME:"Image_Header_Size"},
                        6:{TYPE:Timestamp,  NAME:"Time_Date"},
                        7:{TYPE:Pointer32, NAME:"Certificate_Address"},
                        8:{TYPE:UInt32, NAME:"Section_Count"},
                        9:{TYPE:Pointer32, NAME:"Section_Headers_Address"},
                        10:{TYPE:Enum32, NAME:"Init_Flags",
                            0:{NAME:"Mount_Utility_Drive"},
                            1:{NAME:"Format_Utility_Drive"},
                            2:{NAME:"Limit_64MB"},
                            3:{NAME:"Dont_Setup_HDD"}
                            },
                        #Entry Point is encoded with an XOR key.
                        #The XOR key used depends on the XBE build.
                        #Debug  = 0x94859D4B
                        #Retail = 0xA8FC57AB
                        11:{TYPE:UInt32, NAME:"Entry_Point"},
                        12:{TYPE:UInt32, NAME:"TLS_Address"},
                        13:{TYPE:UInt32, NAME:"PE_Stack_Commit"},
                        14:{TYPE:UInt32, NAME:"PE_Heap_Reserve"},
                        15:{TYPE:UInt32, NAME:"PE_Heap_Commit"},
                        16:{TYPE:UInt32, NAME:"PE_Base_Address"},
                        17:{TYPE:UInt32, NAME:"PE_Image_Size"},
                        18:{TYPE:UInt32, NAME:"PE_Checksum"},
                        19:{TYPE:Timestamp, NAME:"PE_Time_Date"},
                        20:{TYPE:Pointer32, NAME:"Debug_Path_Address"},
                        21:{TYPE:Pointer32, NAME:"Debug_File_Address"},
                        22:{TYPE:Pointer32, NAME:"Debug_Unicode_File_Address"},
                        
                        #Kernel Image Thunk Address is encoded with an XOR key.
                        #The XOR key used depends on the XBE build.
                        #Debug  = 0xEFB1F152
                        #Retail = 0x5B6D40B6
                        23:{TYPE:UInt32, NAME:"Kernel_Image_Thunk_Address"},
                        24:{TYPE:Pointer32, NAME:"Non_Kernel_Import_Dir_Address"},      
                        25:{TYPE:UInt32, NAME:"Lib_Vers_Count"},
                        26:{TYPE:Pointer32, NAME:"Lib_Vers_Address"},
                        27:{TYPE:Pointer32, NAME:"Kernel_Lib_Ver_Address"},
                        28:{TYPE:Pointer32, NAME:"XAPI_Lib_Ver_Address"},
                        29:{TYPE:Pointer32, NAME:"Logo_Bitmap_Address"},
                        30:{TYPE:UInt32, NAME:"Logo_Bitmap_Size"},
                        CHILD:{ TYPE:Container, NAME:"Debug_Strings",
                                0:{ TYPE:CStr_Latin1, NAME:"Debug_Path",
                                    POINTER:(lambda *a, **k: XBE_Def.Base_Rel_Pointer(*a,
                                             P_Path='..Debug_Path_Address',**k)) },
                                1:{ TYPE:CStr_Latin1, NAME:"Debug_File",
                                    POINTER:(lambda *a, **k: XBE_Def.Base_Rel_Pointer(*a,
                                             P_Path='..Debug_File_Address',**k)) },
                                2:{ TYPE:CStr_UTF16, NAME:"Debug_Unicode_File",
                                    POINTER:(lambda *a, **k: XBE_Def.Base_Rel_Pointer(*a,
                                             P_Path='..Debug_Unicode_File_Address',**k)) }
                                }
                        }

    
    XBE_Certificate = {TYPE:Struct, NAME:"XBE_Certificate", SIZE:464,
                       POINTER:(lambda *a, **k:
                                XBE_Def.Base_Rel_Pointer(*a,
                                P_Path='.XBE_Image_Header.Certificate_Address',**k)),
                       
                       0:{TYPE:UInt32, NAME:"Struct_Size",
                          EDITABLE:False, DEFAULT:464},
                       1:{TYPE:Timestamp,  NAME:"Time_Date"},
                       #least significant 2 bytes of title ID are treated as
                       #an int and most significant 2 are a 2 char string.
                       2:{TYPE:Bytearray_Raw,NAME:"Title_ID", SIZE:4},
                       3:{TYPE:Str_UTF16,   NAME:"Title_Name", SIZE:80},
                       4:{TYPE:UInt32_Array, NAME:"Alt_Title_IDs", SIZE:64},
                       5:{TYPE:Enum32,       NAME:"Allowed_Media",
                          0:{NAME:"Hard_Disk"},
                          1:{NAME:"DVD_X2"},
                          2:{NAME:"DVD_CD"},
                          3:{NAME:"CD"},
                          4:{NAME:"DVD_5_RO"},
                          5:{NAME:"DVD_9_RO"},
                          6:{NAME:"DVD_5_RW"},
                          7:{NAME:"DVD_9_RW"},
                          8:{NAME:"USB"},
                          9:{NAME:"Media_Board"},
                          10:{NAME:"Nonsecure_Hard_Disk", VALUE:0x40000000},
                          11:{NAME:"Nonsecure_Mode",      VALUE:0x80000000}
                          },
                       6:{TYPE:Enum32, NAME:"Game_Region",
                          0:{NAME:"USA_Canada"},
                          1:{NAME:"Japan"},
                          2:{NAME:"Rest_of_World"},
                          3:{NAME:"Debug", VALUE:0x80000000}
                          },
                       7:{TYPE:Enum32, NAME:"Game_Ratings",
                          0:{NAME:"RP"},#All
                          1:{NAME:"AO"},#Adult only
                          2:{NAME:"M"}, #Mature
                          3:{NAME:"T"}, #Teen
                          4:{NAME:"E"}, #Everyone
                          5:{NAME:"KA"},#Kids_to_Adults
                          6:{NAME:"EC"} #Early_Childhood
                          },
                       8:{TYPE:UInt32,     NAME:"Disk_Number"},
                       9:{TYPE:UInt32,     NAME:"Version"},
                       10:{TYPE:Bytearray_Raw, NAME:"Lan_Key", SIZE:16},
                       11:{TYPE:Bytearray_Raw, NAME:"Signature_Key", SIZE:16},
                       12:{TYPE:Bytearray_Raw, NAME:"Alt_Signature_Keys", SIZE:256},
                       }

    XBE_Sec_Header = {TYPE:Struct, NAME:"XBE_Section_Header",
                      0:{TYPE:Enum32, NAME:"Flags",
                         0:{NAME:"Writable"},
                         1:{NAME:"Preload"},
                         2:{NAME:"Executable"},
                         3:{NAME:"Inserted_File"},
                         4:{NAME:"Head_Page_Read_Only"},
                         5:{NAME:"Tail_Page_Read_Only"}
                         },
                      1:{TYPE:UInt32, NAME:"Virtual_Address"},
                      2:{TYPE:UInt32, NAME:"Virtual_Size"},
                      3:{TYPE:Pointer32, NAME:"Raw_Address"},
                      4:{TYPE:UInt32, NAME:"Raw_Size"},
                      5:{TYPE:Pointer32, NAME:"Section_Name_Address"},
                      6:{TYPE:UInt32, NAME:"Section_Name_Ref_Count"},
                      7:{TYPE:Pointer32, NAME:"Head_Shared_Page_Ref_Count_Address"},
                      8:{TYPE:Pointer32, NAME:"Tail_Shared_Page_Ref_Count_Address"},
                      9:{TYPE:Bytearray_Raw, NAME:"Section_Digest", SIZE:20},
                      CHILD:{ TYPE:CStr_Latin1, NAME:'Section_Name',
                              POINTER:(lambda *a, **k: XBE_Def.Base_Rel_Pointer(*a,
                                       P_Path='.Section_Name_Address',**k))
                              }
                      }
                      

    XBE_Lib_Ver = { TYPE:Struct, NAME:"XBE_Lib_Version",
                    0:{TYPE:Str_Latin1, NAME:"Library_Name", SIZE:8},
                    1:{TYPE:UInt16,          NAME:"Major_Ver"},
                    2:{TYPE:UInt16,          NAME:"Minor_Ver"},
                    3:{TYPE:UInt16,          NAME:"Build_Ver"},
                    4:{TYPE:Bit_Struct,      NAME:"Flags",
                       0:{TYPE:Bit_UInt, NAME:"QFE_Ver",  SIZE:13},
                       1:{TYPE:Bit_Enum, NAME:"Approved", SIZE:2,
                          0:{NAME:"No"},
                          1:{NAME:"Possibly"},
                          2:{NAME:"Yes"}
                          },
                       2:{TYPE:Bit_Enum, NAME:"Debug_Build", SIZE:1,
                          0:{NAME:"No"},
                          1:{NAME:"Yes"}
                          }
                       }
                    }

    XBE_TLS = { TYPE:Struct, NAME:"XBE_TLS",
                0:{TYPE:UInt32, NAME:"Data_Start_Address"},
                1:{TYPE:UInt32, NAME:"Data_End_Address"},
                2:{TYPE:UInt32, NAME:"TLS_Index_Address"},
                3:{TYPE:UInt32, NAME:"TLS_Callback_Address"},
                4:{TYPE:UInt32, NAME:"Size_of_Zero_Fill"},
                5:{TYPE:UInt32, NAME:"Characteristics"},
                }

    XBE_Sec_Headers = { TYPE:Array, NAME:"Section_Headers",
                        SIZE:'.XBE_Image_Header.Section_Count',
                        POINTER:(lambda *a, **k:
                                 XBE_Def.Base_Rel_Pointer(*a,
                                 P_Path='.XBE_Image_Header.Section_Headers_Address',**k)),
                        SUB_STRUCT:XBE_Sec_Header,
                        }

    XBE_Lib_Ver_Headers = { TYPE:Array, NAME:"Lib_Ver_Headers",
                            SIZE:'.XBE_Image_Header.Lib_Vers_Count',
                            POINTER:(lambda *a, **k:
                                     XBE_Def.Base_Rel_Pointer(*a,
                                     P_Path='.XBE_Image_Header.Lib_Vers_Address',**k)),
                            SUB_STRUCT:XBE_Lib_Ver,
                            }

    Tag_Structure = { TYPE:Container, NAME:"Xbox_Executable",
                      0:XBE_Image_Header,
                      1:XBE_Certificate,
                      2:XBE_Sec_Headers,
                      3:XBE_Lib_Ver_Headers
                      }
