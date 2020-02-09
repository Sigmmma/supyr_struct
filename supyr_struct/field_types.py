'''
A collection of common and flexible FieldType instances and their base class.

FieldTypes are a read-only description of how this library
needs to treat a certain type of binary data or structure.

FieldTypes define functions for parsing/writing the data to/from
a buffer, decoding/encoding the data(if applicable), a function
to calculate the byte size of the data, and several properties
which determine how the data should be treated.

One way to view a FieldType is as the generalized, static properties
one would need to define in order to describe a type of data.
A descriptor holds a FieldType to describe most of the properties of
the binary data, while the descriptor stores the more specific details,
such as the number of elements in an array, length of a string, etc.

If certain data needs to be handeled in a way currently not supported, then
custom FieldTypes can be created with customized properties and functions.
'''
import struct

from array import array
from copy import deepcopy
from decimal import Decimal
from time import time, ctime
from types import FunctionType, MethodType

from supyr_struct.defs.constants import (
    NAME, SIZE, TYPE, ENTRIES, byteorder_char
    )
from supyr_struct.defs import sanitizers
from supyr_struct.field_type_methods import (
    parsers, serializers, decoders, encoders, sizecalcs
    )
from supyr_struct.buffer import BytesBuffer, BytearrayBuffer
from supyr_struct import blocks

# ######################################
#  collections of specific FieldTypes  #
# ######################################
__all__ = [
    'FieldType', 'all_field_types',
    'str_field_types', 'str_nnt_field_types',
    'cstr_field_types', 'str_raw_field_types',

    # hierarchy and structure
    'Container', 'Array', 'WhileArray',
    'Struct', 'QStruct', 'QuickStruct', 'BBitStruct', 'LBitStruct',
    'Union', 'Switch', 'StreamAdapter',

    # special FieldTypes
    'BPointer32', 'LPointer32',
    'BPointer64', 'LPointer64',
    'Void', 'Pad', 'Computed', 'WritableComputed',

    # integers and floats
    'BUIntBig', 'BSIntBig', 'BS1IntBig',
    'LUIntBig', 'LSIntBig', 'LS1IntBig',
    'UBitInt',  'SBitInt',  'S1BitInt',
    'Bit', 'UInt8', 'SInt8',
    'BUInt16', 'BSInt16', 'LUInt16', 'LSInt16',
    'BUInt24', 'BSInt24', 'LUInt24', 'LSInt24',
    'BUInt32', 'BSInt32', 'LUInt32', 'LSInt32',
    'BUInt64', 'BSInt64', 'LUInt64', 'LSInt64',
    'BFloat',  'BDouble', 'LFloat',  'LDouble',
    'BUDecimal', 'BSDecimal', 'LUDecimal', 'LSDecimal',

    # float and long int timestamps
    'BFloatTimestamp',  'LFloatTimestamp',  'BTimestamp32', 'LTimestamp32',
    'BDoubleTimestamp', 'LDoubleTimestamp', 'BTimestamp64', 'LTimestamp64',

    # enumerators and booleans
    'UBitEnum',  'SBitEnum',  'BitBool',
    'LUEnumBig', 'LSEnumBig', 'LBoolBig',
    'BUEnumBig', 'BSEnumBig', 'BBoolBig',
    'UEnum8',   'SEnum8',   'Bool8',
    'BUEnum16', 'BUEnum24', 'BUEnum32', 'BUEnum64',
    'LUEnum16', 'LUEnum24', 'LUEnum32', 'LUEnum64',
    'BSEnum16', 'BSEnum24', 'BSEnum32', 'BSEnum64',
    'LSEnum16', 'LSEnum24', 'LSEnum32', 'LSEnum64',
    'BBool16', 'BBool24', 'BBool32', 'BBool64',
    'LBool16', 'LBool24', 'LBool32', 'LBool64',

    # integers and float arrays
    'UInt8Array',   'SInt8Array', 'BytesRaw', 'BytearrayRaw', 'BytesRawEnum',
    'BUInt16Array', 'BSInt16Array', 'LUInt16Array', 'LSInt16Array',
    'BUInt32Array', 'BSInt32Array', 'LUInt32Array', 'LSInt32Array',
    'BUInt64Array', 'BSInt64Array', 'LUInt64Array', 'LSInt64Array',
    'BFloatArray',  'BDoubleArray', 'LFloatArray',  'LDoubleArray',

    # strings
    'StrLatin1',  'StrNntLatin1',  'CStrLatin1',  'StrRawLatin1',
    'StrAscii',   'StrNntAscii',   'CStrAscii',   'StrRawAscii',
    'StrUtf8',    'StrNntUtf8',    'CStrUtf8',    'StrRawUtf8',
    'BStrUtf16',  'BStrNntUtf16',  'BCStrUtf16',  'BStrRawUtf16',
    'BStrUtf32',  'BStrNntUtf32',  'BCStrUtf32',  'BStrRawUtf32',
    'LStrUtf16',  'LStrNntUtf16',  'LCStrUtf16',  'LStrRawUtf16',
    'LStrUtf32',  'LStrNntUtf32',  'LCStrUtf32',  'LStrRawUtf32',
    'StrHex',

    # #########################################################
    # short hand names that use the endianness of the system  #
    # #########################################################
    'BitStruct', 'Pointer32', 'Pointer64',

    # integers and floats
    'UIntBig', 'SIntBig', 'S1IntBig',
    'UInt16',  'UInt24',  'UInt32', 'UInt64', 'Float',
    'SInt16',  'SInt24',  'SInt32', 'SInt64', 'Double',
    'UDecimal', 'SDecimal',

    # float and long int timestamps
    'FloatTimestamp', 'DoubleTimestamp', 'Timestamp32', 'Timestamp64',

    # enumerators and booleans
    'UEnumBig', 'SEnumBig', 'BoolBig',
    'UEnum16', 'UEnum24', 'UEnum32', 'UEnum64', 'Bool16', 'Bool24',
    'SEnum16', 'SEnum24', 'SEnum32', 'SEnum64', 'Bool32', 'Bool64',
    'StrAsciiEnum', 'StrUtf8Enum',

    # integers and float arrays
    'UInt16Array', 'SInt16Array', 'UInt32Array', 'SInt32Array',
    'UInt64Array', 'SInt64Array', 'FloatArray',  'DoubleArray',

    # strings
    'StrUtf16', 'StrNntUtf16', 'CStrUtf16', 'StrRawUtf16',
    'StrUtf32', 'StrNntUtf32', 'CStrUtf32', 'StrRawUtf32'
    ]

# a list containing all valid created FieldTypes
all_field_types = []

# these are where all the single byte, less common encodings
# are located for Strings, CStrings, and raw Strings
str_field_types = {}
str_nnt_field_types  = {}
cstr_field_types = {}
str_raw_field_types = {}

# used for mapping the keyword arguments to
# the attribute name of FieldType instances
field_type_base_name_map = {'default': '_default'}
for string in ('parser', 'serializer', 'decoder', 'encoder'):
    field_type_base_name_map[string] = '_' + string

for string in ('is_data', 'is_block', 'is_str', 'is_raw',
               'is_array', 'is_container', 'is_struct', 'is_delimited',
               'is_var_size', 'is_bit_based', 'is_oe_size',
               'size', 'enc', 'max', 'min', 'data_cls', 'node_cls',
               'str_delimiter', 'delimiter', 'sanitizer', 'sizecalc'):
    field_type_base_name_map[string] = string

