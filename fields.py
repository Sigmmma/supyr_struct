'''
A collection of common and flexible Field instances and their base class.

Fields are a read-only description of how this library needs
to treat a certain type of binary data or structure.

Fields define functions for reading/writing the data to/from a
buffer, decoding/encoding the data(if applicable), a function
to calculate the byte size of the data, and several properties
which determine how the data should be treated.

One way to view a Field is as the generalized, static properties
one would need to define in order to describe a type of data.
A descriptor holds a Field to describe most of the properties of the
binary data, while the descriptor stores the more specific details,
such as the number of elements in an array, length of a string, etc.

If certain data needs to be handeled in a way currently not supported, then
custom fields can be created with customized properties and functions.
'''

from array import array
from copy import deepcopy
from struct import unpack
from time import time, ctime
from types import FunctionType

from supyr_struct.field_methods import *
from supyr_struct.buffer import BytesBuffer, BytearrayBuffer
from supyr_struct import blocks
from supyr_struct.defs.constants import *
from supyr_struct.defs.frozen_dict import FrozenDict

# ##################################
#  collections of specific fields  #
# ##################################
__all__ = [
    'Field', 'all_fields',
    'str_fields', 'cstr_fields', 'str_raw_fields',

    # hierarchy and structure
    'Container', 'Array', 'WhileArray',
    'Struct', 'QStruct', 'QuickStruct', 'BBitStruct', 'LBitStruct',
    'Union', 'Switch', 'StreamAdapter',

    # special Fields
    'BPointer32', 'LPointer32',
    'BPointer64', 'LPointer64',
    'Void', 'Pad',

    # integers and floats
    'BBigUInt', 'BBigSInt', 'BBig1SInt',
    'LBigUInt', 'LBigSInt', 'LBig1SInt',
    'BitUInt', 'BitSInt', 'Bit1SInt',
    'Bit', 'UInt8', 'SInt8',
    'BUInt16', 'BSInt16', 'LUInt16', 'LSInt16',
    'BUInt24', 'BSInt24', 'LUInt24', 'LSInt24',
    'BUInt32', 'BSInt32', 'LUInt32', 'LSInt32',
    'BUInt64', 'BSInt64', 'LUInt64', 'LSInt64',
    'BFloat',  'BDouble', 'LFloat',  'LDouble',

    # float and long int timestamps
    'BTimestampFloat', 'LTimestampFloat',
    'BTimestamp',      'LTimestamp',

    # enumerators and booleans
    'BitUEnum', 'BitSEnum', 'BitBool',
    'LBigUEnum', 'LBigSEnum', 'LBigBool',
    'BBigUEnum', 'BBigSEnum', 'BBigBool',
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
    'StrLatin1',  'CStrLatin1',  'StrRawLatin1',
    'StrAscii',   'CStrAscii',   'StrRawAscii',
    'StrUtf8',    'CStrUtf8',    'StrRawUtf8',
    'BStrUtf16',  'BCStrUtf16',  'BStrRawUtf16',
    'BStrUtf32',  'BCStrUtf32',  'BStrRawUtf32',
    'LStrUtf16',  'LCStrUtf16',  'LStrRawUtf16',
    'LStrUtf32',  'LCStrUtf32',  'LStrRawUtf32',
    'StrHex',

    # #########################################################
    # short hand names that use the endianness of the system  #
    # #########################################################
    'BitStruct', 'Pointer32', 'Pointer64',

    # integers and floats
    'BigUInt', 'BigSInt', 'Big1SInt',
    'UInt16', 'UInt24', 'UInt32', 'UInt64', 'Float',
    'SInt16', 'SInt24', 'SInt32', 'SInt64', 'Double',

    # float and long int timestamps
    'TimestampFloat', 'Timestamp',

    # enumerators and booleans
    'BigUEnum', 'BigSEnum', 'BigBool',
    'UEnum16', 'UEnum24', 'UEnum32', 'UEnum64',
    'SEnum16', 'SEnum24', 'SEnum32', 'SEnum64',
    'Bool16',   'Bool24',  'Bool32',  'Bool64',

    # integers and float arrays
    'UInt16Array', 'SInt16Array', 'UInt32Array', 'SInt32Array',
    'UInt64Array', 'SInt64Array', 'FloatArray',  'DoubleArray',

    # strings
    'StrUtf16', 'CStrUtf16', 'StrRawUtf16',
    'StrUtf32', 'CStrUtf32', 'StrRawUtf32'
    ]

# a list containing all valid created fields
all_fields = []

# these are where all the single byte, less common encodings
# are located for Strings, CStrings, and raw Strings
str_fields = {}
cstr_fields = {}
str_raw_fields = {}

# used for mapping the keyword arguments to
# the attribute name of Field instances
field_base_name_map = {'default': '_default'}
for string in ('reader', 'writer', 'decoder', 'encoder', 'sizecalc'):
    field_base_name_map[string] = string + '_func'
for string in ('is_data', 'is_str', 'is_raw', 'is_enum', 'is_bool',
               'is_array', 'is_container', 'is_struct', 'is_delimited',
               'is_var_size', 'is_bit_based', 'is_oe_size',
               'size', 'enc', 'max', 'min', 'data_type', 'py_type',
               'str_delimiter', 'delimiter', 'sanitizer'):
    field_base_name_map[string] = string

# Names of all the keyword argument allowed to be given to a Field.
valid_field_kwargs = set(field_base_name_map.keys())
valid_field_kwargs.update(('reader', 'writer', 'decoder', 'encoder',
                           'sizecalc', 'default', 'is_block', 'name', 'base'))
# These are keyword arguments specifically used to communicate
# between Fields, and are not intended for use by developers.
valid_field_kwargs.update(('endian', 'other_endian', 'sizecalc_wrapper',
                           'decoder_wrapper', 'encoder_wrapper'))


