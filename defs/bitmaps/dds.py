'''
Dual-Draw Surface image file definitions

Structures were pieced together from various online sources.

Look here for a description of most of these formats.
https://msdn.microsoft.com/en-us/library/windows/desktop/bb153349(v=vs.85).aspx
'''

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.constants import NAME, VALUE, DEFAULT
from supyr_struct.field_types import *
from supyr_struct.defs.common_descs import remaining_data_length

__all__ = ("dds_def", "get", )


def get(): return dds_def

pixelformat_typecodes = (
    # the enum_names of these should NOT be changed as Arbytmap uses them
    ("None", 0),
    ("DXT1", '1TXD'),
    ("DXT2", '2TXD'),
    ("DXT3", '3TXD'),
    ("DXT4", '4TXD'),
    ("DXT5", '5TXD'),
    ("DXN",  '2ITA'),
    ("UYVY", 'YVYU'),
    ("YUY2", '2YUY'),
    ("DX10", '01XD'),
    ("XBOX", 'XOBX'),
    ("BC4U", 'U4CB'),
    ("BC4S", 'S4CB'),
    ("BC5U", 'U5CB'),
    ("BC5S", 'S5CB'),
    ("RGBG", 'GBGR'),
    ("GRGB", 'BGRG'),
    ("MULTI2_ARGB8", '1TEM'),

    ("R8G8B8",   20),
    ("A8R8G8B8", 21),
    ("X8R8G8B8", 22),
    ("R5G6B5",   23),
    ("X1R5G5B5", 24),
    ("A1R5G5B5", 25),
    ("A4R4G4B4", 26),
    ("R3G3B2",   27),
    ("A8",       28),
    ("A8R3G3B2", 29),
    ("X4R4G4B4", 30),
    ("A2B10G10R10",  31),
    ("A8B8G8R8",     32),
    ("X8B8G8R8",     33),
    ("G16R16",       34),
    ("A2R10G10B10",  35),
    ("A16B16G16R16", 36),

    ("A8P8", 40),
    ("P8",   41),

    ("L8",   50),
    ("A8L8", 51),
    ("A4L4", 52),

    ("V8U8",        60),
    ("L5V5U5",      61),
    ("X8L8V8U8",    62),
    ("Q8W8V8U8",    63),
    ("V16U16",      64),
    ("A2W10V10U10", 65),

    ("D16_LOCKABLE", 70),
    ("D32",          71),
    #("????",        72),
    ("D15S1",        73),
    #("????",        74),
    ("D24S8",        75),
    #("????",        76),
    ("D24X8",        77),
    #("????",        78),
    ("D24X4S4",      79),
    ("D16",          80),

    ("L16",           81),
    ("D32F_LOCKABLE", 82),
    ("D24FS8",        83),
    ("D32_LOCKABLE",  84),
    ("S8_LOCKABLE",   85),

    ("VERTEXDATA",     100),
    ("INDEX16",        101),
    ("INDEX32",        102),

    ("Q16W16V16U16",   110),
    ("R16_F",          111),
    ("G16R16_F",       112),
    ("A16B16G16R16_F", 113),
    ("R32_F",          114),
    ("G32R32_F",       115),
    ("A32B32G32R32_F", 116),
    ("CxV8U8",         117),

    ("A1",                  118),
    ("A2B10G10R10_XR_BIAS", 119),
    ("BINARYBUFFER",        199),

    # These are all Xbox 360 formats
    # LIN stands for linear, and means the textures are NOT swizzled
    ("LIN_DXT1",      0x1A200052),
    ("LIN_DXT2",      0x9A200053),
    ("LIN_DXT3",      0x1A200053),
    ("LIN_DXT4",      0x9A200054),
    ("LIN_DXT5",      0x1A200054),
    ("LIN_DXN",       0x1A200071),
    ("LIN_DXT3A",     0x1A20007A),
    ("LIN_DXT5A",     0x1A20007B),
    ("LIN_CTX1",      0x1A20007C),
    ("LIN_G8R8_G8B8", 0x1828004C),
    ("LIN_UYVY",      0x5A20004C),

    # These are all Halo 3+ formats, and are tiled
    ("TILED_Y8",        0x28000102),
    ("TILED_AY8",       0x1A200102),
    ("TILED_UNKNOWN25", 0x1A22AB5D),  # might be a 256 palette of 32bpp
    ("TILED_A8R8G8B8",  0x18287FB2),
    ("TILED_DXT1",      0x1A207F73),
    ("TILED_DXT2",      0x9A207F74), # guess
    ("TILED_DXT3",      0x1A207F74),
    ("TILED_DXT4",      0x9A207F74), # guess
    ("TILED_DXT5",      0x1A207F75),
    ("TILED_DXN",       0x1A215571),
    ("TILED_CTX1",      0x1A21557C),
    ("TILED_DXT3Y",     0x2A207F7A),
    ("TILED_DXT5Y",     0x2A207F7B), # guess
    ("TILED_DXT3A",     0x1A20007A), # TDB
    ("TILED_DXT5A",     0x1A20007B), # TDB
    ("TILED_DXT5AY",    0x08007F71),
    )


