'''
    All structure definitions within this file
    were written using the work of Caustik.
    Information can be found on his website:
       http://www.caustik.com/cxbx/download/xbe.htm

    Their e-mail address is:
    caustik@caustik.com
'''

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.common_descriptors import *
from supyr_struct.fields import *

def get(): return xbe_def

XBE_HEADER_MAGIC = 0x48454258

def base_rel_pointer(block=None, parent=None, attr_index=None,
                     rawdata=None, new_value=None, *args, **kwargs):       
    '''Used for getting and setting pointers relative
    to the XBE Base Address in the XBE Image Header.'''
    
    path    = kwargs.get("p_path")
    
    if parent is None:
        raise KeyError("Cannot get or set base address relative "+
                       "pointers without the parent block.")
    if path == '':
        raise KeyError("Cannot get or set base address relative "+
                       "pointers without a path to the pointer.")
    
    this_tag  = parent.tag
    base_addr = this_tag.data.xbe_image_header.base_address
    
    if new_value is None:
        return parent.get_neighbor(path)-base_addr
    return parent.set_neighbor(path, new_value+base_addr)

    
xbe_image_header = Struct("xbe_image_header",
    LUInt32("xbe_magic", DEFAULT=XBE_HEADER_MAGIC),
    BytearrayRaw("digital_signature", SIZE=256),
    LPointer32("base_address"),
    LUInt32("headers_size"),
    LUInt32("image_size"),
    LUInt32("image_header_size"),
    LTimestamp("time_date"),
    LPointer32("certificate_address"),
    LUInt32("section_count"),
    LPointer32("section_headers_address"),
    LBool32("init_flags",
        "mount_utility_drive",
        "format_utility_drive",
        "limit_64mb",
        "dont_setup_hdd"
        ),
    #Entry Point is encoded with an XOR key.
    #The XOR key used depends on the XBE build.
    #debug  = 0x94859D4B
    #Retail = 0xA8FC57AB
    LUInt32("entry_point"),
    LUInt32("tls_address"),
    LUInt32("pe_stack_commit"),
    LUInt32("pe_heap_reserve"),
    LUInt32("pe_heap_commit"),
    LUInt32("pe_base_address"),
    LUInt32("pe_image_size"),
    LUInt32("pe_checksum"),
    LTimestamp("pe_time_date"),
    LPointer32("debug_path_address"),
    LPointer32("debug_file_address"),
    LPointer32("debug_unicode_file_address"),

    #Kernel Image Thunk Address is encoded with an XOR key.
    #The XOR key used depends on the XBE build.
    #debug  = 0xEFB1F152
    #Retail = 0x5B6D40B6
    LUInt32("kernel_image_thunk_address"),
    LPointer32("non_kernel_import_dir_address"),      
    LUInt32("lib_vers_count"),
    LPointer32("lib_vers_address"),
    LPointer32("kernel_lib_ver_address"),
    LPointer32("xapi_lib_ver_address"),
    LPointer32("logo_bitmap_address"),
    LUInt32("logo_bitmap_size"),
    CHILD=Container("debug_strings",
        CStrLatin1("debug_path",
            POINTER=lambda *a, **k: base_rel_pointer\
                (*a,p_path='..debug_path_address',**k)
            ),
        CStrLatin1("debug_file",
            POINTER=lambda *a, **k: base_rel_pointer\
                (*a,p_path='..debug_file_address',**k)
            ),
        CStrUtf16("debug_unicode_file",
            POINTER=lambda *a, **k: base_rel_pointer\
                (*a,p_path='..debug_unicode_file_address',**k)
            )
        )
    )

xbe_certificate = Struct("xbe_certificate",
    LUInt32("struct_size", EDITABLE=False, DEFAULT=464),
    LTimestamp("time_date"),

    #least significant 2 bytes of title ID are treated as
    #an int and most significant 2 are a 2 char string.
    BytearrayRaw("title_id",  SIZE=4),
    LStrRawUtf16("title_name", SIZE=80),
    LUInt32Array("alt_title_ids", SIZE=64),
    LBool32("allowed_media",
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
    LUEnum32("game_region",
        "usa_canada",
        "japan",
        "rest_of_world",
        ("debug", 0x80000000)
        ),
    LUEnum32("game_ratings",
        "rp",#All
        "ao",#Adult only
        "m", #Mature
        "t", #Teen
        "e", #Everyone
        "ka",#Kids_to_Adults
        "ec" #Early_Childhood
        ),
    LUInt32("disk_number"),
    LUInt32("version"),
    BytearrayRaw("lan_key", SIZE=16),
    BytearrayRaw("signature_key", SIZE=16),
    BytearrayRaw("alt_signature_keys", SIZE=256),

    SIZE=464,
    POINTER=lambda *a, **k: base_rel_pointer\
        (*a, p_path='.xbe_image_header.certificate_address',**k),
    )

xbe_sec_header = Struct("xbe_section_header",
    LBool32("flags",
        "writable",
        "preload",
        "executable",
        "inserted_file",
        "head_page_read_only",
        "tail_page_read_only"
        ),
    LUInt32("virtual_address"),
    LUInt32("virtual_size"),
    LPointer32("raw_address"),
    LUInt32("raw_size"),
    LPointer32("section_name_address"),
    LUInt32("section_name_ref_count"),
    LPointer32("head_shared_page_ref_count_address"),
    LPointer32("tail_shared_page_ref_count_address"),
    BytearrayRaw("section_digest", SIZE=20),
    CHILD=CStrLatin1('section_name',
        POINTER=(lambda *a, **k: base_rel_pointer\
            (*a, p_path='.section_name_address',**k))
        )
    )

xbe_lib_ver = Struct("xbe_lib_version",
    StrRawLatin1("library_name", SIZE=8),
    LUInt16("major_ver"),
    LUInt16("minor_ver"),
    LUInt16("build_ver"),
    LBitStruct("flags",
        BitUInt("qfe_ver",   SIZE=13),
        BitUEnum("approved",
            "no",
            "maybe",
            "yes",
            SIZE=2
            ),
        Bit("debug_build")
        )
    )

xbe_tls = Struct("xbe_tls",
    LUInt32("data_start_address"),
    LUInt32("data_end_address"),
    LUInt32("tls_index_address"),
    LUInt32("tls_callback_address"),
    LUInt32("size_of_zero_fill"),
    LUInt32("characteristics")
    )

xbe_sec_headers = Array("section_headers",
    SIZE='.xbe_image_header.section_count',
    POINTER=(lambda *a, **k:
        base_rel_pointer(*a,
        p_path='.xbe_image_header.section_headers_address',**k)),
    SUB_STRUCT=xbe_sec_header,
    )

xbe_lib_ver_headers = Array("lib_ver_headers",
    SIZE='.xbe_image_header.lib_vers_count',
    POINTER=(lambda *a, **k:
        base_rel_pointer(*a,
        p_path='.xbe_image_header.lib_vers_address',**k)),
    SUB_STRUCT=xbe_lib_ver,
    )

xbe_def = TagDef(
    xbe_image_header,
    xbe_certificate,
    xbe_sec_headers,
    xbe_lib_ver_headers,
    NAME="xbox_executable",

    ext=".xbe", def_id="xbe", incomplete=True)