class Field():
    '''
    Fields are a read-only description of a certain kind of binary
    data, structure, or flow control system(like a switch).

    Fields define functions for reading/writing the data to/from
    a buffer, encoding/decoding the data(if applicable), a function
    to calculate the byte size of the data, and numerous other
    properties which determine how the data should be treated.

    Each Field which is endianness dependent has a reference to the Field
    with the other endianness. Fields should never be copied(only referenced)
    as they are read-only descriptions of how to handle data.

    Calling a Field will return an incomplete descriptor made from the
    given positional and keyword arguments. The called Field will be
    added to the dictionary under TYPE and the first argument will be
    added under NAME. The only exception to this is Pad. Pad takes the
    first argument to mean the size of the padding(since naming padding
    is meaningless), and adds it to the descriptor under SIZE.
    This descriptor can then be used in a BlockDef.

    Calling __copy__ or __deepcopy__ will instead return the called Field.

    Instance properties:
        bool:
            is_data
            is_block
            is_str
            is_raw
            is_enum
            is_bool
            is_struct
            is_array
            is_container
            is_var_size
            is_oe_size
            is_bit_based
            is_delimited
        function:
            sanitizer
        int:
            size
            min
            max
        method:
            reader
            writer
            decoder
            encoder
            sizecalc
        str:
            name
            enc
            endian
            f_endian ----- endian char the Field is forced to encode/decode in
            delimiter
            str_delimiter
        type:
            py_type
            data_type

    Read this classes __init__.__doc__ for descriptions of these properties.
    '''

    # The initial forced endianness 'do not force'
    # This is the ONLY variable thing in a Field.
    f_endian = '='

    def __init__(self, **kwargs):
        '''
        Initializes a Field with the supplied keyword arguments.

        Raises TypeError if invalid keyword combinations are provided.
        Raises KeyError if unknown arguments are provided.

        All Fields must be either Block or data, and will start with
        is_data set to True and all other flags set to False.
        Certain flags being set implies that others are set, and if the
        implied flag is not provided, it will be automatically set.
        
        size not being provided implies that is_var_size is True.
        is_array being True implies that is_container is True.
        is_str being True implies that is_var_size is True.
        is_struct, or is_container being True implies that is_block is True
        is_block is implemented as literally "not self.is_data"

        is_enum and is_bool cannot be both set.
        is_struct and is_container cannot be both set.

        if endian is not supplied, it defaults to '=', which says that
        endianness has no meaning for the Field(BytesRaw for example)
        and that self.little and self.big reference the same instance.

        Keyword arguments:

        # bool:
        is_block ----- Is a form of hierarchy(struct, array, container, etc).
                       If something is a block, it is expected to have a desc
                       attribute, meaning it holds its own descriptor rather
                       than having its parent hold its descriptor for it.
        is_data ------ Is a form of data(opposite of being a block).
                       If something is data, it is expected to not have a desc
                       attribute, and its parent holds its descriptor for it.
                       This was done as it would otherwise require a wrapper
                       around each attribute in a Block so they can hold DESCs.
        is_str ------- Is a string.
        is_raw ------- Is unencoded raw data(example: bitmap pixel bytes).
        is_array ----- Is an array of instanced elements.
        is_enum ------ Has a collection of enumerations it may be set to.
        is_bool ------ Has a collection of T/F flags that can be set.
        is_struct ---- Has a fixed size and its indexed attributes have offsets
        is_container - Has no fixed size and no attributes have no offsets.
                       The other important detail about a Field being a
                       container is that its size is measured in entry counts
                       rather than serialized byte size. This also means that
                       its Blocks get_size and set_size set the number of
                       entries in the Block rather than its byte size.
        is_var_size -- Byte size of object can vary(descriptor defined size).
        is_oe_size --- The objects size can only be determined after the
                       rawdata has been parsed as it relies on a sort of
                       delimiter, or it is a stream of data that must be
                       parsed to find the end(the stream is open ended).
        is_bit_based - Whether or not the data is described as bits(not bytes).
                       Within a BitStruct, offsets, sizes, etc, are in bits.
                       However, BitStruct offsets, sizes, etc, are in bytes.
        is_delimited - Whether or not the string is terminated with
                       a delimiter character.

        # Field:
        base ----------- Used as an initializer for a new Field instance.
                         When supplied, most of the bases attributes are
                         copied into kwargs using kwargs.setdefault().
                         The attributes that are copied are as follows:
                             is_data, is_block, is_str, is_raw, is_enum,
                             is_bool, is_struct, is_array, is_container,
                             is_var_size, is_bit_based, is_delimited,
                             py_type, data_type, default, delimiter,
                             enc, max, min, size, str_delimiter
                             reader_func, writer_func, sizecalc_func,
                             decoder_func, encoder_func, sanitizer

        # function:
        reader ------ A function for reading bytes from a buffer and calling
                      its decoder on them. For a Block, this instead calls
                      the readers of each of the Blocks attributes.
        writer ------ A function for calling its encoder on an object and
                      writing the bytes to a buffer. For a Block, this instead
                      calls the writers of each of the Blocks attributes.
        decoder ----- A function for decoding bytes from a buffer into an
                      object(ex: convert b'\xD1\x22\xAB\x3F' to a float).
        encoder ----- A function for encoding an object into a writable
                      bytes form(ex: convert "test" into b'\x74\x65\x73\x74').
        sizecalc ---- An optional function for calculating how large the object
                      would be if written to a buffer. Most of the time this
                      isn't needed, but for variable length data(data whose
                      size is determined by some previously parsed field)
                      the size will need to properly calculated after an edit.
        sanitizer --- A function which checks and properly sanitizes
                      descriptors that have this field as their type.

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
                         A good example is the Timestamp Field which calls
                         ctime(time()) and returns a current timestamp string.
        # type:
        py_type -------- The python type associated with this Field.
                         For example, this set to the int type for all of the
                         integer Fields(UInt8, Bit, BSInt64, Pointer32, etc)
                         and to ListBlock for Container, Struct, Array, etc.
                         If py_type isnt provided on instantiation(or a base
                         isnt) type(self._default) will be used instead.
                         Used mainly for type checking and creating new
                         instances of the object associated with this Field.
        data_type ------ The python type that the 'data' attribute in
                         a DataBlock is supposed to be an instance of.
                         If this is anything other than type(None), the
                         block must be a DataBlock with a 'data' attribute
                         which should be an instance of 'data_type'.
                         For example, all the bools and integer enum
                         Fields have their py_type as EnumBlock or
                         BoolBlock and their data_type is int.

        # str:
        name ----------- The name of this Field.
        enc ------------ A string used to specify the format for encoding
                         and decoding the data. This is expected to exist for
                         non-raw "data" fields, but there is no set convention
                         as it depends on what the de/encode function needs.

                         For example, enc for numbers de/encoded by pythons
                         struct module would be any one character in '<>'
                         for the endianness followed by any one character in
                         'bhiqfBHIQD'. Str_UTF_16_LE and Str_Latin_1 on the
                         other hand use "UTF_16_LE" and "latin-1" respectively.
        endian --------- The endianness of this Field. Must be one of '<>='.
        f_endian ------- The endianness that this Field is being forced into.
        delimiter ------ The string delimiter in its encoded, bytes form.
        str_delimiter -- The string delimiter in its decoded, python form.
        '''

        # check for unknown keyword arguments
        given_kwargs, kwargs = kwargs, {}
        for kwarg in valid_field_kwargs:
            if kwarg in given_kwargs:
                kwargs[kwarg] = given_kwargs.pop(kwarg)
        # if there are any remaining keyword arguments, raise an error
        if given_kwargs:
            raise KeyError('Unknown supplied keyword arguments:\n    %s' %
                           given_kwargs.keys())

        # set the Field as editable
        self._instantiated = False

        # set up the default values for each attribute.
        # default endianness of the initial Field is No Endianness
        self.endian = '='
        self.little = self.big = self
        self.min = self.max = self._default = self.enc = None
        self.delimiter = self.str_delimiter = None
        self.size = None

        # set the Field's flags
        self.is_data = True
        self.is_str = self.is_delimited = self.is_raw = \
            self.is_enum = self.is_bool = self.is_struct = \
            self.is_array = self.is_container = self.is_var_size = \
            self.is_oe_size = self.is_bit_based = False

        # if a base was provided, use it to update kwargs with its settings
        base = kwargs.get('base')
        if isinstance(base, Field):
            # if the base has separate encodings for the
            # different endiannesses, make sure to set
            # the default encoding of this Field as theirs
            if base.little.enc != base.big.enc:
                kwargs.setdefault('enc', {'<': base.little.enc,
                                          '>': base.big.enc})

            # whether or not the decoder, encoder, and sizecalc will
            # need to be wrapped in a function to redirect to 'data'
            base_is_wrapped = not isinstance(None, base.data_type)
            # whether or not the base's decoder, encoder, and sizecalc
            # function are already wrapped(DO NOT want to wrap them again)
            must_be_wrapped = not isinstance(None, kwargs.get('data_type',
                                                              type(None)))

            # loop over each attribute in the base that can be copied
            for attr in field_base_name_map:
                if attr in kwargs:
                    continue

                if must_be_wrapped and not base_is_wrapped:
                    pass
                elif attr == 'encoder':
                    kwargs['encoder_wrapper'] = base.encoder_func
                elif attr == 'decoder':
                    kwargs['decoder_wrapper'] = base.decoder_func
                elif attr == 'sizecalc':
                    kwargs['sizecalc_wrapper'] = base.sizecalc_func
                kwargs[attr] = base.__getattribute__(field_base_name_map[attr])

        # setup the Field's main properties
        self.name = kwargs.get("name")
        self.reader_func = kwargs.get("reader", self.not_imp)
        self.writer_func = kwargs.get("writer", self.not_imp)
        self.decoder_func = kwargs.get("decoder", no_decode)
        self.encoder_func = kwargs.get("encoder", no_encode)
        self.sizecalc_func = def_sizecalc
        self.sanitizer = kwargs.get("sanitizer", standard_sanitizer)
        self.data_type = kwargs.get("data_type", type(None))
        self._default = kwargs.get("default", None)
        self.py_type = kwargs.get("py_type", type(self._default))
        self.size = kwargs.get("size", self.size)

        # set the Field's flags
        self.is_data = not bool(kwargs.get("is_block",
                                           not kwargs.get("is_data",
                                                          self.is_data)))
        self.is_str = bool(kwargs.get("is_str", self.is_str))
        self.is_raw = bool(kwargs.get("is_raw", self.is_raw))
        self.is_enum = bool(kwargs.get("is_enum", self.is_enum))
        self.is_bool = bool(kwargs.get("is_bool", self.is_bool))
        self.is_array = bool(kwargs.get("is_array", self.is_array))
        self.is_struct = bool(kwargs.get("is_struct", self.is_struct))
        self.is_oe_size = bool(kwargs.get("is_oe_size", self.is_oe_size))
        self.is_var_size = bool(kwargs.get("is_var_size", self.is_var_size))
        self.is_container = bool(kwargs.get("is_container", self.is_container))
        self.is_bit_based = bool(kwargs.get("is_bit_based", self.is_bit_based))
        self.is_delimited = bool(kwargs.get("is_delimited", self.is_delimited))

        # arrays are also a container
        self.is_container |= self.is_array
        # All strings are variable size since the 'size' property
        # refers to the size of each character in the string.
        self.is_var_size |= self.is_str

        # certain bool properties are only True when is_block is True
        self.is_data = not(self.is_block or self.is_struct or
                           self.is_container)

        if self.name is None:
            raise TypeError("'name' is a required identifier for data types.")

        if self.size is None:
            # if size isnt specified then the Field is of variable size.
            self.is_var_size = True
        else:
            # if the delimiter isnt specified, set it to 0x00*size
            kwargs.setdefault("delimiter", b'\x00' * int(self.size))

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
                raise TypeError("When providing endianness reliant " +
                                "encodings, big and little endian\n" +
                                "must both be provided under the " +
                                "keys '>' and '<' respectively.")
            # make the first encoding the endianness of the system
            self.enc = enc[byteorder_char]
            self.endian = byteorder_char

        if self.is_bool and self.is_enum:
            raise TypeError('A Field can not be both an enumerator and ' +
                            'a collection of booleans at the same time.')

        if self.is_container and self.is_struct:
            raise TypeError('A Field can not be both a struct ' +
                            'and a container at the same time.')

        other_endian = kwargs.get('other_endian')

        # if the endianness is specified as '=' it means that
        # endianness has no meaning for this Field and that
        # big and little should be the same. Otherwise, create
        # a similar Field, but with an opposite endianness
        if self.endian != "=" and other_endian is None:
            # set the endianness kwarg to the opposite of this one
            kwargs["endian"] = {'<': '>', '>': '<'}[self.endian]
            kwargs["other_endian"] = self

            # if the provided enc kwarg is a dict, get the encoding
            # of the endianness opposite the current Field.
            if 'enc' in kwargs and isinstance(kwargs["enc"], dict):
                kwargs["enc"] = kwargs["enc"][kwargs["endian"]]
            else:
                kwargs["enc"] = self.enc

            # create the other endian Field
            other_endian = Field(**kwargs)

        # set the other endianness Field
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
            self.sizecalc_func = kwargs['sizecalc']
        elif issubclass(self.py_type, str):
            self.sizecalc_func = str_sizecalc
        elif issubclass(self.py_type, array):
            self.sizecalc_func = array_sizecalc
        elif issubclass(self.py_type, (bytearray, bytes)) or self.is_array:
            self.sizecalc_func = len_sizecalc
        elif self.is_var_size:
            self.sizecalc_func = no_sizecalc

        # if self.data_type is not type(None), then it means
        # that self.sizecalc_func, self._encode, and self._decode
        # might need to be wrapped functions to redirect to block.data
        if not isinstance(None, self.data_type):
            _sc = self.sizecalc_func
            _de = self.decoder_func
            _en = self.encoder_func

            sizecalc_wrapper = kwargs.get('sizecalc_wrapper')
            decoder_wrapper = kwargs.get('decoder_wrapper')
            encoder_wrapper = kwargs.get('encoder_wrapper')

            if sizecalc_wrapper is None:
                def sizecalc_wrapper(self, block, _sizecalc=_sc, *a, **kw):
                    try:
                        return _sizecalc(self, block.data, *a, **kw)
                    except AttributeError:
                        return _sizecalc(self, block, *a, **kw)
            if decoder_wrapper is None:
                # this function expects to return a constructed Block, so it
                # provides the appropriate args and kwargs to the constructor
                def decoder_wrapper(self, rawdata, desc=None, parent=None,
                                    attr_index=None, _decode=_de):
                    try:
                        return self.py_type(desc, parent,
                                            initdata=_decode(self, rawdata,
                                                             desc, parent,
                                                             attr_index))
                    except AttributeError:
                        return _decode(self, rawdata, desc, parent, attr_index)
            if encoder_wrapper is None:
                # this function expects the actual value being
                # encoded to be in 'block' under the name 'data',
                # so it passes the args over to the actual encoder
                # function, but replaces 'block' with 'block.data'
                def encoder_wrapper(self, block, parent=None,
                                    attr_index=None, _encode=_en):
                    try:
                        return _encode(self, block.data, parent, attr_index)
                    except AttributeError:
                        return _encode(self, block, parent, attr_index)

            # now that the functions have either been wrapped or are
            # confirmed to already be wrapped, add them to the Field
            self.sizecalc_func = sizecalc_wrapper
            self.decoder_func = decoder_wrapper
            self.encoder_func = encoder_wrapper

        # if a default wasn't provided, try to create one from self.py_type
        if self._default is None:
            if self.is_block:
                # Create a default descriptor to give to the default Block
                # This descriptor isnt meant to actually be used, its just
                # meant to exist so the Block instance doesnt raise errors
                desc = {TYPE: self, NAME: UNNAMED,
                        SIZE: 0, ENTRIES: 0, ATTR_OFFS: [],
                        NAME_MAP: {}, VALUE_MAP: {}, CASE_MAP: {}}
                try:
                    desc[SUB_STRUCT] = desc[CHILD] = {TYPE: Void,
                                                      NAME: UNNAMED}
                except NameError:
                    pass
                self._default = self.py_type(FrozenDict(desc))
            else:
                try:
                    self._default = self.py_type()
                except Exception:
                    raise TypeError(
                        "Could not create Field 'default' instance. " +
                        "You must manually supply a default value.")

        # now that setup is concluded, set the object as read-only
        self._instantiated = True

        # add this to the collection of all field types
        all_fields.append(self)

    # these functions are just alias's and are done this way so
    # that this class can pass itself as a reference manually
    # and enabling the endianness to be forced to big or little.
    def reader(self, *args, **kwargs):
        '''
        Calls this fields reader function, passing on all args and kwargs.
        Returns the return value of this fields reader, which
        should be the offset the reader function left off at.

        Optional kwargs:
            parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested readers unless a reader removes or changes them.
        '''
        return self.reader_func(self, *args, **kwargs)

    def writer(self, *args, **kwargs):
        '''
        Calls this fields writer function, passing on all args and kwargs.
        Returns the return value of this fields writer, which
        should be the offset the writer function left off at.

        Optional kwargs:
            parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested writers unless a writer removes or changes them.
        '''
        return self.writer_func(self, *args, **kwargs)

    def decoder(self, *args, **kwargs):
        '''
        Calls this fields decoder function, passing on all args and kwargs.
        Returns the return value of this fields decoder, which should
        be a python object decoded represention of the "Bytes" argument.
        '''
        return self.decoder_func(self, *args, **kwargs)

    def encoder(self, *args, **kwargs):
        '''
        Calls this fields encoder function, passing on all args and kwargs.
        Returns the return value of this fields encoder, which should
        be a bytes object encoded represention of the "block" argument.
        '''
        return self.encoder_func(self, *args, **kwargs)

    # these next functions are used to force the reading
    # and writing to conform to one endianness or the other
    def _little_reader(self, *args, **kwargs):
        return self.reader_func(self.little, *args, **kwargs)

    def _little_writer(self, *args, **kwargs):
        return self.writer_func(self.little, *args, **kwargs)

    def _little_encoder(self, *args, **kwargs):
        return self.encoder_func(self.little, *args, **kwargs)

    def _little_decoder(self, *args, **kwargs):
        return self.decoder_func(self.little, *args, **kwargs)

    def _big_reader(self, *args, **kwargs):
        return self.reader_func(self.big, *args, **kwargs)

    def _big_writer(self, *args, **kwargs):
        return self.writer_func(self.big, *args, **kwargs)

    def _big_encoder(self, *args, **kwargs):
        return self.encoder_func(self.big, *args, **kwargs)

    def _big_decoder(self, *args, **kwargs):
        return self.decoder_func(self.big, *args, **kwargs)

    _normal_reader = reader
    _normal_writer = writer
    _normal_encoder = encoder
    _normal_decoder = decoder

    def __call__(self, name, *desc_entries, **desc):
        '''
        Creates a dict formatted properly to be used as a descriptor.
        The first argument must be blocks name.
        If the field is Pad, the first argument is the padding size.
        The remaining positional args are the numbered entries in the
        descriptor, and the keyword arguments are the non-numbered entries
        in the descriptor. This is only a macro though, meaning descriptors
        created by it must still be run through a sanitization routine.

        Returns the created descriptor dict.
        '''
        if self is Pad:
            desc.setdefault(NAME, 'pad_entry')
            desc.setdefault(SIZE, name)
        else:
            if not isinstance(name, str):
                raise TypeError("'name' must be of type '%s', not '%s'" %
                                (type(str), type(name)))
            desc.setdefault(NAME, name)

        desc[TYPE] = self

        # add all the positional arguments to the descriptor
        for i in range(len(desc_entries)):
            desc[i] = desc_entries[i]

        return desc

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        '''
        Returns this object.
        You should never need to make a deep copy of ANY Field.
        '''
        return self

    def __str__(self):
        return("<Field:'%s', endian:'%s', enc:'%s'>" %
               (self.name, self.endian, self.enc))

    def __repr__(self): pass
    __repr__ = __str__

    # To prevent editing of Fields once they are instintiated, the
    # default __setattr__ and __delattr__ methods are overloaded
    def __setattr__(self, attr, value):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError(
                "Fields are read-only and may not be changed once created.")
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr, value):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError(
                "Fields are read-only and may not be changed once created.")
        object.__delattr__(self, attr)

    @property
    def is_block(self):
        return not self.is_data

    def default(self, *args, **kwargs):
        '''
        Returns a deepcopy of the python object associated with this
        Field. If self._default is a function it instead passes
        args and kwargs over and returns what is returned to it.
        '''
        if isinstance(self._default, FunctionType):
            return self._default(*args, **kwargs)
        return deepcopy(self._default)

    def force_little(self=None):
        '''
        Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the little
        endian version of the Field(if it exists).
        '''
        if self is None:
            Field.reader = Field._little_reader
            Field.writer = Field._little_writer
            Field.encoder = Field._little_encoder
            Field.decoder = Field._little_decoder
            Field.f_endian = '<'
            return
        self.__dict__['reader'] = Field._little_reader
        self.__dict__['writer'] = Field._little_writer
        self.__dict__['encoder'] = Field._little_encoder
        self.__dict__['decoder'] = Field._little_decoder
        self.__dict__['f_endian'] = '<'

    def force_big(self=None):
        '''
        Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the big
        endian version of the Field(if it exists).
        '''
        if self is None:
            Field.reader = Field._big_reader
            Field.writer = Field._big_writer
            Field.encoder = Field._big_encoder
            Field.decoder = Field._big_decoder
            Field.f_endian = '>'
            return
        self.__dict__['reader'] = Field._big_reader
        self.__dict__['writer'] = Field._big_writer
        self.__dict__['encoder'] = Field._big_encoder
        self.__dict__['decoder'] = Field._big_decoder
        self.__dict__['f_endian'] = '>'

    def force_normal(self=None):
        '''
        Replaces the Field class's reader, writer, encoder,
        and decoder with methods that do not force them to use an
        endianness other than the one they are currently set to.
        '''
        if self is None:
            Field.reader = Field._normal_reader
            Field.writer = Field._normal_writer
            Field.encoder = Field._normal_encoder
            Field.decoder = Field._normal_decoder
            Field.f_endian = '='
            return
        try:
            del self.__dict__['reader']
        except KeyError:
            pass
        try:
            del self.__dict__['writer']
        except KeyError:
            pass
        try:
            del self.__dict__['encoder']
        except KeyError:
            pass
        try:
            del self.__dict__['decoder']
        except KeyError:
            pass
        try:
            del self.__dict__['f_endian']
        except KeyError:
            pass

    def sizecalc(self, *args, **kwargs):
        '''
        A redirect that provides 'self' as
        an arg to the actual sizecalc function.
        '''
        return self.sizecalc_func(self, *args, **kwargs)

    def not_imp(self, *args, **kwargs):
        raise NotImplementedError(
            "This operation not implemented in %s Field." % self.name)


