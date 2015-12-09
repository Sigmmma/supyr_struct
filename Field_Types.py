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

__all__ = ['No_Size_Calc', 'Default_Size_Calc',
           'Str_Size_Calc', 'Str_Size_Calc_UTF',
           'Array_Size_Calc', 'Len_Size_Calc',
           'Big_Int_Size_Calc', 'Bit_Int_Size_Calc',

           'Field_Type', 'All_Field_Types',
           'Str_Field_Types', 'CStr_Field_Types', 'Str_Raw_Field_Types',

           'Null', 'Container', 'Struct', 'Array', 'Bit_Struct',
           'Pointer32', 'Pointer64',

           'Bit_UInt', 'Bit_SInt', 'Bit_sInt',
           'Big_UInt', 'Big_SInt', 'Big_sInt',
           'UInt8', 'UInt16', 'UInt32', 'UInt64', 'Float',
           'SInt8', 'SInt16', 'SInt32', 'SInt64', 'Double',
           
           'Float_Array',  'Double_Array', 'Bytes_Raw',    'Bytearray_Raw',
           'UInt8_Array',  'SInt8_Array',  'UInt16_Array', 'SInt16_Array',
           'UInt32_Array', 'SInt32_Array', 'UInt64_Array', 'SInt64_Array',

           'Str_ASCII',  'CStr_ASCII',  'Str_Raw_ASCII',
           'Str_Latin1', 'CStr_Latin1', 'Str_Raw_Latin1',
           'Str_UTF8',   'CStr_UTF8',   'Str_Raw_UTF8',
           'Str_UTF16',  'CStr_UTF16',  'Str_Raw_UTF16',
           'Str_UTF32',  'CStr_UTF32',  'Str_Raw_UTF32']

from copy import deepcopy
from math import log, ceil
from struct import unpack

from supyr_struct.Re_Wr_De_En import *
from supyr_struct.Tag_Block import Tag_Block, List_Block, P_List_Block

#a list containing all valid created Field_Types
All_Field_Types = []


def No_Size_Calc(self, *args, **kwargs):
    '''
    If a Size_Calc routine wasnt provided for this
    Field_Type and one can't be decided upon as a
    default, then the size can't be calculated.
    Raises Not_ImplementedError when called.
    '''
    
    raise NotImplementedError("Calculating size for this " +
                              "data type is not supported.")

def Default_Size_Calc(self, *args, **kwargs):
    '''
    Returns the byte size specified by the Field_Type.
    Only used if the self.Var_Size == False.
    '''
    
    return self.Size

def Str_Size_Calc(self, Block, **kwargs):
    '''
    Returns the byte size of a string if it were converted to bytes.

    Required arguments:
        Block(str)
    '''
    if self.Is_Delimited:
        if len(Block):
            #if the string is already delimited do
            #not add the delimiter to the length
            if Block[-1] == self.Str_Delimiter:
                return len(Block) * self.Size
            return (len(Block)+1) * self.Size
    return len(Block)*self.Size

