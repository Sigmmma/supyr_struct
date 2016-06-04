'''
A collection of common and flexible binary fields and their base class.

fields are a read-only description of how to handle a certain type
of binary data. They define functions for reading and writing the data
to and from a buffer, encoding and decoding the data(if applicable),
a function to calculate the byte size of the data, and several properties
which determine how the data should be treated.

If certain data needs to be handeled in a way currently not supported, then
custom fields can be created with customized properties and functions.
'''

####################################
#  collections of specific fields  #
####################################
__all__ = [ 'Field', 'all_fields',
            'str_fields', 'cstr_fields', 'str_raw_fields',

            #hierarchy and structure
            'Struct', 'Union', 'Switch', 'Container', 'Array',  'WhileArray',
            'BBitStruct', 'LBitStruct',
            
            #special 'data' types
            'BPointer32', 'LPointer32',
            'BPointer64', 'LPointer64',
            'Void', 'Pad',

            #integers and floats
            'BBigUInt', 'BBigSInt', 'BBig1SInt',
            'LBigUInt', 'LBigSInt', 'LBig1SInt',
            'BitUInt', 'BitSInt', 'Bit1SInt', 'Bit', 'UInt8', 'SInt8',
            'BUInt16', 'BSInt16', 'LUInt16', 'LSInt16',
            'BUInt24', 'BSInt24', 'LUInt24', 'LSInt24',
            'BUInt32', 'BSInt32', 'LUInt32', 'LSInt32',
            'BUInt64', 'BSInt64', 'LUInt64', 'LSInt64',
            'BFloat',  'BDouble', 'LFloat',  'LDouble',
 
            #float and long int timestamps
            'BTimestampFloat', 'LTimestampFloat',
            'BTimestamp',      'LTimestamp',
 
            #enumerators and booleans
            'BitUEnum', 'BitSEnum', 'BitBool',
            'UEnum8',   'SEnum8',   'Bool8',
            'BigUEnum', 'BigSEnum', 'BigBool',
            'BUEnum16', 'BUEnum24', 'BUEnum32', 'BUEnum64',
            'LUEnum16', 'LUEnum24', 'LUEnum32', 'LUEnum64',
            'BSEnum16', 'BSEnum24', 'BSEnum32', 'BSEnum64',
            'LSEnum16', 'LSEnum24', 'LSEnum32', 'LSEnum64',
            'BBool16', 'BBool24', 'BBool32', 'BBool64', 
            'LBool16', 'LBool24', 'LBool32', 'LBool64',
            
            #integers and float arrays
            'UInt8Array',  'SInt8Array', 'BytesRaw', 'BytearrayRaw',
            'BUInt16Array', 'BSInt16Array', 'LUInt16Array', 'LSInt16Array',
            'BUInt32Array', 'BSInt32Array', 'LUInt32Array', 'LSInt32Array',
            'BUInt64Array', 'BSInt64Array', 'LUInt64Array', 'LSInt64Array',
            'BFloatArray',  'BDoubleArray', 'LFloatArray',  'LDoubleArray',
 
            #strings
            'StrLatin1', 'CStrLatin1', 'StrRawLatin1',
            'StrAscii',  'CStrAscii',  'StrRawAscii',
            'StrUtf8',   'CStrUtf8',   'StrRawUtf8',
            'BStrUtf16',  'BCStrUtf16',  'BStrRawUtf16',
            'BStrUtf32',  'BCStrUtf32',  'BStrRawUtf32',
            'LStrUtf16',  'LCStrUtf16',  'LStrRawUtf16',
            'LStrUtf32',  'LCStrUtf32',  'LStrRawUtf32',
           
            #used for fixed length string based keywords or constants
            'StrLatin1Enum',
            
            #######################################################
            #short hand names that use the endianness of the system
            #######################################################
            'BitStruct', 'Pointer32', 'Pointer64',
            
            #integers and floats
            'BigUInt', 'BigSInt', 'Big1SInt',
            'UInt16', 'UInt24', 'UInt32', 'UInt64', 'Float',
            'SInt16', 'SInt24', 'SInt32', 'SInt64', 'Double',
            
            #float and long int timestamps
            'TimestampFloat', 'Timestamp',
            
            #enumerators and booleans
            'BigUEnum', 'BigSEnum', 'BigBool',
            'UEnum16', 'UEnum24', 'UEnum32', 'UEnum64',
            'SEnum16', 'SEnum24', 'SEnum32', 'SEnum64',
            'Bool16',   'Bool24',  'Bool32',  'Bool64',
            
            #integers and float arrays
            'UInt16Array', 'SInt16Array', 'UInt32Array', 'SInt32Array',
            'UInt64Array', 'SInt64Array', 'FloatArray',  'DoubleArray',
            
            #strings
            'StrUtf16',  'CStrUtf16',  'StrRawUtf16',
            'StrUtf32',  'CStrUtf32',  'StrRawUtf32'
            ]

from array import array
from copy import deepcopy
from struct import unpack
from time import time, ctime
from types import FunctionType

from supyr_struct.field_methods import *
from supyr_struct.buffer import BytesBuffer, BytearrayBuffer
from supyr_struct import blocks
from supyr_struct.defs.constants import *
from supyr_struct.defs.descriptor import Descriptor

#a list containing all valid created fields
all_fields = []

#these are where all the single byte, less common encodings
#are located for Strings, CStrings, and raw Strings
str_fields = {}
cstr_fields = {}
str_raw_fields = {}

#used for mapping the keyword arguments to
#the attribute name of Field instances
slotmap={'default':'_default'}
for string in ('data', 'str', 'raw', 'enum', 'bool', 'array', 'container',
               'struct', 'delimited', 'var_size', 'bit_based', 'oe_size'):
    slotmap[string] = 'is_'+string