# Names of all the keyword argument allowed to be given to a FieldType.
valid_field_type_kwargs = set(field_type_base_name_map.keys())
valid_field_type_kwargs.update(
    ('parser', 'serializer', 'decoder', 'encoder',
     'sizecalc', 'default', 'is_block', 'name', 'base'))
# These are keyword arguments specifically used to communicate
# between Fields, and are not intended for use by developers.
valid_field_type_kwargs.update(('endian', 'other_endian'))


class EndiannessEnforcer:
    '''
    A context manager to handle forcing endianness using "with" statements.
    Can also be called to force endianness without context management.
    '''
    _f_type_instance = None
    _forced_endian = "="
    _endian_stack = None

    def __init__(self, f_type_instance=None, forced_endian="="):
        self._f_type_instance = f_type_instance
        self._forced_endian = forced_endian
        self._endian_stack = []

    def __call__(self):
        endian = self._forced_endian
        if   endian == ">":
            self.force_big()
        elif endian == "<":
            self.force_little()
        elif endian == "=":
            self.force_normal()

    def _force(self, endian):
        '''
        Replaces the FieldType class's parser, serializer, encoder,
        and decoder with methods that force them to use the little
        endian version of the FieldType(if it exists).
        '''
        if self._f_type_instance is None:
            f_types_to_swap = tuple(all_field_types)
            orig_endian = FieldType.f_endian
        else:
            f_types_to_swap = (self._f_type_instance, )
            orig_endian = self._f_type_instance.f_endian

        for f_type in f_types_to_swap:
            if endian == "<":
                endian_f_type = f_type.little
            elif endian == ">":
                endian_f_type = f_type.big
            else:
                endian_f_type = f_type

            f_type.__dict__['parser']     = endian_f_type._parser
            f_type.__dict__['serializer'] = endian_f_type._serializer
            f_type.__dict__['encoder']    = endian_f_type._encoder
            f_type.__dict__['decoder']    = endian_f_type._decoder
            f_type.__dict__['f_endian']   = endian

        return orig_endian

    def force_little(self):
        '''
        Replaces the FieldType class's parser, serializer, encoder,
        and decoder with methods that force them to use the little
        endian version of the FieldType(if it exists).
        '''
        return self._force("<")

    def force_big(self):
        '''
        Replaces the FieldType class's parser, serializer, encoder,
        and decoder with methods that force them to use the little
        endian version of the FieldType(if it exists).
        '''
        return self._force(">")

    def force_normal(self):
        '''
        Replaces the FieldType class's parser, serializer, encoder,
        and decoder with methods that do not force them to use an
        endianness other than the one they are currently set to.
        '''
        return self._force("=")

    def __enter__(self):
        endian = self._forced_endian
        if   endian == ">":
            self._endian_stack.append(self.force_big())
        elif endian == "<":
            self._endian_stack.append(self.force_little())
        elif endian == "=":
            self._endian_stack.append(self.force_normal())

    def __exit__(self, except_type, except_value, traceback):
        try:
            endian = self._endian_stack.pop()
        except IndexError:
            return

        if endian == ">":
            self.force_big()
        elif endian == "<":
            self.force_little()
        elif endian == "=":
            self.force_normal()
        # TODO, raise if endian value is invalid?