def Str_Size_Calc_UTF(self, Block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were converted to bytes.
    This function is potentially slower than the above one, but is
    necessary to get an accurate byte length for UTF8/16 strings.
    
    This should only be used for UTF8 and UTF16. 

    Required arguments:
        Block(str)
    '''
    Block_Len = len(Block.encode(encoding=self.Enc))
    
    if self.Is_Delimited:
        if Block_Len:
            #if the string is not already delimited
            #then add the delimiter size to the length
            if Block[-1] != self.Str_Delimiter:
                return Block_Len + self.Size
            return Block_Len
        #return the length of the delimiter character
        return self.Size
    #return the length of the entire string of bytes
    return Block_Len

    
def Array_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the byte size of an array if it were converted to bytes.

    Required arguments:
        Block(array.array)
    '''
    
    return len(Block)*Block.itemsize
    
def Big_Int_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.

    Required arguments:
        Block(int)
    '''
    
    if self.Enc[1] == 's':
        #ones compliment
        return int(ceil( (log(abs(Block)+1,2)+1.0)/8.0 ))
    elif self.Enc[1] == 'S':
        #twos compliment
        if Block >= 0:
            return int(ceil( (log(Block+1,2)+1.0)/8.0 ))
        else:
            return int(ceil( (log(0-Block,2)+1.0)/8.0 ))
    else:
        #unsigned
        return int(ceil( log(abs(Block)+1,2)/8.0 ))
    
def Bit_Int_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.

    Required arguments:
        Block(int)
    '''
    
    if self.Enc[1] == 's':
        #ones compliment
        return int(ceil( log(abs(Block)+1,2)+1.0 ))
    elif self.Enc[1] == 'S':
        #twos compliment
        if Block >= 0:
            return int(ceil( log(Block+1,2)+1.0 ))
        else:
            return int(ceil( log(0-Block,2)+1.0 ))
    else:
        #unsigned
        return int(ceil( log(abs(Block)+1,2) ))
    
def Len_Size_Calc(self, Block, *args, **kwargs):
    '''
    Returns the byte size of an object whose length is its
    size if it were converted to bytes(bytes, bytearray).

    Required arguments:
        Block(sequence)
    '''
    
    return len(Block)

    






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

    __slots__ = ('_Default', '_Name', '_Size', '_Enc', '_Max', '_Min',
                 '_Reader', '_Writer', '_Decoder', '_Encoder', '_Size_Calc',
                 '_Endian_Types', '_Endian', '_Py_Type',
                 '_Is_Data', '_Is_Str', '_Is_Raw', '_Is_Struct', '_Is_Array',
                 '_Is_Container', '_Is_Var_Size', '_Is_Bit_Based', 
                 '_Is_OE_Size', '_Str_Delimiter', '_Delimiter', '_Is_Delimited')
    
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
                         'bhiqfBHIQD' for integers decoded and encoded by
                         pythons struct module, whereas Str_UTF_16 and
                         Str_Latin_1 use "UTF-16" and "latin-1" respectively.
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
        Struct -----  Object has a fixed size and attributes have offsets
        Container --  Object has no fixed size and attributes have no offsets
        Array ------  Object is an array of instanced elements
        Var_Size ---  Byte size of the object can vary(descriptor defined size)
        OE_Size ----  Byte size of the object cant be determined in advance
                      as it relies on some sort of null termination(open ended)
        Bit_Based --  Whether the data should be worked on a bit or byte level
        Delimited --  Whether or not the string is terminated with a delimiter
                      character(the type MUST be a string)
        
        #int
        Size -------  The byte size of the data when in binary form.
                      For strings this is how many bytes a single character is
        Max --------  For floats/ints, this is the largest a value can be
        Min --------  For floats/ints, this is the smallest a value can be
        '''
        
        self._Reader = self.NotImp
        self._Writer = self.NotImp
        self._Decoder = self.NotImp
        self._Encoder = self.NotImp
        self._Size_Calc = self.NotImp
        
        #so that we don't need to create a new data type with the opposite
        #encoding everytime we need to reverse the endianness AND so that
        #we can reverse the endianness with just a reference to the
        #un-reversed type, we keep a reference to the other types here
        self._Endian_Types = {}
        
        self._Name = ""       #the name of the data type
        self._Default = None  #a python object to copy as the default value
        self._Py_Type = None  #the python type associated with this Field_Type

        self._Is_Data = False      #some form of data(as opposed to hierarchy)
        self._Is_Str = False       #a string
        self._Is_Raw = False       #raw data that isnt decoded(i.e. pixel bytes)
        self._Is_Struct = False    #set size. non-child attributes have offsets
        self._Is_Array = False     #indexes are some form of arrayed data
        self._Is_Container = False #no defined size and attrs have no offsets.
        self._Is_Var_Size = False  #descriptor defines the size, as it can vary
        self._Is_OE_Size = False   #size of data cant be determined until the
                                   #data is being read or written(open ended)
        self._Is_Bit_Based = False #whether the data should be worked on at
                                   #the bit level or byte level

        #required if type is a variable
        self._Size = 0 #determines how many bytes this variable always is
                       #OR how many bytes each character of a string uses
        self._Enc = ''
        self._Endian = '<'
        self._Min = None
        self._Max = None
        
        #required if type is a string
        self._Is_Delimited = False
        self._Delimiter = None
        self._Str_Delimiter = None
        
        if kwargs.get("Name") is None:
            raise TypeError("'Name' is a required identifier for data types.")
        
        self._Name = kwargs["Name"]

        if kwargs.get("Reader") is not None:
            self._Reader = kwargs["Reader"]
        if kwargs.get("Writer") is not None:
            self._Writer = kwargs["Writer"]
        if "Default" in kwargs:
            self._Default = kwargs["Default"]
        if "Py_Type" in kwargs:
            self._Py_Type = kwargs["Py_Type"]
            if self._Default is None:
                if issubclass(self._Py_Type, Tag_Block):
                    self._Default = self._Py_Type(Type=self)
                else:
                    self._Default = self._Py_Type()
        else:
            self._Py_Type = type(self._Default)
            
        if "Data" in kwargs:
            self._Is_Data = bool(kwargs["Data"])
        if "Hierarchy" in kwargs:
            self._Is_Data = not bool(kwargs["Hierarchy"])
        if "Str" in kwargs:
            self._Is_Str = bool(kwargs["Str"])
        if "Raw" in kwargs:
            self._Is_Raw = bool(kwargs["Raw"])
        if "Struct" in kwargs:
            self._Is_Struct = bool(kwargs["Struct"])
        if "Array" in kwargs:
            self._Is_Array = bool(kwargs["Array"])
        if "Container" in kwargs:
            self._Is_Container = bool(kwargs["Container"])
        if "Var_Size" in kwargs:
            self._Is_Var_Size = bool(kwargs["Var_Size"])
        if "OE_Size" in kwargs:
            self._Is_OE_Size = bool(kwargs["OE_Size"])
        if "Bit_Based" in kwargs:
            self._Is_Bit_Based = bool(kwargs["Bit_Based"])
        if "Delimited" in kwargs:
            self._Is_Delimited = bool(kwargs["Delimited"])

        if self._Is_Str:
            if "Delimiter" in kwargs:
                self._Delimiter = kwargs["Delimiter"]
            elif "Size" in kwargs:
                self._Delimiter = b'\x00' * int(kwargs["Size"])
                
            if "Str_Delimiter" in kwargs:
                self._Str_Delimiter = kwargs["Str_Delimiter"]
                

        if self._Is_Str or self._Is_Raw:
            self._Is_Data = True     
            self._Is_Var_Size = True
        elif not self._Is_Data:
            self._Is_Var_Size = True

        
        if kwargs.get("Endian") in ('<','>'):
            self._Endian = kwargs["Endian"]
        else:
            #default endianness of the initial Field_Type is 'little'
            self._Endian = '<'
            
        if self.Is_Data:
            if "Decoder" in kwargs:
                self._Decoder = kwargs["Decoder"]
            if "Encoder" in kwargs:
                self._Encoder = kwargs["Encoder"]
                
            if "Size" in kwargs:
                self._Size = kwargs["Size"]
            else:
                if not self.Is_Var_Size:
                    raise TypeError("Data size required for 'Data' " +
                                    "Field_Types of non variable size")

            if "Enc" in kwargs:
                if isinstance(kwargs["Enc"], str):
                    self._Enc = kwargs["Enc"]
                elif isinstance(kwargs["Enc"], dict):
                    if not('<' in kwargs["Enc"] and '>' in kwargs["Enc"]):
                        raise TypeError("When providing endianness reliant "+
                                        "encodings, big and little endian\n"+
                                        "must both be provided under the "+
                                        "keys '>' and '<' respectively.")
                    self._Enc = kwargs["Enc"]['<']
            else:
                if not self.Is_Raw:
                    raise TypeError("'Enc' required for " +
                                    "non-Raw 'Data' Field_Types")
                
            #figure out the size of the data 
            if not self._Is_Var_Size:
                if self._Py_Type == int:
                    '''the encoding for ints is expected to be the format
                    accepted by the struct module, namely endianness 
                    character followed by a char specifying the int type.
                    This is why the below code only uses index[1] of self._Enc
                    
                    Example: '<H' for a little endian unsigned short.'''
                    self._Min = 0
                    
                    if self._Enc[-1] in 'Ss':
                        self._Max = 2**(self._Size-1) -  1
                        self._Min = 2**(self._Size-1) * -1
                        if self._Enc[-1] == 's':
                            self._Min = self._Min + 1
                    elif self._Enc[-1] in "bhiq":
                        self._Max = 2**((self._Size*8)-1) - 1
                        self._Min = 2**((self._Size*8)-1) *-1
                    else:
                        self._Max = 2**(self._Size*8) - 1
                elif self._Py_Type == float:
                    self._Max = float('inf')
                    self._Min = float('-inf')


        #setup the dictionary containing this Field_Type
        #and its equivalent swapped endianness version.
        '''Even if a Field_Type isn't endianness specific
        (UInt8 for example) it still needs both endiannesses
        defined for it to function properly in the library.'''
        if kwargs.get('Endian_Types') is None:
            kwargs["Endian_Types"] = self._Endian_Types
            kwargs["Endian"] = {'<':'>','>':'<'}[self._Endian]
            
            self._Endian_Types[self._Endian] = self
            #if the provided Enc kwarg is a dict, get the encoding
            #of the endianness opposite the current Field_Type.
            if 'Enc' in kwargs and isinstance(kwargs["Enc"], dict):
                kwargs["Enc"] = kwargs["Enc"][kwargs["Endian"]]
            else:
                kwargs["Enc"] = self._Enc
                
            Field_Type(**kwargs)
        else:
            self._Endian_Types = kwargs["Endian_Types"]
            self._Endian_Types[self._Endian] = self
                    
            
        if "Min" in kwargs:
            self._Min = kwargs["Min"]
        if "Max" in kwargs:
            self._Max = kwargs["Max"]
        
        if self.Is_Str and self.Is_Delimited:
            if self._Delimiter is None:
                self._Delimiter = self._Str_Delimiter.encode(encoding=self._Enc)
            if self._Str_Delimiter is None:
                self._Str_Delimiter = self._Delimiter.decode(encoding=self._Enc)

        #Decode on a Size_Calc method to use based on the
        #data type or use the one provided, if provided
        if "Size_Calc" in kwargs:
            self._Size_Calc = kwargs['Size_Calc']
        elif isinstance(self._Default, str):
            self._Size_Calc = Str_Size_Calc
        elif isinstance(self._Default, array):
            self._Size_Calc = Array_Size_Calc
        elif isinstance(self._Default, (bytearray, bytes)) or self.Is_Array:
            self._Size_Calc = Len_Size_Calc
        else:
            if self.Is_Var_Size:
                self._Size_Calc = No_Size_Calc
            else:
                self._Size_Calc = Default_Size_Calc

        #add this to the collection of all field types
        All_Field_Types.append(self)


    @property
    def Name(self):
        return self._Name
    @property
    def Py_Type(self):
        return self._Py_Type
    
    @property
    def Is_Data(self):
        return self._Is_Data
    @property
    def Is_Hierarchy(self):
        return not self._Is_Data
    
    @property
    def Is_Str(self):
        return self._Is_Str
    @property
    def Is_Raw(self):
        return self._Is_Raw
    @property
    def Is_Struct(self):
        return self._Is_Struct
    @property
    def Is_Array(self):
        return self._Is_Array
    @property
    def Is_Container(self):
        return self._Is_Container
    @property
    def Is_Var_Size(self):
        return self._Is_Var_Size
    @property
    def Is_OE_Size(self):
        return self._Is_OE_Size
    @property
    def Is_Bit_Based(self):
        return self._Is_Bit_Based
    @property
    def Is_Delimited(self):
        return self._Is_Delimited
    
    @property
    def Size(self):
        return self._Size
    @property
    def Enc(self):
        return self._Enc
    @property
    def Endian(self):
        return self._Endian
    @property
    def Min(self):
        return self._Min
    @property
    def Max(self):
        return self._Max
    
    @property
    def Delimiter(self):
        return self._Delimiter
    @property
    def Str_Delimiter(self):
        return self._Str_Delimiter


    def Default(self, *args, **kwargs):
        '''
         Provides a copy of the default python object that
        this data type describes. Providing arguments will call
        the object's constructor while passing on the provided
        arguments and returning the constructed object. Calling
        without arguments instead returns a deepcopy of it.
        '''
        if args or kwargs:
            return type(self._Default)(*args, **kwargs)
        else:
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

    def __call__(self, Endian):
        '''
        The object call is setup to return the same
        Field_Type, but with the endianness you supply.
        '''
        try:
            return self._Endian_Types[Endian]
        except:
            raise KeyError('Invalid endianness character "%s"' % Enc)

    def __eq__(self, other):
        '''Returns whether or not an object is equivalent to this one.'''
        #returns True for the same Field_Type, but with a different endianness
        return(isinstance(other, type(self))
               and (hasattr(other, "Name") and self._Name == other.Name)
               and (hasattr(other, "Enc" ) and self._Enc  == other.Enc))

    def __ne__(self, other):
        '''Returns whether or not an object isnt equivalent to this one.'''
        #returns False for the same Field_Type, but with a different endianness
        return(isinstance(other, type(self))
               or (not hasattr(other, "Name") or self._Name != other.Name)
               or (not hasattr(other, "Enc" ) or self._Enc  != other.Enc))

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        '''
        Returns this object.
        You should never need to make a deep copy of ANY Field_Type.
        '''
        return self

    def __str__(self):
        return("Field_Type:'%s', Endianness:'%s', Encoding:'%s'" %
               (self._Name, self.Endian, self.Enc))


#The Null field type needs more work to make it fit in and make sense.
#As it is right now I don't know how a Null field type will affect each
#part of supyr_struct and where it'll cause exceptions and such.
Null = Field_Type(Name="Null", Data=True, Py_Type=object, Enc="B", Size=0,
                  Reader=No_Read, Writer=No_Write,
                  Decoder=No_Decode, Encoder=No_Encode)
Container = Field_Type(Name="Container", Container=True, Py_Type=List_Block,
                       Reader=Container_Reader, Writer=Container_Writer)
Struct = Field_Type(Name="Struct", Struct=True, Py_Type=List_Block,
                    Reader=Struct_Reader, Writer=Struct_Writer)
Array = Field_Type(Name="Array", Container=True, Array=True, Py_Type=List_Block,
                   Reader=Array_Reader, Writer=Array_Writer)


#Bit Based Data
'''When within a Bit_Struct, offsets and sizes
are in bits instead of bytes. Bit_Struct sizes
MUST BE WHOLE byte amounts(1byte, 2bytes, etc)'''
Bit_Struct = Field_Type(Name="Bit Struct",
                        Py_Type=List_Block, Struct=True, Bit_Based=True,
                        Reader=Bit_Struct_Reader, Writer=Bit_Struct_Writer)

'''There is no reader or writer for Bit_Ints because
the Bit_Struct handles getting and combining the
Bit_Ints together to ensure proper endianness'''
tmp = {"Data":True, 'Var_Size':True, 'Bit_Based':True,
       'Size_Calc':Bit_Int_Size_Calc, "Default":0,
       'Reader':Default_Reader,#needs a reader so default values can be set
       'Decoder':Decode_Bit_Int, 'Encoder':Encode_Bit_Int}
Com = Combine

'''UInt, sInt, and SInt MUST be in a Bit_Struct as the Bit_Struct
acts as a bridge between byte level and bit level objects.
Bit_sInt is signed in 1's compliment and Bit_SInt is in 2's compliment.'''
Bit_UInt = Field_Type(**Com({"Name":"Bit UInt", "Enc":{'<':"<U",'>':">U"}},tmp))
Bit_SInt = Field_Type(**Com({"Name":"Bit SInt", "Enc":{'<':"<S",'>':">S"}},tmp))
Bit_sInt = Field_Type(**Com({"Name":"Bit sInt", "Enc":{'<':"<s",'>':">s"}},tmp))


#Pointers, Integers, and Floats
tmp['Bit_Based'], tmp['Size_Calc'] = False, Big_Int_Size_Calc
tmp["Reader"], tmp["Writer"] = Data_Reader, Data_Writer
tmp["Decoder"], tmp["Encoder"] = Decode_Big_Int, Encode_Big_Int

Big_UInt = Field_Type(**Com({"Name":"Big UInt", "Enc":{'<':"<U",'>':">U"}},tmp))
Big_SInt = Field_Type(**Com({"Name":"Big SInt", "Enc":{'<':"<S",'>':">S"}},tmp))
Big_sInt = Field_Type(**Com({"Name":"Big sInt", "Enc":{'<':"<s",'>':">s"}},tmp))

tmp['Var_Size'], tmp['Size_Calc'] = False, Default_Size_Calc
tmp["Decoder"], tmp["Encoder"] = Decode_Numeric, Encode_Numeric

Pointer32 = Field_Type(**Com({"Name":"Pointer32", "Size":4,
                              "Enc":{'<':"<I",'>':">I"}}, tmp))
Pointer64 = Field_Type(**Com({"Name":"Pointer64", "Size":8,
                              "Enc":{'<':"<Q",'>':">Q"}}, tmp))

UInt8 = Field_Type(**Com({"Name":"UInt8", "Size":1, "Enc":{'<':"<B",'>':">B"}},tmp))
UInt16 = Field_Type(**Com({"Name":"UInt16", "Size":2, "Enc":{'<':"<H",'>':">H"}}, tmp))
UInt32 = Field_Type(**Com({"Name":"UInt32", "Size":4, "Enc":{'<':"<I",'>':">I"}}, tmp))
UInt64 = Field_Type(**Com({"Name":"UInt64", "Size":8, "Enc":{'<':"<Q",'>':">Q"}}, tmp))

SInt8 = Field_Type(**Com({"Name":"SInt8", "Size":1, "Enc":{'<':"<b",'>':">b"}}, tmp))
SInt16 = Field_Type(**Com({"Name":"SInt16", "Size":2, "Enc":{'<':"<h",'>':">h"}}, tmp))
SInt32 = Field_Type(**Com({"Name":"SInt32", "Size":4, "Enc":{'<':"<i",'>':">i"}}, tmp))
SInt64 = Field_Type(**Com({"Name":"SInt64", "Size":8, "Enc":{'<':"<q",'>':">q"}}, tmp))

tmp["Default"] = 0.0
Float = Field_Type(**Com({"Name":"Float", "Size":4, "Enc":{'<':"<f",'>':">f"},
                          "Max":unpack('>f',b'\x7f\x7f\xff\xff'),
                          "Min":unpack('>f',b'\xff\x7f\xff\xff') }, tmp))
Double = Field_Type(**Com({"Name":"Double", "Size":8, "Enc":{'<':"<d",'>':">d"},
                           "Max":unpack('>d',b'\x7f\xef\xff\xff\xff\xff\xff\xff'),
                           "Min":unpack('>d',b'\xff\xef\xff\xff\xff\xff\xff\xff')}, tmp))



tmp = {'Var_Size':True, 'Array':True, 'Raw':True, 'Size_Calc':Array_Size_Calc,
       'Reader':Py_Array_Reader, 'Writer':Py_Array_Writer}

#Arrays
UInt8_Array = Field_Type(**Com({"Name":"UInt8 Array", "Size":1,
                                "Default":array("B", []), "Enc":"B"}, tmp))
SInt8_Array = Field_Type(**Com({"Name":"SInt8 Array", "Size":1,
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


tmp['Raw'] = tmp['Var_Size'] = tmp['Array'] = True
tmp['Size_Calc'] = Len_Size_Calc
tmp['Reader'], tmp['Writer'] = Bytes_Reader, Bytes_Writer


Bytes_Raw = Field_Type(**Com({'Name':"Bytes Raw", 'Default':bytes()}, tmp))
Bytearray_Raw = Field_Type(**Com({'Name':"Bytearray Raw", 'Default':bytearray()}, tmp))


#Strings
tmp = {'Str':True, 'Default':'', 'Delimited':True,
       'Reader':Data_Reader, 'Writer':Data_Writer,
       'Decoder':Decode_String, 'Encoder':Encode_String,
       'Size_Calc':Str_Size_Calc, 'Size':1}

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
                             'Size_Calc':Str_Size_Calc_UTF},tmp))
Str_UTF16 = Field_Type(**Com({'Name':"Str UTF16", 'Size':2,
                              'Size_Calc':Str_Size_Calc_UTF,
                              'Enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
Str_UTF32 = Field_Type(**Com({'Name':"Str UTF32", 'Size':4,
                              'Enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#Null terminated strings
tmp['OE_Size'] = True
tmp['Reader'], tmp['Writer'] = CString_Reader, CString_Writer

for enc in Other_Enc:
    CStr_Field_Types[enc] = Field_Type(**Com({'Name':"Str "+enc,
                                              'Enc':enc},tmp))

CStr_ASCII   = Field_Type(**Com({'Name':"CStr ASCII", 'Enc':'ascii'}, tmp) )
CStr_Latin1 = Field_Type(**Com({'Name':"CStr Latin1", 'Enc':'latin1'}, tmp) )
CStr_UTF8   = Field_Type(**Com({'Name':"CStr UTF8", 'Enc':'utf8',
                                'Size_Calc':Str_Size_Calc_UTF},tmp))
CStr_UTF16  = Field_Type(**Com({'Name':"CStr UTF16", 'Size':2,
                                'Size_Calc':Str_Size_Calc_UTF,
                                'Enc':{"<":"utf_16_le", ">":"utf_16_be"}},tmp))
CStr_UTF32  = Field_Type(**Com({'Name':"CStr UTF32", 'Size':4,
                                'Enc':{"<":"utf_32_le", ">":"utf_32_be"}},tmp))


#Raw strings
'''Raw strings are different in that they ARE NOT sliced off at their
delimiter. They are treated as if they dont have a delimiter while
calculating size. They are equivalent to an encoded string of bytes.'''
tmp['OE_Size'], tmp['Delimited'] = False, False
tmp['Reader'], tmp['Writer'] = Data_Reader, Data_Writer
tmp['Decoder'], tmp['Encoder'] = Decode_Raw_String, Encode_Raw_String

for enc in Other_Enc:
    Str_Raw_Field_Types[enc] = Field_Type(**Com({'Name':"Str "+enc,
                                                 'Enc':enc},tmp))

Str_Raw_ASCII   = Field_Type(**Com({'Name':"Str Raw ASCII",'Enc':'ascii'},tmp))
Str_Raw_Latin1 = Field_Type(**Com({'Name':"Str Raw Latin 1",'Enc':'latin1'},tmp))
Str_Raw_UTF8   = Field_Type(**Com({'Name':"Str Raw UTF8", 'Enc':'utf8',
                                   'Size_Calc':Str_Size_Calc_UTF}, tmp))
Str_Raw_UTF16  = Field_Type(**Com({'Name':"Str Raw UTF16", 'Size':2,
                                   'Size_Calc':Str_Size_Calc_UTF,
                                   'Enc':{"<":"utf_16_le", ">":"utf_16_be"}}, tmp))
Str_Raw_UTF32  = Field_Type(**Com({'Name':"Str Raw UTF32", 'Size':4,
                                   'Enc':{"<":"utf_32_le", ">":"utf_32_be"}}, tmp))
