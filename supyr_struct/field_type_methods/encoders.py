'''
Encoder functions for all standard FieldTypes.

Encoders are responsible for converting a python object into bytes*

*Not all encoders return bytes objects.
FieldTypes that operate on the bit level cant be expected to return
even byte sized amounts of bits, so they operate differently.
A FieldTypes serializer and encoder simply need to
be working with the same parameter and return data types.
'''
__all__ = [
    # basic encoders
    'encode_numeric', 'encode_string', 'no_encode',
    'encode_big_int', 'encode_bit_int',
    # specialized encoders
    'encode_24bit_numeric', 'encode_decimal', 'encode_bit', 'encode_raw_string',
    'encode_int_timestamp', 'encode_float_timestamp', 'encode_string_hex',

    # wrapper functions
    'encoder_wrapper', 
    ]

from decimal import Decimal
from struct import pack
from time import mktime, strptime

from supyr_struct.defs.constants import ATTR_OFFS


def encoder_wrapper(en):
    '''
    This function is for wrapping encoders in functions which properly
    work with FieldTypes where is_block and is_data are both True.
    This is because the node will be a Block with some attribute
    that stores the "data" of the node.
    '''
    def wrapped_encoder(
            self, node, parent=None, attr_index=None, _encode=en):
        return _encode(self, node.data, parent, attr_index)

    return wrapped_encoder


def no_encode(self, node, parent=None, attr_index=None):
    '''
    Does not encode and just returns the node.
    '''
    return node


def encode_numeric(self, node, parent=None, attr_index=None):
    '''
    Encodes a python int into a bytes representation.
    Encoding is done using struct.pack

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return self.struct_packer(node)


def encode_decimal(self, node, parent=None, attr_index=None):
    '''
    Encodes a python Decimal into a bytes representation.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    raise NotImplementedError('Encoding Decimal objects is not supported yet.')


def encode_24bit_numeric(self, node, parent=None, attr_index=None):
    '''
    Encodes a python int to a signed or unsigned 24-bit bytes representation.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    if self.enc[1] == 't':
        # int can be signed
        assert node >= -0x800000 and node <= 0x7fffff, (
            '%s is too large to pack as a 24bit signed int.' % node)
        if node < 0:
            # int IS signed
            node += 0x1000000
    else:
        assert node >= 0 and node <= 0xffffff, (
            '%s is too large to pack as a 24bit unsigned int.' % node)

    # pack and return the int
    if self.endian == '<':
        return pack('<I', node)[0:3]
    return pack('>I', node)[1:4]


def encode_int_timestamp(self, node, parent=None, attr_index=None):
    '''
    '''
    return self.struct_packer(int(mktime(strptime(node))))


def encode_float_timestamp(self, node, parent=None, attr_index=None):
    '''
    '''
    return self.struct_packer(float(mktime(strptime(node))))


def encode_string(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation,
    making sure there is a delimiter character on the end.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "node" argument.
    '''
    if not node.endswith(self.str_delimiter):
        return (node + self.str_delimiter).encode(self.enc)
    return node.encode(self.enc)


def encode_raw_string(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return node.encode(self.enc)


def encode_string_hex(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string formatted as a hex string into a bytes object.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return int(node, 16).to_bytes((len(node) + 1)//2, 'big')


def encode_big_int(self, node, parent=None, attr_index=None):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Encoding is done using int.to_bytes

    Returns a bytes object encoded represention of the "node" argument.
    '''
    bytecount = parent.get_size(attr_index)

    if not bytecount:
        return b''

    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'

    if self.enc[-1] == 'S':
        # twos compliment
        return node.to_bytes(bytecount, endian, signed=True)
    elif self.enc[-1] == 's':
        # ones compliment
        if node < 0:
            return (node-1).to_bytes(bytecount, endian, signed=True)
        return node.to_bytes(bytecount, endian, signed=False)

    return node.to_bytes(bytecount, endian)


def encode_bit(self, node, parent=None, attr_index=None):
    '''
    Encodes an int to a single bit.
    Returns the encoded int, the offset it should be
    shifted to, and a mask that covers its range.
    '''
    # return the int with the bit offset and a mask of 1
    return(node, parent.ATTR_OFFS[attr_index], 1)


def encode_bit_int(self, node, parent=None, attr_index=None):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment

    Returns the encoded int, the offset it should be
    shifted to, and a mask that covers its range.
    '''

    bitcount = parent.get_size(attr_index)
    offset = parent.ATTR_OFFS[attr_index]
    mask = (1 << bitcount) - 1

    # if the number is signed
    if node < 0:
        signmask = 1 << (bitcount - 1)
        if self.enc == 'S':
            # twos signed
            return(2*signmask + node, offset, mask)
        # ones signed
        return(2*signmask + (node-1), offset, mask)
    return(node, offset, mask)

