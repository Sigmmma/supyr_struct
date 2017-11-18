'''
Defines a rough description of cryptography keyblob structs.
This isn't perfect, and only really supports RSA and AES keyblobs.
Other keyblob formats aren't defined, though the header should
still be accurate enough to tell you what type of keyblob it is.

Structures were pieced together from various online sources
'''
from supyr_struct.defs.tag_def import *
from supyr_struct.defs.constants import *


def get(): return keyblob_def


def size8(parent=None, new_value=None, **kwargs):
    '''
    Size getter for rsa key data where the byte size
    of the integer is (parent.parent.bitlen + 7) // 8
    (the + 7 is to round up to the nearest multiple of 8)

    We dont want to have this be a setter since bitlen
    is used by more than one attribute and while it may
    work for some bigints, it may be too small for others.
    '''
    if new_value is None:
        return (parent.parent.bitlen + 7) // 8


def size16(parent=None, new_value=None, **kwargs):
    '''
    Size getter for rsa key data where the byte size
    of the integer is (parent.parent.bitlen + 15) // 16
    (the + 15 is to round up to the nearest multiple of 16)

    We dont want to have this be a setter since bitlen
    is used by more than one attribute and while it may
    work for some bigints, it may be too small for others.
    '''
    if new_value is None:
        return (parent.parent.bitlen + 15) // 16


b_type = UEnum8("b_type",
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

# for a description of each of these, go to this site:
# msdn.microsoft.com/en-us/library/windows/desktop/aa375549%28v=vs.85%29.aspx
ai_key_alg = UEnum32("ai_key_alg",
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
    ("CALG_MAC", 0x00008005),
    ("CALG_MD2", 0x00008001),
    ("CALG_MD4", 0x00008002),
    ("CALG_MD5", 0x00008003),
    ("CALG_NO_SIGN", 0x00002000),
    ("CALG_PCT1_MASTER", 0x00004c04),
    ("CALG_RC2", 0x00006602),
    ("CALG_RC4", 0x00006801),
    ("CALG_RC5", 0x0000660d),
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

# #########################
# --  RSA descriptors  -- #
# #########################

rsa_pub_key = Container('rsa_pub_key',
    UIntBig("modulus", SIZE=size8)
    )

rsa_pri_key = Container('rsa_pri_key',
    UIntBig("modulus", SIZE=size8),
    UIntBig("prime1",      SIZE=size16),
    UIntBig("prime2",      SIZE=size16),
    UIntBig("exponent1",   SIZE=size16),
    UIntBig("exponent2",   SIZE=size16),
    UIntBig("coefficient", SIZE=size16),
    UIntBig("private_exponent", SIZE=size8)
    )

rsa_key_data = Container('rsa_key_data',
    UEnum32("magic",
        ("RSA1", '1ASR'),
        ("RSA2", '2ASR')
        ),
    UInt32("bitlen"),
    UInt32("pubexp"),
    Switch('rsa_data',
        CASE='.magic.enum_name',
        CASES={"RSA1": rsa_pub_key,
               "RSA2": rsa_pri_key}
        )
    )

# #########################
# --  AES descriptors  -- #
# #########################

aes_key_data = Container('aes_key_data',
    UInt32("bytelen"),
    StrHex("key", SIZE='.bytelen')
    )

aes_key_data_128 = Container('aes_key_data',
    UInt32("bytelen", DEFAULT=16),
    StrHex("key", SIZE='.bytelen')
    )

aes_key_data_192 = Container('aes_key_data',
    UInt32("bytelen", DEFAULT=24),
    StrHex("key", SIZE='.bytelen')
    )

aes_key_data_256 = Container('aes_key_data',
    UInt32("bytelen", DEFAULT=32),
    StrHex("key", SIZE='.bytelen')
    )


# ########################
# --  Main Structure  -- #
# ########################

keyblob_header = Struct("header",
    b_type,
    UInt8("b_ver", DEFAULT=2, MIN=2),
    Pad(2),
    ai_key_alg
    )

key_data = Switch('key_data',
    DEFAULT=Void('key_data'),
    CASE='.header.ai_key_alg.enum_name',
    CASES={"CALG_RSA_KEYX": rsa_key_data,
           "CALG_AES":      aes_key_data,
           "CALG_AES_128":  aes_key_data_128,
           "CALG_AES_192":  aes_key_data_192,
           "CALG_AES_256":  aes_key_data_256}
    )

keyblob_def = TagDef("keyblob",
    keyblob_header,
    key_data,
    ext=".bin", endian="<"
    )