class FieldType():
    '''
    FieldTypes are a read-only description of a certain kind of binary
    data, structure, or flow control system(like a switch).

    FieldTypes define functions for reading/writing the data to/from
    a buffer, encoding/decoding the data(if applicable), a function
    to calculate the byte size of the data, and numerous other
    properties which determine how the data should be treated.

    Each FieldType which is endianness dependent has a reference to the
    FieldType with the opposite endianness.

    Calling a FieldType will return an incomplete descriptor made from
    the given positional and keyword arguments. The called FieldType
    will be added to the dictionary under TYPE and the first argument
    will be added under NAME. The only exception to this is Pad, which
    takes the first argument to be the size of the padding(since naming
    padding is meaningless), and adds it to the descriptor under SIZE.
    This descriptor can then be used in a BlockDef.

    Calling __copy__ or __deepcopy__ will instead return the called FieldType.

    Instance properties:
        bool:
            is_data
            is_block
            is_str
            is_raw
            is_struct
            is_array
            is_container
            is_var_size
            is_oe_size
            is_bit_based
            is_delimited
        function:
            sanitizer
            struct_packer
            struct_unpacker
        int:
            size
            min
            max
        method:
            parser
            serializer
            decoder
            encoder
            sizecalc
        str:
            name
            enc
            endian
            f_endian ----- endianness character representing the endianness
                           the FieldType is being forced to encode/decode in.
            delimiter
            str_delimiter
        type:
            node_cls
            data_cls

    Read this classes __init__.__doc__ for descriptions of these properties.
    '''

    # The initial forced endianness 'do not force'
    f_endian = '='

    def __init__(self, **kwargs):
        '''
        Initializes a FieldType with the supplied keyword arguments.

        Raises TypeError if invalid keyword combinations are provided.
        Raises KeyError if unknown arguments are provided.

        All FieldTypes must be either Block, data, or both, and will start
        with is_data set to True and all other flags set to False.
        Certain flags being set implies that others are set, and if the
        implied flag is not provided, it will be automatically set.

        size not being provided implies that is_var_size is True.
        is_array being True implies that is_container is True.
        is_str being True implies that is_var_size is True.
        is_struct, or is_container being True implies that is_block is True
        is_struct and is_container cannot be both True.

        If endian is not supplied, it defaults to '='

        Keyword arguments:

        # bool:
        is_block ----- Is a form of hierarchy(struct, array, container, etc).
                       If something is a Block, it is expected to have a desc
                       attribute, meaning it holds its own descriptor rather
                       than having its parent hold its descriptor for it.
                       If a FieldType is a Block, it also means it can have
                       child nodes within it; It can be a parent node.
        is_data ------ Is a form of data(string, integer, float, bytes, etc).
                       A FieldType being data means it represents a single
                       piece of information. This extends to FieldTypes
                       where is_block is True, such as enums and bools.
                       In those cases, the "piece of information" is the
                       enumeration value or the int that the booleans are
                       stored in respectively.
                       If a FieldType is data, it also means it will not
                       have child nodes within it; It is a leaf node.
        is_str ------- Is a python string with a specific encoding
                       (If is_str is True, is_var_size is also True).
                       enc must be the encoding of the string, and size
                       must be the number of bytes per string character.
        is_raw ------- Is unencoded rawdata(usually bytes or a bytearray).
                       If is_raw is True, is_var_size is also True.
        is_array ----- Is an array of instanced elements(is also a container).
        is_struct ---- Has a fixed size and its numbered fields have offsets
                       (if True, is_var_size is also True).
        is_container - Has a variable size and its fields dont have offsets
                       (if True, is_block and is_var_size are also True).
                       Containers are also automatically assumed to be a
                       subtree_root for STEPTREE nodes, and their size is
                       measured in the number of fields in them rather than
                       a serialized byte size. This means that a container
                       Blocks get/set_size methods operate on the number
                       of fields in the Block rather than its byte size.
        is_var_size -- Size of object can vary(descriptor defined size).
        is_oe_size --- The fields size can only be determined after the
                       field has been parsed as it relies on a sort of
                       delimiter, or it is a stream of data that must be
                       parsed to find the end(the stream is open ended).
        is_bit_based - Whether or not the data is measured in bits(not bytes).
                       Within a BitStruct, offsets, sizes, etc, are in bits.
                       However, a BitStructs offset, size, etc are in bytes.
        is_delimited - Whether or not the string is terminated with a
                       delimiter character(only valid when is_str == True).

        # FieldType:
        base ----------- Used as an initializer for a new FieldType instance.
                         When supplied, most of the bases attributes are
                         copied into kwargs using kwargs.setdefault().
                         The attributes that are copied are as follows:
                             is_data, is_block, is_str, is_raw,
                             is_struct, is_array, is_container,
                             is_var_size, is_bit_based, is_delimited,
                             node_cls, data_cls, default, delimiter,
                             enc, max, min, size, str_delimiter
                             _parser, _serializer, sizecalc,
                             _decoder, _encoder, sanitizer

        # function:
        parser ------ A function for reading bytes from a buffer and calling
                      its decoder on them. For a Block, this instead calls
                      the readers of each of the child nodes.
                      Read docs/parsers.txt for more info.
        serializer -- An optional function for calling its encoder on an object
                      and writing the bytes to a buffer. For a Block, this
                      instead calls the writers of each of the its child nodes.
                      Read docs/serializers.txt for more info.
        decoder ----- An optional function for decoding bytes from a buffer
                      into an object(ex: b'\xD1\x22\xAB\x3F' to a float).
                      Read docs/decoders.txt for more info.
        encoder ----- An optional function for encoding an object into a
                      writable raw form(ex: "test" into b'\x74\x65\x73\x74').
                      Read docs/encoders.txt for more info.
        sizecalc ---- An optional function for calculating the size of an
                      object in whatever units it's measured in(usually bytes).
                      Most of the time this isn't needed, but for variable
                      length data(size is determined by some previously parsed
                      field) the size may need to be calculated after an edit.

                      If a sizecalc isnt provided, one will be decided upon
                      based on the node_cls as follows:
                          str = str_sizecalc
                          array.array = array_sizecalc
                          bytearray or bytes = len_sizecalc

                      If the node_cls doesnt fall under any of these, a couple
                      bools will be checked:
                          is_array is True = len_sizecalc
                          is_var_size is True = no_sizecalc

                      Failing all that, sizecalc will default to def_sizecalc.
                      Read docs/sizecalcs.txt for more info.
        sanitizer --- An optional function which checks and properly sanitizes
                      descriptors that have this FieldType as their TYPE.
                      Read docs/sanitizers.txt for more info.

        # int:
        size -------- The byte size of the data when in binary form.
                      For strings this is how many bytes a single character is.
        max --------- For floats/ints, this is the largest a value can be.
        min --------- For floats/ints, this is the smallest a value can be.

        # object
        default -------- A python object to use as a default value.
                         This can also be a function which will be called
                         with the provided args and kwargs passed to it.
                         The function is expected to return a default value.
                         A good example is the Timestamp FieldType2 which call
                         ctime(time()) and returns a current timestamp string.
        # type:
        node_cls ------- The python type associated with this FieldType.
                         For example, this is set to int for all of the integer
                         FieldTypes(UInt8, Bit, BSInt64, Pointer32, etc) and
                         to ListBlock for Container, Struct, Array, etc.
                         If node_cls isnt provided on instantiation(or a
                         base isnt) type(self._default) will be used instead.
                         Used mainly for type checking and creating new
                         instances of the object associated with this FieldType
        data_cls ------- The python type that the 'data' attribute in
                         a DataBlock is supposed to be an instance of.
                         If this is anything other than type(None), the
                         node must be a DataBlock with a 'data' attribute
                         which should be an instance of 'data_cls'.
                         For example, all the bools and integer enum
                         FieldTypes have their node_cls as EnumBlock or
                         BoolBlock and int as their data_cls.

        # str:
        name ----------- The name of this FieldType.
        enc ------------ A string used to specify the format for encoding
                         and decoding the data. This is expected to exist
                         for non-raw "data" FieldTypes, but there is no set
                         convention as it depends on what the decode/encode
                         function requires.

                         For example, enc for numbers de/encoded by pythons
                         struct module would be any one character in '<>'
                         for the endianness followed by any one character in
                         'bhiqfBHIQD'. Str_UTF_16_LE and Str_Latin_1 on the
                         other hand use "UTF_16_LE" and "latin-1" respectively.
        endian --------- The endianness of this FieldType.
                         Must be one of the following characters: '<>='
                         '>' means big endian, '<' means little endian, and
                         '=' means endianness has no meaning for the FieldType.
        f_endian ------- The endianness character representing the endianness
                         the FieldType is being forced to encode/decode in.
        delimiter ------ The string delimiter in its encoded, bytes form.
        str_delimiter -- The string delimiter in its decoded, python form.
        '''

        # check for unknown keyword arguments
        given_kwargs, kwargs = kwargs, {}
        for kwarg in valid_field_type_kwargs:
            if kwarg in given_kwargs:
                kwargs[kwarg] = given_kwargs.pop(kwarg)
        # if there are any remaining keyword arguments, raise an error
        if given_kwargs:
            raise KeyError('Unknown supplied keyword arguments:\n    %s' %
                           given_kwargs.keys())

        # set the FieldType as editable
        self._instantiated = False

        # set up the default values for each attribute.
        # default endianness of the initial FieldType is "no endianness"
        self.endian = '='
        self.little = self.big = self
        self.min = self.max = self._default = self.enc = None
        self.delimiter = self.str_delimiter = None
        self.size = None

        # set the FieldTypes flags
        self.is_str = self.is_data = self.is_block = \
                      self.is_raw = self.is_delimited = self.is_struct = \
                      self.is_array = self.is_container = self.is_var_size = \
                      self.is_oe_size = self.is_bit_based = False

        # if a base was provided, use it to update kwargs with its settings
        base = kwargs.get('base')
        if isinstance(base, FieldType):
            # if the base has separate encodings for the
            # different endiannesses, make sure to set the
            # default encoding of this FieldType as theirs
            if base.little.enc != base.big.enc:
                kwargs.setdefault(
                    'enc', {'<': base.little.enc, '>': base.big.enc})

            # loop over each attribute in the base that can be copied
            for attr in field_type_base_name_map:
                if attr in kwargs:
                    continue
                kwargs[attr] = base.__getattribute__(
                    field_type_base_name_map[attr])
                if isinstance(kwargs[attr], MethodType):
                    kwargs[attr] = kwargs[attr].__func__

        # if both is_block and is_data arent supplied, is_data defaults to True
        if 'is_data' not in kwargs and 'is_block' not in kwargs:
            self.is_data = kwargs["is_data"] = True

        # setup the FieldTypes main properties
        self.name = kwargs.get("name")

        self._parser = (MethodType(kwargs["parser"], self)
                        if kwargs.get("parser") else self._not_imp)
        self._serializer = (MethodType(kwargs["serializer"], self)
                            if kwargs.get("serializer") else self._not_imp)

        self._decoder = MethodType(kwargs.get("decoder", decoders.no_decode), self)
        self._encoder = MethodType(kwargs.get("encoder", encoders.no_encode), self)

        self.sanitizer = kwargs.get("sanitizer", sanitizers.standard_sanitizer)

        self.data_cls = kwargs.get("data_cls", type(None))

        self._default = kwargs.get("default", None)
        self.size = kwargs.get("size", self.size)
        self.node_cls = kwargs.get("node_cls", type(self._default))

        # set the FieldTypes flags
        self.is_block = bool(kwargs.get("is_block", self.is_block))
        self.is_data = bool(kwargs.get("is_data", self.is_data))
        self.is_str = bool(kwargs.get("is_str", self.is_str))
        self.is_raw = bool(kwargs.get("is_raw", self.is_raw))
        self.is_array = bool(kwargs.get("is_array", self.is_array))
        self.is_struct = bool(kwargs.get("is_struct", self.is_struct))
        self.is_oe_size = bool(kwargs.get("is_oe_size", self.is_oe_size))
        self.is_var_size = bool(kwargs.get("is_var_size", self.is_var_size))
        self.is_container = bool(kwargs.get("is_container", self.is_container))
        self.is_bit_based = bool(kwargs.get("is_bit_based", self.is_bit_based))
        self.is_delimited = bool(kwargs.get("is_delimited", self.is_delimited))

        # arrays are also containers
        self.is_container |= self.is_array
        # All strings are variable size since the 'size' property
        # refers to the size of each character in the string.
        # Raw data, structs, and containers are also variable size.
        self.is_var_size |= (self.is_str or self.is_raw or
                             self.is_struct or self.is_container)
        # structs and containers are always blocks
        self.is_block |= self.is_struct or self.is_container

        if self.name is None:
            raise TypeError("'name' is a required identifier for data types.")

        if self.size is None:
            # if size isnt specified then the FieldType is of variable size.
            self.is_var_size = True
        else:
            # if the delimiter isnt specified, set it to 0x00*size
            kwargs.setdefault("delimiter", b'\x00'*int(self.size))

        if self.is_str:
            self.delimiter = kwargs.get("delimiter")
            self.str_delimiter = kwargs.get("str_delimiter",
                                            self.str_delimiter)

        if kwargs.get("endian") in ('<', '>', '='):
            self.endian = kwargs["endian"]
        elif "endian" in kwargs:
            raise TypeError("Supplied endianness must be one of the " +
                            "following characters: '<', '>', or '='")

        if isinstance(kwargs.get("enc"), str):
            self.enc = kwargs["enc"]
        elif isinstance(kwargs.get("enc"), dict):
            enc = kwargs["enc"]
            if not('<' in enc and '>' in enc):
                raise TypeError(
                    "When providing endianness reliant encodings, " +
                    "big and little endian\nmust both be provided " +
                    "under the keys '>' and '<' respectively.")
            # make the first encoding the endianness of the system
            self.enc = enc['<']
            self.endian = byteorder_char

        if self.is_container and self.is_struct:
            raise TypeError('A FieldType can not be both a struct ' +
                            'and a container at the same time.')

        other_endian = kwargs.get('other_endian')

        # if the endianness is specified as '=' it means that
        # endianness has no meaning for this FieldType and that
        # big and little should be the same. Otherwise, create
        # a similar FieldType, but with an opposite endianness
        if self.endian != "=" and other_endian is None:
            # set the endianness kwarg to the opposite of this one
            kwargs["endian"] = {'<': '>', '>': '<'}[self.endian]
            kwargs["other_endian"] = self

            # if the provided enc kwarg is a dict, get the encoding
            # of the endianness opposite the current FieldType.
            if 'enc' in kwargs and isinstance(kwargs["enc"], dict):
                kwargs["enc"] = kwargs["enc"][kwargs["endian"]]
            else:
                kwargs["enc"] = self.enc

            # create the other endian FieldType
            other_endian = FieldType(**kwargs)

        # set the other endianness FieldType
        if self.endian == '<':
            self.big = other_endian
        elif self.endian == '>':
            self.little = other_endian

        self.min = kwargs.get("min", self.min)
        self.max = kwargs.get("max", self.max)

        if self.str_delimiter is not None and self.delimiter is None:
            self.delimiter = self.str_delimiter.encode(encoding=self.enc)
        if self.delimiter is not None and self.str_delimiter is None:
            self.str_delimiter = self.delimiter.decode(encoding=self.enc)

        # Decide on a sizecalc method to use based on the
        # data type or use the one provided, if provided
        if "sizecalc" in kwargs:
            sizecalc = kwargs['sizecalc']
        elif issubclass(self.node_cls, str):
            sizecalc = sizecalcs.str_sizecalc
        elif issubclass(self.node_cls, array):
            sizecalc = sizecalcs.array_sizecalc
        elif issubclass(self.node_cls, (bytearray, bytes)) or self.is_array:
            sizecalc = sizecalcs.len_sizecalc
        elif self.is_var_size:
            sizecalc = sizecalcs.no_sizecalc
        else:
            sizecalc = sizecalcs.def_sizecalc

        self.sizecalc = MethodType(sizecalc, self)
        self.parser = self._parser
        self.serializer = self._serializer
        self.decoder = self._decoder
        self.encoder = self._encoder

        try:
            # cache these as methods bound to their encoding
            self.struct_packer = MethodType(struct.pack, self.enc)
            self.struct_unpacker = MethodType(struct.unpack, self.enc)
        except (struct.error, TypeError):
            self.struct_packer = self._not_imp
            self.struct_unpacker = self._not_imp

        try:
            # if a default wasn't provided, create one from self.node_cls
            if self._default is None and not self.is_block:
                self._default = self.node_cls()
        except Exception:
            raise TypeError(
                ("Could not create an instance of self.node_cls to " +
                 "set the default value of the %s FieldType to.\n" +
                 "You must manually supply a default value.") % self.name)

        # set up self.default to return a copy of self._default when called
        if isinstance(self._default, FunctionType):
            self.default = self._default
        elif self._default is None:
            self.default = lambda *a, **kw: None
        else:
            self.default = MethodType(deepcopy, self._default)

        self.force_normal = EndiannessEnforcer(self, "=")
        self.force_little = EndiannessEnforcer(self, "<")
        self.force_big    = EndiannessEnforcer(self, ">")

        # now that setup is concluded, set the object as read-only
        self._instantiated = True

        # add this to the collection of all FieldTypes
        all_field_types.append(self)

    def __call__(self, name, *desc_entries, **desc):
        '''
        Creates a dict formatted properly to be used as a descriptor.
        The first argument must be nodes name.
        If the FieldType is Pad, the first argument is the padding size.
        The remaining positional args are the numbered entries in the
        descriptor, and the keyword arguments are the non-numbered entries
        in the descriptor. This is only a macro though, meaning descriptors
        created by it must still be run through a sanitization routine.

        Returns the created descriptor dict.
        '''
        if self is Pad:
            desc.setdefault(NAME, '_')
            desc.setdefault(SIZE, name)
        elif isinstance(name, str):
            desc.setdefault(NAME, name)
        else:
            raise TypeError("'name' must be of type '%s', not '%s'" %
                            (type(str), type(name)))

        desc[TYPE] = self

        i = 0
        # add all the positional arguments to the descriptor
        for entry in desc_entries:
            desc[i] = entry
            i += 1

        desc[ENTRIES] = i

        return desc

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        '''
        Returns this object.
        You should never need to make a deep copy of ANY FieldType.
        '''
        return self

    def __str__(self):
        return("<FieldType:'%s', endian:'%s', enc:'%s'>" %
               (self.name, self.endian, self.enc))

    __repr__ = __str__

    # To prevent editing of FieldTypes once they are instintiated, the
    # default __setattr__ and __delattr__ methods are overloaded
    def __setattr__(self, attr, value):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError(
                "FieldTypes are read-only and cannot be changed once created.")
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError(
                "FieldTypes are read-only and cannot be changed once created.")
        object.__delattr__(self, attr)

    force_normal = EndiannessEnforcer(None, "=")
    force_little = EndiannessEnforcer(None, "<")
    force_big    = EndiannessEnforcer(None, ">")

    def _not_imp(self, *args, **kwargs):
        raise NotImplementedError(
            "This operation not implemented in the %s FieldType." % self.name)


