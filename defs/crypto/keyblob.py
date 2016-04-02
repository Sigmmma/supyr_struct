'''Defines a rough description of cryptography keyblob structs.
   This isn't perfect, and only really supports RSA and AES keyblobs.
   Other keyblob formats aren't defined, though the header should
   still be accurate enough to tell you what type of keyblob it is.'''
from supyr_struct.defs.tag_def import *


def get():
    return keyblob_def
    
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


b_type = Enum8("b_type",
               ("SIMPLEBLOB",           0x1),
               ("PUBLICKEYBLOB",        0x6),
               ("PRIVATEKEYBLOB",       0x7),
               ("PLAINTEXTKEYBLOB",     0x8),
               ("OPAQUEKEYBLOB",        0x9),
               ("PUBLICKEYBLOBEX",      0xA),
               ("SYMMETRICWRAPKEYBLOB", 0xB),
               ("KEYSTATEBLOB",         0xC),
               DEFAULT=0x1
               )

#for a description of each of these, go to this site:
#msdn.microsoft.com/en-us/library/windows/desktop/aa375549%28v=vs.85%29.aspx
ai_key_alg = Enum32("ai_key_alg",
                    ("CALG_3DES",     0x00006603),
                    ("CALG_3DES_112", 0x00006609),
                    ("CALG_AES",      0x00006611),
                    ("CALG_AES_128",  0x0000660e),
                    ("CALG_AES_192",  0x0000660f),
                    ("CALG_AES_256",  0x00006610),
                    ("CALG_AGREEDKEY_ANY", 0x0000aa03),
                    ("CALG_CYLINK_MEK",    0x0000660c),
                    ("CALG_DES",       0x00006601),
                    ("CALG_DESX",      0x00006604),
                    ("CALG_DH_EPHEM", 0x0000aa02),
                    ("CALG_DH_SF",    0x0000aa01),
                    ("CALG_DSS_SIGN", 0x00002200),
                    ("CALG_ECDH",     0x0000aa05),
                    ("CALG_ECDH_EPHEM", 0x0000ae06),
                    ("CALG_ECDSA",      0x00002203),
                    ("CALG_ECMQV",      0x0000a001),
                    ("CALG_HUGHES_MD5", 0x0000a003),
                    ("CALG_HMAC",       0x00008009),
                    ("CALG_KEA_KEYX",   0x0000aa04),
                    ("CALG_MAC",     0x00008005),
                    ("CALG_MD2",     0x00008001),
                    ("CALG_MD4",     0x00008002),
                    ("CALG_MD5",     0x00008003),
                    ("CALG_NO_SIGN", 0x00002000),
                    ("CALG_PCT1_MASTER", 0x00004c04),
                    ("CALG_RC2",         0x00006602),
                    ("CALG_RC4",         0x00006801),
                    ("CALG_RC5",         0x0000660d),
                    ("CALG_RSA_KEYX", 0x0000a400),
                    ("CALG_RSA_SIGN", 0x00002400),
                    ("CALG_SEAL",     0x00006802),
                    ("CALG_SHA",      0x00008004),
                    ("CALG_SHA1",     0x00008004),
                    ("CALG_SHA_256",  0x0000800c),
                    ("CALG_SHA_384",  0x0000800d),
                    ("CALG_SHA_512",  0x0000800e),
                    ("CALG_SKIPJACK", 0x0000660a),
                    ("CALG_SSL2_MASTER", 0x00004c05),
                    ("CALG_SSL3_MASTER", 0x00004c01),
                    ("CALG_SSL3_SHAMD5", 0x00008008),
                    ("CALG_TEK",         0x0000660b),
                    ("CALG_TLS1_MASTER", 0x00004c06),
                    ("CALG_TLS1PRF",     0x0000800a),
                    
                    ("CALG_HASH_REPLACE_OWF",     0x0000800b),
                    ("CALG_SCHANNEL_ENC_KEY",     0x00004c07),
                    ("CALG_SCHANNEL_MAC_KEY",     0x00004c03),
                    ("CALG_SCHANNEL_MASTER_HASH", 0x00004c02)
                    )

'''####################'''
####  RSA descriptors  ####
'''####################'''

rsa_pub_key = Container('rsa_pub_key',
                        BigUInt("modulus", SIZE=size8)
                        )

rsa_pri_key = Container('rsa_pri_key',
                        BigUInt("modulus",          SIZE=size8),
                        BigUInt("prime1",           SIZE=size16),
                        BigUInt("prime2",           SIZE=size16),
                        BigUInt("exponent1",        SIZE=size16),
                        BigUInt("exponent2",        SIZE=size16),
                        BigUInt("coefficient",      SIZE=size16),
                        BigUInt("private_exponent", SIZE=size8)
                        )

rsa_key_data = Struct('rsa_key_data',
                      Enum32("magic",
                             ("RSA1", '1ASR'),
                             ("RSA2", '2ASR')
                             ),
                      UInt32("bitlen"),
                      UInt32("pubexp"),
                      Switch('rsa_data',
                             CASE='.magic.data_name',
                             CASES={ "RSA1":rsa_pub_key,
                                     "RSA2":rsa_pri_key }
                             )
                      )

'''####################'''
###   AES descriptors   ###
'''####################'''

aes_key_data     = Container('aes_key_data',
                             UInt32("bytelen"),
                             BytesRaw("key", SIZE='.bytelen')
                             )
aes_key_data_128 = Container('aes_key_data',
                             UInt32("bytelen", DEFAULT=16),
                             BytesRaw("key",   SIZE='.bytelen')
                             )
aes_key_data_192 = Container('aes_key_data',
                             UInt32("bytelen", DEFAULT=24),
                             BytesRaw("key",   SIZE='.bytelen')
                             )
aes_key_data_256 = Container('aes_key_data',
                             UInt32("bytelen", DEFAULT=32),
                             BytesRaw("key",   SIZE='.bytelen')
                             )


'''####################'''
####  Main Structure  ####
'''####################'''

    
keyblob_def = TagDef( Struct("header",
                             b_type,
                             UInt8("b_ver", DEFAULT=2, MIN=2),
                             Pad(2),
                             ai_key_alg
                             ),
                      Switch('key_data',
                             CASE='.header.ai_key_alg.data_name',
                             CASES={ "CALG_RSA_KEYX":rsa_key_data,
                                     "CALG_AES":    aes_key_data,
                                     "CALG_AES_128":aes_key_data_128,
                                     "CALG_AES_192":aes_key_data_192,
                                     "CALG_AES_256":aes_key_data_256 }
                             ),
                      ext=".bin", def_id="keyblob", endian="<"
                      )
