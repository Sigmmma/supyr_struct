from supyr_struct.Defs.Tag_Def import *


def Construct():
    return Key_Blob_Def

class Key_Blob_Def(Tag_Def):
    
    Tag_Ext = ".bin"

    Tag_ID = "keyblob"

    Endianness = "<"

    BLOBHEADER = {TYPE:Struct, NAME:"BLOBHEADER",
                  0:{ TYPE:UInt8, NAME:"bType", DEFAULT:1,
                      ELEMENTS:{ 0:{ NAME:"SIMPLEBLOB",      VALUE:0x1 },
                                 1:{ NAME:"PUBLICKEYBLOB",   VALUE:0x6 },
                                 2:{ NAME:"PRIVATEKEYBLOB",  VALUE:0x7 },
                                 3:{ NAME:"PLAINTEXTKEYBLOB",VALUE:0x8 },
                                 4:{ NAME:"OPAQUEKEYBLOB",   VALUE:0x9 },
                                 5:{ NAME:"PUBLICKEYBLOBEX", VALUE:0xA },
                                 6:{ NAME:"SYMMETRICWRAPKEYBLOB", VALUE:0xB },
                                 7:{ NAME:"KEYSTATEBLOB",    VALUE:0xC }
                                 }
                      },
                  1:{ TYPE:UInt8, NAME:"bVersion", DEFAULT:2, MIN:2 },
                  2:{ PAD:2 },
                  3:{ TYPE:UInt32, NAME:"aiKeyAlg",
                      #for a description of what each of these is, go to this site:
                      #https://msdn.microsoft.com/en-us/library/windows/desktop/aa375549%28v=vs.85%29.aspx

                      #for information on some of the algorithms, go to this site:
                      #https://msdn.microsoft.com/en-us/library/windows/desktop/aa382020%28v=vs.85%29.aspx
                      ELEMENTS:{ 0:{ NAME:"CALG_3DES",     VALUE:0x00006603 },
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
                                 47:{ NAME:"CALG_SCHANNEL_MASTER_HASH", VALUE:0x00004c02 },
                                 48:{ NAME:"CALG_OID_INFO_CNG_ONLY",    VALUE:0xffffffff },
                                 49:{ NAME:"CALG_OID_INFO_PARAMETERS",  VALUE:0xfffffffe }
                                 }
                      }
                  }

    '''#####################'''
    #####  RSA Structures  ####
    '''#####################'''

    RSAPUBKEY = { TYPE:Struct, NAME:"RSAPUBKEY",
                  0:{ TYPE:Str_Raw_ASCII, NAME:"magic", SIZE:4,
                      ELEMENTS:{ 0:{ NAME:"RSA1", VALUE:"RSA1" },#Public key blob
                                 1:{ NAME:"RSA2", VALUE:"RSA2" }#Private key blob
                                 }
                      },
                  1:{ TYPE:UInt32, NAME:"bitlen"},
                  2:{ TYPE:UInt32, NAME:"pubexp"}
                  }

    RSAPUBKEYBLOB = { TYPE:Container, NAME:"RSAPUBKEYBLOB",
                      0:BLOBHEADER,
                      1:Combine( { 0:{DEFAULT:"RSA1"} }, RSAPUBKEY),
                      2:{ TYPE:Big_UInt, NAME:"modulus",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a, Path='.RSAPUBKEY.bitlen',**k))
                          }
                      }

    RSAPRIKEYBLOB = { TYPE:Container, NAME:"RSAPRIKEYBLOB",
                      0:BLOBHEADER,
                      1:Combine( { 0:{DEFAULT:"RSA2"} }, RSAPUBKEY),
                      2:{ TYPE:Big_UInt, NAME:"modulus",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=8,**k))
                          },
                      3:{ TYPE:Big_UInt, NAME:"prime1",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=16,**k))
                          },
                      4:{ TYPE:Big_UInt, NAME:"prime2",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=16,**k))
                          },
                      5:{ TYPE:Big_UInt, NAME:"exponent1",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=16,**k))
                          },
                      6:{ TYPE:Big_UInt, NAME:"exponent2",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=16,**k))
                          },
                      7:{ TYPE:Big_UInt, NAME:"coefficient",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=16,**k))
                          },
                      8:{ TYPE:Big_UInt, NAME:"privateExponent",
                          SIZE:(lambda *a, **k: Tag_Def.Mod_Get_Set\
                                (*a,Path='.RSAPUBKEY.bitlen',Mod=8,**k))
                          },
                      }

    '''#####################'''
    #####  AES Structures  ####
    '''#####################'''

    CRYPT_AES_256_KEY_STATE = { TYPE:Container, NAME:"CRYPT_AES_256_KEY_STATE",
                                0:{ TYPE:Bytearray_Raw, NAME:"Key", SIZE:32 },
                                1:{ TYPE:Bytearray_Raw, NAME:"IV", SIZE:16 },
                                2:{ TYPE:Bytearray_Raw, NAME:"EncryptionState", SIZE:15*16 },
                                3:{ TYPE:Bytearray_Raw, NAME:"DecryptionState", SIZE:15*16 },
                                4:{ TYPE:Bytearray_Raw, NAME:"Feedback", SIZE:16 },
                                }

    AESKEYBLOB = { TYPE:Container, NAME:"AESKEYBLOB",
                   0:BLOBHEADER,
                   1:{ TYPE:UInt32, NAME:"bytelen" },
                   2:{ TYPE:Bytearray_Raw, NAME:"key", SIZE:'.bytelen' }
                   }


    '''#####################'''
    #####  Main Structure  ####
    '''#####################'''


    '''Finish this by making the Tag_Structure a "Switch" Field_Type'''
    #Tag_Structure = { }

    #THIS IS JUST A TEMPORARY SETUP UNTIL SWITCH BLOCKS ARE IMPLEMENTED
    Tag_Structure = RSAPRIKEYBLOB
    

    Structures = { "BLOBHEADER":BLOBHEADER,
                   "RSAPUBKEY":RSAPUBKEY, "AESKEYBLOB":AESKEYBLOB,
                   "RSAPUBKEYBLOB":RSAPUBKEYBLOB, "RSAPRIKEYBLOB":RSAPRIKEYBLOB,
                   "CRYPT_AES_256_KEY_STATE":CRYPT_AES_256_KEY_STATE}
