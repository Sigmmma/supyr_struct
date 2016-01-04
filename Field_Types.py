'''
A collection of common and flexible binary Field_Types and their base class.

Field_Types are a read-only description of how to handle a certain type
of binary data. They define functions for reading and writing the data
to and from a buffer, encoding and decoding the data(if applicable),
a function to calculate the byte size of the data, and several properties
which determine how the data should be treated.

If certain data needs to be handeled in a way currently not supported, then
custom Field_Types can be created with customized properties and functions.
'''

__all__ = [#size calculation functions
           'No_Size_Calc', 'Default_Size_Calc',
           'Str_Size_Calc', 'Str_Size_Calc_UTF',
           'Array_Size_Calc', 'Len_Size_Calc',
           'Big_SInt_Size_Calc', 'Big_sInt_Size_Calc', 'Big_UInt_Size_Calc',
           'Bit_SInt_Size_Calc', 'Bit_sInt_Size_Calc', 'Bit_UInt_Size_Calc',

           #########################################
           #  collections of specific Field_Types  #
           #########################################
           
           'Field_Type', 'All_Field_Types',
           'Str_Field_Types', 'CStr_Field_Types', 'Str_Raw_Field_Types',

           #hierarchy and structure
           'Container', 'Struct', 'Array', 'Bit_Struct', 'Switch',
           'Pointer32', 'Pointer64', 'Void',

           #integers and floats
           'Bit_UInt', 'Bit_SInt', 'Bit_sInt',
           'Big_UInt', 'Big_SInt', 'Big_sInt',
           'UInt8', 'UInt16', 'UInt24', 'UInt32', 'UInt64', 'Float',
           'SInt8', 'SInt16', 'SInt24', 'SInt32', 'SInt64', 'Double',

           #float and long int timestamps
           'UTC_Timestamp', 'Timestamp',

           #enumerators and booleans
           'Bit_Enum', 'Bit_Bool', 'Big_Enum', 'Big_Bool',
           'Enum8', 'Enum16', 'Enum24', 'Enum32', 'Enum64',
           'Bool8', 'Bool16', 'Bool24', 'Bool32', 'Bool64',
           
           #integers and float arrays
           'Float_Array',  'Double_Array', 'Bytes_Raw',    'Bytearray_Raw',
           'UInt8_Array',  'SInt8_Array',  'UInt16_Array', 'SInt16_Array',
           'UInt32_Array', 'SInt32_Array', 'UInt64_Array', 'SInt64_Array',

           #strings
           'Str_ASCII',  'CStr_ASCII',  'Str_Raw_ASCII',
           'Str_Latin1', 'CStr_Latin1', 'Str_Raw_Latin1',
           'Str_UTF8',   'CStr_UTF8',   'Str_Raw_UTF8',
           'Str_UTF16',  'CStr_UTF16',  'Str_Raw_UTF16',
           'Str_UTF32',  'CStr_UTF32',  'Str_Raw_UTF32',
           
           #used for fixed length string based keywords or constants
           'Str_Latin1_Enum']
import sys

from copy import deepcopy
from math import log, ceil
from struct import unpack
from time import time, ctime
from types import FunctionType

from supyr_struct.Re_Wr_De_En import *
try:
    from supyr_struct import Tag_Blocks
    Tag_Blocks.Field_Types = sys.modules[__name__]
except ImportError:
    pass

#a list containing all valid created Field_Types
All_Field_Types = []


def No_Size_Calc(self, Block=None, **kwargs):
    '''
    If a Size_Calc routine wasnt provided for this
    Field_Type and one can't be decided upon as a
    default, then the size can't be calculated.
    Returns 0 when called
    '''
    
    return 0

def Default_Size_Calc(self, Block=None, **kwargs):
    '''
    Returns the byte size specified by the Field_Type.
    Only used if the self.Var_Size == False.
    '''
    
    return self.Size

def Delim_Str_Size_Calc(self, Block, **kwargs):
    '''
    Returns the byte size of a delimited string if it were converted to bytes.
    '''
    #dont add the delimiter size if the string is already delimited
    if Block.endswith(self.Str_Delimiter):
        return len(Block) * self.Size
    return (len(Block)+1) * self.Size

def Str_Size_Calc(self, Block, **kwargs):
    '''
    Returns the byte size of a string if it were converted to bytes.
    '''
    return len(Block)*self.Size

