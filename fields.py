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
__all__ = ['Field', 'all_fields',
           'str_fields', 'cstr_fields', 'str_raw_fields',

           #hierarchy and structure
           'Struct', 'BitStruct', 'Switch',
           'Container', 'Array', 'WhileArray', 
           
           #special 'data' types
           'Pointer32', 'Pointer64', 'Void', 'Pass', 'Pad',

           #integers and floats
           'Bit', 'BitUInt', 'BitSInt', 'Bit1SInt',
           'BigUInt', 'BigSInt', 'Big1SInt',
           'UInt8', 'UInt16', 'UInt24', 'UInt32', 'UInt64', 'Float',
           'SInt8', 'SInt16', 'SInt24', 'SInt32', 'SInt64', 'Double',

           #float and long int timestamps
           'TimestampUtc', 'Timestamp',

           #enumerators and booleans
           'BitEnum', 'BitBool', 'BigEnum', 'BigBool',
           'Enum8', 'Enum16', 'Enum24', 'Enum32', 'Enum64',
           'Bool8', 'Bool16', 'Bool24', 'Bool32', 'Bool64',
           
           #integers and float arrays
           'FloatArray',  'DoubleArray', 'BytesRaw',    'BytearrayRaw',
           'UInt8Array',  'SInt8Array',  'UInt16Array', 'SInt16Array',
           'UInt32Array', 'SInt32Array', 'UInt64Array', 'SInt64Array',

           #strings
           'StrAscii',  'CStrAscii',  'StrRawAscii',
           'StrLatin1', 'CStrLatin1', 'StrRawLatin1',
           'StrUtf8',   'CStrUtf8',   'StrRawUtf8',
           'StrUtf16',  'CStrUtf16',  'StrRawUtf16',
           'StrUtf32',  'CStrUtf32',  'StrRawUtf32',
           
           #used for fixed length string based keywords or constants
           'StrLatin1Enum',
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

#a list containing all valid created fields
all_fields = []


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
            delimiter
            str_delimiter
        type:
            py_type
        bool:
            is_data
            is_hierarchy
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
    '''

    __slots__ = ('instantiated', 'name', 'size', 'enc', 'max', 'min',
                 'little', 'big', 'endian', 'data_type', 'py_type', '_default',
                 'is_data', 'is_str', 'is_raw', 'is_enum', 'is_bool',
                 'is_struct', 'is_array', 'is_container',
                 'is_var_size', 'is_bit_based',  'is_oe_size',
                 'str_delimiter', 'delimiter', 'is_delimited',
                 
                 '_reader', '_writer', '_decoder', '_encoder', '_sizecalc')
    
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

        #bool
        hierarchy --  Object is a form of hierarchy(struct,array,container,etc)
        data -------  Object is a form of data(as opposed to hierarchy)
        str --------  Object is a string
        raw --------  Object is unencoded raw data(ex: pixel bytes)
        enum -------  Object has a set of modes it may be set to
        bool -------  Object has a set of T/F flags that can be set
        struct -----  Object has a fixed size and attributes have offsets
        container --  Object has no fixed size and attributes have no offsets
        array ------  Object is an array of instanced elements
        varsize ----  Byte size of the object can vary(descriptor defined size)
        oesize -----  Byte size of the object cant be determined in advance
                      as it relies on some sort of delimiter(open ended)
        bitbased ---  Whether the data should be worked on a bit or byte level
        delimited --  Whether or not the string is terminated with a delimiter
                      character(the type MUST be a string)
        
        #int
        size -------  The byte size of the data when in binary form.
                      For strings this is how many bytes a single character is
        max --------  For floats/ints, this is the largest a value can be
        min --------  For floats/ints, this is the smallest a value can be
        '''

        #set the Field as editable
        self.instantiated = False
        
        #required if type is a variable
        self.size = 0 #determines how many bytes this variable always is
                      #OR how many bytes each character of a string uses
        self.enc = None
        #default endianness of the initial Field is No Endianness
        self.endian = '='
        self.little = self.big = self
        self.min    = self.max = None
        
        #required if type is a string
        self.is_delimited = False
        self.delimiter = self.str_delimiter = None

        #setup the Field's main properties
        self.name = kwargs.get("name")
        self._reader = kwargs.get("reader", self.not_imp)
        self._writer = kwargs.get("writer", self.not_imp)
        self._decoder = kwargs.get("decoder", no_decode)
        self._encoder = kwargs.get("encoder", no_encode)
        self._sizecalc = def_sizecalc
        self._default = kwargs.get("default",  None)
        self.py_type  = kwargs.get("py_type",  type(self._default))
        self.data_type = kwargs.get("data_type", type(None))

        #set the Field's flags
        self.is_data = not bool(kwargs.get("hierarchy", True))
        self.is_data = bool(kwargs.get("data", self.is_data))
        self.is_str  = bool(kwargs.get("str",  False))
        self.is_raw  = bool(kwargs.get("raw",  False))
        self.is_enum   = bool(kwargs.get("enum",   False))
        self.is_bool   = bool(kwargs.get("bool",   False))
        self.is_struct = bool(kwargs.get("struct", False))
        self.is_array  = bool(kwargs.get("array",  False))
        self.is_container = bool(kwargs.get("container", False))
        self.is_var_size  = bool(kwargs.get("varsize",  False))
        self.is_oe_size   = bool(kwargs.get("oesize",   False))
        self.is_bit_based = bool(kwargs.get("bitbased", False))
        self.is_delimited = bool(kwargs.get("delimited", False))
        
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
        if self.is_array:
            self.is_container = True
        if self.is_str or self.is_raw:
            self.is_data = self.is_var_size = True
        elif self.is_hierarchy:
            self.is_var_size = True

        
        if "endian" in kwargs:
            if kwargs.get("endian") in ('<','>','='):
                self.endian = kwargs["endian"]
            else:
                raise TypeError("Supplied endianness must be one of the "+
                                "following characters: '<', '>', or '='")

        #if the Field is a form of data, checks need to be done about
        #its properties, like its size, encoding, and encoder/decoder
        if self.is_data:
            if "size" in kwargs:
                self.size = kwargs["size"]
            else:
                if not self.is_var_size:
                    raise TypeError("Data size required for 'data' " +
                                    "fields of non variable size")

            if "enc" in kwargs:
                if isinstance(kwargs["enc"], str):
                    self.enc = kwargs["enc"]
                elif isinstance(kwargs["enc"], dict):
                    if not('<' in kwargs["enc"] and '>' in kwargs["enc"]):
                        raise TypeError("When providing endianness reliant "+
                                        "encodings, big and little endian\n"+
                                        "must both be provided under the "+
                                        "keys '>' and '<' respectively.")
                    self.enc = kwargs["enc"]['<']
                    self.endian = '<'

        if self.is_bool and self.is_enum:
            raise TypeError('A Field can not be both an enumerator '+
                            'and a set of booleans at the same time.')

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
            self._sizecalc = kwargs['sizecalc']
        elif issubclass(self.py_type, str):
            self._sizecalc = str_sizecalc
        elif issubclass(self.py_type, array):
            self._sizecalc = array_sizecalc
        elif issubclass(self.py_type, (bytearray, bytes)) or self.is_array:
            self._sizecalc = len_sizecalc
        elif self.is_var_size:
            self._sizecalc = no_sizecalc


        '''if self.data_type is not None, then it means that self._sizecalc,
        self._Encode, and self._Decode need to be wrapped in a lambda'''
        if self.data_type is not type(None):
            _sc = self._sizecalc
            _en = self._encoder
            _de = self._decoder
            
            self._sizecalc = lambda self, block, _sc=_sc, *args, **kwargs:\
                              _sc(self, block.data, *args, **kwargs)
            '''this function expects to return a constructed Block, so
            it provides the appropriate args and kwargs to the constructor'''
            self._decoder = lambda self, raw_bytes, parent, attr_index,_de=_de:\
                            self.py_type(parent.DESC[attr_index], parent,
                                         init_data = _de(self, raw_bytes,
                                                         parent, attr_index))
            """this function expects the actual value being encoded to be in
            'block' under the name 'data', so it passes the args over to the
            actual encoder function, but replaces 'block' with 'block.data'"""
            self._encoder = lambda self, block, parent, attr_index, _en=_en:\
                            _en(self, block.data, parent, attr_index)
            
        #if a default wasn't provided, try to create one from self.py_type
        if self._default is None:
            if issubclass(self.py_type, blocks.Block):
                #create a default descriptor to give to the default Block
                desc = { TYPE:self, NAME:'<UNNAMED>' }
                if self.is_hierarchy:
                    desc[ENTRIES] = 0
                    desc[NAME_MAP] = {}
                    desc[ATTR_OFFS] = []
                if self.is_enum or self.is_bool:
                    desc[ENTRIES] = 0
                    desc[NAME_MAP] = {}
                if self.is_var_size and not self.is_oe_size:
                    desc[SIZE] = 0
                if self.is_array:
                    desc[SUB_STRUCT] = {TYPE:Void, NAME:'<UNNAMED>'}
                if CHILD in self.py_type.__slots__:
                    desc[CHILD] = {TYPE:Void, NAME:'<UNNAMED>'}
                self._default = self.py_type(desc)
            else:
                try:
                    self._default = self.py_type()
                except Exception:
                    raise TypeError("Could not create Field 'default' "+
                                    "instance. You must manually supply "+
                                    "a default value.")

        #now that setup is concluded, set the object as read-only
        self.instantiated = True
        
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
            raw_data(buffer) = None
            attr_index(int, str) = None
            root_offset(int) = 0
            offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Readers unless a reader removes or changes them.
        '''
        return self._reader(self, *args, **kwargs)

    def _normal_writer(self, *args, **kwargs):
        '''
        Calls this fields writer function, passing on all args and kwargs.
        Returns the return value of this fields writer, which
        should be the offset the writer function left off at.
        
        Required arguments:
            parent(Block)
        Optional arguments:
            raw_data(buffer) = None
            attr_index(int, str) = None
            root_offset(int) = 0
            offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Writers unless a writer removes or changes them.
        '''
        
        return self._writer(self, *args, **kwargs)

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
        
        return self._decoder(self, *args, **kwargs)

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
        
        return self._encoder(self, *args, **kwargs)

    reader  = _normal_reader
    writer  = _normal_writer
    encoder = _normal_encoder
    decoder = _normal_decoder

    '''these next functions are used to force the reading/writing to
    conform to one endianness or another'''
    def _little_reader(self, *args, **kwargs):
        return self._reader(self.little, *args, **kwargs)
    def _little_writer(self, *args, **kwargs):
        return self._writer(self.little, *args, **kwargs)
    def _little_encoder(self, *args, **kwargs):
        return self._encoder(self.little, *args, **kwargs)
    def _little_decoder(self, *args, **kwargs):
        return self._decoder(self.little, *args, **kwargs)

    def _big_reader(self, *args, **kwargs):
        return self._reader(self.big, *args, **kwargs)
    def _big_writer(self, *args, **kwargs):
        return self._writer(self.big, *args, **kwargs)
    def _big_encoder(self, *args, **kwargs):
        return self._encoder(self.big, *args, **kwargs)
    def _big_decoder(self, *args, **kwargs):
        return self._decoder(self.big, *args, **kwargs)

    def __eq__(self, other):
        '''Returns whether or not an object is equivalent to this one.'''
        #returns True for the same Field, but with a different endianness
        try:
            return(isinstance(other, Field)
                   and self.name == other.name and self.enc == other.enc)
        except AttributeError:
            return False

    def __ne__(self, other):
        '''Returns whether or not an object isnt equivalent to this one.'''
        #returns False for the same Field, but with a different endianness
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
        return("< Field:'%s', endian:'%s', enc:'%s' >" %
               (self.name, self.endian, self.enc))

    def __repr__(self):
        return("< Field:'%s', endian:'%s', enc:'%s' >" %
               (self.name, self.endian, self.enc))

    '''
    To prevent editing of fields once they are instintiated, the
    default setattr and delattr methods are overloaded with these
    '''
    def __setattr__(self, attr, value):
        if hasattr(self, "instantiated") and self.instantiated:
            raise AttributeError("fields are read-only and may "+
                                 "not be changed once created.")
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr, value):
        if hasattr(self, "instantiated") and self.instantiated:
            raise AttributeError("fields are read-only and may "+
                                 "not be changed once created.")
        object.__delattr__(self, attr)

    @property
    def is_hierarchy(self):
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
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the little
        endian version of the Field(if it exists).'''
        self.reader  = Field._little_reader
        self.writer  = Field._little_writer
        self.encoder = Field._little_encoder
        self.decoder = Field._little_decoder

    def force_big(self=None):
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that force them to use the big
        endian version of the Field(if it exists).'''
        self.reader  = Field._big_reader
        self.writer  = Field._big_writer
        self.encoder = Field._big_encoder
        self.decoder = Field._big_decoder

    def force_normal(self=None):
        '''Replaces the Field class's reader, writer, encoder,
        and decoder with methods that do not force them to use an
        endianness other than the one they are currently set to.'''
        self.reader  = Field._normal_reader
        self.writer  = Field._normal_writer
        self.encoder = Field._normal_encoder
        self.decoder = Field._normal_decoder

    def sizecalc(self, *args, **kwargs):
        '''A redirect that provides 'self' as
        an arg to the actual sizecalc function.'''
        return self._sizecalc(self, *args, **kwargs)

    def not_imp(self, *args, **kwargs):
        raise NotImplementedError(("This operation not implemented in %s "+
                                   "Field.") % self.name)


#Now that the Field has been defined, we're gonna
#do something that may seem hacky, but will prevent
#an "if else" setup in each of the Force functions.
Field.force_big.__defaults__ = (Field,)
Field.force_little.__defaults__ = (Field,)
Field.force_normal.__defaults__ = (Field,)


Void = Field( name="Void", data=True, size=0, py_type=blocks.VoidBlock,
              reader=void_reader, writer=void_writer)
Pad = Field( name="Pad", data=True, varsize=True, py_type=blocks.VoidBlock,
             reader=no_read, writer=no_write)
Pass = Field( name="Pass", data=True, size=0, py_type=blocks.VoidBlock,
              reader=no_read, writer=no_write)
Container = Field( name="Container", container=True, py_type=blocks.ListBlock,
                   reader=container_reader, writer=container_writer)
Struct = Field( name="Struct", struct=True, py_type=blocks.ListBlock,
                reader=struct_reader, writer=struct_writer)
Array = Field( name="Array", array=True, py_type=blocks.ListBlock,
               reader=array_reader, writer=array_writer)
WhileArray = Field( name="WhileArray", array=True, py_type=blocks.WhileBlock,
                    reader=while_array_reader, writer=array_writer)
Switch = Field( name='Switch', hierarchy=True, size=0, py_type=blocks.VoidBlock,
                reader=switch_reader, writer=void_writer)

#Bitbased data
'''When within a BitStruct, offsets and sizes are in bits instead of bytes.
BitStruct sizes MUST BE SPECIFIED IN WHOLE BYTE AMOUNTS(1byte, 2bytes, etc)'''
BitStruct = Field( name="BitStruct", struct=True, bitbased=True,
                   py_type=blocks.ListBlock,
                   reader=bit_struct_reader, writer=bit_struct_writer)
'''For when you dont need multiple bits. It's faster and
easier to use this than a BitUInt with a size of 1.'''
Bit = Field( name="Bit", data=True, bitbased=True,
             size=1, enc='U', default=0, reader=default_reader,
             decoder=decode_bit, encoder=encode_bit)

'''There is no reader or writer for Bit_Ints because the BitStruct handles
getting and combining the Bit_Ints together to ensure proper endianness'''
tmp = {'data':True, 'varsize':True, 'bitbased':True,
       'sizecalc':bit_uint_sizecalc, "default":0, "enc":"U",
       'reader':default_reader,#needs a reader so default values can be set
       'decoder':decode_bit_int, 'encoder':encode_bit_int}
com = combine
'''UInt, sInt, and SInt MUST be in a BitStruct as the BitStruct
acts as a bridge between byte level and bit level objects.
Bit1SInt is signed in 1's compliment and BitSInt is in 2's compliment.'''
BitSInt = Field(**com({"name":"BitSInt", "enc":"S",
                       'sizecalc':bit_sint_sizecalc },tmp))
Bit1SInt = Field(**com({"name":"Bit1SInt", "enc":"s",
                        'sizecalc':bit_1sint_sizecalc },tmp))
BitUInt = Field(**com({"name":"BitUInt"},tmp))
BitEnum = Field(**com({"name":"BitEnum", 'enum':True,
                       'default':None, 'data_type':int,
                       'py_type':blocks.EnumBlock },tmp))
BitBool = Field(**com({"name":"BitBool", 'bool':True,
                       'default':None, 'data_type':int,
                       'py_type':blocks.BoolBlock },tmp))

#Pointers, Integers, and Floats
tmp['bitbased'], tmp['sizecalc'] = False, big_uint_sizecalc
tmp["reader"], tmp["writer"] = data_reader, data_writer
tmp["decoder"], tmp["encoder"] = decode_big_int, encode_big_int

BigSInt = Field(**com({"name":"BigSInt", 'sizecalc':big_sint_sizecalc,
                       "enc":{'<':"<S",'>':">S"}},tmp))
Big1SInt = Field(**com({"name":"Big1SInt", 'sizecalc':big_1sint_sizecalc,
                        "enc":{'<':"<s",'>':">s"}},tmp))
tmp['enc'] = {'<':"<U",'>':">U"}
BigUInt = Field(**com({"name":"BigUInt"},tmp))
BigEnum = Field(**com({"name":"BigEnum", 'enum':True, 'default':None,
                       'py_type':blocks.EnumBlock,'data_type':int},tmp))
BigBool = Field(**com({"name":"BigBool", 'bool':True, 'default':None,
                       'py_type':blocks.BoolBlock,'data_type':int},tmp))

tmp['varsize'], tmp['sizecalc'] = False, def_sizecalc
tmp['decoder'], tmp['encoder'] = decode_numeric, encode_numeric
tmp['reader'] = f_s_data_reader

Pointer32 = Field(**com({"name":"Pointer32", "size":4,
                         'min':0, 'max':4294967295,
                         "enc":{'<':"<I",'>':">I"}}, tmp))
Pointer64 = Field(**com({"name":"Pointer64", "size":8,
                         'min':0, 'max':18446744073709551615,
                         "enc":{'<':"<Q",'>':">Q"}}, tmp))

tmp['size'], tmp['min'], tmp['max'], tmp['enc'] = 1, 0, 255, 'B'
UInt8 = Field(**com({"name":"UInt8"},tmp))
Enum8 = Field(**com({"name":"Enum8", 'enum':True, 'default':None,
                     'py_type':blocks.EnumBlock,'data_type':int},tmp))
Bool8 = Field(**com({"name":"Bool8", 'bool':True, 'default':None,
                     'py_type':blocks.BoolBlock,'data_type':int},tmp))
tmp['size'], tmp['max'], tmp['enc'] = 2, 2**16-1, {'<':"<H",'>':">H"}
UInt16 = Field(**com({"name":"UInt16"}, tmp))
Enum16 = Field(**com({"name":"Enum16", 'enum':True, 'default':None,
                      'py_type':blocks.EnumBlock,'data_type':int},tmp))
Bool16 = Field(**com({"name":"Bool16", 'bool':True, 'default':None,
                      'py_type':blocks.BoolBlock,'data_type':int},tmp))

tmp['size'], tmp['max'], tmp['enc'] = 4, 2**32-1, {'<':"<I",'>':">I"}
UInt32 = Field(**com({"name":"UInt32"}, tmp))
Enum32 = Field(**com({"name":"Enum32", 'enum':True, 'default':None,
                      'py_type':blocks.EnumBlock,'data_type':int},tmp))
Bool32 = Field(**com({"name":"Bool32", 'bool':True, 'default':None,
                      'py_type':blocks.BoolBlock,'data_type':int},tmp))

tmp['size'], tmp['max'], tmp['enc'] = 8, 2**64-1, {'<':"<Q",'>':">Q"}
UInt64 = Field(**com({"name":"UInt64"}, tmp))
Enum64 = Field(**com({"name":"Enum64", 'enum':True, 'default':None,
                      'py_type':blocks.EnumBlock,'data_type':int},tmp))
Bool64 = Field(**com({"name":"Bool64", 'bool':True, 'default':None,
                      'py_type':blocks.BoolBlock,'data_type':int},tmp))

SInt8 = Field(**com({"name":"SInt8", "size":1, "enc":{'<':"<b",'>':">b"},
                     'min':-128, 'max':127}, tmp))
SInt16 = Field(**com({"name":"SInt16", "size":2, "enc":{'<':"<h",'>':">h"},
                      'min':-32768, 'max':32767 }, tmp))
SInt32 = Field(**com({"name":"SInt32", "size":4, "enc":{'<':"<i",'>':">i"},
                      'min':-2147483648, 'max':2147483647 }, tmp))
SInt64 = Field(**com({"name":"SInt64", "size":8, "enc":{'<':"<q",'>':">q"},
                      'min':-2**63, 'max':2**63-1 }, tmp))

tmp["default"] = 0.0
Float = Field(**com({"name":"Float", "size":4, "enc":{'<':"<f",'>':">f"},
                     "max":unpack('>f',b'\x7f\x7f\xff\xff'),
                     "min":unpack('>f',b'\xff\x7f\xff\xff') }, tmp))
Double = Field(**com({"name":"Double", "size":8, "enc":{'<':"<d",'>':">d"},
                      "max":unpack('>d',b'\x7f\xef'+b'\xff'*6),
                      "min":unpack('>d',b'\xff\xef'+b'\xff'*6)}, tmp))

#24 bit integers
tmp['decoder'], tmp['encoder'] = decode_24bit_numeric, encode_24bit_numeric
tmp['size'], tmp['max'], tmp['enc'] = 3, 2**24-1, {'<':"<I",'>':">I"}
UInt24 = Field(**com({"name":"UInt24", "default":0}, tmp))
Enum24 = Field(**com({"name":"Enum24", 'enum':True, 'default':None,
                      'py_type':blocks.EnumBlock, 'data_type':int,
                      'reader':f_s_data_reader, "default":0}, tmp))
Bool24 = Field(**com({"name":"Bool24", 'bool':True, 'default':None,
                      'py_type':blocks.BoolBlock, 'data_type':int,
                      'reader':f_s_data_reader, "default":0}, tmp))
SInt24 = Field(**com({"name":"SInt24", "size":3, "enc":{'<':"<i",'>':">i"},
                      'min':-8388608, 'max':8388607, "default":0 }, tmp))


tmp["py_type"], tmp["default"] = str, lambda *a, **kwa:ctime(time())
tmp["decoder"], tmp["encoder"], tmp["size"] = decode_timestamp,encode_numeric,4
tmp["min"], tmp["max"] = 'Wed Dec 31 19:00:00 1969', 'Thu Jan  1 02:59:59 3001' 
TimestampUtc = Field(**com({"name":"TimestampUtc",
                            "enc":{'<':"<f",'>':">f"},
                            "encoder":encode_float_timestamp},tmp))
Timestamp = Field(**com({"name":"Timestamp", "enc":{'<':"<I",'>':">I"},
                         "encoder":encode_int_timestamp},tmp))

tmp = {'varsize':True, 'raw':True, 'sizecalc':array_sizecalc,
       'reader':py_array_reader, 'writer':py_array_writer,'min':None,'max':None}

#Arrays
UInt8Array = Field(**com({"name":"UInt8Array", "size":1,
                          "default":array("B", []), "enc":"B"}, tmp))
SInt8Array = Field(**com({"name":"SInt8Array", "size":1,
                          "default":array("b", []), "enc":"b"}, tmp))
UInt16Array = Field(**com({"name":"UInt16Array", "size":2,
                           "default":array("H", []),
                           "enc":{"<":"H",">":"H"}}, tmp))
SInt16Array = Field(**com({"name":"SInt16Array", "size":2,
                           "default":array("h", []),
                           "enc":{"<":"h",">":"h"}}, tmp))
UInt32Array = Field(**com({"name":"UInt32Array", "size":4,
                           "default":array("I", []),
                           "enc":{"<":"I",">":"I"}}, tmp))
SInt32Array = Field(**com({"name":"SInt32Array", "size":4,
                           "default":array("i", []),
                           "enc":{"<":"i",">":"i"}}, tmp))
UInt64Array = Field(**com({"name":"UInt64Array", "size":8,
                           "default":array("Q", []),
                           "enc":{"<":"Q",">":"Q"}}, tmp))
SInt64Array = Field(**com({"name":"SInt64Array", "size":8,
                           "default":array("q", []),
                           "enc":{"<":"q",">":"q"}}, tmp))

FloatArray = Field(**com({"name":"FloatArray", "size":4,
                          "default":array("f", []),
                          "enc":{"<":"f",">":"f"}}, tmp))
DoubleArray = Field(**com({"name":"DoubleArray", "size":8,
                           "default":array("d", []),
                           "enc":{"<":"d",">":"d"}}, tmp))

tmp['raw'] = tmp['varsize'] = True
tmp['sizecalc'] = len_sizecalc
tmp['reader'], tmp['writer'] = bytes_reader, bytes_writer


BytesRaw = Field(**com({'name':"Bytes", 'default':BytesBuffer()}, tmp))
BytearrayRaw = Field(**com({'name':"Bytearray",
                            'default':BytearrayBuffer()}, tmp))


#Strings
tmp = {'str':True, 'default':'', 'delimited':True,
       'reader':data_reader, 'writer':data_writer,
       'decoder':decode_string, 'encoder':encode_string,
       'sizecalc':delim_str_sizecalc, 'size':1}

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

#these are where all the single byte, less common encodings
#are located for Strings, CStrings, and raw Strings
str_fields = {}
cstr_fields = {}
str_raw_fields = {}


for enc in other_enc:
    str_fields[enc] = Field(**com({'name':"Str"+enc, 'enc':enc},tmp))
    
StrAscii  = Field(**com({'name':"StrAscii",  'enc':'ascii'}, tmp) )
StrLatin1 = Field(**com({'name':"StrLatin1", 'enc':'latin1'}, tmp) )
StrUtf8   = Field(**com({'name':"StrUtf8",   'enc':'utf8',
                               'sizecalc':delim_utf_sizecalc},tmp))

StrUtf16 = Field(**com({'name':"StrUtf16", 'size':2,
                              'sizecalc':delim_utf_sizecalc,
                              'enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
StrUtf32 = Field(**com({'name':"StrUtf32", 'size':4,
                              'enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#Null terminated strings
tmp['oesize'] = True
tmp['reader'], tmp['writer'] = cstring_reader, cstring_writer

for enc in other_enc:
    name = "CStr"+enc
    cstr_fields[enc] = Field(**com({'name':name,'enc':enc},tmp))

CStrAscii  = Field(**com({'name':"CStrAscii", 'enc':'ascii'}, tmp))
CStrLatin1 = Field(**com({'name':"CStrLatin1", 'enc':'latin1'}, tmp))
CStrUtf8   = Field(**com({'name':"CStrUtf8", 'enc':'utf8',
                                'sizecalc':delim_utf_sizecalc},tmp))
CStrUtf16  = Field(**com({'name':"CStrUtf16", 'size':2,
                                'sizecalc':delim_utf_sizecalc,
                                'enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
CStrUtf32  = Field(**com({'name':"CStrUtf32", 'size':4,
                                'enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#raw strings
'''raw strings are different in that they ARE NOT expected to
have a delimiter. A fixed length string can have all characters
used and not require a delimiter character to be on the end.'''
tmp['oesize'],  tmp['delimited'], tmp['sizecalc'] = False, False, str_sizecalc
tmp['reader'],  tmp['writer']  = data_reader, data_writer
tmp['decoder'], tmp['encoder'] = decode_string, encode_raw_string

for enc in other_enc:
    str_raw_fields[enc] = Field(**com({'name':"Str_Raw_"+enc,
                                                 'enc':enc},tmp))

StrRawAscii  = Field(**com({'name':"StrRawAscii",'enc':'ascii'},tmp))
StrRawLatin1 = Field(**com({'name':"StrRawLatin1",'enc':'latin1'},tmp))
StrRawUtf8   = Field(**com({'name':"StrRawUtf8", 'enc':'utf8',
                                   'sizecalc':utf_sizecalc}, tmp))
StrRawUtf16 = Field(**com({'name':"StrRawUtf16", 'size':2,
                                  'sizecalc':utf_sizecalc,
                                  'enc':{"<":"utf_16_le",">":"utf_16_be"}},tmp))
StrRawUtf32 = Field(**com({'name':"StrRawUtf32", 'size':4,
                                  'enc':{"<":"utf_32_le",">":"utf_32_be"}},tmp))

#used for places in a file where a string is used as an enumerator
#to represent a setting in a file (a 4 character code for example)
StrLatin1Enum = Field(**com({'name':"StrLatin1Enum", 'enc':'latin1',
                                    'py_type':blocks.EnumBlock,
                                    'enum':True,'data_type':str},tmp))

#little bit of cleanup
del tmp
del other_enc
del com