dx10_resource_format = UEnum32("format",
    ("Unknown", 0),
    ("R32G32B32A32_TYPELESS", 1),
    ("R32G32B32A32_FLOAT", 2),
    ("R32G32B32A32_UINT",  3),
    ("R32G32B32A32_SINT",  4),
    ("R32G32B32_TYPELESS", 5),
    ("R32G32B32_FLOAT",    6),
    ("R32G32B32_UINT",     7),
    ("R32G32B32_SINT",     8),
    ("R16G16B16A16_TYPELESS", 9),
    ("R16G16B16A16_FLOAT",   10),
    ("R16G16B16A16_UNORM",   11),
    ("R16G16B16A16_UINT",    12),
    ("R16G16B16A16_SNORM",   13),
    ("R16G16B16A16_SINT",    14),
    ("R32G32_TYPELESS",      15),
    ("R32G32_FLOAT",         16),
    ("R32G32_UINT",          17),
    ("R32G32_SINT",          18),
    ("R32G8X24_TYPELESS",    19),
    ("D32_FLOAT_S8X24_UINT", 20),
    ("R32_FLOAT_X8X24_TYPELESS", 21),
    ("X32_TYPELESS_G8X24_UINT",  22),
    ("R10G10B10A2_TYPELESS", 23),
    ("R10G10B10A2_UNORM",    24),
    ("R10G10B10A2_UINT",     25),
    ("R11G11B10_FLOAT",      26),
    ("R8G8B8A8_TYPELESS",    27),
    ("R8G8B8A8_UNORM",       28),
    ("R8G8B8A8_UNORM_SRGB",  29),
    ("R8G8B8A8_UINT",   30),
    ("R8G8B8A8_SNORM",  31),
    ("R8G8B8A8_SINT",   32),
    ("R16G16_TYPELESS", 33),
    ("R16G16_FLOAT", 34),
    ("R16G16_UNORM", 35),
    ("R16G16_UINT",  36),
    ("R16G16_SNORM", 37),
    ("R16G16_SINT",  38),
    ("R32_TYPELESS", 39),
    ("D32_FLOAT",    40),
    ("R32_FLOAT",    41),
    ("R32_UINT",     42),
    ("R32_SINT",     43),
    ("R24G8_TYPELESS",        44),
    ("D24_UNORM_S8_UINT",     45),
    ("R24_UNORM_X8_TYPELESS", 46),
    ("X24_TYPELESS_G8_UINT",  47),
    ("R8G8_TYPELESS", 48),
    ("R8G8_UNORM",    49),
    ("R8G8_UINT",     50),
    ("R8G8_SNORM",    51),
    ("R8G8_SINT",     52),
    ("R16_TYPELESS",  53),
    ("R16_FLOAT",     54),
    ("D16_UNORM",     55),
    ("R16_UNORM",     56),
    ("R16_UINT",      57),
    ("R16_SNORM",     58),
    ("R16_SINT",      59),
    ("R8_TYPELESS",   60),
    ("R8_UNORM",      61),
    ("R8_UINT",       62),
    ("R8_SNORM",      63),
    ("R8_SINT",       64),
    ("A8_UNORM",      65),
    ("R1_UNORM",      66),
    ("R9G9B9E5_SHAREDEXP", 67),
    ("R8G8_B8G8_UNORM", 68),
    ("G8R8_G8B8_UNORM", 69),
    ("BC1_TYPELESS",    70),
    ("BC1_UNORM",       71),
    ("BC1_UNORM_SRGB",  72),
    ("BC2_TYPELESS",    73),
    ("BC2_UNORM",       74),
    ("BC2_UNORM_SRGB",  75),
    ("BC3_TYPELESS",    76),
    ("BC3_UNORM",       77),
    ("BC3_UNORM_SRGB",  78),
    ("BC4_TYPELESS",    79),
    ("BC4_UNORM",       80),
    ("BC4_SNORM",       81),
    ("BC5_TYPELESS",    82),
    ("BC5_UNORM",       83),
    ("BC5_SNORM",       84),
    ("B5G6R5_UNORM",    85),
    ("B5G5R5A1_UNORM",  86),
    ("B8G8R8A8_UNORM",  87),
    ("B8G8R8X8_UNORM",  88),
    ("R10G10B10_XR_BIAS_A2_UNORM", 89),
    ("B8G8R8A8_TYPELESS",   90),
    ("B8G8R8A8_UNORM_SRGB", 91),
    ("B8G8R8X8_TYPELESS",   92),
    ("B8G8R8X8_UNORM_SRGB", 93),
    ("BC6H_TYPELESS",  94),
    ("BC6H_UF16",      95),
    ("BC6H_SF16",      96),
    ("BC7_TYPELESS",   97),
    ("BC7_UNORM",      98),
    ("BC7_UNORM_SRGB", 99),
    ("AYUV", 100),
    ("Y410", 101),
    ("Y416", 102),
    ("NV12", 103),
    ("P010", 104),
    ("P016", 105),
    ("420_OPAQUE", 106),
    ("YUY2", 107),
    ("Y210", 108),
    ("Y216", 109),
    ("NV11", 110),
    ("AI44", 111),
    ("IA44", 112),
    ("P8",   113),
    ("A8P8", 114),
    ("B4G4R4A4_UNORM", 115),
    ("P208", 130),
    ("V208", 131),
    ("V408", 132)
    )

