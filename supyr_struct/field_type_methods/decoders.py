'''
Decoder functions for all standard FieldTypes.

Decoders are responsible for converting bytes into a python object*

*Not all decoders receive bytes objects.
FieldTypes that operate on the bit level cant be expected to return
even byte sized amounts of bits, so they operate differently.
A FieldTypes parser and decoder simply need to
be working with the same parameter and return data types.
'''
__all__ = [
    # basic decoders
    'decode_numeric', 'decode_string', 'no_decode',
    'decode_big_int', 'decode_bit_int', 'decode_raw_string',
    # specialized decoders
    'decode_24bit_numeric', 'decode_decimal', 'decode_bit',
    'decode_timestamp', 'decode_string_hex',

    # wrapper functions
    'decoder_wrapper', 
    ]

from decimal import Decimal
from struct import unpack
from time import ctime

from supyr_struct.defs.constants import ATTR_OFFS


def decoder_wrapper(de):
    '''
    This function is for wrapping decoders in functions which properly
    work with FieldTypes where is_block and is_data are both True.
    This is because the node will be a Block with some attribute
    that stores the "data" of the node.
    '''
    def wrapped_decoder(
            self, rawdata, desc=None, parent=None,
            attr_index=None, _decode=de):
        return self.node_cls(desc, parent, initdata=_decode(
            self, rawdata, desc, parent, attr_index))

    return wrapped_decoder


def no_decode(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Does not decode and just returns the raw data.
    '''
    return rawdata


def decode_numeric(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Converts a bytes object into a python int.
    Decoding is done using struct.unpack

    Returns an int decoded represention of the "rawdata" argument.
    '''
    return self.struct_unpacker(rawdata)[0]


def decode_decimal(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Converts a bytes object into a python Decimal.

    Returns a Decimal represention of the "rawdata" argument.
    '''
    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'
    d_exp = parent.get_meta('DECIMAL_EXP', attr_index)
    bigint = str(int.from_bytes(
        rawdata, endian, signed=self.enc.endswith('S')))

    return Decimal(bigint[:len(bigint)-d_exp] + '.' +
                   bigint[len(bigint)-d_exp:])


def decode_24bit_numeric(self, rawdata, desc=None,
                         parent=None, attr_index=None):
    '''
    Converts a 24-bit bytes object into a python int.
    Decoding is done using struct.unpack and a manual twos-signed check.

    Returns an int decoded represention of the "rawdata" argument.
    '''
    if self.endian == '<':
        rawint = unpack('<I', rawdata + b'\x00')[0]
    else:
        rawint = unpack('>I', b'\x00' + rawdata)[0]

    # if the int can be signed and IS signed then take care of that
    if rawint & 0x800000 and self.enc[1] == 't':
        return rawint - 0x1000000  # 0x1000000 == 0x800000 * 2
    return rawint


def decode_timestamp(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    '''
    return ctime(self.struct_unpacker(rawdata)[0])


def decode_string(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string
    with the delimiter character sliced off the end.
    Decoding is done using bytes.decode

    Returns a string decoded represention of the "rawdata" argument.
    '''
    return rawdata.decode(encoding=self.enc).split(self.str_delimiter)[0]


def decode_raw_string(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string that can contain delimiters.
    Decoding is done using bytes.decode

    Returns a string decoded represention of the "rawdata" argument.
    '''
    return rawdata.decode(encoding=self.enc)


def decode_string_hex(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string representing
    the original bytes object in a hexadecimal form.

    Returns a string decoded represention of the "rawdata" argument.
    '''
    length = len(rawdata) * 2
    return (('%%0%dx' % length) % int.from_bytes(rawdata, 'big'))[-length: ]


def decode_big_int(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Decoding is done using int.from_bytes

    Returns an int represention of the "rawdata" argument.
    '''
    # If an empty bytes object was provided, return a zero.
    if not len(rawdata):
        return 0

    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'

    if self.enc[-1] == 's':
        # ones compliment
        bigint = int.from_bytes(rawdata, endian, signed=True)
        if bigint < 0:
            return bigint + 1
        return bigint
    elif self.enc[-1] == 'S':
        # twos compliment
        return int.from_bytes(rawdata, endian, signed=True)

    return int.from_bytes(rawdata, endian)


def decode_bit(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a single bit from the given int into an int.
    Returns a 1 if the bit is set, or a 0 if it isnt.
    '''
    # mask and shift the int out of the rawdata
    return (rawdata >> parent.ATTR_OFFS[attr_index]) & 1


def decode_bit_int(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment

    Returns an int represention of the "rawdata" argument
    after masking and bit-shifting.
    '''
    bitcount = parent.get_size(attr_index)

    # If the bit count is zero, return a zero
    if not bitcount:
        return 0

    offset = parent.ATTR_OFFS[attr_index]
    mask = (1 << bitcount) - 1

    # mask and shift the int out of the rawdata
    bitint = (rawdata >> offset) & mask

    # if the number would be negative if signed
    if bitint & (1 << (bitcount - 1)):
        intmask = ((1 << (bitcount - 1)) - 1)
        if self.enc == 's':
            # get the ones compliment and change the sign
            return -1*((~bitint) & intmask)
        elif self.enc == 'S':
            # get the twos compliment and change the sign
            bitint = -1*((~bitint + 1) & intmask)
            # if only the negative sign was set, the bitint will be
            # masked off to 0, and end up as 0 rather than the max
            # negative number it should be. instead, return negative max
            if not bitint:
                return -(1 << (bitcount - 1))

    return bitint
