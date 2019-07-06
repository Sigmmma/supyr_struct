'''
All structure definitions within this file
were written using the work of Caustik.
Information can be found on his website:
   http://www.caustik.com/cxbx/download/xbe.htm

Their e-mail address is:
caustik@caustik.com
'''

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *

__all__ = ("xbe_def", "get", )


def get(): return xbe_def

XBE_HEADER_MAGIC = 0x48454258


def base_rel_pointer(node=None, parent=None, attr_index=None,
                     rawdata=None, new_value=None, **kwargs):
    '''
    Pointer getter/setter for getting and setting pointers
    relative to the base_address in the xbe_image_header.
    '''

    path = kwargs.get("p_path")

    if parent is None:
        raise KeyError("Cannot get or set base address relative " +
                       "pointers without the parent.")
    if path == '':
        raise KeyError("Cannot get or set base address relative " +
                       "pointers without a path to the pointer.")

    this_tag = parent.get_root()
    base_addr = this_tag.data.xbe_image_header.base_address

    if new_value is None:
        return parent.get_neighbor(path) - base_addr
    return parent.set_neighbor(path, new_value + base_addr)


xbe_image_header = Struct("xbe_image_header",
    UInt32("xbe_magic", DEFAULT=XBE_HEADER_MAGIC),
    BytearrayRaw("digital_signature", SIZE=256),
    Pointer32("base_address"),
    UInt32("headers_size"),
    UInt32("image_size"),
    UInt32("image_header_size"),
    Timestamp32("time_date"),
    Pointer32("certificate_address"),
    UInt32("section_count"),
    Pointer32("section_headers_address"),
    Bool32("init_flags",
        "mount_utility_drive",
        "format_utility_drive",
        "limit_64mb",
        "dont_setup_hdd"
        ),
    # Entry Point is encoded with an XOR key.
    # The XOR key used depends on the XBE build.
    # debug  = 0x94859D4B
    # retail = 0xA8FC57AB
    UInt32("entry_point"),
    UInt32("tls_address"),
    UInt32("pe_stack_commit"),
    UInt32("pe_heap_reserve"),
    UInt32("pe_heap_commit"),
    UInt32("pe_base_address"),
    UInt32("pe_image_size"),
    UInt32("pe_checksum"),
    Timestamp32("pe_time_date"),
    Pointer32("debug_path_address"),
    Pointer32("debug_file_address"),
    Pointer32("debug_unicode_file_address"),

    # Kernel Image Thunk Address is encoded with an XOR key.
    # The XOR key used depends on the XBE build.
    # debug  = 0xEFB1F152
    # retail = 0x5B6D40B6
    UInt32("kernel_image_thunk_address"),
    Pointer32("non_kernel_import_dir_address"),
    UInt32("lib_vers_count"),
    Pointer32("lib_vers_address"),
    Pointer32("kernel_lib_ver_address"),
    Pointer32("xapi_lib_ver_address"),
    Pointer32("logo_bitmap_address"),
    UInt32("logo_bitmap_size"),
    STEPTREE=Container("debug_strings",
        CStrLatin1("debug_path",
            POINTER=lambda *a, **k: base_rel_pointer(
                *a, p_path='..debug_path_address', **k)
            ),
        CStrLatin1("debug_file",
            POINTER=lambda *a, **k: base_rel_pointer(
                *a, p_path='..debug_file_address', **k)
            ),
        CStrUtf16("debug_unicode_file",
            POINTER=lambda *a, **k: base_rel_pointer(
                *a, p_path='..debug_unicode_file_address', **k)
            )
        )
    )

xbe_certificate = Struct("xbe_certificate",
    UInt32("struct_size", EDITABLE=False, DEFAULT=464),
    Timestamp32("time_date"),

    # least significant 2 bytes of title ID are treated as
    # an int and most significant 2 are a 2 char string.
    BytearrayRaw("title_id",  SIZE=4),
    StrNntUtf16("title_name", SIZE=80),
    UInt32Array("alt_title_ids", SIZE=64),
    Bool32("allowed_media",
        "hdd",
        "dvd_x2",
        "dvd_cd",
        "cd",
        "dvd_5_ro",
        "dvd_9_ro",
        "dvd_5_rw",
        "dvd_9_rw",
        "usb",
        "media_board",
        ("nonsecure_hard_disk", 0x40000000),
        ("nonsecure_mode",      0x80000000)
        ),
    Bool32("game_region",
        "usa_canada",
        "japan",
        "rest_of_world",
        ("debug", 0x80000000)
        ),
    UEnum32("game_ratings",
        "rp",  # All
        "ao",  # Adult only
        "m",   # Mature
        "t",   # Teen
        "e",   # Everyone
        "ka",  # Kids_to_Adults
        "ec"   # Early_Childhood
        ),
    UInt32("disk_number"),
    UInt32("version"),
    BytearrayRaw("lan_key", SIZE=16),
    BytearrayRaw("signature_key", SIZE=16),
    BytearrayRaw("alt_signature_keys", SIZE=256),

    SIZE=464,
    POINTER=lambda *a, **k: base_rel_pointer(
        *a, p_path='.xbe_image_header.certificate_address', **k),
    )

xbe_sec_header = Struct("xbe_section_header",
    Bool32("flags",
        "writable",
        "preload",
        "executable",
        "inserted_file",
        "head_page_read_only",
        "tail_page_read_only"
        ),
    UInt32("virtual_address"),
    UInt32("virtual_size"),
    Pointer32("raw_address"),
    UInt32("raw_size"),
    Pointer32("section_name_address"),
    UInt32("section_name_ref_count"),
    Pointer32("head_shared_page_ref_count_address"),
    Pointer32("tail_shared_page_ref_count_address"),
    BytearrayRaw("section_digest", SIZE=20),
    STEPTREE=CStrLatin1('section_name',
        POINTER=lambda *a, **k: base_rel_pointer
                (*a, p_path='.section_name_address', **k)
        )
    )

xbe_lib_ver = Struct("xbe_lib_version",
    StrNntLatin1("library_name", SIZE=8),
    UInt16("major_ver"),
    UInt16("minor_ver"),
    UInt16("build_ver"),
    BitStruct("flags",
        UBitInt("qfe_ver", SIZE=13),
        UBitEnum("approved",
            "no",
            "maybe",
            "yes",
            SIZE=2
            ),
        Bit("debug_build")
        )
    )

xbe_tls = QuickStruct("xbe_tls",
    UInt32("data_start_address"),
    UInt32("data_end_address"),
    UInt32("tls_index_address"),
    UInt32("tls_callback_address"),
    UInt32("size_of_zero_fill"),
    UInt32("characteristics")
    )

xbe_sec_headers = Array("section_headers",
    SIZE='.xbe_image_header.section_count',
    POINTER=(lambda *a, **k:
        base_rel_pointer(*a,
        p_path='.xbe_image_header.section_headers_address', **k)),
    SUB_STRUCT=xbe_sec_header,
    )

xbe_lib_ver_headers = Array("lib_ver_headers",
    SIZE='.xbe_image_header.lib_vers_count',
    POINTER=(lambda *a, **k:
        base_rel_pointer(*a,
        p_path='.xbe_image_header.lib_vers_address', **k)),
    SUB_STRUCT=xbe_lib_ver,
    )

xbe_def = TagDef("xbox_executable",
    xbe_image_header,
    xbe_certificate,
    xbe_sec_headers,
    xbe_lib_ver_headers,

    ext=".xbe", endian="<", incomplete=True
    )
