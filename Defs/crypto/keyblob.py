from supyr_struct.defs.tag_def import *


def get():
    return KeyBlobDef

class KeyBlobDef(TagDef):
    '''Defines a rough description of cryptography keyblob structs.
       This isn't perfect, and only really supports RSA and AES keyblobs.
       Other keyblob formats aren't defined, though the header should
       still be accurate enough to tell you what type of keyblob it is.'''
    
    def size8(*args, **kwargs):
        New_Val = kwargs.get("new_value")
        if New_Val is None:
            return kwargs.get("parent").get_neighbor('..bitlen')//8
        return kwargs.get("parent").set_neighbor('..bitlen', New_Val*8)
    
    def size16(*args, **kwargs):
        New_Val = kwargs.get("new_value")
        if New_Val is None:
            return kwargs.get("parent").get_neighbor('..bitlen')//16
        return kwargs.get("parent").set_neighbor('..bitlen', New_Val*16)
    
    ext = ".bin"

    tag_id = "keyblob"

    endian = "<"

    BLOBHEADER = {TYPE:Struct, NAME:"header",
                  0:{ TYPE:Enum8, NAME:"bType", DEFAULT:0x1,
                      0:{ NAME:"SIMPLEBLOB",           VALUE:0x1 },
                      1:{ NAME:"PUBLICKEYBLOB",        VALUE:0x6 },
                      2:{ NAME:"PRIVATEKEYBLOB",       VALUE:0x7 },
                      3:{ NAME:"PLAINTEXTKEYBLOB",     VALUE:0x8 },
                      4:{ NAME:"OPAQUEKEYBLOB",        VALUE:0x9 },
                      5:{ NAME:"PUBLICKEYBLOBEX",      VALUE:0xA },
                      6:{ NAME:"SYMMETRICWRAPKEYBLOB", VALUE:0xB },
                      7:{ NAME:"KEYSTATEBLOB",         VALUE:0xC }
                      },
                  1:{ TYPE:UInt8, NAME:"bVersion", DEFAULT:2, MIN:2 },
                  2:{ TYPE:Pad, SIZE:2 },
                  3:{ TYPE:Enum32, NAME:"aiKeyAlg",
                      #for a description of what each of these is, go to this site:
                      #https://msdn.microsoft.com/en-us/library/windows/desktop/aa375549%28v=vs.85%29.aspx
                      0:{ NAME:"CALG_3DES",     VALUE:0x00006603 },
                      1:{ NAME:"CALG_3DES_112", VALUE:0x00006609 },
                      2:{ NAME:"CALG_AES",      VALUE:0x00006611 },
                      3:{ NAME:"CALG_AES_128",  VALUE:0x0000660e },
                      4:{ NAME:"CALG_AES_192",  VALUE:0x0000660f },
                      5:{ NAME:"CALG_AES_256",  VALUE:0x00006610 },
                      6:{ NAME:"CALG_AGREEDKEY_ANY", VALUE:0x0000aa03 },
                      7:{ NAME:"CALG_CYLINK_MEK",    VALUE:0x0000660c },
                      8:{ NAME:"CALG_DES",       VALUE:0x00006601 },
                      9:{ NAME:"CALG_DESX",      VALUE:0x00006604 },
                      10:{ NAME:"CALG_DH_EPHEM", VALUE:0x0000aa02 },
                      11:{ NAME:"CALG_DH_SF",    VALUE:0x0000aa01 },
                      12:{ NAME:"CALG_DSS_SIGN", VALUE:0x00002200 },
                      13:{ NAME:"CALG_ECDH",     VALUE:0x0000aa05 },
                      14:{ NAME:"CALG_ECDH_EPHEM", VALUE:0x0000ae06 },
                      15:{ NAME:"CALG_ECDSA",      VALUE:0x00002203 },
                      16:{ NAME:"CALG_ECMQV",      VALUE:0x0000a001 },
                      17:{ NAME:"CALG_HUGHES_MD5", VALUE:0x0000a003 },
                      18:{ NAME:"CALG_HMAC",       VALUE:0x00008009 },
                      19:{ NAME:"CALG_KEA_KEYX",   VALUE:0x0000aa04 },
                      20:{ NAME:"CALG_MAC",     VALUE:0x00008005 },
                      21:{ NAME:"CALG_MD2",     VALUE:0x00008001 },
                      22:{ NAME:"CALG_MD4",     VALUE:0x00008002 },
                      23:{ NAME:"CALG_MD5",     VALUE:0x00008003 },
                      24:{ NAME:"CALG_NO_SIGN", VALUE:0x00002000 },
                      25:{ NAME:"CALG_PCT1_MASTER", VALUE:0x00004c04 },
                      26:{ NAME:"CALG_RC2",         VALUE:0x00006602 },
                      27:{ NAME:"CALG_RC4",         VALUE:0x00006801 },
                      28:{ NAME:"CALG_RC5",         VALUE:0x0000660d },
                      29:{ NAME:"CALG_RSA_KEYX", VALUE:0x0000a400 },
                      30:{ NAME:"CALG_RSA_SIGN", VALUE:0x00002400 },
                      31:{ NAME:"CALG_SEAL",     VALUE:0x00006802 },
                      32:{ NAME:"CALG_SHA",      VALUE:0x00008004 },
                      33:{ NAME:"CALG_SHA1",     VALUE:0x00008004 },
                      34:{ NAME:"CALG_SHA_256",  VALUE:0x0000800c },
                      35:{ NAME:"CALG_SHA_384",  VALUE:0x0000800d },
                      36:{ NAME:"CALG_SHA_512",  VALUE:0x0000800e },
                      37:{ NAME:"CALG_SKIPJACK", VALUE:0x0000660a },
                      38:{ NAME:"CALG_SSL2_MASTER", VALUE:0x00004c05 },
                      39:{ NAME:"CALG_SSL3_MASTER", VALUE:0x00004c01 },
                      40:{ NAME:"CALG_SSL3_SHAMD5", VALUE:0x00008008 },
                      41:{ NAME:"CALG_TEK",         VALUE:0x0000660b },
                      42:{ NAME:"CALG_TLS1_MASTER", VALUE:0x00004c06 },
                      43:{ NAME:"CALG_TLS1PRF",     VALUE:0x0000800a },
                      
                      44:{ NAME:"CALG_HASH_REPLACE_OWF",     VALUE:0x0000800b },
                      45:{ NAME:"CALG_SCHANNEL_ENC_KEY",     VALUE:0x00004c07 },
                      46:{ NAME:"CALG_SCHANNEL_MAC_KEY",     VALUE:0x00004c03 },
                      47:{ NAME:"CALG_SCHANNEL_MASTER_HASH", VALUE:0x00004c02 }
                      }
                  }

    '''####################'''
    ####  RSA descriptors  ####
    '''####################'''

    RSAPUBKEY = { TYPE:Container, GUI_NAME:'rsaPubKey',
                  0:{ TYPE:BigUInt, NAME:"modulus", SIZE:size8 }
                  }

    RSAPRIKEY = { TYPE:Container, GUI_NAME:'rsaPriKey',
                  0:{ TYPE:BigUInt, NAME:"modulus", SIZE:size8 },
                  1:{ TYPE:BigUInt, NAME:"prime1",  SIZE:size16 },
                  2:{ TYPE:BigUInt, NAME:"prime2",  SIZE:size16},
                  3:{ TYPE:BigUInt, NAME:"exponent1",   SIZE:size16},
                  4:{ TYPE:BigUInt, NAME:"exponent2",   SIZE:size16},
                  5:{ TYPE:BigUInt, NAME:"coefficient", SIZE:size16},
                  6:{ TYPE:BigUInt, NAME:"privateExponent", SIZE:size8 }
                  }

    RSAKEYDATA = { TYPE:Struct, GUI_NAME:'rsaKeyData',
                   0:{ TYPE:Enum32, NAME:"magic",
                       0:{ NAME:"RSA1", VALUE:'1ASR' },
                       1:{ NAME:"RSA2", VALUE:'2ASR' }
                       },
                   1:{ TYPE:UInt32, NAME:"bitlen" },
                   2:{ TYPE:UInt32, NAME:"pubexp" },
                   CHILD:{ TYPE:Switch, NAME:'rsaData',
                           CASE:'.magic.data_name',
                           CASES:{ "RSA1":RSAPUBKEY,
                                   "RSA2":RSAPRIKEY }
                         }
                   }

    '''####################'''
    ###   AES descriptors   ###
    '''####################'''

    AESKEYDATA = { TYPE:Container, GUI_NAME:'aesKeyData',
                   0:{ TYPE:UInt32, NAME:"bytelen" },
                   1:{ TYPE:BytesRaw, NAME:"key", SIZE:'.bytelen' }
                   }

    AESKEYDATA128 = combine( { 0:{DEFAULT:16} }, AESKEYDATA )
    AESKEYDATA192 = combine( { 0:{DEFAULT:24} }, AESKEYDATA )
    AESKEYDATA256 = combine( { 0:{DEFAULT:32} }, AESKEYDATA )


    '''####################'''
    ####  Main Structure  ####
    '''####################'''

    descriptor = { TYPE:Container, NAME:"keyBlob",
                      0:BLOBHEADER,
                      1:{ TYPE:Switch, NAME:'keyData',
                          CASE:'.header.aiKeyAlg.data_name',
                          CASES:{ "CALG_RSA_KEYX":RSAKEYDATA,
                                  "CALG_AES":    AESKEYDATA,
                                  "CALG_AES_128":AESKEYDATA128,
                                  "CALG_AES_192":AESKEYDATA192,
                                  "CALG_AES_256":AESKEYDATA256 }
                          }
                      }
    

    descriptors = { "BLOBHEADER":BLOBHEADER,
                   
                   "RSAKEYDATA":RSAKEYDATA,
                   "RSAPUBKEY":RSAPUBKEY, "RSAPRIKEY":RSAPRIKEY,
                   
                   "AESKEYDATA":   AESKEYDATA,    "AESKEYDATA128":AESKEYDATA128,
                   "AESKEYDATA192":AESKEYDATA192, "AESKEYDATA256":AESKEYDATA256}