# The main hierarchial and special Fields
Void = Field(name="Void", is_block=True, size=0, py_type=blocks.VoidBlock,
             reader=void_reader, writer=void_writer)
Pad = Field(name="Pad", is_block=True, py_type=blocks.VoidBlock,
            reader=pad_reader, writer=pad_writer)
Container = Field(name="Container", is_container=True, is_block=True,
                  py_type=blocks.ListBlock, sanitizer=sequence_sanitizer,
                  reader=container_reader, writer=container_writer,
                  sizecalc=len_sizecalc)
Struct = Field(name="Struct", is_struct=True, is_block=True,
               py_type=blocks.ListBlock, sanitizer=struct_sanitizer,
               reader=struct_reader, writer=struct_writer)
QuickStruct = Field(name="QuickStruct", base=Struct,
                    sanitizer=quickstruct_sanitizer,
                    reader=quickstruct_reader, writer=quickstruct_writer)
Array = Field(name="Array", is_array=True, is_block=True,
              py_type=blocks.ArrayBlock, sanitizer=sequence_sanitizer,
              reader=array_reader, writer=array_writer)
WhileArray = Field(name="WhileArray",
                   is_array=True, is_block=True, is_oe_size=True,
                   py_type=blocks.WhileBlock, sanitizer=sequence_sanitizer,
                   reader=while_array_reader, writer=array_writer)
