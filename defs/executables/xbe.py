from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.common_descriptors import *
from supyr_struct.fields import *

'''
All structure definitions within this file
were written using the work of Caustik.
Information can be found on his website:
    http://www.caustik.com/cxbx/download/xbe.htm

Their e-mail address is:
caustik@caustik.com
'''

def get():
    return xbe_def

def base_rel_pointer(*args, **kwargs):        
    '''Used for getting and setting pointers relative
    to the XBE Base Address in the XBE Image Header.'''
    
    new_val = kwargs.get("new_value")
    parent  = kwargs.get("parent")
    path    = kwargs.get("p_path")
    
    if parent is None:
        raise KeyError("Cannot get or set base address relative "+
                       "pointers without the parent block.")
    if path == None:
        raise KeyError("Cannot get or set base address relative "+
                       "pointers without a path to the pointer.")
    
    this_tag  = parent.get_tag()
    base_addr = this_tag.tagdata.get_neighbor("xbe_image_header.base_address")
    
    if new_val is None:
        return parent.get_neighbor(path)-base_addr
    else:
        return parent.set_neighbor(path, new_val+base_addr)

    
xbe_image_header = {TYPE:Struct, NAME:"xbe_image_header",
                    0:{TYPE:StrRawLatin1, NAME:"xbe_magic",
                       SIZE:4, DEFAULT:"XBEH"},
                    1:{TYPE:BytearrayRaw, NAME:"digital_signature", SIZE:256},
                    2:{TYPE:Pointer32,  NAME:"base_address"},
                    3:{TYPE:UInt32,     NAME:"headers_size"},
                    4:{TYPE:UInt32,     NAME:"image_size"},
                    5:{TYPE:UInt32,     NAME:"image_header_size"},
                    6:{TYPE:Timestamp,  NAME:"time_date"},
                    7:{TYPE:Pointer32,  NAME:"certificate_address"},
                    8:{TYPE:UInt32,     NAME:"section_count"},
                    9:{TYPE:Pointer32,  NAME:"section_headers_address"},
                    10:{TYPE:Bool32,    NAME:"init_flags",
                        0:{ NAME:"mount_utility_drive" },
                        1:{ NAME:"format_utility_drive" },
                        2:{ NAME:"limit_64mb" },
                        3:{ NAME:"dont_setup_hdd" }
                        },
                    #Entry Point is encoded with an XOR key.
                    #The XOR key used depends on the XBE build.
                    #debug  = 0x94859D4B
                    #Retail = 0xA8FC57AB
                    11:{TYPE:UInt32, NAME:"entry_point"},
                    12:{TYPE:UInt32, NAME:"tls_address"},
                    13:{TYPE:UInt32, NAME:"pe_stack_commit"},
                    14:{TYPE:UInt32, NAME:"pe_heap_reserve"},
                    15:{TYPE:UInt32, NAME:"pe_heap_commit"},
                    16:{TYPE:UInt32, NAME:"pe_base_address"},
                    17:{TYPE:UInt32, NAME:"pe_image_size"},
                    18:{TYPE:UInt32, NAME:"pe_checksum"},
                    19:{TYPE:Timestamp, NAME:"pe_time_date"},
                    20:{TYPE:Pointer32, NAME:"debug_path_address"},
                    21:{TYPE:Pointer32, NAME:"debug_file_address"},
                    22:{TYPE:Pointer32, NAME:"debug_unicode_file_address"},
                    
                    #Kernel Image Thunk Address is encoded with an XOR key.
                    #The XOR key used depends on the XBE build.
                    #debug  = 0xEFB1F152
                    #Retail = 0x5B6D40B6
                    23:{TYPE:UInt32,    NAME:"kernel_image_thunk_address"},
                    24:{TYPE:Pointer32, NAME:"non_kernel_import_dir_address"},      
                    25:{TYPE:UInt32,    NAME:"lib_vers_count"},
                    26:{TYPE:Pointer32, NAME:"lib_vers_address"},
                    27:{TYPE:Pointer32, NAME:"kernel_lib_ver_address"},
                    28:{TYPE:Pointer32, NAME:"xapi_lib_ver_address"},
                    29:{TYPE:Pointer32, NAME:"logo_bitmap_address"},
                    30:{TYPE:UInt32,    NAME:"logo_bitmap_size"},
                    CHILD:{ TYPE:Container, NAME:"debug_strings",
                            0:{ TYPE:CStrLatin1, NAME:"debug_path",
                                POINTER:(lambda *a, **k: base_rel_pointer(*a,
                                         p_path='..debug_path_address',**k)) },
                            1:{ TYPE:CStrLatin1, NAME:"debug_file",
                                POINTER:(lambda *a, **k: base_rel_pointer(*a,
                                         p_path='..debug_file_address',**k)) },
                            2:{ TYPE:CStrUtf16, NAME:"debug_unicode_file",
                                POINTER:(lambda *a, **k: base_rel_pointer(*a,
                                         p_path='..debug_unicode_file_address',**k)) }
                            }
                    }