for string in ('reader', 'writer', 'decoder', 'encoder', 'sizecalc'):
    slotmap[string] = string+'_func'
for string in ('size', 'enc', 'max', 'min', 'data_type', 'py_type',
               'str_delimiter', 'delimiter', 'sanitizer'):
    slotmap[string] = string


class Field():
    '''
    A read-only description of how to handle a certain type of binary data.
    
    fields define functions for reading/writing the data to/from a buffer,
    encoding/decoding the data(if applicable), an optional function to
    calculate the byte size of the data, and numerous other properties
    which determine how the data should be treated.
    
    Each Field contains a dictionary of references to each of the other
    endiannesses of that same Field. Calling a Field with one of the
    following characters "<>" will return that type with that endianness.
    fields should never be duplicated as they are read-only descriptions
    of how to handle data. Copying will instead return the supplied Field.

    Read this classes __init__.__doc__ for descriptions of these properties.
    
    Object Properties:
        int:
            size
            min
            max
        str:
            name
            enc
            endian
            delimiter
            str_delimiter
        type:
            py_type
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
            is_bit_based
            is_delimited
            
    Object Methods:
        default(*args, **kwargs)
        reader(*args, **kwargs)
        writer(*args, **kwargs)
        encoder(*args, **kwargs)
        decoder(*args, **kwargs)
        sizecalc(*args, **kwargs)
        sanitizer(*args, **kwargs)
    '''

    f_endian = '='
    
    def __init__(self, **kwargs):
        '''
        Initializes a Field with the supplied keyword arguments.
        Raises TypeError if invalid keyword combinations are provided.
        
        Keyword arguments:

        #object
        default ----  A python object to copy as the default value. If the
                      supplied value is a python 'type' object which is a
                      sub-class of Block then the supplied 'default'
                      will be called with this Field(self) supplied as
                      the 'Type' keyword. This is the only way to use any
                      Block as a default since they cannot be created
                      without either a descriptor or a Field and
                      fields cannot be edited.
        #type
        py_type ----  The python type associated with this Field.
                      The type of 'default' will be used if one isnt provided.
                      (mainly used for verifying if a different python object
                      is a valid type to replace a previous value with)
        
        #str
        name ----------  The name of this Field
        delimiter -----  The delimiter in its encoded, bytes form(for strings)
        str_delimiter -  The delimiter in its decoded, python form(for strings)
        enc -----------  A string used to specify the format for encoding and
                         decoding the data. This string is required for non-raw
                         "data" fields, but there is no set convention as
                         it depends on what the de/encode function accepts.

                         For example, enc would be any one character in
                         'bhiqfBHIQD' for numbers de/encoded by pythons
                         struct module, whereas Str_UTF_16_LE and Str_Latin_1
                         use "UTF_16_LE" and "latin-1" respectively.
        endian --------  The endianness of this Field
        

        #function
        reader -----  A function for reading the bytes data from a buffer.
                      Also handles calling of the reader of any structures or
                      containers within it (including its child if it has one)
        writer -----  A function for writing the object as binary data to a
                      buffer. Also handles calling of the writer of any
                      structures or containers within it.
        decoder ----  A function for decoding bytes data from a buffer into a
                      python object(ex: convert b'\xD1\x22\xAB\x3F' to a float)
        encoder ----  A function for encoding the python object into a writable
                      bytes form(ex: convert "test" into b'\x74\x65\x73\x74')
        sizecalc ---  An optional function for calculating how large the object
                      would be if written to a buffer. Most of the time this
                      isn't needed, but for variable length data(strings whose
                      lengths are determined by some previously parsed field)
                      the size will need to properly calculated after an edit.
        sanitizer --  A function which checks and properly sanitizes
                      descriptors that have this field as their type

        #bool
        block ------  Is a form of hierarchy(struct, array, container, etc)
        data -------  Is a form of data(as opposed to hierarchy)
        str --------  Is a string
        raw --------  Is unencoded raw data(ex: pixel bytes)
        array ------  Is an array of instanced elements
        enum -------  Has a set of modes it may be set to
        bool -------  Has a set of T/F flags that can be set
        struct -----  Has a fixed size and attributes have offsets
        container --  Has no fixed size and attributes have no offsets
        varsize ----  Byte size of the object can vary(descriptor defined size)
        oe_size ----  Byte size of the object cant be determined in advance
                      as it relies on some sort of delimiter, or is a stream
                      of data that must be parsed to find the end(open ended)
        bit_based --  Whether the data should be worked on a bit or byte level
        delimited --  Whether or not the string is terminated with a delimiter
                      character(self.str MUST be True)
        
        #int
        size -------  The byte size of the data when in binary form.
                      For strings this is how many bytes a single character is
        max --------  For floats/ints, this is the largest a value can be
        min --------  For floats/ints, this is the smallest a value can be
        '''

        #set the Field as editable
        self._instantiated = False

        '''Set up the default values for each attribute'''
        #default endianness of the initial Field is No Endianness
        self.endian = '='
        self.little = self.big = self
        self.min = self.max = self._default = self.enc = None
        self.delimiter = self.str_delimiter = None
        self.size = None

        #set the Field's flags
        self.is_data = self.is_str  = self.is_delimited = False
        self.is_raw  = self.is_enum = self.is_bool = False
        self.is_struct   = self.is_array   = self.is_container = False
        self.is_var_size = self.is_oe_size = self.is_bit_based = False

        #if a base was provided, use it to update the kwargs with its settings
        base = kwargs.get('base')
        if isinstance(base, Field):
            #if the base has separate encodings for the different endiannesses,
            #make sure to set the default encoding of this Field as theirs
            if base.little.enc != base.big.enc:
                kwargs.setdefault('enc', {'<':base.little.enc, '>':base.big.enc})
            for slot in slotmap:
                if base.is_enum or base.is_bool:
                    if slot == 'encoder':
                        kwargs['encoder_set'] = True
                    elif slot == 'decoder':
                        kwargs['decoder_set'] = True
                    elif slot == 'sizecalc':
                        kwargs['sizecalc_set'] = True
                kwargs.setdefault(slot, base.__getattribute__(slotmap[slot]))

        #setup the Field's main properties
        self.name      = kwargs.get("name")
        self.reader_func   = kwargs.get("reader", self.not_imp)
        self.writer_func   = kwargs.get("writer", self.not_imp)
        self.decoder_func  = kwargs.get("decoder", no_decode)
        self.encoder_func  = kwargs.get("encoder", no_encode)
        self.sizecalc_func = def_sizecalc
        self.sanitizer = kwargs.get("sanitizer", standard_sanitizer)
        self._default  = kwargs.get("default",  None)
        self.py_type   = kwargs.get("py_type",  type(self._default))
        self.data_type = kwargs.get("data_type", type(None))

        #set the Field's flags
        self.is_data = not bool(kwargs.get("block", not self.is_data))
        self.is_data = bool(kwargs.get("data", self.is_data))
        self.is_str  = bool(kwargs.get("str",  self.is_str))
        self.is_raw  = bool(kwargs.get("raw",  self.is_raw))
        self.is_enum   = bool(kwargs.get("enum",   self.is_enum))
        self.is_bool   = bool(kwargs.get("bool",   self.is_bool))
        self.is_struct = bool(kwargs.get("struct", self.is_struct))
        self.is_array  = bool(kwargs.get("array",  self.is_array))
        self.is_container = bool(kwargs.get("container", self.is_container))
        self.is_var_size  = bool(kwargs.get("varsize",   self.is_var_size))
        self.is_oe_size   = bool(kwargs.get("oe_size",   self.is_oe_size))
        self.is_bit_based = bool(kwargs.get("bit_based", self.is_bit_based))
        self.is_delimited = bool(kwargs.get("delimited", self.is_delimited))
        
        if self.name is None:
            raise TypeError("'name' is a required identifier for data types.")

        '''Some assumptions are made based on the flags provided. Fill in the
        rest of the flags that must be true, even if they werent provided'''
        if self.is_str:
            if "delimiter" in kwargs:
                self.delimiter = kwargs["delimiter"]
            elif "size" in kwargs:
                #if the delimiter isnt specified, assume it's 0x00*size
                self.delimiter = b'\x00' * int(kwargs["size"])
                
            self.str_delimiter = kwargs.get("str_delimiter",self.str_delimiter)
            
        self.is_container |= self.is_array
            
        if self.is_str or self.is_raw:
            self.is_data = self.is_var_size = True
        elif self.is_block:
            self.is_var_size = True

        
        if "endian" in kwargs:
            if kwargs.get("endian") in ('<','>','='):
                self.endian = kwargs["endian"]
            else:
                raise TypeError("Supplied endianness must be one of the "+
                                "following characters: '<', '>', or '='")

        if self.is_data:
            if "size" in kwargs:
                self.size = kwargs["size"]
            elif not self.is_var_size:
                raise TypeError("Data size required for 'data' " +
                                "fields of non variable size")

        if isinstance(kwargs.get("enc"), str):
            self.enc = kwargs["enc"]
        elif isinstance(kwargs.get("enc"), dict):
            enc = kwargs["enc"]
            if not('<' in enc and '>' in enc):
                raise TypeError("When providing endianness reliant "+
                                "encodings, big and little endian\n"+
                                "must both be provided under the "+
                                "keys '>' and '<' respectively.")
            #make the first encoding the endianness of the system
            self.enc = enc[byteorder_char]
            self.endian = byteorder_char

        if self.is_bool and self.is_enum:
            raise TypeError('A Field can not be both an enumerator '+
                            'and a set of booleans at the same time.')

        if self.is_container and self.is_struct:
            raise TypeError('A Field can not be both a struct '+
                            'and a container at the same time.')

        other_endian = kwargs.get('other_endian')

        '''if the endianness is specified as '=' it means that
        endianness has no meaning for this Field and that
        big and little should be the same. Otherwise, create a
        similar Field, but with an opposite endianness'''
        if self.endian != "=" and other_endian is None:
            #set the endianness kwarg to the opposite of this one
            kwargs["endian"] = {'<':'>','>':'<'}[self.endian]
            kwargs["other_endian"] = self
            
            #if the provided enc kwarg is a dict, get the encoding
            #of the endianness opposite the current Field.
            if 'enc' in kwargs and isinstance(kwargs["enc"], dict):
                kwargs["enc"] = kwargs["enc"][kwargs["endian"]]
            else:
                kwargs["enc"] = self.enc
                
            #create the other endian Field
            other_endian = Field(**kwargs)

        #set the other endianness Field
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

        '''Decide on a sizecalc method to use based on the
        data type or use the one provided, if provided'''
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


        '''if self.data_type is not None, then it means that self.sizecalc_func,
        self._Encode, and self._Decode need to be wrapped in a lambda'''
        if self.data_type is not type(None):
            if not kwargs.get('sizecalc_set'):
                _sc = self.sizecalc_func
                def sizecalc_wrapper(self, block, _sizecalc=_sc, *a, **kw):
                    try:
                        return _sizecalc(self, block.data, *a, **kw)
                    except AttributeError:
                        return _sizecalc(self, block, *a, **kw)
                    
                self.sizecalc_func = sizecalc_wrapper
            if not kwargs.get('decoder_set'):
                _de = self.decoder_func
                '''this function expects to return a constructed Block, so it
                provides the appropriate args and kwargs to the constructor'''
                def decoder_wrapper(self, raw_bytes, desc, parent=None,
                                    attr_index=None, _decode=_de):
                    try:
                        return self.py_type(desc, parent, init_data=
                                   _decode(self, raw_bytes, desc,
                                           parent, attr_index))
                    except AttributeError:
                        return _decode(self, raw_bytes, desc, parent,attr_index)
                    
                self.decoder_func = decoder_wrapper
                
            if not kwargs.get('encoder_set'):
                _en = self.encoder_func
                """this function expects the actual value being
                encoded to be in 'block' under the name 'data',
                so it passes the args over to the actual encoder
                function, but replaces 'block' with 'block.data'"""
                def encoder_wrapper(self, block, parent=None,
                                    attr_index=None, _encode=_en):
                    try:
                        return _encode(self, block.data, parent,attr_index)
                    except AttributeError:
                        return _encode(self, block, parent, attr_index)
                    
                self.encoder_func = encoder_wrapper
                
        #if a default wasn't provided, try to create one from self.py_type
        if self._default is None:
            if issubclass(self.py_type, blocks.Block):
                #create a default descriptor to give to the default Block
                desc = { TYPE:self, NAME:UNNAMED }
                if self.is_block:
                    desc[ENTRIES] = 0
                    desc[NAME_MAP] = {}
                    desc[ATTR_OFFS] = []
                if self.is_enum or self.is_bool:
                    desc[ENTRIES] = 0
                    desc[NAME_MAP] = {}
                if self.is_var_size and not self.is_oe_size:
                    desc[SIZE] = 0
                if self.is_array:
                    desc[SUB_STRUCT] = {TYPE:Void, NAME:UNNAMED}
                if CHILD in self.py_type.__slots__:
                    desc[CHILD] = {TYPE:Void, NAME:UNNAMED}
                self._default = self.py_type(Descriptor(desc))
            else:
                try:
                    self._default = self.py_type()
                except Exception:
                    raise TypeError("Could not create Field 'default' "+
                                    "instance. You must manually supply "+
                                    "a default value.")

        #now that setup is concluded, set the object as read-only
        self._instantiated = True
        
        #add this to the collection of all field types
        all_fields.append(self)


    '''these functions are just alias's and are done this way so
    that this class can pass itself as a reference manually as well
    as to allow the endianness to the forced to big or little.'''
    def _normal_reader(self, *args, **kwargs):
        '''
        Calls this fields reader function, passing on all args and kwargs.
        Returns the return value of this fields reader, which
        should be the offset the reader function left off at.
        
        Required arguments:
            parent(Block)
        Optional arguments:
            rawdata(buffer) = None
            attr_index(int, str) = None
            root_offset(int) = 0
            offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Readers unless a reader removes or changes them.
        '''
        return self.reader_func(self, *args, **kwargs)

    def _normal_writer(self, *args, **kwargs):
        '''
        Calls this fields writer function, passing on all args and kwargs.
        Returns the return value of this fields writer, which
        should be the offset the writer function left off at.
        
        Required arguments:
            parent(Block)
        Optional arguments:
            writebuffer(buffer) = None
            attr_index(int, str) = None
            root_offset(int) = 0
            offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Writers unless a writer removes or changes them.
        '''
        
        return self.writer_func(self, *args, **kwargs)

    def _normal_decoder(self, *args, **kwargs):
        '''
        Calls this fields decoder function, passing on all args and kwargs.
        Returns the return value of this fields decoder, which should
        be a python object decoded represention of the "Bytes" argument.
        
        Required arguments:
            Bytes(bytes)
        Optional arguments:
            parent(Block) = None
            attr_index(int) = None
        '''
        
        return self.decoder_func(self, *args, **kwargs)

    def _normal_encoder(self, *args, **kwargs):
        '''
        Calls this fields encoder function, passing on all args and kwargs.
        Returns the return value of this fields encoder, which should
        be a bytes object encoded represention of the "block" argument.
        
        Required arguments:
            block(object)
        Optional arguments:
            parent(Block) = None
            attr_index(int) = None
        '''
        
        return self.encoder_func(self, *args, **kwargs)

    reader  = _normal_reader
    writer  = _normal_writer
    encoder = _normal_encoder
    decoder = _normal_decoder

    '''these next functions are used to force the reading
    and writing to conform to one endianness or the other'''
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

    def __call__(self, name, *desc_entries, **desc):
        '''Creates and returns a dict formatted properly to be
        used as a descriptor. The first argument is the block's name.
        The remaining positional args are the numbered entries
        in the descriptor, and the keyword arguments
        are the non-numbered entries in the descriptor.

        If the field is Pad, the first argument is the padding size.'''
        if self is Pad:
            desc.setdefault(NAME, 'pad_entry')
            desc.setdefault(SIZE, name)
        else:
            if not isinstance(name, str):
                raise TypeError("'name' must be of type '%s', not '%s'"%
                                (type(str), type(name)))
            desc.setdefault(NAME, name)
            
        desc[TYPE] = self
            
        #remove all keyword arguments that aren't descriptor keywords
        for key in tuple(desc.keys()):
            if key not in desc_keywords:
                del desc[key]; continue
            elif hasattr(desc[key], 'descriptor'):
                '''if the entry in desc is a BlockDef, it
                needs to be replaced with its descriptor.'''
                desc[key] = desc[key].descriptor
                
        #add all the positional arguments to the descriptor
        for i in range(len(desc_entries)):
            desc[i] = desc_entries[i]
            if hasattr(desc[i], 'descriptor'):
                '''if the entry in desc is a BlockDef, it
                needs to be replaced with its descriptor.'''
                desc[i] = desc[i].descriptor
                
        return desc

    def __eq__(self, other):
        '''Returns whether or not an object is equivalent to this one.
        Returns True for the same Field, but with a different endianness'''
        try:
            return(isinstance(other, Field)
                   and self.name == other.name and self.enc == other.enc)
        except AttributeError:
            return False

    def __ne__(self, other):
        '''Returns whether or not an object isnt equivalent to this one.
        Returns False for the same Field, but with a different endianness'''
        try:
            return(not isinstance(other, Field)
                   or self.name != other.name or self.enc != other.enc)
        except AttributeError:
            return True

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

    __repr__ = __str__

    '''
    To prevent editing of fields once they are instintiated, the
    default setattr and delattr methods are overloaded with these
    '''
    def __setattr__(self, attr, value):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError("fields are read-only and may "+
                                 "not be changed once created.")
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr, value):
        if hasattr(self, "_instantiated") and self._instantiated:
            raise AttributeError("fields are read-only and may "+
                                 "not be changed once created.")
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

    def force_little(self = None):
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the little
        endian version of the Field(if it exists).'''
        if self is None:
            Field.reader   = Field._little_reader
            Field.writer   = Field._little_writer
            Field.encoder  = Field._little_encoder
            Field.decoder  = Field._little_decoder
            Field.f_endian = '<'
        else:
            self.__dict__['reader']   = Field._little_reader
            self.__dict__['writer']   = Field._little_writer
            self.__dict__['encoder']  = Field._little_encoder
            self.__dict__['decoder']  = Field._little_decoder
            self.__dict__['f_endian'] = '<'

    def force_big(self = None):
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the big
        endian version of the Field(if it exists).'''
        if self is None:
            Field.reader   = Field._big_reader
            Field.writer   = Field._big_writer
            Field.encoder  = Field._big_encoder
            Field.decoder  = Field._big_decoder
            Field.f_endian = '>'
        else:
            self.__dict__['reader']   = Field._big_reader
            self.__dict__['writer']   = Field._big_writer
            self.__dict__['encoder']  = Field._big_encoder
            self.__dict__['decoder']  = Field._big_decoder
            self.__dict__['f_endian'] = '>'

    def force_normal(self = None):
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that do not force them to use an
        endianness other than the one they are currently set to.'''
        if self is None:
            Field.reader   = Field._normal_reader
            Field.writer   = Field._normal_writer
            Field.encoder  = Field._normal_encoder
            Field.decoder  = Field._normal_decoder
            Field.f_endian = '='
        else:
            try:   del self.__dict__['reader']
            except KeyError: pass
            try:   del self.__dict__['writer']
            except KeyError: pass
            try:   del self.__dict__['encoder']
            except KeyError: pass
            try:   del self.__dict__['decoder']
            except KeyError: pass
            try:   del self.__dict__['f_endian']
            except KeyError: pass

    def sizecalc(self, *args, **kwargs):
        '''A redirect that provides 'self' as
        an arg to the actual sizecalc function.'''
        return self.sizecalc_func(self, *args, **kwargs)

    def not_imp(self, *args, **kwargs):
        raise NotImplementedError(("This operation not implemented "+
                                   "in %s Field.") % self.name)


Void = Field( name="Void", data=True, size=0, py_type=blocks.VoidBlock,
              reader=void_reader, writer=void_writer)
Pad = Field( name="Pad", data=True, varsize=True, py_type=blocks.VoidBlock,
             reader=no_read, writer=no_write)
Container = Field( name="Container", container=True, block=True,
                   py_type=blocks.ListBlock, sanitizer=sequence_sanitizer,
                   reader=container_reader, writer=container_writer)
Struct = Field( name="Struct", struct=True, block=True,
                py_type=blocks.ListBlock, sanitizer=sequence_sanitizer,
                reader=struct_reader, writer=struct_writer)
Array = Field( name="Array", array=True, block=True,
               py_type=blocks.ListBlock, sanitizer=sequence_sanitizer,
               reader=array_reader, writer=array_writer)
WhileArray = Field( name="WhileArray", array=True,  block=True, oe_size=True,
                    py_type=blocks.WhileBlock, sanitizer=sequence_sanitizer,
                    reader=while_array_reader, writer=array_writer)
Switch = Field( name='Switch', block=True, varsize=True,
                py_type=blocks.VoidBlock, sanitizer=switch_sanitizer,
                reader=switch_reader, writer=void_writer)
Union = Field( base=Struct, name="Union", block=True,
               py_type=blocks.UnionBlock, sanitizer=union_sanitizer,
               reader=union_reader, writer=union_writer)

#bit_based data
'''When within a BitStruct, offsets and sizes are in bits instead of bytes.
BitStruct sizes MUST BE SPECIFIED IN WHOLE BYTE AMOUNTS(1byte, 2bytes, etc)'''
BitStruct = Field( name="BitStruct",
                   struct=True, bit_based=True, enc={'<':'<', '>':'>'},
                   py_type=blocks.ListBlock, sanitizer=sequence_sanitizer,
                   reader=bit_struct_reader, writer=bit_struct_writer)
BBitStruct, LBitStruct = BitStruct.big, BitStruct.little

'''For when you dont need multiple bits. It's faster and
easier to use this than a BitUInt with a size of 1.'''
Bit = Field( name="Bit", data=True, bit_based=True, size=1, enc='U', default=0,
             reader=default_reader, decoder=decode_bit, encoder=encode_bit)

'''UInt, sInt, and SInt MUST be in a BitStruct as the BitStruct
acts as a bridge between byte level and bit level objects.
Bit1SInt is signed in 1's compliment and BitSInt is in 2's compliment.'''
BitSInt = Field(data=True, varsize=True, bit_based=True,
                name='BitSInt', enc='S', sizecalc=bit_sint_sizecalc,
                default=0, reader=default_reader,
                decoder=decode_bit_int,  encoder=encode_bit_int)
Bit1SInt = Field(base=BitSInt, name="Bit1SInt",
                 enc="s", sizecalc=bit_sint_sizecalc)
BitUInt  = Field(base=BitSInt, name="BitUInt",
                 enc="U", sizecalc=bit_uint_sizecalc)
BitUEnum = Field(base=BitUInt, name="BitUEnum",
                 enum=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BitSEnum = Field(base=BitSInt, name="BitSEnum",
                 enum=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BitBool = Field(base=BitSInt, name="BitBool",
                bool=True, default=None, data_type=int,
                sanitizer=bool_enum_sanitizer, py_type=blocks.BoolBlock)

BigSInt = Field(base=BitUInt, name="BigSInt", bit_based=False,
                reader=data_reader,     writer=data_writer,
                decoder=decode_big_int, encoder=encode_big_int,
                sizecalc=big_sint_sizecalc, enc={'<':"<S",'>':">S"} )
Big1SInt = Field(base=BigSInt, name="Big1SInt",
                 sizecalc=big_sint_sizecalc, enc={'<':"<s",'>':">s"} )
BigUInt = Field(base=BigSInt, name="BigUInt",
                sizecalc=big_uint_sizecalc, enc={'<':"<U",'>':">U"} )
BigUEnum = Field(base=BigUInt, name="BigUEnum",
                 enum=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BigSEnum = Field(base=BigSInt, name="BigSEnum",
                 enum=True, default=None, data_type=int,
                 sanitizer=bool_enum_sanitizer, py_type=blocks.EnumBlock)
BigBool = Field(base=BigUInt, name="BigBool",
                bool=True, default=None, data_type=int,
                sanitizer=bool_enum_sanitizer, py_type=blocks.BoolBlock)

BBigSInt,  LBigSInt  = BigSInt.big,  BigSInt.little
BBigUInt,  LBigUInt  = BigUInt.big,  BigUInt.little
BBig1SInt, LBig1SInt = Big1SInt.big, Big1SInt.little
BBigUEnum, LBigUEnum = BigUEnum.big, BigUEnum.little
BBigSEnum, LBigSEnum = BigSEnum.big, BigSEnum.little
BBigBool,  LBigBool  = BigBool.big,  BigBool.little

#8/16/32/64-bit integers
UInt8  = Field(base=BigUInt, name="UInt8", size=1, min=0, max=255, enc='B',
               reader=f_s_data_reader, sizecalc=def_sizecalc, varsize=False,
               decoder=decode_numeric, encoder=encode_numeric )
UInt16 = Field(base=UInt8, name="UInt16", size=2, max=2**16-1, enc={'<':"<H",'>':">H"})
UInt32 = Field(base=UInt8, name="UInt32", size=4, max=2**32-1, enc={'<':"<I",'>':">I"})
UInt64 = Field(base=UInt8, name="UInt64", size=8, max=2**64-1, enc={'<':"<Q",'>':">Q"})

SInt8  = Field(base=UInt8,  name="SInt8",  enc={'<':"<b",'>':">b"}, min=-2**7,  max=2**7-1)
SInt16 = Field(base=UInt16, name="SInt16", enc={'<':"<h",'>':">h"}, min=-2**15, max=2**15-1)
SInt32 = Field(base=UInt32, name="SInt32", enc={'<':"<i",'>':">i"}, min=-2**31, max=2**31-1)
SInt64 = Field(base=UInt64, name="SInt64", enc={'<':"<q",'>':">q"}, min=-2**63, max=2**63-1)

BUInt16, LUInt16 = UInt16.big, UInt16.little
BUInt32, LUInt32 = UInt32.big, UInt32.little
BUInt64, LUInt64 = UInt64.big, UInt64.little

BSInt16, LSInt16 = SInt16.big, SInt16.little
BSInt32, LSInt32 = SInt32.big, SInt32.little
BSInt64, LSInt64 = SInt64.big, SInt64.little

#pointers
Pointer32 = Field(base=UInt32, name="Pointer32")
Pointer64 = Field(base=UInt64, name="Pointer64")

BPointer32, LPointer32 = Pointer32.big, Pointer32.little
BPointer64, LPointer64 = Pointer64.big, Pointer64.little

enum_kwargs = {'enum':True, 'py_type':blocks.EnumBlock, 'default':None,
               'data_type':int, 'sanitizer':bool_enum_sanitizer}

bool_kwargs = {'bool':True, 'py_type':blocks.BoolBlock, 'default':None,
               'data_type':int, 'sanitizer':bool_enum_sanitizer}
#enumerators
UEnum8  = Field(base=UInt8,  name="UEnum8",  **enum_kwargs)
UEnum16 = Field(base=UInt16, name="UEnum16", **enum_kwargs)
UEnum32 = Field(base=UInt32, name="UEnum32", **enum_kwargs)
UEnum64 = Field(base=UInt64, name="UEnum64", **enum_kwargs)

SEnum8  = Field(base=SInt8,  name="SEnum8",  **enum_kwargs)
SEnum16 = Field(base=SInt16, name="SEnum16", **enum_kwargs)
SEnum32 = Field(base=SInt32, name="SEnum32", **enum_kwargs)
SEnum64 = Field(base=SInt64, name="SEnum64", **enum_kwargs)

BUEnum16, LUEnum16 = UEnum16.big, UEnum16.little
BUEnum32, LUEnum32 = UEnum32.big, UEnum32.little
BUEnum64, LUEnum64 = UEnum64.big, UEnum64.little

BSEnum16, LSEnum16 = SEnum16.big, SEnum16.little
BSEnum32, LSEnum32 = SEnum32.big, SEnum32.little
BSEnum64, LSEnum64 = SEnum64.big, SEnum64.little

#booleans
Bool8  = Field(base=UInt8,  name="Bool8",  **bool_kwargs)
Bool16 = Field(base=UInt16, name="Bool16", **bool_kwargs)
Bool32 = Field(base=UInt32, name="Bool32", **bool_kwargs)
Bool64 = Field(base=UInt64, name="Bool64", **bool_kwargs)

BBool16, LBool16 = Bool16.big, Bool16.little
BBool32, LBool32 = Bool32.big, Bool32.little
BBool64, LBool64 = Bool64.big, Bool64.little

#24-bit integers
UInt24 = Field(base=UInt8, name="UInt24", size=3,
               max=2**24-1, enc={'<':"<I",'>':">I"},
               decoder=decode_24bit_numeric, encoder=encode_24bit_numeric)
SInt24 = Field(base=UInt24, name="SInt24",
               enc={'<':"<i",'>':">i"},
               min=-2**23, max=2**23-1)
UEnum24 = Field(base=UInt24, name="UEnum24", **enum_kwargs)
SEnum24 = Field(base=SInt24, name="SEnum24", **enum_kwargs)
Bool24  = Field(base=UInt24, name="Bool24",  **bool_kwargs)

BUInt24,  LUInt24  = UInt24.big,  UInt24.little
BSInt24,  LSInt24  = SInt24.big,  SInt24.little
BUEnum24, LUEnum24 = UEnum24.big, UEnum24.little
BSEnum24, LSEnum24 = SEnum24.big, SEnum24.little
BBool24,  LBool24  = Bool24.big,  Bool24.little

#floats
Float = Field(base=UInt32, name="Float", default=0.0, py_type=float,
              enc={'<':"<f",'>':">f"},
              max=unpack('>f',b'\x7f\x7f\xff\xff'),
              min=unpack('>f',b'\xff\x7f\xff\xff') )
Double = Field(base=Float, name="Double", size=8,     enc={'<':"<d",'>':">d"},
               max=unpack('>d',b'\x7f\xef' + (b'\xff'*6)),
               min=unpack('>d',b'\xff\xef' + (b'\xff'*6)) )

BFloat,  LFloat  = Float.big,  Float.little
BDouble, LDouble = Double.big, Double.little

 
TimestampFloat = Field(base=Float, name="TimestampFloat",
                     py_type=str, default=lambda *a, **kwa:ctime(time()),
                     encoder=encode_float_timestamp, decoder=decode_timestamp,
                 min='Wed Dec 31 19:00:00 1969', max='Thu Jan  1 02:59:59 3001')
Timestamp = Field(base=TimestampFloat, name="Timestamp",
                  enc={'<':"<I",'>':">I"}, encoder=encode_int_timestamp)

BTimestampFloat, LTimestampFloat = TimestampFloat.big, TimestampFloat.little
BTimestamp,      LTimestamp      = Timestamp.big,      Timestamp.little

#Arrays
UInt8Array  = Field(name="UInt8Array", size=1, varsize=True, raw=True, 
                    default=array("B", []), enc="B", sizecalc=array_sizecalc,
                    reader=py_array_reader, writer=py_array_writer)
UInt16Array = Field(base=UInt8Array, name="UInt16Array", size=2,
                    default=array("H",[]), enc={"<":"H",">":"H"})
UInt32Array = Field(base=UInt8Array, name="UInt32Array", size=4,
                    default=array("I",[]), enc={"<":"I",">":"I"})
UInt64Array = Field(base=UInt8Array, name="UInt64Array", size=8,
                    default=array("Q",[]), enc={"<":"Q",">":"Q"})

SInt8Array  = Field(base=UInt8Array, name="SInt8Array",
                    default=array("b",[]), enc="b")
SInt16Array = Field(base=UInt8Array, name="SInt16Array", size=2,
                    default=array("h",[]), enc={"<":"h",">":"h"})
SInt32Array = Field(base=UInt8Array, name="SInt32Array", size=4,
                    default=array("i",[]), enc={"<":"i",">":"i"})
SInt64Array = Field(base=UInt8Array, name="SInt64Array", size=8,
                    default=array("q",[]), enc={"<":"q",">":"q"})

FloatArray  = Field(base=UInt32Array, name="FloatArray",
                    default=array("f", []), enc={"<":"f",">":"f"})
DoubleArray = Field(base=UInt64Array, name="DoubleArray",
                    default=array("d", []), enc={"<":"d",">":"d"})

BytesRaw = Field(base=UInt8Array, name="BytesRaw", py_type=BytesBuffer,
                 reader=bytes_reader, writer=bytes_writer,
                 sizecalc=len_sizecalc, default=BytesBuffer())
BytearrayRaw = Field(base=BytesRaw, name="BytearrayRaw",
                     py_type=BytearrayBuffer, default=BytearrayBuffer())

BUInt16Array, LUInt16Array = UInt16Array.big, UInt16Array.little
BUInt32Array, LUInt32Array = UInt32Array.big, UInt32Array.little
BUInt64Array, LUInt64Array = UInt64Array.big, UInt64Array.little
BSInt16Array, LSInt16Array = SInt16Array.big, SInt16Array.little
BSInt32Array, LSInt32Array = SInt32Array.big, SInt32Array.little
BSInt64Array, LSInt64Array = SInt64Array.big, SInt64Array.little

BFloatArray,  LFloatArray  = FloatArray.big,  FloatArray.little
BDoubleArray, LDoubleArray = DoubleArray.big, DoubleArray.little


#Strings
other_enc = ("big5","hkscs","cp037","cp424","cp437","cp500","cp720","cp737",
             "cp775","cp850","cp852","cp855","cp856","cp857","cp858","cp860",
             "cp861","cp862","cp863","cp864","cp865","cp866","cp869","cp874",
             "cp875","cp932","cp949","cp950","cp1006","cp1026","cp1140",
             "cp1250","cp1251","cp1252","cp1253","cp1254","cp1255","cp1256",
             "cp1257","cp1258","euc_jp","euc_jis_2004","euc_jisx0213","euc_kr",
             "gb2312","gbk","gb18030","hz","iso2022_jp","iso2022_jp_1",
             "iso2022_jp_2","iso2022_jp_2004","iso2022_jp_3","iso2022_jp_ext",
             "iso2022_kr","iso8859_2","iso8859_3","iso8859_4","iso8859_5",
             "iso8859_6","iso8859_7","iso8859_8","iso8859_9","iso8859_10",
             "iso8859_11","iso8859_13","iso8859_14","iso8859_15","iso8859_16",
             "johab","koi8_r","koi8_u","mac_cyrillic","mac_greek",
             "mac_iceland", "mac_latin2","mac_roman","mac_turkish","ptcp154",
             "shift_jis", "shift_jis_2004","shift_jisx0213",
             "idna","mbcs","palmos","utf_7","utf_8_sig")

#standard strings
StrAscii  = Field(name="StrAscii", enc='ascii',
                  str=True, delimited=True,
                  default='', sizecalc=delim_str_sizecalc, size=1,
                  reader=data_reader, writer=data_writer,
                  decoder=decode_string, encoder=encode_string )
StrLatin1 = Field(base=StrAscii, name="StrLatin1", enc='latin1' )
StrUtf8   = Field(base=StrAscii, name="StrUtf8", enc='utf8',
                  sizecalc=delim_utf_sizecalc)
StrUtf16  = Field(base=StrUtf8, name="StrUtf16", size=2,
                  enc={"<":"utf_16_le", ">":"utf_16_be"})
StrUtf32  = Field(base=StrUtf8, name="StrUtf32", size=4,
                  enc={"<":"utf_32_le", ">":"utf_32_be"})

BStrUtf16, LStrUtf16 = StrUtf16.big, StrUtf16.little
BStrUtf32, LStrUtf32 = StrUtf32.big, StrUtf32.little

#null terminated strings
CStrAscii  = Field(name="CStrAscii", enc='ascii',
                   str=True, delimited=True, oe_size=True,
                   default='', sizecalc=delim_str_sizecalc, size=1,
                   reader=cstring_reader, writer=cstring_writer,
                   decoder=decode_string, encoder=encode_string )
CStrLatin1 = Field(base=CStrAscii, name="CStrLatin1", enc='latin1' )
CStrUtf8   = Field(base=CStrAscii, name="CStrUtf8", enc='utf8',
                   sizecalc=delim_utf_sizecalc)
CStrUtf16  = Field(base=CStrUtf8, name="CStrUtf16", size=2,
                   enc={"<":"utf_16_le", ">":"utf_16_be"})
CStrUtf32  = Field(base=CStrUtf8, name="CStrUtf32", size=4,
                   enc={"<":"utf_32_le", ">":"utf_32_be"})

BCStrUtf16, LCStrUtf16 = CStrUtf16.big, CStrUtf16.little
BCStrUtf32, LCStrUtf32 = CStrUtf32.big, CStrUtf32.little

#raw strings
'''raw strings are special in that they ARE NOT expected to have
a delimiter. A fixed length raw string can have all characters
used and not require a delimiter character to be on the end.'''
StrRawAscii  = Field(name="StrRawAscii", enc='ascii',
                     str=True, delimited=False,
                     default='', sizecalc=str_sizecalc, size=1,
                     reader=data_reader, writer=data_writer,
                     decoder=decode_string, encoder=encode_raw_string )
StrRawLatin1 = Field(base=StrRawAscii, name="StrRawLatin1", enc='latin1' )
StrRawUtf8   = Field(base=StrRawAscii, name="StrRawUtf8", enc='utf8',
                     sizecalc=utf_sizecalc)
StrRawUtf16  = Field(base=StrRawUtf8, name="StrRawUtf16", size=2,
                     enc={"<":"utf_16_le", ">":"utf_16_be"})
StrRawUtf32  = Field(base=StrRawUtf8, name="StrRawUtf32", size=4,
                     enc={"<":"utf_32_le", ">":"utf_32_be"})

BStrRawUtf16, LStrRawUtf16 = StrRawUtf16.big, StrRawUtf16.little
BStrRawUtf32, LStrRawUtf32 = StrRawUtf32.big, StrRawUtf32.little


for enc in other_enc:
    str_fields[enc]     = Field(base=StrAscii,    name="Str"+enc,    enc=enc)
    cstr_fields[enc]    = Field(base=CStrAscii,   name="CStr"+enc,   enc=enc)
    str_raw_fields[enc] = Field(base=StrRawAscii, name="StrRaw"+enc, enc=enc)

#Used for places in a file where a string is used as an enumerator
#to represent a setting in a file (a 4 character code for example)
#This is not likely to see a use, especially since 4 character codes
#are endianness reliant, but strings arent. Still, it might be useful.
StrLatin1Enum = Field(base=StrRawLatin1, name="StrLatin1Enum",
                      enum=True, data_type=str, py_type=blocks.EnumBlock,
                      sanitizer=bool_enum_sanitizer)
