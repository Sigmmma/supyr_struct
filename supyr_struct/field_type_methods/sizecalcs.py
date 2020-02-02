__all__ = [
    # basic size calculators
    'no_sizecalc', 'def_sizecalc', 'len_sizecalc',
    'delim_str_sizecalc', 'str_sizecalc',
    # specialized size calculators
    'delim_utf_sizecalc', 'utf_sizecalc', 'array_sizecalc',
    'big_sint_sizecalc', 'big_uint_sizecalc', 'str_hex_sizecalc',
    'bit_sint_sizecalc', 'bit_uint_sizecalc', 'computed_sizecalc',

    # wrapper functions
    'sizecalc_wrapper', 
    ]

from supyr_struct.defs.constants import COMPUTE_SIZECALC


# This function is for wrapping sizecalcs in functions which properly
# work with FieldTypes where is_block and is_data are both True.
# This is because the node will be a Block with some attribute
# that stores the "data" of the node.
def sizecalc_wrapper(sc):
    '''
    '''
    def wrapped_sizecalc(self, node, _sizecalc=sc, *a, **kw):
        return _sizecalc(self, node.data, *a, **kw)

    return wrapped_sizecalc


def no_sizecalc(self, node, **kwargs):
    '''
    If a sizecalc routine wasnt provided for this FieldType and one can't
    be decided upon as a default, then the size can't be calculated.
    Returns 0 when called.
    '''
    return 0


def def_sizecalc(self, node, **kwargs):
    '''
    Only used if the self.var_size == False.
    Returns the byte size specified by the FieldType.
    '''
    return self.size


def len_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of an object whose length is its
    size if it were converted to bytes(bytes, bytearray).
    '''
    return len(node)


def str_sizecalc(self, node, **kwargs):
    '''Returns the byte size of a string if it were encoded to bytes.'''
    return len(node)*self.size


def str_hex_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of a string of hex characters if it were encoded
    to a bytes object. Add 1 to round up to the nearest multiple of 2.
    '''
    return (len(node) + 1)//2


def delim_str_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of a delimited string if it were encoded to bytes.
    '''
    return (len(node) + self.size * (not node.endswith(self.str_delimiter)))


def delim_utf_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of a UTF string if it were encoded to bytes.

    Only use this for UTF8 and UTF16 as it is slower than delim_str_sizecalc.
    '''
    # dont add the delimiter size if the string is already delimited
    return len(node.encode(encoding=self.enc)) + (
        self.size * (not node.endswith(self.str_delimiter)))


def utf_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of a UTF string if it were encoded to bytes.

    Only use this for UTF8 and UTF16 as it is slower than str_sizecalc.
    '''
    # return the length of the entire string of bytes
    return len(node.encode(encoding=self.enc))


def array_sizecalc(self, node, **kwargs):
    '''
    Returns the byte size of an array if it were encoded to bytes.
    '''
    return len(node)*node.itemsize


def computed_sizecalc(self, node, parent=None, attr_index=None, **kwargs):
    '''
    If a sizecalc routine wasnt provided for this FieldType and one can't
    be decided upon as a default, then the size can't be calculated.
    Returns 0 when called.
    '''
    return parent.get_desc(COMPUTE_SIZECALC, attr_index)(
        node, parent=parent, attr_index=attr_index, **kwargs)


def big_sint_sizecalc(self, node, **kwargs):
    '''
    Returns the number of bytes required to represent a twos signed integer.
    NOTE: returns a size of 0 for the int 0
    '''
    # add 7 bits for rounding up, and 1 for the sign
    return (node.bit_length() + 7 + (1 if node else 0)) // 8


def big_uint_sizecalc(self, node, **kwargs):
    '''
    Returns the number of bytes required to represent an unsigned integer.
    NOTE: returns a size of 0 for the int 0
    '''
    # add 7 bits for rounding up
    return (node.bit_length() + 7) // 8


def bit_sint_sizecalc(self, node, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    NOTE: returns a size of 0 for the int 0
    '''
    # add 1 bit for the sign
    return node.bit_length() + (1 if node else 0)


def bit_uint_sizecalc(self, node, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    NOTE: returns a size of 0 for the int 0
    '''
    return node.bit_length()