Switch = Field(name='Switch', is_block=True,
               sanitizer=switch_sanitizer, py_type=blocks.VoidBlock,
               reader=switch_reader, writer=void_writer)
StreamAdapter = Field(name="StreamAdapter", is_block=True, is_oe_size=True,
                      py_type=blocks.WrapperBlock,
                      sanitizer=stream_adapter_sanitizer,
                      reader=stream_adapter_reader,
                      writer=stream_adapter_writer)
Union = Field(base=Struct, name="Union", is_block=True,
              py_type=blocks.UnionBlock, sanitizer=union_sanitizer,
              reader=union_reader, writer=union_writer)
# shorthand alias
QStruct = QuickStruct

# bit_based data
'''When within a BitStruct, offsets and sizes are in bits instead of bytes.
BitStruct sizes, however, must be specified in bytes(1byte, 2bytes, etc)'''
BitStruct = Field(name="BitStruct",
                  is_struct=True, is_bit_based=True, enc={'<': '<', '>': '>'},
                  py_type=blocks.ListBlock, sanitizer=struct_sanitizer,
                  reader=bit_struct_reader, writer=bit_struct_writer)
BBitStruct, LBitStruct = BitStruct.big, BitStruct.little

'''For when you dont need multiple bits. It's faster and
easier to use this than a BitUInt with a size of 1.'''
Bit = Field(name="Bit", is_bit_based=True,
            size=1, enc='U', default=0, reader=default_reader,
            decoder=decode_bit, encoder=encode_bit)