# The main hierarchial and special FieldTypes
Void = FieldType(
    name="Void", is_block=True, size=0, node_cls=blocks.VoidBlock,
    parser=parsers.void_parser,
    serializer=serializers.void_serializer
    )
Pad = FieldType(
    name="Pad", is_block=True, node_cls=blocks.VoidBlock,
    parser=parsers.pad_parser,
    serializer=serializers.pad_serializer
    )
Computed = FieldType(
    name="Computed", size=0,
    parser=parsers.computed_parser,
    serializer=serializers.void_serializer
    )
WritableComputed = FieldType(
    name="WritableComputed", is_var_size=True,
    parser=parsers.computed_parser,
    sizecalc=sizecalcs.computed_sizecalc,
    serializer=serializers.computed_serializer
    )
Container = FieldType(
    name="Container", is_container=True, is_block=True,
    node_cls=blocks.ListBlock,
    sanitizer=sanitizers.sequence_sanitizer,
    parser=parsers.container_parser,
    serializer=serializers.container_serializer,
    sizecalc=sizecalcs.len_sizecalc
    )
Struct = FieldType(
    name="Struct", is_struct=True, is_block=True, node_cls=blocks.ListBlock,
    sanitizer=sanitizers.struct_sanitizer,
    parser=parsers.struct_parser,
    serializer=serializers.struct_serializer
    )