def Str_Size_Calc_UTF(self, Block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were converted to bytes.
    This function is potentially slower than the above one, but is
    necessary to get an accurate byte length for UTF8/16 strings.
    
    This should only be used for UTF8 and UTF16. 
    '''
    #return the length of the entire string of bytes
    return len(Block.encode(encoding=self.Enc))

def Delim_Str_Size_Calc_UTF(self, Block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were converted to bytes.
    This function is potentially slower than the above one, but is
    necessary to get an accurate byte length for UTF8/16 strings.
    
    This should only be used for UTF8 and UTF16. 
    '''
    Block_Len = len(Block.encode(encoding=self.Enc))
    
    #dont add the delimiter size if the string is already delimited
    if Block.endswith(self.Str_Delimiter):
        return Block_Len
    return Block_Len + self.Size

    
def Array_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the byte size of an array if it were converted to bytes.
    '''
    
    return len(Block)*Block.itemsize
    
def Big_sInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent a ones signed integer
    '''
    #ones compliment
    return int(ceil( (log(abs(Block)+1,2)+1.0)/8.0 ))
    
def Big_SInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent a twos signed integer
    '''
    #twos compliment
    if Block >= 0:
        return int(ceil( (log(Block+1,2)+1.0)/8.0 ))
    else:
        return int(ceil( (log(0-Block,2)+1.0)/8.0 ))
    
def Big_UInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent an unsigned integer
    '''
    return int(ceil( log(abs(Block)+1,2)/8.0 ))
    
def Bit_sInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    
    #ones compliment
    return int(ceil( log(abs(Block)+1,2)+1.0 ))
    
def Bit_SInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    
    #twos compliment
    if Block >= 0:
        return int(ceil( log(Block+1,2)+1.0 ))
    else:
        return int(ceil( log(0-Block,2)+1.0 ))
    
def Bit_UInt_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    
    #unsigned
    return int(ceil( log(abs(Block)+1,2) ))
    
def Len_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the byte size of an object whose length is its
    size if it were converted to bytes(bytes, bytearray).
    '''
    
    return len(Block)


def Val_Size_Wrapper(self, Block, Size_Calc, *args, **kwargs):
    '''
    A wrapper function for calculating the size of blocks which
    store their actual value as an attribute called Val
    '''
    return Size_Calc(self, Block.Val, *args, **kwargs)



class Field_Type():
    '''
    A read-only description of how to handle a certain type of binary data.
    
    Field_Types define functions for reading/writing the data to/from a buffer,
    encoding/decoding the data(if applicable), an optional function to
    calculate the byte size of the data, and numerous other properties
    which determine how the data should be treated.
    
    Each Field_Type contains a dictionary of references to each of the other
    endiannesses of that same Field_Type. Calling a Field_Type with one of the
    following characters "<>" will return that type with that endianness.
    Field_Types should never be duplicated as they are read-only descriptions
    of how to handle data. Copying will instead return the supplied Field_Type.

    Read this classes __init__.__doc__ for descriptions of these properties.
    
    Object Properties:
        int:
            Size
            Min
            Max
        str:
            Name
            Enc
            Delimiter
            Str_Delimiter
        type:
            Py_Type
        bool:
            Is_Data
            Is_Hierarchy
            Is_Str
            Is_Raw
            Is_Enum
            Is_Bool
            Is_Struct
            Is_Array
            Is_Container
            Is_Var_Size
            Is_Bit_Based
            Is_Delimited
            
    Object Methods:
        Default(*args, **kwargs)
        Reader(*args, **kwargs)
        Writer(*args, **kwargs)
        Encoder(*args, **kwargs)
        Decoder(*args, **kwargs)
        Size_Calc(*args, **kwargs)
    '''

    __slots__ = ('Instantiated', 'Name', 'Size', 'Enc', 'Max', 'Min',
                 'Little', 'Big', 'Endian', 'Val_Type', 'Py_Type', '_Default',
                 'Is_Data', 'Is_Str', 'Is_Raw', 'Is_Enum', 'Is_Bool',
                 'Is_Struct', 'Is_Array', 'Is_Container',
                 'Is_Var_Size', 'Is_Bit_Based',  'Is_OE_Size',
                 'Str_Delimiter', 'Delimiter', 'Is_Delimited',
                 
                 '_Reader', '_Writer', '_Decoder', '_Encoder', '_Size_Calc')
    
    def __init__(self, **kwargs):
        '''
        Initializes a Field_Type with the supplied keyword arguments.
        Raises TypeError if invalid keyword combinations are provided.
        
        Keyword arguments:

        #object
        Default ----  A python object to copy as the default value. If the
                      supplied value is a python 'type' object which is a
                      sub-class of Tag_Block then the supplied 'Default'
                      will be called with this Field_Type(self) supplied as
                      the 'Type' keyword. This is the only way to use any
                      Tag_Block as a Default since they cannot be created
                      without either a descriptor or a Field_Type and
                      Field_Types cannot be edited.
        #type
        Py_Type ----  The python type associated with this Field_Type.
                      The type of 'Default' will be used if one isnt provided.
                      (mainly used for verifying if a different python object
                      is a valid type to replace a previous value with)
        
        #str
        Name ----------  The name of this Field_Type
        Delimiter -----  The delimiter in its encoded, bytes form(for strings)
        Str_Delimiter -  The delimiter in its decoded, python form(for strings)
        Enc -----------  A string used to specify the format for encoding and
                         decoding the data. This string is required for non-raw
                         "Data" Field_Types, but there is no set convention as
                         it depends on what the de/encode function accepts.

                         For example, Enc would be any one character in
                         'bhiqfBHIQD' for numbers de/encoded by pythons
                         struct module, whereas Str_UTF_16_LE and Str_Latin_1
                         use "UTF_16_LE" and "latin-1" respectively.
        Endian --------  The endianness of this Field_Type
        

        #function
        Reader -----  A function for reading the bytes data from a buffer.
                      Also handles calling of the reader of any structures or
                      containers within it (including its child if it has one)
        Writer -----  A function for writing the object as binary data to a
                      buffer. Also handles calling of the writer of any
                      structures or containers within it.
        Decoder ----  A function for decoding bytes data from a buffer into a
                      python object(ex: convert b'\xD1\x22\xAB\x3F' to a float)
        Encoder ----  A function for encoding the python object into a writable
                      bytes form(ex: convert "test" into b'\x74\x65\x73\x74')
        Size_Calc --  An optional function for calculating how large the object
                      would be if written to a buffer. Most of the time this
                      isn't needed, but for variable length data(strings whose
                      lengths are determined by some previously parsed field)
                      the size will need to properly calculated after an edit.

        #bool
        Hierarchy --  Object is a form of hierarchy(struct,array,container,etc)
        Data -------  Object is a form of data(as opposed to hierarchy)
        Str --------  Object is a string
        Raw --------  Object is unencoded raw data(ex: pixel bytes)
        Enum -------  Object has a set of modes it may be set to
        Bool -------  Object has a set of T/F flags that can be set
        Struct -----  Object has a fixed size and attributes have offsets
        Container --  Object has no fixed size and attributes have no offsets
        Array ------  Object is an array of instanced elements
        Var_Size ---  Byte size of the object can vary(descriptor defined size)
        OE_Size ----  Byte size of the object cant be determined in advance
                      as it relies on some sort of delimiter(open ended)
        Bit_Based --  Whether the data should be worked on a bit or byte level
        Delimited --  Whether or not the string is terminated with a delimiter
                      character(the type MUST be a string)
        
        #int
        Size -------  The byte size of the data when in binary form.
                      For strings this is how many bytes a single character is
        Max --------  For floats/ints, this is the largest a value can be
        Min --------  For floats/ints, this is the smallest a value can be
        '''

        #set the Field_Type as editable
        self.Instantiated = False
        
        #required if type is a variable
        self.Size = 0 #determines how many bytes this variable always is
                      #OR how many bytes each character of a string uses
        self.Enc = ''
        #default endianness of the initial Field_Type is 'little'
        self.Endian = '<'
        self.Little = self.Big = self
        self.Min    = self.Max = None
        
        #required if type is a string
        self.Is_Delimited = False
        self.Delimiter = self.Str_Delimiter = None

        #setup the Field_Type's main properties
        self.Name = kwargs.get("Name")
        self._Reader = kwargs.get("Reader", self.NotImp)
        self._Writer = kwargs.get("Writer", self.NotImp)
        self._Decoder = kwargs.get("Decoder", self.NotImp)
        self._Encoder = kwargs.get("Encoder", self.NotImp)
        self._Size_Calc = Default_Size_Calc
        self._Default = kwargs.get("Default",  None)
        self.Py_Type  = kwargs.get("Py_Type",  type(self._Default))
        self.Val_Type = kwargs.get("Val_Type", None)

        #set the Field_Type's flags
        self.Is_Data = not bool(kwargs.get("Hierarchy", True))
        self.Is_Data = bool(kwargs.get("Data", self.Is_Data))
        self.Is_Str  = bool(kwargs.get("Str",  False))
        self.Is_Raw  = bool(kwargs.get("Raw",  False))
        self.Is_Enum   = bool(kwargs.get("Enum",   False))
        self.Is_Bool   = bool(kwargs.get("Bool",   False))
        self.Is_Struct = bool(kwargs.get("Struct", False))
        self.Is_Array  = bool(kwargs.get("Array",  False))
        self.Is_Container = bool(kwargs.get("Container", False))
        self.Is_Var_Size  = bool(kwargs.get("Var_Size",  False))
        self.Is_OE_Size   = bool(kwargs.get("OE_Size",   False))
        self.Is_Bit_Based = bool(kwargs.get("Bit_Based", False))
        self.Is_Delimited = bool(kwargs.get("Delimited", False))
        
        if self.Name is None:
            raise TypeError("'Name' is a required identifier for data types.")

        '''Some assumptions are made based on the flags provided. Fill in the
        rest of the flags that must be true, even if they werent provided'''
        if self.Is_Str:
            if "Delimiter" in kwargs:
                self.Delimiter = kwargs["Delimiter"]
            elif "Size" in kwargs:
                #if the delimiter isnt specified, assume it's 0x00*Size
                self.Delimiter = b'\x00' * int(kwargs["Size"])
                
            self.Str_Delimiter = kwargs.get("Str_Delimiter",self.Str_Delimiter)
        if self.Is_Array:
            self.Is_Container = True
        if self.Is_Str or self.Is_Raw:
            self.Is_Data = self.Is_Var_Size = True
        elif self.Is_Hierarchy:
            self.Is_Var_Size = True

        
        if "Endian" in kwargs:
            if kwargs.get("Endian") in ('<','>','='):
                self.Endian = kwargs["Endian"]
            else:
                raise TypeError("Supplied endianness must be one of the "+
                                "following characters: '<', '>', or '='")

        #if the Field_Type is a form of data, checks need to be done about
        #its properties, like its size, encoding, and encoder/decoder
        if self.Is_Data:
            if "Size" in kwargs:
                self.Size = kwargs["Size"]
            else:
                if not self.Is_Var_Size:
                    raise TypeError("Data size required for 'Data' " +
                                    "Field_Types of non variable size")

            if "Enc" in kwargs:
                if isinstance(kwargs["Enc"], str):
                    self.Enc = kwargs["Enc"]
                elif isinstance(kwargs["Enc"], dict):
                    if not('<' in kwargs["Enc"] and '>' in kwargs["Enc"]):
                        raise TypeError("When providing endianness reliant "+
                                        "encodings, big and little endian\n"+
                                        "must both be provided under the "+
                                        "keys '>' and '<' respectively.")
                    self.Enc = kwargs["Enc"]['<']

        if self.Is_Bool and self.Is_Enum:
            raise TypeError('A Field_Type can not be both an enumerator '+
                            'and a set of booleans at the same time.')

        Other_Endian = kwargs.get('Other_Endian')

        '''if the endianness is specified as '=' it means that
        endianness has no meaning for this Field_Type and that
        Big and Little should be the same. Otherwise, create a
        similar Field_Type, but with an opposite endianness'''
        if self.Endian != "=" and Other_Endian is None:
            #set the endianness kwarg to the opposite of this one
            kwargs["Endian"] = {'<':'>','>':'<'}[self.Endian]
            kwargs["Other_Endian"] = self
            
            #if the provided Enc kwarg is a dict, get the encoding
            #of the endianness opposite the current Field_Type.
            if 'Enc' in kwargs and isinstance(kwargs["Enc"], dict):
                kwargs["Enc"] = kwargs["Enc"][kwargs["Endian"]]
            else:
                kwargs["Enc"] = self.Enc
                
            #create the other endian Field_Type
            Other_Endian = Field_Type(**kwargs)

        #set the other endianness Field_Type
        if self.Endian == '<':
            self.Big = Other_Endian
        elif self.Endian == '>':
            self.Little = Other_Endian
            
        self.Min = kwargs.get("Min", self.Min)
        self.Max = kwargs.get("Max", self.Max)
        
        if self.Str_Delimiter is not None and self.Delimiter is None:
            self.Delimiter = self.Str_Delimiter.encode(encoding=self.Enc)
        if self.Delimiter is not None and self.Str_Delimiter is None:
            self.Str_Delimiter = self.Delimiter.decode(encoding=self.Enc)

        '''Decide on a Size_Calc method to use based on the
        data type or use the one provided, if provided'''
        if "Size_Calc" in kwargs:
            self._Size_Calc = kwargs['Size_Calc']
        elif issubclass(self.Py_Type, str):
            self._Size_Calc = Str_Size_Calc
        elif issubclass(self.Py_Type, array):
            self._Size_Calc = Array_Size_Calc
        elif issubclass(self.Py_Type, (bytearray, bytes)) or self.Is_Array:
            self._Size_Calc = Len_Size_Calc
        elif self.Is_Var_Size:
            self._Size_Calc = No_Size_Calc


        '''if self.Val_Type is not None, then it means that self._Size_Calc,
        self._Encode, and self._Decode need to be wrapped in a lambda'''
        if self.Val_Type is not None:
            _Sc = self._Size_Calc
            _En = self._Encoder
            _De = self._Decoder
            
            self._Size_Calc = lambda self, Block, _Sc=_Sc, *args, **kwargs:\
                              _Sc(self, Block.Val, *args, **kwargs)
            '''this function expects to return a constructed Tag_Block, so
            it provides the appropriate args and kwargs to the constructor'''
            self._Decoder = lambda self, Bytes, Parent, Attr_Index, _De=_De:\
                            self.Py_Type(Parent.DESC[Attr_Index], Parent,
                                         Init_Data = _De(self, Bytes,
                                                         Parent, Attr_Index))
            """this function expects the actual value being encoded to be in
            'Block' under the name 'Val', so it passes the args over to the
            actual encoder function, but replaces 'Block' with 'Block.Val'"""
            self._Encoder = lambda self, Block, Parent, Attr_Index, _En=_En:\
                            _En(self, Block.Val, Parent, Attr_Index)
            
        #if a default wasn't provided, try to create one from self.Py_Type
        if self._Default is None:
            if issubclass(self.Py_Type, Tag_Blocks.Tag_Block):
                #create a default descriptor to give to the default Tag_Block
                Desc = { TYPE:self, NAME:'<UNNAMED>' }
                if self.Is_Hierarchy:
                    Desc[ENTRIES] = 0
                    Desc[NAME_MAP] = {}
                    Desc[ATTR_OFFS] = {}
                if self.Is_Enum or self.Is_Bool:
                    Desc[ENTRIES] = 0
                    Desc[NAME_MAP] = {}
                if self.Is_Var_Size:
                    Desc[SIZE] = 0
                if self.Is_Array:
                    Desc[SUB_STRUCT] = {TYPE:Void, NAME:'<UNNAMED>'}
                if CHILD in self.Py_Type.__slots__:
                    Desc[CHILD] = {TYPE:Void, NAME:'<UNNAMED>'}
                self._Default = self.Py_Type(Desc)
            else:
                try:
                    self._Default = self.Py_Type()
                except Exception:
                    raise TypeError("Could not create Field_Type 'Default' "+
                                    "instance. You must manually supply "+
                                    "a Default value.")

        #now that setup is concluded, set the object as read-only
        self.Instantiated = True
        
        #add this to the collection of all field types
        All_Field_Types.append(self)


    @property
    def Is_Hierarchy(self):
        return not self.Is_Data


    def Default(self, *args, **kwargs):
        '''
        Returns a deepcopy of the python object associated with this
        Field_Type. If self._Default is a function it instead passes
        args and kwargs over and returns what is returned to it.
        '''
        if isinstance(self._Default, FunctionType):
            return self._Default(*args, **kwargs)
        return deepcopy(self._Default)


    '''these functions are just alias's and are done this way so
    that this class can pass itself as a reference manually'''
    def Reader(self, *args, **kwargs):
        '''
        Calls this Field_Types Reader function, passing on all args and kwargs.
        Returns the return value of this Field_Types Reader, which
        should be the offset the Reader function left off at.
        
        Required arguments:
            Parent(Tag_Block)
        Optional arguments:
            Raw_Data(buffer) = None
            Attr_Index(int, str) = None
            Root_Offset(int) = 0
            Offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Readers unless a Reader removes or changes them.
        '''
        
        return self._Reader(self, *args, **kwargs)

    def Writer(self, *args, **kwargs):
        '''
        Calls this Field_Types Writer function, passing on all args and kwargs.
        Returns the return value of this Field_Types Writer, which
        should be the offset the Writer function left off at.
        
        Required arguments:
            Parent(Tag_Block)
        Optional arguments:
            Raw_Data(buffer) = None
            Attr_Index(int, str) = None
            Root_Offset(int) = 0
            Offset(int) = 0
        Optional kwargs:
            Parents(list)

        Extra arguments and keyword arguments can be passed as well if a
        custom function requires them. All keyword arguments will be passed
        to all nested Writers unless a Writer removes or changes them.
        '''
        
        return self._Writer(self, *args, **kwargs)

    def Decoder(self, *args, **kwargs):
        '''
        Calls this Field_Types Decoder function, passing on all args and kwargs.
        Returns the return value of this Field_Types Decoder, which should
        be a python object decoded represention of the "Bytes" argument.
        
        Required arguments:
            Bytes(bytes)
        Optional arguments:
            Parent(Tag_Block) = None
            Attr_Index(int) = None
        '''
        
        return self._Decoder(self, *args, **kwargs)

    def Encoder(self, *args, **kwargs):
        '''
        Calls this Field_Types Encoder function, passing on all args and kwargs.
        Returns the return value of this Field_Types Encoder, which should
        be a bytes object encoded represention of the "Block" argument.
        
        Required arguments:
            Block(object)
        Optional arguments:
            Parent(Tag_Block) = None
            Attr_Index(int) = None
        '''
        
        return self._Encoder(self, *args, **kwargs)

    def Size_Calc(self, *args, **kwargs):
        '''A redirect that provides 'self' as
        an arg to the actual Size_Calc function.'''
        return self._Size_Calc(self, *args, **kwargs)

    def NotImp(self, *args, **kwargs):
        raise NotImplementedError

    def __eq__(self, other):
        '''Returns whether or not an object is equivalent to this one.'''
        #returns True for the same Field_Type, but with a different endianness
        try:
            return(isinstance(other, Field_Type)
                   and self.Name == other.Name and self.Enc == other.Enc)
        except AttributeError:
            return False

    def __ne__(self, other):
        '''Returns whether or not an object isnt equivalent to this one.'''
        #returns False for the same Field_Type, but with a different endianness
        try:
            return(not isinstance(other, Field_Type)
                   or self.Name != other.Name or self.Enc != other.Enc)
        except AttributeError:
            return True

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        '''
        Returns this object.
        You should never need to make a deep copy of ANY Field_Type.
        '''
        return self

    def __str__(self):
        return("< Field_Type:'%s', Endian:'%s', Enc:'%s' >" %
               (self.Name, self.Endian, self.Enc))

    def __repr__(self):
        return("< Field_Type:'%s', Endian:'%s', Enc:'%s' >" %
               (self.Name, self.Endian, self.Enc))

    '''
    To prevent editing of Field_Types once they are instintiated, the
    default setattr and delattr methods are overloaded with these
    '''
    def __setattr__(self, attr, value):
        if hasattr(self, "Instantiated") and self.Instantiated:
            raise AttributeError("Field_Types are read-only and may "+
                                 "not be changed once created.")
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr, value):
        if hasattr(self, "Instantiated") and self.Instantiated:
            raise AttributeError("Field_Types are read-only and may "+
                                 "not be changed once created.")
        object.__delattr__(self, attr)


Void = Field_Type(Name="Void", Data=True, Endian='=',
                  Size=0, Py_Type=Tag_Blocks.Void_Block,
                  Reader=Void_Reader, Writer=Void_Writer)
Container = Field_Type(Name="Container", Endian='=',
                       Container=True, Py_Type=Tag_Blocks.List_Block,
                       Reader=Container_Reader, Writer=Container_Writer)
Struct = Field_Type(Name="Struct", Struct=True, Endian='=',
                    Py_Type=Tag_Blocks.List_Block,
                    Reader=Struct_Reader, Writer=Struct_Writer)
Array = Field_Type(Name="Array", Array=True, Endian='=',
                   Py_Type=Tag_Blocks.List_Block,
                   Reader=Array_Reader, Writer=Array_Writer)
Switch = Field_Type(Name='Switch', Hierarchy=True, Endian='=',
                    Reader=Switch_Reader)

#Bit Based Data
'''When within a Bit_Struct, offsets and sizes are in bits instead of bytes.
Bit_Struct sizes MUST BE SPECIFIED IN WHOLE BYTE AMOUNTS(1byte, 2bytes, etc)'''
Bit_Struct = Field_Type(Name="Bit Struct", Struct=True, Bit_Based=True,
                        Py_Type=Tag_Blocks.List_Block,
                        Reader=Bit_Struct_Reader, Writer=Bit_Struct_Writer)

'''There is no reader or writer for Bit_Ints because the Bit_Struct handles
getting and combining the Bit_Ints together to ensure proper endianness'''
tmp = {'Data':True, 'Var_Size':True, 'Bit_Based':True,
       'Size_Calc':Bit_UInt_Size_Calc, "Default":0,
       'Reader':Default_Reader,#needs a reader so default values can be set
       'Decoder':Decode_Bit_Int, 'Encoder':Encode_Bit_Int}
Com = Combine

'''UInt, sInt, and SInt MUST be in a Bit_Struct as the Bit_Struct
acts as a bridge between byte level and bit level objects.
Bit_sInt is signed in 1's compliment and Bit_SInt is in 2's compliment.'''
Bit_SInt = Field_Type(**Com({"Name":"Bit SInt", 'Size_Calc':Bit_SInt_Size_Calc,
                             "Enc":{'<':"<S",'>':">S"}},tmp))
Bit_sInt = Field_Type(**Com({"Name":"Bit sInt", 'Size_Calc':Bit_sInt_Size_Calc,
                             "Enc":{'<':"<s",'>':">s"}},tmp))
tmp['Enc'] = {'<':"<U",'>':">U"}
Bit_UInt = Field_Type(**Com({"Name":"Bit UInt"},tmp))
Bit_Enum = Field_Type(**Com({"Name":"Bit Enum", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block,'Val_Type':int},tmp))
Bit_Bool = Field_Type(**Com({"Name":"Bit Bool", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block,'Val_Type':int},tmp))

#Pointers, Integers, and Floats
tmp['Bit_Based'], tmp['Size_Calc'] = False, Big_UInt_Size_Calc
tmp["Reader"], tmp["Writer"] = Data_Reader, Data_Writer
tmp["Decoder"], tmp["Encoder"] = Decode_Big_Int, Encode_Big_Int

Big_SInt = Field_Type(**Com({"Name":"Big SInt", 'Size_Calc':Big_SInt_Size_Calc,
                             "Enc":{'<':"<S",'>':">S"}},tmp))
Big_sInt = Field_Type(**Com({"Name":"Big sInt", 'Size_Calc':Big_sInt_Size_Calc,
                             "Enc":{'<':"<s",'>':">s"}},tmp))
tmp['Enc'] = {'<':"<U",'>':">U"}
Big_UInt = Field_Type(**Com({"Name":"Big UInt"},tmp))
Big_Enum = Field_Type(**Com({"Name":"Big Enum", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block,'Val_Type':int},tmp))
Big_Bool = Field_Type(**Com({"Name":"Big Bool", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block,'Val_Type':int},tmp))

tmp['Var_Size'], tmp['Size_Calc'] = False, Default_Size_Calc
tmp['Decoder'], tmp['Encoder'] = Decode_Numeric, Encode_Numeric
tmp['Reader'] = F_S_Data_Reader

Pointer32 = Field_Type(**Com({"Name":"Pointer32", "Size":4,
                              'Min':0, 'Max':4294967295,
                              "Enc":{'<':"<I",'>':">I"}}, tmp))
Pointer64 = Field_Type(**Com({"Name":"Pointer64", "Size":8,
                              'Min':0, 'Max':18446744073709551615,
                              "Enc":{'<':"<Q",'>':">Q"}}, tmp))

tmp['Size'], tmp['Min'], tmp['Max'] = 1, 0, 255
tmp['Enc'], tmp['Endian'] = 'B', '='
UInt8 = Field_Type(**Com({"Name":"UInt8"},tmp))
Enum8 = Field_Type(**Com({"Name":"Enum8", 'Enum':True, 'Default':None,
                          'Py_Type':Tag_Blocks.Enum_Block, 'Val_Type':int,
                          'Reader':F_S_Data_Reader},tmp))
Bool8 = Field_Type(**Com({"Name":"Bool8", 'Bool':True, 'Default':None,
                          'Py_Type':Tag_Blocks.Bool_Block, 'Val_Type':int,
                          'Reader':F_S_Data_Reader},tmp))
del tmp['Endian']
tmp['Size'], tmp['Max'], tmp['Enc'] = 2, 2**16-1, {'<':"<H",'>':">H"}
UInt16 = Field_Type(**Com({"Name":"UInt16"}, tmp))
Enum16 = Field_Type(**Com({"Name":"Enum16", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader},tmp))
Bool16 = Field_Type(**Com({"Name":"Bool16", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader},tmp))

tmp['Size'], tmp['Max'], tmp['Enc'] = 4, 2**32-1, {'<':"<I",'>':">I"}
UInt32 = Field_Type(**Com({"Name":"UInt32"}, tmp))
Enum32 = Field_Type(**Com({"Name":"Enum32", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader}, tmp))
Bool32 = Field_Type(**Com({"Name":"Bool32", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader}, tmp))

tmp['Size'], tmp['Max'], tmp['Enc'] = 8, 2**64-1, {'<':"<Q",'>':">Q"}
UInt64 = Field_Type(**Com({"Name":"UInt64"}, tmp))
Enum64 = Field_Type(**Com({"Name":"Enum64", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader}, tmp))
Bool64 = Field_Type(**Com({"Name":"Bool64", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader}, tmp))

SInt8 = Field_Type(**Com({"Name":"SInt8", "Size":1, "Enc":{'<':"<b",'>':">b"},
                          'Min':-128, 'Max':127, 'Endian':'='}, tmp))
SInt16 = Field_Type(**Com({"Name":"SInt16", "Size":2, "Enc":{'<':"<h",'>':">h"},
                           'Min':-32768, 'Max':32767 }, tmp))
SInt32 = Field_Type(**Com({"Name":"SInt32", "Size":4, "Enc":{'<':"<i",'>':">i"},
                           'Min':-2147483648, 'Max':2147483647 }, tmp))
SInt64 = Field_Type(**Com({"Name":"SInt64", "Size":8, "Enc":{'<':"<q",'>':">q"},
                           'Min':-2**63, 'Max':2**63-1 }, tmp))

tmp["Default"] = 0.0
Float = Field_Type(**Com({"Name":"Float", "Size":4, "Enc":{'<':"<f",'>':">f"},
                          "Max":unpack('>f',b'\x7f\x7f\xff\xff'),
                          "Min":unpack('>f',b'\xff\x7f\xff\xff') }, tmp))
Double = Field_Type(**Com({"Name":"Double", "Size":8, "Enc":{'<':"<d",'>':">d"},
                           "Max":unpack('>d',b'\x7f\xef'+b'\xff'*6),
                           "Min":unpack('>d',b'\xff\xef'+b'\xff'*6)}, tmp))

#24 bit integers
tmp['Decoder'], tmp['Encoder'] = Decode_24Bit_Numeric, Encode_24Bit_Numeric
tmp['Size'], tmp['Max'], tmp['Enc'] = 3, 2**24-1, {'<':"<I",'>':">I"}
UInt24 = Field_Type(**Com({"Name":"UInt24", "Default":0}, tmp))
Enum24 = Field_Type(**Com({"Name":"Enum24", 'Enum':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Enum_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader, "Default":0}, tmp))
Bool24 = Field_Type(**Com({"Name":"Bool24", 'Bool':True, 'Default':None,
                           'Py_Type':Tag_Blocks.Bool_Block, 'Val_Type':int,
                           'Reader':F_S_Data_Reader, "Default":0}, tmp))
SInt24 = Field_Type(**Com({"Name":"SInt24", "Size":3, "Enc":{'<':"<i",'>':">i"},
                           'Min':-8388608, 'Max':8388607, "Default":0 }, tmp))


tmp["Py_Type"], tmp["Default"] = str, lambda *a, **kwa:ctime(time())
tmp["Decoder"], tmp["Encoder"], tmp["Size"] = Decode_Timestamp,Encode_Numeric,4
tmp["Min"], tmp["Max"] = 'Wed Dec 31 19:00:00 1969', 'Thu Jan  1 02:59:59 3001' 
UTC_Timestamp = Field_Type(**Com({"Name":"UTC Timestamp",
                                  "Enc":{'<':"<f",'>':">f"},
                                  "Encoder":Encode_Float_Timestamp},tmp))
Timestamp = Field_Type(**Com({"Name":"Timestamp", "Enc":{'<':"<I",'>':">I"},
                              "Encoder":Encode_Int_Timestamp},tmp))

tmp = {'Var_Size':True, 'Raw':True, 'Size_Calc':Array_Size_Calc,
       'Reader':Py_Array_Reader, 'Writer':Py_Array_Writer,'Min':None,'Max':None}

#Arrays
UInt8_Array = Field_Type(**Com({"Name":"UInt8 Array", "Size":1, 'Endian':'=',
                                "Default":array("B", []), "Enc":"B"}, tmp))
SInt8_Array = Field_Type(**Com({"Name":"SInt8 Array", "Size":1, 'Endian':'=',
                                "Default":array("b", []), "Enc":"b"}, tmp))
UInt16_Array = Field_Type(**Com({"Name":"UInt16 Array", "Size":2,
                                 "Default":array("H", []), "Enc":"H"}, tmp))
SInt16_Array = Field_Type(**Com({"Name":"SInt16 Array", "Size":2,
                                 "Default":array("h", []), "Enc":"h"}, tmp))
UInt32_Array = Field_Type(**Com({"Name":"UInt32 Array", "Size":4,
                                 "Default":array("I", []), "Enc":"I"}, tmp))
SInt32_Array = Field_Type(**Com({"Name":"SInt32 Array", "Size":4,
                                 "Default":array("i", []), "Enc":"i"}, tmp))
UInt64_Array = Field_Type(**Com({"Name":"UInt64 Array", "Size":8,
                                 "Default":array("Q", []), "Enc":"Q"}, tmp))
SInt64_Array = Field_Type(**Com({"Name":"SInt64 Array", "Size":8,
                                 "Default":array("q", []), "Enc":"q"}, tmp))

Float_Array = Field_Type(**Com({"Name":"Float Array", "Size":4,
                                "Default":array("f", []), "Enc":"f"}, tmp))
Double_Array = Field_Type(**Com({"Name":"Double Array", "Size":8,
                                 "Default":array("d", []), "Enc":"d"}, tmp))

tmp['Raw'] = tmp['Var_Size'] = True
tmp['Size_Calc'], tmp['Endian'] = Len_Size_Calc, '='
tmp['Reader'], tmp['Writer'] = Bytes_Reader, Bytes_Writer


Bytes_Raw = Field_Type(**Com({'Name':"Bytes Raw", 'Default':bytes()}, tmp))
Bytearray_Raw = Field_Type(**Com({'Name':"Bytearray Raw",
                                  'Default':bytearray()}, tmp))


#Strings
tmp = {'Str':True, 'Default':'', 'Delimited':True, 'Endian':'=',
       'Reader':Data_Reader, 'Writer':Data_Writer,
       'Decoder':Decode_String, 'Encoder':Encode_String,
       'Size_Calc':Delim_Str_Size_Calc, 'Size':1}

Other_Enc = ("big5","hkscs","cp037","cp424","cp437","cp500","cp720","cp737",
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
#are located for Strings, CStrings, and Raw Strings
Str_Field_Types = {}
CStr_Field_Types = {}
Str_Raw_Field_Types = {}


for enc in Other_Enc:
    Str_Field_Types[enc] = Field_Type(**Com({'Name':"Str "+enc, 'Enc':enc},tmp))
    
Str_ASCII = Field_Type(**Com({'Name':"Str ASCII", 'Enc':'ascii'}, tmp) )
Str_Latin1 = Field_Type(**Com({'Name':"Str Latin1", 'Enc':'latin1'}, tmp) )
Str_UTF8 = Field_Type(**Com({'Name':"Str UTF8", 'Enc':'utf8',
                             'Size_Calc':Delim_Str_Size_Calc_UTF},tmp))
del tmp['Endian']
Str_UTF16 = Field_Type(**Com({'Name':"Str UTF16", 'Size':2,
                              'Size_Calc':Delim_Str_Size_Calc_UTF,
                              'Enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
Str_UTF32 = Field_Type(**Com({'Name':"Str UTF32", 'Size':4,
                              'Enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#Null terminated strings
tmp['OE_Size'], tmp['Endian'] = True, '='
tmp['Reader'], tmp['Writer'] = CString_Reader, CString_Writer

for enc in Other_Enc:
    CStr_Field_Types[enc] = Field_Type(**Com({'Name':"Str "+enc,'Enc':enc},tmp))

CStr_ASCII   = Field_Type(**Com({'Name':"CStr ASCII", 'Enc':'ascii'}, tmp) )
CStr_Latin1 = Field_Type(**Com({'Name':"CStr Latin1", 'Enc':'latin1'}, tmp) )
CStr_UTF8   = Field_Type(**Com({'Name':"CStr UTF8", 'Enc':'utf8',
                                'Size_Calc':Delim_Str_Size_Calc_UTF},tmp))
del tmp['Endian']
CStr_UTF16  = Field_Type(**Com({'Name':"CStr UTF16", 'Size':2,
                                'Size_Calc':Delim_Str_Size_Calc_UTF,
                                'Enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
CStr_UTF32  = Field_Type(**Com({'Name':"CStr UTF32", 'Size':4,
                                'Enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#Raw strings
'''Raw strings are different in that they ARE NOT expected to
have a delimiter. A fixed length string can have all characters
used and not require a delimiter character to be on the end.'''
tmp['OE_Size'], tmp['Delimited'], tmp['Size_Calc'] = False, False, Str_Size_Calc
tmp['Reader'], tmp['Writer'], tmp['Endian'] = Data_Reader, Data_Writer, '='
tmp['Decoder'], tmp['Encoder'] = Decode_String, Encode_Raw_String

for enc in Other_Enc:
    Str_Raw_Field_Types[enc] = Field_Type(**Com({'Name':"Str "+enc,
                                                 'Enc':enc},tmp))

Str_Raw_ASCII  = Field_Type(**Com({'Name':"Str Raw ASCII",'Enc':'ascii'},tmp))
Str_Raw_Latin1 = Field_Type(**Com({'Name':"Str Raw Latin1",'Enc':'latin1'},tmp))
Str_Raw_UTF8   = Field_Type(**Com({'Name':"Str Raw UTF8", 'Enc':'utf8',
                                   'Size_Calc':Str_Size_Calc_UTF}, tmp))
del tmp['Endian']
Str_Raw_UTF16 = Field_Type(**Com({'Name':"Str Raw UTF16", 'Size':2,
                                  'Size_Calc':Str_Size_Calc_UTF,
                                  'Enc':{"<":"utf_16_le",">":"utf_16_be"}},tmp))
Str_Raw_UTF32 = Field_Type(**Com({'Name':"Str Raw UTF32", 'Size':4,
                                  'Enc':{"<":"utf_32_le",">":"utf_32_be"}},tmp))

tmp['Endian'] = '='
#used for places in a file where a string is used as an enumerator
#to represent a setting in a file (a 4 character code for example)
Str_Latin1_Enum = Field_Type(**Com({'Name':"Str Latin1 Enum", 'Enc':'latin1',
                                    'Py_Type':Tag_Blocks.Enum_Block,
                                    'Enum':True,'Val_Type':str},tmp))

#little bit of cleanup
del tmp
del Other_Enc
del Com
