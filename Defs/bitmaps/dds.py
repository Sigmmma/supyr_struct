from supyr_struct.Defs.Tag_Def import *


def Construct():
    return DDS_Def

class DDS_Def(Tag_Def):
    
    Ext = ".dds"

    Cls_ID = "dds"

    Endian = "<"

    DDS_Header_DX10 = { TYPE:Struct, NAME:"DXT10_Header",
                        0:{ TYPE:Enum32, NAME:"Format",
                            0:{ NAME:"Unknown",               VALUE:0 },
                            1:{ NAME:"R32G32B32A32_TYPELESS", VALUE:1 },
                            2:{ NAME:"R32G32B32A32_FLOAT",    VALUE:2 },
                            3:{ NAME:"R32G32B32A32_UINT",     VALUE:3 },
                            4:{ NAME:"R32G32B32A32_SINT",     VALUE:4 },
                            5:{ NAME:"R32G32B32_TYPELESS",    VALUE:5 },
                            6:{ NAME:"R32G32B32_FLOAT",       VALUE:6 },
                            7:{ NAME:"R32G32B32_UINT",        VALUE:7 },
                            8:{ NAME:"R32G32B32_SINT",        VALUE:8 },
                            9:{ NAME:"R16G16B16A16_TYPELESS", VALUE:9 },
                            10:{ NAME:"R16G16B16A16_FLOAT",   VALUE:10 },
                            11:{ NAME:"R16G16B16A16_UNORM",   VALUE:11 },
                            12:{ NAME:"R16G16B16A16_UINT",    VALUE:12 },
                            13:{ NAME:"R16G16B16A16_SNORM",   VALUE:13 },
                            14:{ NAME:"R16G16B16A16_SINT",    VALUE:14 },
                            15:{ NAME:"R32G32_TYPELESS",      VALUE:15 },
                            16:{ NAME:"R32G32_FLOAT",         VALUE:16 },
                            17:{ NAME:"R32G32_UINT",          VALUE:17 },
                            18:{ NAME:"R32G32_SINT",          VALUE:18 },
                            19:{ NAME:"R32G8X24_TYPELESS",    VALUE:19 },
                            20:{ NAME:"D32_FLOAT_S8X24_UINT", VALUE:20 },
                            21:{ NAME:"R32_FLOAT_X8X24_TYPELESS", VALUE:21 },
                            22:{ NAME:"X32_TYPELESS_G8X24_UINT",  VALUE:22 },
                            23:{ NAME:"R10G10B10A2_TYPELESS",  VALUE:23 },
                            24:{ NAME:"R10G10B10A2_UNORM",     VALUE:24 },
                            25:{ NAME:"R10G10B10A2_UINT",      VALUE:25 },
                            26:{ NAME:"R11G11B10_FLOAT",       VALUE:26 },
                            27:{ NAME:"R8G8B8A8_TYPELESS",     VALUE:27 },
                            28:{ NAME:"R8G8B8A8_UNORM",        VALUE:28 },
                            29:{ NAME:"R8G8B8A8_UNORM_SRGB",   VALUE:29 },
                            30:{ NAME:"R8G8B8A8_UINT",         VALUE:30 },
                            31:{ NAME:"R8G8B8A8_SNORM",        VALUE:31 },
                            32:{ NAME:"R8G8B8A8_SINT",         VALUE:32 },
                            33:{ NAME:"R16G16_TYPELESS",       VALUE:33 },
                            34:{ NAME:"R16G16_FLOAT",          VALUE:34 },
                            35:{ NAME:"R16G16_UNORM",          VALUE:35 },
                            36:{ NAME:"R16G16_UINT",           VALUE:36 },
                            37:{ NAME:"R16G16_SNORM",          VALUE:37 },
                            38:{ NAME:"R16G16_SINT",           VALUE:38 },
                            39:{ NAME:"R32_TYPELESS",          VALUE:39 },
                            40:{ NAME:"D32_FLOAT",             VALUE:40 },
                            41:{ NAME:"R32_FLOAT",             VALUE:41 },
                            42:{ NAME:"R32_UINT",              VALUE:42 },
                            43:{ NAME:"R32_SINT",              VALUE:43 },
                            44:{ NAME:"R24G8_TYPELESS",        VALUE:44 },
                            45:{ NAME:"D24_UNORM_S8_UINT",     VALUE:45 },
                            46:{ NAME:"R24_UNORM_X8_TYPELESS", VALUE:46 },
                            47:{ NAME:"X24_TYPELESS_G8_UINT",  VALUE:47 },
                            48:{ NAME:"R8G8_TYPELESS",         VALUE:48 },
                            49:{ NAME:"R8G8_UNORM",            VALUE:49 },
                            50:{ NAME:"R8G8_UINT",             VALUE:50 },
                            51:{ NAME:"R8G8_SNORM",            VALUE:51 },
                            52:{ NAME:"R8G8_SINT",             VALUE:52 },
                            53:{ NAME:"R16_TYPELESS",          VALUE:53 },
                            54:{ NAME:"R16_FLOAT",             VALUE:54 },
                            55:{ NAME:"D16_UNORM",             VALUE:55 },
                            56:{ NAME:"R16_UNORM",             VALUE:56 },
                            57:{ NAME:"R16_UINT",              VALUE:57 },
                            58:{ NAME:"R16_SNORM",             VALUE:58 },
                            59:{ NAME:"R16_SINT",              VALUE:59 },
                            60:{ NAME:"R8_TYPELESS",           VALUE:60 },
                            61:{ NAME:"R8_UNORM",              VALUE:61 },
                            62:{ NAME:"R8_UINT",               VALUE:62 },
                            63:{ NAME:"R8_SNORM",              VALUE:63 },
                            64:{ NAME:"R8_SINT",               VALUE:64 },
                            65:{ NAME:"A8_UNORM",              VALUE:65 },
                            66:{ NAME:"R1_UNORM",              VALUE:66 },
                            67:{ NAME:"R9G9B9E5_SHAREDEXP",    VALUE:67 },
                            68:{ NAME:"R8G8_B8G8_UNORM",       VALUE:68 },
                            69:{ NAME:"G8R8_G8B8_UNORM",       VALUE:69 },
                            70:{ NAME:"BC1_TYPELESS",          VALUE:70 },
                            71:{ NAME:"BC1_UNORM",             VALUE:71 },
                            72:{ NAME:"BC1_UNORM_SRGB",        VALUE:72 },
                            73:{ NAME:"BC2_TYPELESS",          VALUE:73 },
                            74:{ NAME:"BC2_UNORM",             VALUE:74 },
                            75:{ NAME:"BC2_UNORM_SRGB",        VALUE:75 },
                            76:{ NAME:"BC3_TYPELESS",          VALUE:76 },
                            77:{ NAME:"BC3_UNORM",             VALUE:77 },
                            78:{ NAME:"BC3_UNORM_SRGB",        VALUE:78 },
                            79:{ NAME:"BC4_TYPELESS",          VALUE:79 },
                            80:{ NAME:"BC4_UNORM",             VALUE:80 },
                            81:{ NAME:"BC4_SNORM",             VALUE:81 },
                            82:{ NAME:"BC5_TYPELESS",          VALUE:82 },
                            83:{ NAME:"BC5_UNORM",             VALUE:83 },
                            84:{ NAME:"BC5_SNORM",             VALUE:84 },
                            85:{ NAME:"B5G6R5_UNORM",          VALUE:85 },
                            86:{ NAME:"B5G5R5A1_UNORM",        VALUE:86 },
                            87:{ NAME:"B8G8R8A8_UNORM",        VALUE:87 },
                            88:{ NAME:"B8G8R8X8_UNORM",        VALUE:88 },
                            89:{ NAME:"R10G10B10_XR_BIAS_A2_UNORM", VALUE:89 },
                            90:{ NAME:"B8G8R8A8_TYPELESS",     VALUE:90 },
                            91:{ NAME:"B8G8R8A8_UNORM_SRGB",   VALUE:91 },
                            92:{ NAME:"B8G8R8X8_TYPELESS",     VALUE:92 },
                            93:{ NAME:"B8G8R8X8_UNORM_SRGB",   VALUE:93 },
                            94:{ NAME:"BC6H_TYPELESS",   VALUE:94 },
                            95:{ NAME:"BC6H_UF16",       VALUE:95 },
                            96:{ NAME:"BC6H_SF16",       VALUE:96 },
                            97:{ NAME:"BC7_TYPELESS",    VALUE:97 },
                            98:{ NAME:"BC7_UNORM",       VALUE:98 },
                            99:{ NAME:"BC7_UNORM_SRGB",  VALUE:99 },
                            100:{ NAME:"AYUV",           VALUE:100 },
                            101:{ NAME:"Y410",           VALUE:101 },
                            102:{ NAME:"Y416",           VALUE:102 },
                            103:{ NAME:"NV12",           VALUE:103 },
                            104:{ NAME:"P010",           VALUE:104 },
                            105:{ NAME:"P016",           VALUE:105 },
                            106:{ NAME:"420_OPAQUE",     VALUE:106 },
                            107:{ NAME:"YUY2",           VALUE:107 },
                            108:{ NAME:"Y210",           VALUE:108 },
                            109:{ NAME:"Y216",           VALUE:109 },
                            110:{ NAME:"NV11",           VALUE:110 },
                            111:{ NAME:"AI44",           VALUE:111 },
                            112:{ NAME:"IA44",           VALUE:112 },
                            113:{ NAME:"P8",             VALUE:113 },
                            114:{ NAME:"A8P8",           VALUE:114 },
                            115:{ NAME:"B4G4R4A4_UNORM", VALUE:115 },
                            116:{ NAME:"P208",           VALUE:130 },
                            117:{ NAME:"V208",           VALUE:131 },
                            118:{ NAME:"V408",           VALUE:132 }
                            },
                        1:{ TYPE:Enum32, NAME:"Resource_Dimension",
                            0:{ NAME:"Texture_1D", VALUE:0x2 },
                            1:{ NAME:"Texture_2D", VALUE:0x3 },
                            2:{ NAME:"Texture_3D", VALUE:0x4 },
                            },
                        2:{ TYPE:Bool32, NAME:"Flags",
                            0:{ NAME:"Cubemap", VALUE:0x4 }
                            },
                        3:{ TYPE:UInt32, NAME:"Array_Size", DEFAULT:1 },
                        4:{ TYPE:Bool32, NAME:"Flags_2",
                            0:{ NAME:"Unknown",       VALUE:0x0 },
                            1:{ NAME:"Straight",      VALUE:0x1 },
                            2:{ NAME:"Premultiplied", VALUE:0x2 },
                            3:{ NAME:"Opaque",        VALUE:0x3 },
                            4:{ NAME:"Custom",        VALUE:0x4 }
                            }
                        }

    DDS_Header_XBOX = Combine( { 5:{ TYPE:UInt32, NAME:"XG_Tile_Mode" },
                                 6:{ TYPE:UInt32, NAME:"Base_Alignment" },
                                 7:{ TYPE:UInt32, NAME:"Data_Size" },
                                 8:{ TYPE:UInt32, NAME:"XDK_Ver" },
                                 },
                               DDS_Header_DX10 )

    DDS_Pixelformat = { TYPE:Struct, NAME:'DDS_Pixelformat',
                        0:{ TYPE:UInt32, NAME:"Size",
                            DEFAULT:32, MIN:32, MAX:32 },
                        1:{ TYPE:Bool32, NAME:"Flags",
                            0:{ NAME:"Has_Alpha",  VALUE:0x000001 },
                            1:{ NAME:"Alpha_Only", VALUE:0x000002 },
                            2:{ NAME:"FourCC",     VALUE:0x000004 },
                            3:{ NAME:"RGB",        VALUE:0x000040 },
                            4:{ NAME:"YUV",        VALUE:0x000200 },
                            5:{ NAME:"Luminance",  VALUE:0x020000 },
                            6:{ NAME:"U8V8",       VALUE:0x080000 },
                            },
                        2:{ TYPE:Enum32, NAME:"FourCC", DEFAULT:0,
                            0:{ NAME:"None", VALUE:0 },
                            1:{ NAME:"DXT1", VALUE:StrToInt('DXT1') },
                            2:{ NAME:"DXT2", VALUE:StrToInt('DXT2') },
                            3:{ NAME:"DXT3", VALUE:StrToInt('DXT3') },
                            4:{ NAME:"DXT4", VALUE:StrToInt('DXT4') },
                            5:{ NAME:"DXT5", VALUE:StrToInt('DXT5') },
                            6:{ NAME:"DXN",  VALUE:StrToInt('ATI2') },
                            7:{ NAME:"UYVY", VALUE:StrToInt('UYVY') },
                            8:{ NAME:"YUY2", VALUE:StrToInt('YUY2') },
                            9:{ NAME:"DX10", VALUE:StrToInt('DX10') },
                            10:{ NAME:"XBOX", VALUE:StrToInt('XBOX') },
                            11:{ NAME:"BC4U", VALUE:StrToInt('BC4U') },
                            12:{ NAME:"BC4S", VALUE:StrToInt('BC4S') },
                            13:{ NAME:"BC5S", VALUE:StrToInt('BC5S') },
                            14:{ NAME:"RGBG", VALUE:StrToInt('RGBG') },
                            15:{ NAME:"GRGB", VALUE:StrToInt('GRGB') },
                            16:{ NAME:"RGBA_16_UNORM", VALUE:36},
                            17:{ NAME:"RGBA_16_SNORM", VALUE:110},
                            18:{ NAME:"R_16_FLOAT",    VALUE:111},
                            19:{ NAME:"RG_16_FLOAT",   VALUE:112},
                            20:{ NAME:"RGBA_16_FLOAT", VALUE:113},
                            21:{ NAME:"R_32_FLOAT",    VALUE:114},
                            22:{ NAME:"RG_32_FLOAT",   VALUE:115},
                            23:{ NAME:"RGBA_32_FLOAT", VALUE:116},
                            24:{ NAME:"CxV8U8",        VALUE:117}
                            },
                        3:{ TYPE:UInt32, NAME:"RGBBitCount" },
                        4:{ TYPE:UInt32, NAME:"RBitMask" },
                        5:{ TYPE:UInt32, NAME:"GBitMask" },
                        6:{ TYPE:UInt32, NAME:"BBitMask" },
                        7:{ TYPE:UInt32, NAME:"ABitMask" },
                        }
    
    Tag_Structure = { TYPE:Container, NAME:"DDS_Bitmap",
                      0:{ TYPE:Struct, NAME:"Header",
                          0:{ TYPE:UInt32, NAME:"Magic",
                              DEFAULT:StrToInt('DDS '), EDITABLE:False },
                          1:{ TYPE:UInt32, NAME:"Size",
                              DEFAULT:124, MIN:124, MAX:124 },
                          2:{ TYPE:Bool32, NAME:"Flags",
                              0:{ NAME:"Caps",        VALUE:0x000001, DEFAULT:True },
                              1:{ NAME:"Height",      VALUE:0x000002, DEFAULT:True },
                              2:{ NAME:"Width",       VALUE:0x000004, DEFAULT:True },
                              3:{ NAME:"Pitch",       VALUE:0x000008 },
                              4:{ NAME:"Pixelformat", VALUE:0x001000, DEFAULT:True },
                              5:{ NAME:"Mipmaps",     VALUE:0x020000 },
                              6:{ NAME:"Linearsize",  VALUE:0x080000 },
                              7:{ NAME:"Depth",       VALUE:0x800000 }
                              },
                          3:{ TYPE:UInt32, NAME:"Height" },
                          4:{ TYPE:UInt32, NAME:"Width" },
                          5:{ TYPE:UInt32, NAME:"Pitch_or_Linearsize" },
                          6:{ TYPE:UInt32, NAME:"Depth" },
                          7:{ TYPE:UInt32, NAME:"Mipmap_Count" },
                          8:{ TYPE:Pad, SIZE:4*11 },
                          9:DDS_Pixelformat,
                          10:{ TYPE:Bool32, NAME:"Caps",
                              0:{ NAME:"Complex", VALUE:0x000008 },
                              1:{ NAME:"Texture", VALUE:0x001000, DEFAULT:True },
                              2:{ NAME:"Mipmaps", VALUE:0x400000 }
                              },
                          11:{ TYPE:Bool32, NAME:"Caps_2",
                              0:{ NAME:"Cubemap", VALUE:0x000200 },
                              1:{ NAME:"Pos_X",   VALUE:0x000400 },
                              2:{ NAME:"Neg_X",   VALUE:0x000800 },
                              3:{ NAME:"Pos_Y",   VALUE:0x001000 },
                              4:{ NAME:"Neg_Y",   VALUE:0x002000 },
                              5:{ NAME:"Pos_Z",   VALUE:0x004000 },
                              6:{ NAME:"Neg_Z",   VALUE:0x008000 },
                              7:{ NAME:"Volume",  VALUE:0x200000 }
                              },
                          12:{ TYPE:Bool32, NAME:"Caps3" },
                          13:{ TYPE:Bool32, NAME:"Caps4" },
                          14:{ TYPE:Pad, SIZE:4 }
                          },
                          1:{ TYPE:Switch, NAME:"DXT10_Header",
                              CASE:".Header.DDS_Pixelformat.FourCC.Data_Name",
                              CASES:{ 'DX10':DDS_Header_DX10,
                                      'XBOX':DDS_Header_XBOX}
                              },
                          2:{ TYPE:Switch, NAME:"Pixel_Data",
                              #need to finish this up and include all
                              #the different pixel data structures that
                              #can be in a dds file and a case selector.
                              CASE:0,
                              CASES:{},
                              DEFAULT:{ TYPE:Container, NAME:"Remaining_Data",
                                        0:Remaining_Data }
                              }
                 }

    Structures = {"DDS_Header_DX10":DDS_Header_DX10,
                  "DDS_Header_XBOX":DDS_Header_XBOX,
                  "DDS_Pixelformat":DDS_Pixelformat,}