'''UInt, 1SInt, and SInt must be in a BitStruct as the BitStruct
acts as a bridge between byte level and bit level objects.
Bit1SInt is signed in 1's compliment and BitSInt is in 2's compliment.'''
BitSInt = Field(name='BitSInt', is_bit_based=True, enc='S',
                sizecalc=bit_sint_sizecalc, default=0, reader=default_reader,
                decoder=decode_bit_int, encoder=encode_bit_int)
Bit1SInt = Field(base=BitSInt, name="Bit1SInt", enc="s")
BitUInt = Field(base=BitSInt,  name="BitUInt",  enc="U",
                sizecalc=bit_uint_sizecalc)
BitUEnum = Field(base=BitUInt, name="BitUEnum",
                 is_enum=True, is_block=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BitSEnum = Field(base=BitSInt, name="BitSEnum",
                 is_enum=True, is_block=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BitBool = Field(base=BitSInt, name="BitBool",
                is_bool=True, is_block=True, default=None, data_type=int,
                sanitizer=bool_enum_sanitizer, py_type=blocks.BoolBlock)

BigSInt = Field(base=BitUInt, name="BigSInt", is_bit_based=False,
                reader=data_reader,     writer=data_writer,
                decoder=decode_big_int, encoder=encode_big_int,
                sizecalc=big_sint_sizecalc, enc={'<': "<S", '>': ">S"})
Big1SInt = Field(base=BigSInt, name="Big1SInt", enc={'<': "<s", '>': ">s"})
BigUInt = Field(base=BigSInt,  name="BigUInt",  enc={'<': "<U", '>': ">U"},
                sizecalc=big_uint_sizecalc)
BigUEnum = Field(base=BigUInt, name="BigUEnum",
                 is_enum=True, is_block=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BigSEnum = Field(base=BigSInt, name="BigSEnum",
                 is_enum=True, is_block=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BigBool = Field(base=BigUInt, name="BigBool",
                is_bool=True, is_block=True, default=None, data_type=int,
                sanitizer=bool_enum_sanitizer, py_type=blocks.BoolBlock)

BBigSInt,  LBigSInt = BigSInt.big,  BigSInt.little
BBigUInt,  LBigUInt = BigUInt.big,  BigUInt.little
BBig1SInt, LBig1SInt = Big1SInt.big, Big1SInt.little
BBigUEnum, LBigUEnum = BigUEnum.big, BigUEnum.little
BBigSEnum, LBigSEnum = BigSEnum.big, BigSEnum.little
BBigBool,  LBigBool = BigBool.big,  BigBool.little

# 8/16/32/64-bit integers
UInt8 = Field(base=BigUInt, name="UInt8",
              size=1, min=0, max=255, enc='B', is_var_size=False,
              reader=f_s_data_reader, sizecalc=def_sizecalc,
              decoder=decode_numeric, encoder=encode_numeric)
UInt16 = Field(base=UInt8, name="UInt16", size=2,
               max=2**16-1, enc={'<': "<H", '>': ">H"})
UInt32 = Field(base=UInt8, name="UInt32", size=4,
               max=2**32-1, enc={'<': "<I", '>': ">I"})
UInt64 = Field(base=UInt8, name="UInt64", size=8,
               max=2**64-1, enc={'<': "<Q", '>': ">Q"})

SInt8 = Field(base=UInt8,  name="SInt8", min=-2**7, max=2**7-1, enc="b")
SInt16 = Field(base=UInt16, name="SInt16", min=-2**15,
               max=2**15-1, enc={'<': "<h", '>': ">h"})
SInt32 = Field(base=UInt32, name="SInt32", min=-2**31,
               max=2**31-1, enc={'<': "<i", '>': ">i"})
SInt64 = Field(base=UInt64, name="SInt64", min=-2**63,
               max=2**63-1, enc={'<': "<q", '>': ">q"})

BUInt16, LUInt16 = UInt16.big, UInt16.little
BUInt32, LUInt32 = UInt32.big, UInt32.little
BUInt64, LUInt64 = UInt64.big, UInt64.little

BSInt16, LSInt16 = SInt16.big, SInt16.little
BSInt32, LSInt32 = SInt32.big, SInt32.little
BSInt64, LSInt64 = SInt64.big, SInt64.little

# pointers
Pointer32 = Field(base=UInt32, name="Pointer32")
Pointer64 = Field(base=UInt64, name="Pointer64")

BPointer32, LPointer32 = Pointer32.big, Pointer32.little
BPointer64, LPointer64 = Pointer64.big, Pointer64.little

enum_kwargs = {'is_enum': True, 'is_block': True,
               'default': None, 'py_type': blocks.EnumBlock,
               'data_type': int, 'sanitizer': bool_enum_sanitizer}

bool_kwargs = {'is_bool': True, 'is_block': True,
               'default': None, 'py_type': blocks.BoolBlock,
               'data_type': int, 'sanitizer': bool_enum_sanitizer}
# enumerators
UEnum8 = Field(base=UInt8,   name="UEnum8",  **enum_kwargs)
UEnum16 = Field(base=UInt16, name="UEnum16", **enum_kwargs)
UEnum32 = Field(base=UInt32, name="UEnum32", **enum_kwargs)
UEnum64 = Field(base=UInt64, name="UEnum64", **enum_kwargs)

SEnum8 = Field(base=SInt8,   name="SEnum8",  **enum_kwargs)
SEnum16 = Field(base=SInt16, name="SEnum16", **enum_kwargs)
SEnum32 = Field(base=SInt32, name="SEnum32", **enum_kwargs)
SEnum64 = Field(base=SInt64, name="SEnum64", **enum_kwargs)

BUEnum16, LUEnum16 = UEnum16.big, UEnum16.little
BUEnum32, LUEnum32 = UEnum32.big, UEnum32.little
BUEnum64, LUEnum64 = UEnum64.big, UEnum64.little

BSEnum16, LSEnum16 = SEnum16.big, SEnum16.little
BSEnum32, LSEnum32 = SEnum32.big, SEnum32.little
BSEnum64, LSEnum64 = SEnum64.big, SEnum64.little

# booleans
Bool8 = Field(base=UInt8,   name="Bool8",  **bool_kwargs)
Bool16 = Field(base=UInt16, name="Bool16", **bool_kwargs)
Bool32 = Field(base=UInt32, name="Bool32", **bool_kwargs)
Bool64 = Field(base=UInt64, name="Bool64", **bool_kwargs)

BBool16, LBool16 = Bool16.big, Bool16.little
BBool32, LBool32 = Bool32.big, Bool32.little
BBool64, LBool64 = Bool64.big, Bool64.little

# 24-bit integers
UInt24 = Field(base=UInt8, name="UInt24", size=3, max=2**24-1,
               enc={'<': "<T", '>': ">T"},
               decoder=decode_24bit_numeric, encoder=encode_24bit_numeric)
SInt24 = Field(base=UInt24, name="SInt24", min=-2**23, max=2**23-1,
               enc={'<': "<t", '>': ">t"})
UEnum24 = Field(base=UInt24, name="UEnum24", **enum_kwargs)
SEnum24 = Field(base=SInt24, name="SEnum24", **enum_kwargs)
Bool24 = Field(base=UInt24,  name="Bool24",  **bool_kwargs)

BUInt24,  LUInt24 = UInt24.big,  UInt24.little
BSInt24,  LSInt24 = SInt24.big,  SInt24.little
BUEnum24, LUEnum24 = UEnum24.big, UEnum24.little
BSEnum24, LSEnum24 = SEnum24.big, SEnum24.little
BBool24,  LBool24 = Bool24.big,  Bool24.little

# floats
Float = Field(base=UInt32, name="Float",
              default=0.0, py_type=float, enc={'<': "<f", '>': ">f"},
              max=unpack('>f', b'\x7f\x7f\xff\xff'),
              min=unpack('>f', b'\xff\x7f\xff\xff'))
Double = Field(base=Float, name="Double", size=8, enc={'<': "<d", '>': ">d"},
               max=unpack('>d', b'\x7f\xef' + (b'\xff'*6)),
               min=unpack('>d', b'\xff\xef' + (b'\xff'*6)))

BFloat,  LFloat = Float.big,  Float.little
BDouble, LDouble = Double.big, Double.little


TimestampFloat = Field(base=Float, name="TimestampFloat",
                       py_type=str, default=lambda *a, **kwa: ctime(time()),
                       encoder=encode_float_timestamp,
                       decoder=decode_timestamp,
                       min='Wed Dec 31 19:00:00 1969',
                       max='Thu Jan  1 02:59:59 3001')
Timestamp = Field(base=TimestampFloat, name="Timestamp",
                  enc={'<': "<I", '>': ">I"}, encoder=encode_int_timestamp)

BTimestampFloat, LTimestampFloat = TimestampFloat.big, TimestampFloat.little
BTimestamp, LTimestamp = Timestamp.big, Timestamp.little

# Arrays
UInt8Array = Field(name="UInt8Array", size=1, is_var_size=True,
                   default=array("B", []), enc="B", sizecalc=array_sizecalc,
                   reader=py_array_reader, writer=py_array_writer)
UInt16Array = Field(base=UInt8Array, name="UInt16Array", size=2,
                    default=array("H", []), enc={"<": "H", ">": "H"})
UInt32Array = Field(base=UInt8Array, name="UInt32Array", size=4,
                    default=array("I", []), enc={"<": "I", ">": "I"})
UInt64Array = Field(base=UInt8Array, name="UInt64Array", size=8,
                    default=array("Q", []), enc={"<": "Q", ">": "Q"})

SInt8Array = Field(base=UInt8Array, name="SInt8Array",
                   default=array("b", []), enc="b")
SInt16Array = Field(base=UInt8Array, name="SInt16Array", size=2,
                    default=array("h", []), enc={"<": "h", ">": "h"})
SInt32Array = Field(base=UInt8Array, name="SInt32Array", size=4,
                    default=array("i", []), enc={"<": "i", ">": "i"})
SInt64Array = Field(base=UInt8Array, name="SInt64Array", size=8,
                    default=array("q", []), enc={"<": "q", ">": "q"})

FloatArray = Field(base=UInt32Array, name="FloatArray",
                   default=array("f", []), enc={"<": "f", ">": "f"})
DoubleArray = Field(base=UInt64Array, name="DoubleArray",
                    default=array("d", []), enc={"<": "d", ">": "d"})

BytesRaw = Field(base=UInt8Array, name="BytesRaw", py_type=BytesBuffer,
                 reader=bytes_reader, writer=bytes_writer, is_raw=True,
                 sizecalc=len_sizecalc, default=BytesBuffer())
BytearrayRaw = Field(base=BytesRaw, name="BytearrayRaw",
                     py_type=BytearrayBuffer, default=BytearrayBuffer())

BytesRawEnum = Field(base=BytesRaw, name="BytesRawEnum",
                     is_enum=True, is_block=True, py_type=blocks.EnumBlock,
                     reader=data_reader, writer=data_writer,
                     sizecalc=len_sizecalc, data_type=BytesBuffer,
                     sanitizer=bool_enum_sanitizer)

BUInt16Array, LUInt16Array = UInt16Array.big, UInt16Array.little
BUInt32Array, LUInt32Array = UInt32Array.big, UInt32Array.little
BUInt64Array, LUInt64Array = UInt64Array.big, UInt64Array.little
BSInt16Array, LSInt16Array = SInt16Array.big, SInt16Array.little
BSInt32Array, LSInt32Array = SInt32Array.big, SInt32Array.little
BSInt64Array, LSInt64Array = SInt64Array.big, SInt64Array.little

BFloatArray,  LFloatArray = FloatArray.big, FloatArray.little
BDoubleArray, LDoubleArray = DoubleArray.big, DoubleArray.little


# Strings
other_enc = ["big5", "hkscs", "cp037", "cp424", "cp437", "cp500", "cp720",
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
             "idna", "mbcs", "palmos", "utf_7", "utf_8_sig"]

# standard strings
StrAscii = Field(name="StrAscii", enc='ascii',
                 is_str=True, is_delimited=True,
                 default='', sizecalc=delim_str_sizecalc, size=1,
                 reader=data_reader, writer=data_writer,
                 decoder=decode_string, encoder=encode_string)
StrLatin1 = Field(base=StrAscii, name="StrLatin1", enc='latin1')
StrUtf8 = Field(base=StrAscii, name="StrUtf8", enc='utf8',
                sizecalc=delim_utf_sizecalc)
StrUtf16 = Field(base=StrUtf8, name="StrUtf16", size=2,
                 enc={"<": "utf_16_le", ">": "utf_16_be"})
StrUtf32 = Field(base=StrUtf8, name="StrUtf32", size=4,
                 enc={"<": "utf_32_le", ">": "utf_32_be"})
StrHex = Field(base=StrAscii, name="StrHex", sizecalc=str_hex_sizecalc,
               decoder=decode_string_hex, encoder=encode_string_hex)

BStrUtf16, LStrUtf16 = StrUtf16.big, StrUtf16.little
BStrUtf32, LStrUtf32 = StrUtf32.big, StrUtf32.little

# null terminated strings
'''While regular strings also have a delimiter character on the end
of the string, c strings are expected to entirely rely on the delimiter.
Regular strings store their size as an attribute in some parent block, but
c strings dont, and rawdata must be parsed until a delimiter is reached.'''
CStrAscii = Field(name="CStrAscii", enc='ascii',
                  is_str=True, is_delimited=True, is_oe_size=True,
                  default='', sizecalc=delim_str_sizecalc, size=1,
                  reader=cstring_reader, writer=cstring_writer,
                  decoder=decode_string, encoder=encode_string)
CStrLatin1 = Field(base=CStrAscii, name="CStrLatin1", enc='latin1')
CStrUtf8 = Field(base=CStrAscii, name="CStrUtf8", enc='utf8',
                 sizecalc=delim_utf_sizecalc)
CStrUtf16 = Field(base=CStrUtf8, name="CStrUtf16", size=2,
                  enc={"<": "utf_16_le", ">": "utf_16_be"})
CStrUtf32 = Field(base=CStrUtf8, name="CStrUtf32", size=4,
                  enc={"<": "utf_32_le", ">": "utf_32_be"})

BCStrUtf16, LCStrUtf16 = CStrUtf16.big, CStrUtf16.little
BCStrUtf32, LCStrUtf32 = CStrUtf32.big, CStrUtf32.little

# raw strings
'''Raw strings are special in that they are not expected to have
a delimiter. A fixed length raw string can have all characters
used and not require a delimiter character to be on the end.'''
StrRawAscii = Field(name="StrRawAscii",
                    enc='ascii', is_str=True, is_delimited=False,
                    default='', sizecalc=str_sizecalc, size=1,
                    reader=data_reader, writer=data_writer,
                    decoder=decode_string, encoder=encode_raw_string)
StrRawLatin1 = Field(base=StrRawAscii, name="StrRawLatin1", enc='latin1')
StrRawUtf8 = Field(base=StrRawAscii, name="StrRawUtf8", enc='utf8',
                   sizecalc=utf_sizecalc)
StrRawUtf16 = Field(base=StrRawUtf8, name="StrRawUtf16", size=2,
                    enc={"<": "utf_16_le", ">": "utf_16_be"})
StrRawUtf32 = Field(base=StrRawUtf8, name="StrRawUtf32", size=4,
                    enc={"<": "utf_32_le", ">": "utf_32_be"})

BStrRawUtf16, LStrRawUtf16 = StrRawUtf16.big, StrRawUtf16.little
BStrRawUtf32, LStrRawUtf32 = StrRawUtf32.big, StrRawUtf32.little


for enc in other_enc:
    str_fields[enc] = Field(base=StrAscii, enc=enc,
                            name="Str" + enc[0].upper() + enc[1:])
    cstr_fields[enc] = Field(base=CStrAscii, enc=enc,
                             name="CStr" + enc[0].upper() + enc[1:])
    str_raw_fields[enc] = Field(base=StrRawAscii, enc=enc,
                                name="StrRaw" + enc[0].upper() + enc[1:])