QuickStruct = FieldType(
    name="QuickStruct", base=Struct,
    sanitizer=sanitizers.quickstruct_sanitizer,
    parser=parsers.quickstruct_parser,
    serializer=serializers.quickstruct_serializer
    )
Array = FieldType(
    name="Array", is_array=True, is_block=True, node_cls=blocks.ArrayBlock,
    sanitizer=sanitizers.sequence_sanitizer,
    parser=parsers.array_parser,
    serializer=serializers.array_serializer
    )
WhileArray = FieldType(
    name="WhileArray", is_array=True, is_block=True, is_oe_size=True,
    node_cls=blocks.WhileBlock,
    sanitizer=sanitizers.sequence_sanitizer,
    parser=parsers.while_array_parser,
    serializer=serializers.array_serializer
    )
Switch = FieldType(
    name='Switch', is_block=True, node_cls=blocks.VoidBlock,
    sanitizer=sanitizers.switch_sanitizer,
    parser=parsers.switch_parser,
    serializer=serializers.void_serializer
    )
StreamAdapter = FieldType(
    name="StreamAdapter", is_block=True, is_oe_size=True,
    node_cls=blocks.WrapperBlock,
    sanitizer=sanitizers.stream_adapter_sanitizer,
    parser=parsers.stream_adapter_parser,
    serializer=serializers.stream_adapter_serializer
    )
Union = FieldType(
    base=Struct, name="Union", is_block=True, node_cls=blocks.UnionBlock,
    sanitizer=sanitizers.union_sanitizer,
    parser=parsers.union_parser,
    serializer=serializers.union_serializer
    )
# shorthand alias
QStruct = QuickStruct

# bit_based data
'''When within a BitStruct, offsets and sizes are in bits instead of bytes.
BitStruct sizes, however, must be specified in bytes(1byte, 2bytes, etc)'''
BitStruct = FieldType(
    name="BitStruct", is_struct=True, is_bit_based=True, enc={'<': '<', '>': '>'},
    node_cls=blocks.ListBlock,
    sanitizer=sanitizers.struct_sanitizer,
    parser=parsers.bit_struct_parser,
    serializer=serializers.bit_struct_serializer
    )
BBitStruct, LBitStruct = BitStruct.big, BitStruct.little

'''For when you dont need multiple bits. It's faster and
easier to use this than a BitUInt with a size of 1.'''
Bit = FieldType(
    name="Bit", is_bit_based=True, size=1, enc='U', default=0,
    parser=parsers.default_parser,
    decoder=decoders.decode_bit,
    encoder=encoders.encode_bit
    )

'''UBitInt, S1BitInt, and SBitInt must be in a BitStruct as the BitStruct
acts as a bridge between byte level and bit level objects.
S1BitInt is signed in 1's compliment and SBitInt is in 2's compliment.'''
SBitInt = FieldType(
    name='SBitInt', is_bit_based=True, enc='S', default=0,
    sizecalc=sizecalcs.bit_sint_sizecalc,
    parser=parsers.default_parser,
    decoder=decoders.decode_bit_int,
    encoder=encoders.encode_bit_int
    )
S1BitInt = FieldType(
    base=SBitInt, name="S1BitInt", enc="s"
    )
UBitInt  = FieldType(
    base=SBitInt, name="UBitInt",  enc="U", min=0,
    sizecalc=sizecalcs.bit_uint_sizecalc
    )
UBitEnum = FieldType(
    base=UBitInt, name="UBitEnum", is_data=True, is_block=True,
    data_cls=int, node_cls=blocks.EnumBlock, default=None,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.bit_uint_sizecalc),
    decoder=decoders.decoder_wrapper(decoders.decode_bit_int),
    encoder=encoders.encoder_wrapper(encoders.encode_bit_int),
    sanitizer=sanitizers.enum_sanitizer
    )
SBitEnum = FieldType(
    base=SBitInt, name="SBitEnum", is_data=True, is_block=True,
    data_cls=int, node_cls=blocks.EnumBlock, default=None,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.bit_sint_sizecalc),
    decoder=decoders.decoder_wrapper(decoders.decode_bit_int),
    encoder=encoders.encoder_wrapper(encoders.encode_bit_int),
    sanitizer=sanitizers.enum_sanitizer
    )
BitBool = FieldType(
    base=UBitInt, name="BitBool", is_data=True, is_block=True,
    data_cls=int, node_cls=blocks.BoolBlock, default=None,
    decoder=decoders.decoder_wrapper(decoders.decode_bit_int),
    encoder=encoders.encoder_wrapper(encoders.encode_bit_int),
    sanitizer=sanitizers.bool_sanitizer
    )

SIntBig = FieldType(
    base=UBitInt, name="SIntBig", is_bit_based=False, enc={'<': "<S", '>': ">S"},
    parser=parsers.data_parser,
    serializer=serializers.f_s_data_serializer,
    decoder=decoders.decode_big_int,
    encoder=encoders.encode_big_int,
    sizecalc=sizecalcs.big_sint_sizecalc
    )
S1IntBig = FieldType(
    base=SIntBig, name="S1IntBig", enc={'<': "<s", '>': ">s"}
    )
UIntBig  = FieldType(
    base=SIntBig, name="UIntBig",  enc={'<': "<U", '>': ">U"}, min=0,
    sizecalc=sizecalcs.big_uint_sizecalc
    )