xbe_certificate = {TYPE:Struct, NAME:"xbe_certificate", SIZE:464,
                   POINTER:(lambda *a, **k:
                            base_rel_pointer(*a,
                            p_path='.xbe_image_header.certificate_address',**k)),
                   
                   0:{TYPE:UInt32, NAME:"struct_size",
                      EDITABLE:False, DEFAULT:464},
                   1:{TYPE:Timestamp,  NAME:"time_date"},
                   #least significant 2 bytes of title ID are treated as
                   #an int and most significant 2 are a 2 char string.
                   2:{TYPE:BytearrayRaw,  NAME:"title_id", SIZE:4},
                   3:{TYPE:StrRawUtf16,   NAME:"title_name", SIZE:80},
                   4:{TYPE:UInt32Array,   NAME:"alt_title_ids", SIZE:64},
                   5:{TYPE:Bool32,        NAME:"allowed_media",
                      0:{NAME:"hdd"},
                      1:{NAME:"dvd_x2"},
                      2:{NAME:"dvd_cd"},
                      3:{NAME:"cd"},
                      4:{NAME:"dvd_5_ro"},
                      5:{NAME:"dvd_9_ro"},
                      6:{NAME:"dvd_5_rw"},
                      7:{NAME:"dvd_9_rw"},
                      8:{NAME:"usb"},
                      9:{NAME:"media_board"},
                      10:{NAME:"nonsecure_hard_disk", VALUE:0x40000000},
                      11:{NAME:"nonsecure_mode",      VALUE:0x80000000}
                      },
                   6:{TYPE:Enum32, NAME:"game_region",
                      0:{NAME:"usa_canada"},
                      1:{NAME:"japan"},
                      2:{NAME:"rest_of_world"},
                      3:{NAME:"debug", VALUE:0x80000000}
                      },
                   7:{TYPE:Enum32, NAME:"game_ratings",
                      0:{NAME:"rp"},#All
                      1:{NAME:"ao"},#Adult only
                      2:{NAME:"m"}, #Mature
                      3:{NAME:"t"}, #Teen
                      4:{NAME:"e"}, #Everyone
                      5:{NAME:"ka"},#Kids_to_Adults
                      6:{NAME:"ec"} #Early_Childhood
                      },
                   8:{TYPE:UInt32, NAME:"disk_number"},
                   9:{TYPE:UInt32, NAME:"version"},
                   10:{TYPE:BytearrayRaw, NAME:"lan_key", SIZE:16},
                   11:{TYPE:BytearrayRaw, NAME:"signature_key", SIZE:16},
                   12:{TYPE:BytearrayRaw, NAME:"alt_signature_keys", SIZE:256},
                   }

xbe_sec_header = {TYPE:Struct, NAME:"xbe_section_header",
                  0:{TYPE:Bool32, NAME:"flags",
                     0:{NAME:"writable"},
                     1:{NAME:"preload"},
                     2:{NAME:"executable"},
                     3:{NAME:"inserted_file"},
                     4:{NAME:"head_page_read_only"},
                     5:{NAME:"tail_page_read_only"}
                     },
                  1:{TYPE:UInt32,    NAME:"virtual_address"},
                  2:{TYPE:UInt32,    NAME:"virtual_size"},
                  3:{TYPE:Pointer32, NAME:"raw_address"},
                  4:{TYPE:UInt32,    NAME:"raw_size"},
                  5:{TYPE:Pointer32, NAME:"section_name_address"},
                  6:{TYPE:UInt32,    NAME:"section_name_ref_count"},
                  7:{TYPE:Pointer32, NAME:"head_shared_page_ref_count_address"},
                  8:{TYPE:Pointer32, NAME:"tail_shared_page_ref_count_address"},
                  9:{TYPE:BytearrayRaw,    NAME:"section_digest", SIZE:20},
                  CHILD:{ TYPE:CStrLatin1, NAME:'section_name',
                          POINTER:(lambda *a, **k: base_rel_pointer(*a,
                                   p_path='.section_name_address',**k))
                          }
                  }

xbe_lib_ver = { TYPE:Struct, NAME:"xbe_lib_version",
                0:{TYPE:StrRawLatin1, NAME:"library_name", SIZE:8},
                1:{TYPE:UInt16,       NAME:"major_ver"},
                2:{TYPE:UInt16,       NAME:"minor_ver"},
                3:{TYPE:UInt16,       NAME:"build_ver"},
                4:{TYPE:BitStruct,    NAME:"flags",
                   0:{TYPE:BitUInt,   NAME:"qfe_ver",  SIZE:13},
                   1:{TYPE:BitUEnum,   NAME:"approved", SIZE:2,
                      0:{NAME:"no"},
                      1:{NAME:"maybe"},
                      2:{NAME:"yes"}
                      },
                   2:{TYPE:Bit, NAME:"debug_build" }
                   }
                }

xbe_tls = { TYPE:Struct, NAME:"xbe_tls",
            0:{TYPE:UInt32, NAME:"data_start_address"},
            1:{TYPE:UInt32, NAME:"data_end_address"},
            2:{TYPE:UInt32, NAME:"tls_index_address"},
            3:{TYPE:UInt32, NAME:"tls_callback_address"},
            4:{TYPE:UInt32, NAME:"size_of_zero_fill"},
            5:{TYPE:UInt32, NAME:"characteristics"},
            }

xbe_sec_headers = { TYPE:Array, NAME:"section_headers",
                    SIZE:'.xbe_image_header.section_count',
                    POINTER:(lambda *a, **k:
                             base_rel_pointer(*a,
                             p_path='.xbe_image_header.section_headers_address',**k)),
                    SUB_STRUCT:xbe_sec_header,
                    }

xbe_lib_ver_headers = { TYPE:Array, NAME:"lib_ver_headers",
                        SIZE:'.xbe_image_header.lib_vers_count',
                        POINTER:(lambda *a, **k:
                                 base_rel_pointer(*a,
                                 p_path='.xbe_image_header.lib_vers_address',**k)),
                        SUB_STRUCT:xbe_lib_ver,
                        }

xbe_desc = { TYPE:Container, NAME:"xbox_executable",
             0:xbe_image_header,
             1:xbe_certificate,
             2:xbe_sec_headers,
             3:xbe_lib_ver_headers
             }

xbe_def = TagDef( ext=".xbe", def_id="xbe", endian="<",
                  incomplete=True, descriptor=xbe_desc)