dx10_resource_dimension = UEnum32("resource_dimension",
    "unknown",  # not valid
    "buffer",   # not valid
    "tex_1D",
    "tex_2D",
    "tex_3D",
    )

dx10_misc_flags = Bool32("misc_flag",
    ("cubemap", 1<<2)
    )

dx10_misc_flags2 = BitStruct("misc_flags2",
    UBitEnum("alpha_mode",
        "unknown",
        "straight",
        "premultiplied",
        "opaque",
        "custom",
        SIZE=3
        ),
    SIZE=4
    )

dds_header_dx10 = Struct("dds_header_dx10",
    dx10_resource_format,
    dx10_resource_dimension,
    dx10_misc_flags,
    UInt32("array_size", DEFAULT=1),
    dx10_misc_flags2
    )

dds_header_xbox = Struct("dds_header_xbox",
    dx10_resource_format,
    dx10_resource_dimension,
    dx10_misc_flags,
    UInt32("array_size", DEFAULT=1),
    dx10_misc_flags2,
    UInt32("xg_tile_mode"),
    UInt32("base_alignment"),
    UInt32("data_size"),
    UInt32("xdk_ver")
    )

dds_pixelformat = Struct('dds_pixelformat',
    UInt32("size", DEFAULT=32, MIN=32, MAX=32),
    Bool32("flags",
        ("has_alpha",  1<<0),
        ("alpha_only", 1<<1),
        ("four_cc",    1<<2),
        ("palettized", 1<<3),
        ("rgb_space",  1<<6),
        ("yuv_space",  1<<9),
        ("luminance",  1<<17),
        ("vu_space",   1<<19)
        ),
    UEnum32("four_cc",
        *pixelformat_typecodes,
        DEFAULT=0
        ),
    UInt32("rgb_bitcount"),
    UInt32("r_bitmask"),
    UInt32("g_bitmask"),
    UInt32("b_bitmask"),
    UInt32("a_bitmask")
    )

dds_header = Struct("header",
    UInt32("magic", DEFAULT=' SDD', EDITABLE=False),
    UInt32("size",  DEFAULT=124, MIN=124, MAX=124),
    Bool32("flags",
        {NAME: "caps",   VALUE: 1<<0, DEFAULT: True},
        {NAME: "height", VALUE: 1<<1, DEFAULT: True},
        {NAME: "width",  VALUE: 1<<2, DEFAULT: True},
        ("pitch", 1<<3),
        {NAME: "pixelformat", VALUE: 1<<12, DEFAULT: True},
        ("mipmaps",    1<<17),
        ("linearsize", 1<<19),
        ("depth",      1<<23),
        ),
    UInt32("height"),
    UInt32("width"),
    UInt32("pitch_or_linearsize"),
    UInt32("depth", DEFAULT=1),
    UInt32("mipmap_count", DEFAULT=1),
    Pad(44),
    dds_pixelformat,
    Bool32("caps",
        ("complex", 1<<3),
        {NAME: "texture", VALUE: 1<<12, DEFAULT: True},
        ("mipmaps", 1<<22)
        ),
    Bool32("caps2",
        ("cubemap", 1<<9),
        ("pos_x",   1<<10),
        ("neg_x",   1<<11),
        ("pos_y",   1<<12),
        ("neg_y",   1<<13),
        ("pos_z",   1<<14),
        ("neg_z",   1<<15),
        ("volume",  1<<21)
        ),
    Bool32("caps3"),
    Bool32("caps4"),
    Pad(4)
    )

dds_def = TagDef("dds",
    dds_header,
    Switch("dxt10_header",
        CASE=".header.dds_pixelformat.four_cc.enum_name",
        CASES={'DX10': dds_header_dx10,
               'XBOX': dds_header_xbox}
        ),
    BytesRaw("pixel_data", SIZE=remaining_data_length),

    ext=".dds", endian="<"
    )