UEnumBig = FieldType(
    base=UIntBig, name="UEnumBig", is_data=True, is_block=True,
    data_cls=int, default=None, node_cls=blocks.EnumBlock,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.big_uint_sizecalc),
    decoder=decoders.decoder_wrapper(decoders.decode_big_int),
    encoder=encoders.encoder_wrapper(encoders.encode_big_int),
    sanitizer=sanitizers.enum_sanitizer
    )
SEnumBig = FieldType(
    base=SIntBig, name="SEnumBig", is_data=True, is_block=True,
    data_cls=int, default=None, node_cls=blocks.EnumBlock,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.big_sint_sizecalc),
    decoder=decoders.decoder_wrapper(decoders.decode_big_int),
    encoder=encoders.encoder_wrapper(encoders.encode_big_int),
    sanitizer=sanitizers.enum_sanitizer
    )
BoolBig = FieldType(
    base=UIntBig, name="BoolBig", is_data=True, is_block=True,
    data_cls=int, default=None, node_cls=blocks.BoolBlock,
    decoder=decoders.decoder_wrapper(decoders.decode_big_int),
    encoder=encoders.encoder_wrapper(encoders.encode_big_int),
    sanitizer=sanitizers.bool_sanitizer
    )

BSIntBig,  LSIntBig  = SIntBig.big,  SIntBig.little
BUIntBig,  LUIntBig  = UIntBig.big,  UIntBig.little
BS1IntBig, LS1IntBig = S1IntBig.big, S1IntBig.little
BUEnumBig, LUEnumBig = UEnumBig.big, UEnumBig.little
BSEnumBig, LSEnumBig = SEnumBig.big, SEnumBig.little
BBoolBig,  LBoolBig  = BoolBig.big,  BoolBig.little

SDecimal = FieldType(
    base=SIntBig, name="SDecimal", enc={'<': "<S", '>': ">S"}, default=Decimal(0),
    decoder=decoders.decode_decimal,
    encoder=encoders.encode_decimal,
    sizecalc=sizecalcs.def_sizecalc)
UDecimal = FieldType(
    base=SDecimal, name="UDecimal", enc={'<': "<U", '>': ">U"}
    )

BSDecimal, LSDecimal = SDecimal.big, SDecimal.little
BUDecimal, LUDecimal = UDecimal.big, UDecimal.little

# 8/16/32/64-bit integers
UInt8 = FieldType(
    base=UIntBig, name="UInt8", size=1, min=0, max=255, enc='B', is_var_size=False,
    parser=parsers.f_s_data_parser,
    sizecalc=sizecalcs.def_sizecalc,
    decoder=decoders.decode_numeric,
    encoder=encoders.encode_numeric
    )
UInt16 = FieldType(
    base=UInt8, name="UInt16", size=2, max=2**16-1, enc={'<': "<H", '>': ">H"}
    )
UInt32 = FieldType(
    base=UInt8, name="UInt32", size=4, max=2**32-1, enc={'<': "<I", '>': ">I"}
    )
UInt64 = FieldType(
    base=UInt8, name="UInt64", size=8, max=2**64-1, enc={'<': "<Q", '>': ">Q"}
    )

SInt8 = FieldType(base=UInt8,  name="SInt8", min=-2**7, max=2**7-1, enc="b")
SInt16 = FieldType(
    base=UInt16, name="SInt16", min=-2**15, max=2**15-1, enc={'<': "<h", '>': ">h"}
    )
SInt32 = FieldType(
    base=UInt32, name="SInt32", min=-2**31, max=2**31-1, enc={'<': "<i", '>': ">i"}
    )
SInt64 = FieldType(
    base=UInt64, name="SInt64", min=-2**63, max=2**63-1, enc={'<': "<q", '>': ">q"}
    )

BUInt16, LUInt16 = UInt16.big, UInt16.little
BUInt32, LUInt32 = UInt32.big, UInt32.little
BUInt64, LUInt64 = UInt64.big, UInt64.little

BSInt16, LSInt16 = SInt16.big, SInt16.little
BSInt32, LSInt32 = SInt32.big, SInt32.little
BSInt64, LSInt64 = SInt64.big, SInt64.little

# pointers
Pointer32 = FieldType(base=UInt32, name="Pointer32")
Pointer64 = FieldType(base=UInt64, name="Pointer64")

BPointer32, LPointer32 = Pointer32.big, Pointer32.little
BPointer64, LPointer64 = Pointer64.big, Pointer64.little

enum_kwargs = {
    'is_block': True, 'is_data': True,
    'data_cls': int, 'node_cls': blocks.EnumBlock, 'default': None,
    'sanitizer': sanitizers.enum_sanitizer,
    'sizecalc':sizecalcs.sizecalc_wrapper(sizecalcs.def_sizecalc),
    'decoder':decoders.decoder_wrapper(decoders.decode_numeric),
    'encoder':encoders.encoder_wrapper(encoders.encode_numeric)
    }

bool_kwargs = {
    'is_block': True, 'is_data': True,
    'data_cls': int, 'node_cls': blocks.BoolBlock, 'default': None,
    'sanitizer': sanitizers.bool_sanitizer,
    'sizecalc':sizecalcs.sizecalc_wrapper(sizecalcs.def_sizecalc),
    'decoder':decoders.decoder_wrapper(decoders.decode_numeric),
    'encoder':encoders.encoder_wrapper(encoders.encode_numeric)
    }
# enumerators
UEnum8 = FieldType(base=UInt8,   name="UEnum8",  **enum_kwargs)
UEnum16 = FieldType(base=UInt16, name="UEnum16", **enum_kwargs)
UEnum32 = FieldType(base=UInt32, name="UEnum32", **enum_kwargs)
UEnum64 = FieldType(base=UInt64, name="UEnum64", **enum_kwargs)

SEnum8 = FieldType(base=SInt8,   name="SEnum8",  **enum_kwargs)
SEnum16 = FieldType(base=SInt16, name="SEnum16", **enum_kwargs)
SEnum32 = FieldType(base=SInt32, name="SEnum32", **enum_kwargs)
SEnum64 = FieldType(base=SInt64, name="SEnum64", **enum_kwargs)

BUEnum16, LUEnum16 = UEnum16.big, UEnum16.little
BUEnum32, LUEnum32 = UEnum32.big, UEnum32.little
BUEnum64, LUEnum64 = UEnum64.big, UEnum64.little

BSEnum16, LSEnum16 = SEnum16.big, SEnum16.little
BSEnum32, LSEnum32 = SEnum32.big, SEnum32.little
BSEnum64, LSEnum64 = SEnum64.big, SEnum64.little

# booleans
Bool8 = FieldType(base=UInt8,   name="Bool8",  **bool_kwargs)
Bool16 = FieldType(base=UInt16, name="Bool16", **bool_kwargs)
Bool32 = FieldType(base=UInt32, name="Bool32", **bool_kwargs)
Bool64 = FieldType(base=UInt64, name="Bool64", **bool_kwargs)

BBool16, LBool16 = Bool16.big, Bool16.little
BBool32, LBool32 = Bool32.big, Bool32.little
BBool64, LBool64 = Bool64.big, Bool64.little

# 24-bit integers
UInt24 = FieldType(
    base=UInt8, name="UInt24", size=3, max=2**24-1, enc={'<': "<T", '>': ">T"},
    decoder=decoders.decode_24bit_numeric,
    encoder=encoders.encode_24bit_numeric
    )
SInt24 = FieldType(
    base=UInt24, name="SInt24", min=-2**23, max=2**23-1, enc={'<': "<t", '>': ">t"}
    )
enum_kwargs.update(
    decoder=decoders.decoder_wrapper(decoders.decode_24bit_numeric),
    encoder=encoders.encoder_wrapper(encoders.encode_24bit_numeric)
    )
bool_kwargs.update(
    decoder=decoders.decoder_wrapper(decoders.decode_24bit_numeric),
    encoder=encoders.encoder_wrapper(encoders.encode_24bit_numeric)
    )
UEnum24 = FieldType(base=UInt24, name="UEnum24", **enum_kwargs)
SEnum24 = FieldType(base=SInt24, name="SEnum24", **enum_kwargs)
Bool24 = FieldType(base=UInt24,  name="Bool24",  **bool_kwargs)

BUInt24,  LUInt24 = UInt24.big,  UInt24.little
BSInt24,  LSInt24 = SInt24.big,  SInt24.little
BUEnum24, LUEnum24 = UEnum24.big, UEnum24.little
BSEnum24, LSEnum24 = SEnum24.big, SEnum24.little
BBool24,  LBool24 = Bool24.big,  Bool24.little

# floats
Float = FieldType(
    base=UInt32, name="Float", default=0.0, node_cls=float, enc={'<': "<f", '>': ">f"},
    max=struct.unpack('>f', b'\x7f\x7f\xff\xff')[0],
    min=struct.unpack('>f', b'\xff\x7f\xff\xff')[0]
    )
Double = FieldType(
    base=Float, name="Double", size=8, enc={'<': "<d", '>': ">d"},
    max=struct.unpack('>d', b'\x7f\xef\xff\xff\xff\xff\xff\xff')[0],
    min=struct.unpack('>d', b'\xff\xef\xff\xff\xff\xff\xff\xff')[0]
    )

BFloat,  LFloat = Float.big,  Float.little
BDouble, LDouble = Double.big, Double.little


FloatTimestamp = FieldType(
    base=Float, name="FloatTimestamp", node_cls=str,
    default=lambda *a, **kwa: ctime(time()),
    min='Wed Dec 31 19:00:00 1969', max='Thu Jan  1 02:59:59 3001',
    encoder=encoders.encode_float_timestamp,
    decoder=decoders.decode_timestamp
    )
DoubleTimestamp = FieldType(
    base=FloatTimestamp, name="DoubleTimestamp", enc={'<': "<d", '>': ">d"}, size=8
    )
Timestamp32 = FieldType(
    base=FloatTimestamp, name="Timestamp32", enc={'<': "<I", '>': ">I"},
    encoder=encoders.encode_int_timestamp
    )
Timestamp64 = FieldType(
    base=Timestamp32, name="Timestamp64", enc={'<': "<Q", '>': ">Q"}, size=8
    )

BFloatTimestamp,  LFloatTimestamp  = FloatTimestamp.big,  FloatTimestamp.little
BDoubleTimestamp, LDoubleTimestamp = DoubleTimestamp.big, DoubleTimestamp.little
BTimestamp32, LTimestamp32 = Timestamp32.big, Timestamp32.little
BTimestamp64, LTimestamp64 = Timestamp64.big, Timestamp64.little

# Arrays
UInt8Array = FieldType(
    name="UInt8Array", size=1, is_var_size=True, enc='B', default=array("B", []),
    sizecalc=sizecalcs.array_sizecalc,
    parser=parsers.py_array_parser,
    serializer=serializers.py_array_serializer
    )
UInt16Array = FieldType(
    base=UInt8Array, name="UInt16Array", size=2,
    default=array("H", []), enc={"<": "H", ">": "H"}
    )
UInt32Array = FieldType(
    base=UInt8Array, name="UInt32Array", size=4,
    default=array("I", []), enc={"<": "I", ">": "I"}
    )
UInt64Array = FieldType(
    base=UInt8Array, name="UInt64Array", size=8,
    default=array("Q", []), enc={"<": "Q", ">": "Q"}
    )

SInt8Array = FieldType(
    base=UInt8Array, name="SInt8Array", default=array("b", []), enc="b")
SInt16Array = FieldType(
    base=UInt8Array, name="SInt16Array", size=2,
    default=array("h", []), enc={"<": "h", ">": "h"}
    )
SInt32Array = FieldType(
    base=UInt8Array, name="SInt32Array", size=4,
    default=array("i", []), enc={"<": "i", ">": "i"}
    )
SInt64Array = FieldType(
    base=UInt8Array, name="SInt64Array", size=8,
    default=array("q", []), enc={"<": "q", ">": "q"}
    )

FloatArray = FieldType(
    base=UInt32Array, name="FloatArray",
    default=array("f", []), enc={"<": "f", ">": "f"}
    )
DoubleArray = FieldType(
    base=UInt64Array, name="DoubleArray",
    default=array("d", []), enc={"<": "d", ">": "d"}
    )

BytesRaw = FieldType(
    base=UInt8Array, name="BytesRaw", is_raw=True,
    node_cls=BytesBuffer, default=BytesBuffer(),
    parser=parsers.bytes_parser,
    serializer=serializers.bytes_serializer,
    sizecalc=sizecalcs.len_sizecalc
    )
BytearrayRaw = FieldType(
    base=BytesRaw, name="BytearrayRaw",
    node_cls=BytearrayBuffer, default=BytearrayBuffer()
    )

BytesRawEnum = FieldType(
    base=BytesRaw, name="BytesRawEnum", is_block=True, is_data=True,
    data_cls=BytesBuffer, node_cls=blocks.EnumBlock,
    sanitizer=sanitizers.enum_sanitizer,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.len_sizecalc),
    parser=parsers.data_parser,
    serializer=serializers.data_serializer,
    encoder=encoders.encoder_wrapper(encoders.no_encode),
    decoder=decoders.decoder_wrapper(decoders.no_decode),
    )

BUInt16Array, LUInt16Array = UInt16Array.big, UInt16Array.little
BUInt32Array, LUInt32Array = UInt32Array.big, UInt32Array.little
BUInt64Array, LUInt64Array = UInt64Array.big, UInt64Array.little
BSInt16Array, LSInt16Array = SInt16Array.big, SInt16Array.little
BSInt32Array, LSInt32Array = SInt32Array.big, SInt32Array.little
BSInt64Array, LSInt64Array = SInt64Array.big, SInt64Array.little

BFloatArray,  LFloatArray = FloatArray.big, FloatArray.little
BDoubleArray, LDoubleArray = DoubleArray.big, DoubleArray.little


# Strings
other_enc = [
    "big5", "hkscs", "cp037", "cp424", "cp437", "cp500", "cp720",
    "cp737", "cp775", "cp850", "cp852", "cp855", "cp856", "cp857",
    "cp858", "cp860", "cp861", "cp862", "cp863", "cp864", "cp865",
    "cp866", "cp869", "cp874", "cp875", "cp932", "cp949", "cp950",
    "cp1006", "cp1026", "cp1140", "cp1250", "cp1251", "cp1252",
    "cp1253", "cp1254", "cp1255", "cp1256", "cp1257", "cp1258",
    "euc_jp", "euc_jis_2004", "euc_jisx0213", "euc_kr", "gb2312",
    "gbk", "gb18030", "hz", "iso2022_jp", "iso2022_jp_1",
    "iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_3",
    "iso2022_jp_ext", "iso2022_kr", "iso8859_2", "iso8859_3",
    "iso8859_4", "iso8859_5", "iso8859_6", "iso8859_7", "iso8859_8",
    "iso8859_9", "iso8859_10", "iso8859_11", "iso8859_13",
    "iso8859_14", "iso8859_15", "iso8859_16", "johab",
    "koi8_r", "koi8_u", "mac_cyrillic", "mac_greek", "mac_iceland",
    "mac_latin2", "mac_roman", "mac_turkish", "ptcp154",
    "shift_jis",  "shift_jis_2004", "shift_jisx0213",
    "idna", "mbcs", "palmos", "utf_7", "utf_8_sig"
    ]

# standard strings
StrAscii = FieldType(
    name="StrAscii", enc='ascii', is_str=True, is_delimited=True,
    default='', sizecalc=sizecalcs.delim_str_sizecalc, size=1,
    parser=parsers.data_parser,
    serializer=serializers.data_serializer,
    decoder=decoders.decode_string,
    encoder=encoders.encode_string
    )
StrLatin1 = FieldType(base=StrAscii, name="StrLatin1", enc='latin1')
StrUtf8 = FieldType(
    base=StrAscii, name="StrUtf8", enc='utf8',
    sizecalc=sizecalcs.delim_utf_sizecalc
    )
StrUtf16 = FieldType(
    base=StrUtf8, name="StrUtf16", size=2, enc={"<": "utf_16_le", ">": "utf_16_be"}
    )
StrUtf32 = FieldType(
    base=StrUtf8, name="StrUtf32", size=4, enc={"<": "utf_32_le", ">": "utf_32_be"}
    )

BStrUtf16, LStrUtf16 = StrUtf16.big, StrUtf16.little
BStrUtf32, LStrUtf32 = StrUtf32.big, StrUtf32.little

# non-null-terminated strings
StrNntAscii = FieldType(
    name="StrNntAscii", enc='ascii', is_str=True, size=1, default='',
    sizecalc=sizecalcs.str_sizecalc,
    parser=parsers.data_parser,
    serializer=serializers.data_serializer,
    decoder=decoders.decode_string,
    encoder=encoders.encode_raw_string
    )
StrNntLatin1 = FieldType(
    base=StrNntAscii, name="StrNntLatin1", enc='latin1'
    )
StrNntUtf8 = FieldType(
    base=StrNntAscii, name="StrNntUtf8", enc='utf8',
    sizecalc=sizecalcs.utf_sizecalc
    )
StrNntUtf16 = FieldType(
    base=StrNntUtf8, name="StrNntUtf16", size=2, enc={"<": "utf_16_le", ">": "utf_16_be"}
    )
StrNntUtf32 = FieldType(
    base=StrNntUtf8, name="StrNntUtf32", size=4, enc={"<": "utf_32_le", ">": "utf_32_be"}
    )

BStrNntUtf16, LStrNntUtf16 = StrNntUtf16.big, StrNntUtf16.little
BStrNntUtf32, LStrNntUtf32 = StrNntUtf32.big, StrNntUtf32.little

# null terminated strings
'''While regular strings also have a delimiter character on the end
of the string, c strings are expected to entirely rely on the delimiter.
Regular strings store their size as an attribute in some parent node, but
c strings dont, and rawdata must be parsed until a delimiter is reached.'''
CStrAscii = FieldType(
    name="CStrAscii", enc='ascii', is_str=True, is_delimited=True, is_oe_size=True,
    default='', size=1,
    sizecalc=sizecalcs.delim_str_sizecalc,
    parser=parsers.cstring_parser,
    serializer=serializers.cstring_serializer,
    decoder=decoders.decode_string,
    encoder=encoders.encode_string
    )
CStrLatin1 = FieldType(
    base=CStrAscii, name="CStrLatin1", enc='latin1'
    )
CStrUtf8 = FieldType(
    base=CStrAscii, name="CStrUtf8", enc='utf8',
    sizecalc=sizecalcs.delim_utf_sizecalc
    )
CStrUtf16 = FieldType(
    base=CStrUtf8, name="CStrUtf16", size=2, enc={"<": "utf_16_le", ">": "utf_16_be"}
    )
CStrUtf32 = FieldType(
    base=CStrUtf8, name="CStrUtf32", size=4, enc={"<": "utf_32_le", ">": "utf_32_be"}
    )

BCStrUtf16, LCStrUtf16 = CStrUtf16.big, CStrUtf16.little
BCStrUtf32, LCStrUtf32 = CStrUtf32.big, CStrUtf32.little

# raw strings
'''Raw strings are special in that they are not expected to have
a delimiter. A fixed length raw string can have all character values
utilized and not require a delimiter character to be on the end.'''
StrRawAscii = FieldType(
    name="StrRawAscii", enc='ascii', is_str=True, is_delimited=False,
    default='', size=1,
    sizecalc=sizecalcs.str_sizecalc,
    parser=parsers.data_parser,
    serializer=serializers.data_serializer,
    decoder=decoders.decode_raw_string,
    encoder=encoders.encode_raw_string
    )
StrRawLatin1 = FieldType(
    base=StrRawAscii, name="StrRawLatin1", enc='latin1'
    )
StrRawUtf8 = FieldType(
    base=StrRawAscii, name="StrRawUtf8", enc='utf8',
    sizecalc=sizecalcs.utf_sizecalc
    )
StrRawUtf16 = FieldType(
    base=StrRawUtf8, name="StrRawUtf16", size=2, enc={"<": "utf_16_le", ">": "utf_16_be"}
    )
StrRawUtf32 = FieldType(
    base=StrRawUtf8, name="StrRawUtf32", size=4, enc={"<": "utf_32_le", ">": "utf_32_be"}
    )

BStrRawUtf16, LStrRawUtf16 = StrRawUtf16.big, StrRawUtf16.little
BStrRawUtf32, LStrRawUtf32 = StrRawUtf32.big, StrRawUtf32.little


StrHex = FieldType(
    base=StrAscii, name="StrHex",
    sizecalc=sizecalcs.str_hex_sizecalc,
    decoder=decoders.decode_string_hex,
    encoder=encoders.encode_string_hex
    )

StrAsciiEnum = FieldType(
    name='StrAsciiEnum', base=StrRawAscii, is_block=True, is_data=True,
    data_cls=str, node_cls=blocks.EnumBlock,
    sanitizer=sanitizers.enum_sanitizer,
    sizecalc=sizecalcs.sizecalc_wrapper(sizecalcs.len_sizecalc),
    decoder=decoders.decoder_wrapper(decoders.decode_string),
    encoder=encoders.encoder_wrapper(encoders.encode_string),
    )
StrUtf8Enum = FieldType(
    name='StrUtf8Enum', base=StrAsciiEnum, enc='utf8',
    sizecalc=sizecalcs.utf_sizecalc
    )

for enc in other_enc:
    str_field_types[enc] = FieldType(
        base=StrAscii, enc=enc, name="Str" + enc[0].upper() + enc[1:]
        )
    str_nnt_field_types[enc] = FieldType(
        base=StrNntAscii, enc=enc, name="StrNnt" + enc[0].upper() + enc[1:]
        )
    cstr_field_types[enc] = FieldType(
        base=CStrAscii, enc=enc, name="CStr" + enc[0].upper() + enc[1:]
        )
    str_raw_field_types[enc] = FieldType(
        base=StrRawAscii, enc=enc, name="StrRaw" + enc[0].upper() + enc[1:]
        )
