'''
Read, write, encode, and decode functions for all standard Field_Types.

Readers are responsible for reading bytes from a file that are to be turned
into a python object and calling their associated decoder on the bytes.

Writers are responsible for calling their associated encoder, using it
to encode the python object, and writing the encoded bytes to a file.

Readers and Writers are also responsible for calling the Reader/Writer
functions of their attributes and potentially the reader routines of their
Child and the children of all nested sub-structs. They also must return an
integer specifying what offset the last data was read from or written to.

Decoders are responsible for converting bytes into a python object*
Encoders are responsible for converting a python object into bytes*

Some functions do not require all of the arguments they are given, but many
of them do and it is easier to provide extra arguments that are ignored
than to provide exactly what is needed.

*Not all encoders and decoders receive/return bytes objects. Field_Types that
operate on the bit level cant be expected to return even byte sized amounts
of bits, so they instead receive an unsigned python integer and return an
unsigned integer, an offset, and a mask. A Field_Types reader, writer, encoder,
and decoder simply need to be working with the same arg and return data types.
'''

import shutil

from array import array
from struct import pack, unpack
from sys import byteorder
#for use in byteswapping arrays
byteorder_char = {'little':'<','big':'>'}[byteorder]

from supyr_struct.Defs.Constants import *
from supyr_struct.Tag_Block import Tag_Block, List_Block, P_List_Block



def Default_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                   Root_Offset=0, Offset=0, **kwargs):
    """
    This function exists so that blocks which dont actually set
    themselves can still have their default value set properly.
    This applies to Field_Types such as the "Bit_Int" types since
    their value is set by their parent Bit_Struct.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    """
    
    if Raw_Data is None:
        Parent[Attr_Index] = self.Default()
        
    return Offset



def Container_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                     Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a 'Container' type Tag_Block and places it into the
    Tag_Block 'Parent' at 'Attr_Index' and calls the Readers
    of each of its attributes. All the child blocks of this
    containers attributes(including its own child if applicable)
    will be built from here(unless any of those structs or their
    sub-structs designate themselves as a Build_Root).
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Raw_Data is None, the Tag_Block will
    be initialized with default values.
    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being built, rather than its parent.
    """
    
    if Attr_Index is None:
        Desc = Parent.DESC
        New_Container = Parent
    else:
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]

        #If there is a DEFAULT, it MUST be a Tag_Block Type,
        #not an instance. If it is an instance this code will crash.
        #There will be a check in the descriptor sanitization code
        #to make sure it is a Tag_Block subclass and nothing else.
        if CHILD in Desc:
            Block_Type = Desc.get(DEFAULT, P_List_Block)
        else:
            Block_Type = Desc.get(DEFAULT, List_Block)
        New_Container = Block_Type(Desc, Parent=Parent,
                                   Init_Attrs=Raw_Data is None)
        Parent[Attr_Index] = New_Container
        
    kwargs['Parents'] = []
    if CHILD in Desc:
        kwargs['Parents'].append(New_Container)

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
        
    Orig_Offset = Offset
    '''If there is a specific pointer to read the block from then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being built without a parent(such as from an exported .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if (isinstance(Desc.get(POINTER), int) or
        (Desc.get(POINTER) is not None and Attr_Index is not None)):
        Offset = New_Container.Get_Meta(POINTER)
    
    #loop once for each block in the object block
    for i in range(len(New_Container)):
        Offset = Desc[i][TYPE].Reader(New_Container, Raw_Data, i,
                                      Root_Offset, Offset, **kwargs)

    #build the children for all the blocks within this one
    for Block in kwargs['Parents']:
        Offset = Block.DESC[CHILD][TYPE].Reader(Block, Raw_Data, CHILD,
                                                Root_Offset, Offset, **kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset


def Array_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                 Root_Offset=0, Offset=0, **kwargs):
    """
    Builds an 'Array' type Tag_Block and places it into the
    Tag_Block 'Parent' at 'Attr_Index' and calls the shared
    SUB_STRUCT Reader on each of the elements in the array.
    All the child blocks of this arrays structs(including its
    own child if applicable) will be built from here(unless any
    of those structs or their sub-structs designate themselves
    as a Build_Root).
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Raw_Data is None, the Tag_Block will
    be initialized with default values.
    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being built, rather than its parent.
    """
    
    if Attr_Index is None:
        Desc = Parent.DESC
        New_Array_Block = Parent
    else:
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]

        #If there is a DEFAULT, it MUST be a Tag_Block Type,
        #not an instance. If it is an instance this code will crash.
        #There will be a check in the descriptor sanitization code
        #to make sure it is a Tag_Block subclass and nothing else.
        if CHILD in Desc:
            Block_Type = Desc.get(DEFAULT, P_List_Block)
        else:
            Block_Type = Desc.get(DEFAULT, List_Block)
        New_Array_Block = Block_Type(Desc, Parent=Parent,
                                     Init_Attrs=Raw_Data is None)
        Parent[Attr_Index] = New_Array_Block
        
    kwargs['Parents'] = []
    if CHILD in Desc:
        kwargs['Parents'].append(New_Array_Block)
    Array_Type = Desc[SUB_STRUCT][TYPE]

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
    
    Orig_Offset = Offset
    '''If there is a specific pointer to read the block from then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being built without a parent(such as from an exported .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if (isinstance(Desc.get(POINTER), int) or
        (Desc.get(POINTER) is not None and Attr_Index is not None)):
        Offset = New_Array_Block.Get_Meta(POINTER)
        
    for i in range(New_Array_Block.Get_Size()):
        Offset = Array_Type.Reader(New_Array_Block, Raw_Data, i,
                                   Root_Offset, Offset,**kwargs)
    
    for Block in kwargs['Parents']:
        Offset = Block.DESC[CHILD][TYPE].Reader(Block, Raw_Data, CHILD,
                                                Root_Offset, Offset,**kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset


def Switch_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                  Root_Offset=0, Offset=0, **kwargs):
    pass



def Struct_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                  Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a 'Struct' type Tag_Block and places it into the
    Tag_Block 'Parent' at 'Attr_Index' and calls the Readers
    of each of its attributes. If the descriptor specifies
    that this block is a Build_Root, then all the child blocks
    of all its sub-structs will be built from here(unless any
    of those sub-structs designate themselves as a Build_Root).
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Raw_Data is None, the Tag_Block will
    be initialized with default values.
    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being built, rather than its parent.
    """
    
    if Attr_Index is None:
        Desc = Parent.DESC
        New_Struct = Parent
    else:
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]

        #If there is a DEFAULT, it MUST be a Tag_Block Type,
        #not an instance. If it is an instance this code will crash.
        #There will be a check in the descriptor sanitization code
        #to make sure it is a Tag_Block subclass and nothing else.
        if CHILD in Desc:
            Block_Type = Desc.get(DEFAULT, P_List_Block)
        else:
            Block_Type = Desc.get(DEFAULT, List_Block)
        New_Struct = Block_Type(Desc, Parent=Parent,
                                Init_Attrs=Raw_Data is None)
        Parent[Attr_Index] = New_Struct
            
    Build_Root = 'Parents' not in kwargs or Desc.get(CHILD_ROOT)
    if Build_Root:    kwargs["Parents"] = []
    if CHILD in Desc: kwargs['Parents'].append(New_Struct)

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
        
    Orig_Offset = Offset

    """If there is file data to build the structure from"""
    if Raw_Data is not None:
        '''If there is a specific pointer to read the block from then go to it,
        Only do this, however, if the POINTER can be expected to be accurate.
        If the pointer is a path to a previously parsed field, but this block
        is being built without a parent(such as from an exported .blok file)
        then the path wont be valid. The current offset will be used instead.'''
        if (isinstance(Desc.get(POINTER), int) or
            (Desc.get(POINTER) is not None and Attr_Index is not None)):
            Offset = New_Struct.Get_Meta(POINTER)
            
        Offs = Desc['ATTR_OFFS']
        #loop for each attribute in the struct
        for i in range(len(New_Struct)):
            Desc[i][TYPE].Reader(New_Struct, Raw_Data, i, Root_Offset,
                                 Offset+Offs[Desc[i][NAME]], **kwargs)
            
        #increment offset by the size of the struct
        Offset += Desc[SIZE]
        
    if Build_Root:
        for Block in kwargs['Parents']:
            Offset = Block.DESC[CHILD][TYPE].Reader(Block, Raw_Data, CHILD,
                                                 Root_Offset, Offset, **kwargs)
            
    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset



def Fixed_Size_Data_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                           Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a python object determined by the Decoder and
    places it into the Tag_Block 'Parent' at 'Attr_Index'.
    Returns the offset this function finished reading at.

    This function differs from Data_Reader in that it is expected that
    the Size of the Field_Type is completely fixed and determined
    specifically in the Field_Type. A costly Block.Get_Size() isnt needed. 

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    """
    
    if Raw_Data is not None:
        #read and store the variable
        Raw_Data.seek(Root_Offset+Offset)
        Parent[Attr_Index] = self.Decoder(Raw_Data.read(self.Size),
                                          Parent, Attr_Index)
        return Offset + self.Size
    Parent[Attr_Index] = self.Default()
    return Offset


def Data_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a python object determined by the Decoder and
    places it into the Tag_Block 'Parent' at 'Attr_Index'.
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    """
    
    if Raw_Data is not None:
        #read and store the variable
        Raw_Data.seek(Root_Offset+Offset)
        Size = Parent.Get_Size(Attr_Index)
        Parent[Attr_Index] = self.Decoder(Raw_Data.read(Size),
                                          Parent, Attr_Index)
        return Offset + Size
    Parent[Attr_Index] = self.Default()
    return Offset



def CString_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                   Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a python string determined by the Decoder and
    places it into the Tag_Block 'Parent' at 'Attr_Index'.
    
    The strings length is unknown before hand, thus this
    function relies on locating the null terminator.
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    """
    
    if Raw_Data is not None:
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]
            
        if (isinstance(Desc.get(POINTER), int) or
            (Desc.get(POINTER) is not None and Attr_Index is not None)):
            Offset = Parent.Get_Meta(POINTER, Attr_Index)
            
        Start = Root_Offset+Offset
        Char_Size = self.Size
        Delimiter = self.Delimiter
        
        #if the character size is greater than 1 we need to do special
        #checks to ensure the position the null terminator was found at
        #is not overlapping the boundary between individual characters.
        Size = Raw_Data.find(Delimiter, Start)-Start

        #if length % char_size is not zero, it means the location lies
        #between individual characters. Try again from this spot + 1
        while Size % Char_Size:
            Size = Raw_Data.find(Delimiter, Start+Size+1)-Start

            if Size+Start < 0:
                raise IOError("Reached end of raw data and could not "+
                              "locate null terminator for string.")
        Raw_Data.seek(Start)
        #read and store the variable
        Parent[Attr_Index] = self.Decoder(Raw_Data.read(Size),
                                          Parent, Attr_Index)
        return Offset + Size
    Parent[Attr_Index] = self.Default()
        
    return Offset



def Py_Array_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                    Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a python array.array object and places it
    into the Tag_Block 'Parent' at 'Attr_Index'.
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Test(bool)

    If Raw_Data is None, the array will
    be initialized with a default value.
    """
    
    Byte_Count = Parent.Get_Size(Attr_Index)
    if Raw_Data is not None:
        Raw_Data.seek(Root_Offset+Offset)
        
        Offset += Byte_Count
        
        #If the tag is only being test loaded we skip
        #loading any raw data to save on RAM and speed.
        #When we do we make sure to set it's bytes size to 0
        if kwargs.get("Test"):
            Parent.Set_Size(0, Attr_Index)
            Py_Array = array(self.Enc)
        else:
            Py_Array = array(self.Enc, Raw_Data.read(Byte_Count))
            

        '''if the system the array is being created on
        has a different endianness than what the array is
        packed as, swap the endianness after reading it.'''
        if self.Endian != byteorder_char:
            Py_Array.byteswap()
        Parent[Attr_Index] = Py_Array
    else:
        Parent[Attr_Index] = array(self.Enc, b'\x00'*Byte_Count)
        
    return Offset



def Bytes_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                 Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a python bytes or bytearray object and places
    it into the Tag_Block 'Parent' at 'Attr_Index'.
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Test(bool)

    If Raw_Data is None, the Tag_Block will be
    initialized with default values.
    """
    
    if Raw_Data is not None:
        Byte_Count = Parent.Get_Size(Attr_Index)
        Raw_Data.seek(Root_Offset+Offset)
        
        Offset += Byte_Count
        
        #If the tag is only being test loaded we skip
        #loading any raw data to save on RAM and speed.
        #When we do we make sure to set it's bytes size to 0
        if kwargs.get("Test"):
            Parent.Set_Size(0, Attr_Index)
            Parent[Attr_Index] = self.Py_Type()
        else:
            if issubclass(self.Py_Type, bytes):
                Parent[Attr_Index] = Raw_Data.read(Byte_Count)
            else:
                Parent[Attr_Index] = bytearray(Raw_Data.read(Byte_Count))
    else:
        Parent[Attr_Index] = self.Default()
        
    return Offset



def Bit_Struct_Reader(self, Parent, Raw_Data=None, Attr_Index=None,
                      Root_Offset=0, Offset=0, **kwargs):
    """
    Builds a 'Struct' type Tag_Block and places it into the
    Tag_Block 'Parent' at 'Attr_Index' and calls the Readers
    of each of its attributes. If the descriptor specifies
    that this block is a Build_Root, then all the child blocks
    of all its sub-structs will be built from here(unless any
    of those sub-structs designate themselves as a Build_Root).
    Returns the offset this function finished reading at.

    Required arguments:
        Parent(Tag_Block)
    Optional arguments:
        Raw_Data(buffer) = None
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Raw_Data is None, the Tag_Block will
    be initialized with default values.
    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being built, rather than its parent.
    """
    
    #if the Attr_Index is None it means that this
    #is the root of the tag, and Parent is the
    #block we that this function is populating
    if Attr_Index is None:
        Desc = Parent.DESC
        New_Bit_Struct = Parent
    else:
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]
        Block_Type = Desc.get(DEFAULT, List_Block)
        New_Bit_Struct = Block_Type(Desc, Parent=Parent,
                                    Init_Attrs=(Raw_Data is None))
        Parent[Attr_Index] = New_Bit_Struct


    """If there is file data to build the structure from"""
    if Raw_Data is not None:
        Raw_Data.seek(Root_Offset+Offset)
        Struct_Size = Desc[SIZE]
        '''If there is a specific pointer to read the block from then go to it,
        Only do this, however, if the POINTER can be expected to be accurate.
        If the pointer is a path to a previously parsed field, but this block
        is being built without a parent(such as from an exported .blok file)
        then the path wont be valid. The current offset will be used instead.'''
        if (isinstance(Desc.get(POINTER), int) or
            (Desc.get(POINTER) is not None and Attr_Index is not None)):
            Offset = New_Bit_Struct.Get_Meta(POINTER)
            
        if self.Endian == '<':
            Raw_Int = int.from_bytes(Raw_Data.read(Struct_Size), 'little')
        else:
            Raw_Int = int.from_bytes(Raw_Data.read(Struct_Size), 'big')
        

        #loop for each attribute in the struct
        for i in range(len(New_Bit_Struct)):
            New_Bit_Struct[i] = Desc[i][TYPE].Decoder(Raw_Int,New_Bit_Struct,i)
            
        #increment offset by the size of the struct
        Offset += Struct_Size
        
    return Offset



def Container_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                     Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a 'Container' type Tag_Block in 'Attr_Index' of
    'Parent' to the supplied 'Write_Buffer' and calls the Writers
    of each of its attributes.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Container_Block = Parent[Attr_Index]
    except AttributeError:
        Container_Block = Parent
    except TypeError:
        Container_Block = Parent
    except IndexError:
        Container_Block = Parent
        
    Desc = Container_Block.DESC
    kwargs['Parents'] = []
    if hasattr(Container_Block, CHILD):
        kwargs['Parents'].append(Container_Block)

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
    
    Orig_Offset = Offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if (isinstance(Desc.get(POINTER), int) or
        (Desc.get(POINTER) is not None and Attr_Index is not None)):
        Offset = Container_Block.Get_Meta(POINTER)
        
    for i in range(len(Container_Block)):
        Offset = Desc[i][TYPE].Writer(Container_Block, Write_Buffer, i,
                                      Root_Offset, Offset, **kwargs)

    for Block in kwargs['Parents']:
        Offset = Block.DESC[CHILD][TYPE].Writer(Block, Write_Buffer, CHILD,
                                                Root_Offset, Offset,**kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset


def Array_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                 Root_Offset=0, Offset=0, **kwargs):
    """
    Writes an 'Array' type Tag_Block in 'Attr_Index' of
    'Parent' to the supplied 'Write_Buffer' and calls the Writers
    of each of its arrayed elements.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Array_Block = Parent[Attr_Index]
    except AttributeError:
        Array_Block = Parent
    except TypeError:
        Array_Block = Parent
    except IndexError:
        Array_Block = Parent
        
    Desc = Array_Block.DESC
    Element_Writer = Desc[SUB_STRUCT][TYPE].Writer
    kwargs['Parents'] = []
    if hasattr(Array_Block, CHILD):
        kwargs['Parents'].append(Array_Block)

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
    
    Orig_Offset = Offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if (isinstance(Desc.get(POINTER), int) or
        (Desc.get(POINTER) is not None and Attr_Index is not None)):
        Offset = Array_Block.Get_Meta(POINTER)
        
    for i in range(len(Array_Block)):
        Offset = Element_Writer(Array_Block, Write_Buffer, i,
                                Root_Offset, Offset, **kwargs)

    for Block in kwargs['Parents']:
        Offset = Block.DESC[CHILD][TYPE].Writer(Block, Write_Buffer, CHILD,
                                                Root_Offset, Offset,**kwargs)

    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset


def Struct_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                  Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a 'Struct' type Tag_Block in 'Attr_Index' of 'Parent'
    to the supplied 'Write_Buffer' and calls the Writers of
    each of its attributes.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0
    Optional kwargs:
        Parents(list)

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Struct_Block = Parent[Attr_Index]
    except AttributeError:
        Struct_Block = Parent
    except TypeError:
        Struct_Block = Parent
    except IndexError:
        Struct_Block = Parent
        
    Desc = Struct_Block.DESC
    Offsets = Desc['ATTR_OFFS']
    Struct_Size = Desc[SIZE]
    Build_Root = 'Parents' not in kwargs or Desc.get('CHILD_ROOT')
    
    if Build_Root: kwargs['Parents'] = []
    if hasattr(Struct_Block, CHILD):
        kwargs['Parents'].append(Struct_Block)

    if ALIGN in Desc:
        Align = Desc[ALIGN]
        Offset += (Align-(Offset%Align))%Align
    
    Orig_Offset = Offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if (isinstance(Desc.get(POINTER), int) or
        (Desc.get(POINTER) is not None and Attr_Index is not None)):
        Offset = Struct_Block.Get_Meta(POINTER)

    #write the whole size of the block so
    #any padding is filled in properly
    Write_Buffer.seek(Root_Offset+Offset)
    Write_Buffer.write(bytes(Struct_Size))
    
    for i in range(len(Struct_Block)):
        Desc[i][TYPE].Writer(Struct_Block, Write_Buffer, i, Root_Offset,
                             Offset+Offsets[Desc[i][NAME]], **kwargs)
        
    #increment offset by the size of the struct
    Offset += Struct_Size

    if Build_Root:
        for Block in kwargs['Parents']:
            Offset = Block.DESC[CHILD][TYPE].Writer(Block, Write_Buffer,
                                   CHILD, Root_Offset, Offset, **kwargs)

    #pass the incremented offset to the caller, unless specified not to
    if not Desc.get(CARRY_OFF, True):
        return Orig_Offset
    return Offset


    
def Data_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                    Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'Attr_Index' of 'Parent' to the supplied 'Write_Buffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Block = Parent[Attr_Index]
    except AttributeError:
        Block = Parent
    except TypeError:
        Block = Parent
    except IndexError:
        Block = Parent
            
    Block = self.Encoder(Block, Parent, Attr_Index)
    Write_Buffer.seek(Root_Offset+Offset)
    Write_Buffer.write(Block)
    
    return Offset + len(Block)


    
def CString_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                   Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'Attr_Index' of 'Parent' to the supplied 'Write_Buffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    if Attr_Index is None:
        Block = Parent
    else:
        Block = Parent[Attr_Index]
        
        if Parent.TYPE.Is_Array:
            Desc = Parent.DESC[SUB_STRUCT]
        else:
            Desc = Parent.DESC[Attr_Index]
            
        if (isinstance(Desc.get(POINTER), int) or
            (Desc.get(POINTER) is not None and Attr_Index is not None)):
            Offset = Parent.Get_Meta(POINTER, Attr_Index)
            
    Block = self.Encoder(Block, Parent, Attr_Index)
    Write_Buffer.seek(Root_Offset+Offset)
    Write_Buffer.write(Block)
    
    return Offset + len(Block)


def Py_Array_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                    Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a bytes representation of the python array in
    'Attr_Index' of 'Parent' to the supplied 'Write_Buffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Block = Parent[Attr_Index]
    except AttributeError:
        Block = Parent
    except TypeError:
        Block = Parent
    except IndexError:
        Block = Parent
    
    Write_Buffer.seek(Root_Offset+Offset)

    #if the system the array exists on has a different
    #endianness than what the array should be written as,
    #then the endianness is swapped before writing it.
    '''This is the only method I can think of to tell if
    the endianness of an array needs to be changed since
    the array.array objects dont know their own endianness'''
    if self.Endian != byteorder_char:
        Block.byteswap()
        Write_Buffer.write(Block)
        Block.byteswap()
    else:
        Write_Buffer.write(Block)
    
    return Offset + len(Block)*Block.itemsize


def Bytes_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                 Root_Offset=0, Offset=0, **kwargs):
    """
    Writes the bytes or bytearray object in 'Attr_Index'
    of 'Parent' to the supplied 'Write_Buffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Block = Parent[Attr_Index]
    except AttributeError:
        Block = Parent
    except TypeError:
        Block = Parent
    except IndexError:
        Block = Parent
    
    Write_Buffer.seek(Root_Offset+Offset)
    Write_Buffer.write(Block)
    
    return Offset + len(Block)



def Bit_Struct_Writer(self, Parent, Write_Buffer, Attr_Index=None,
                      Root_Offset=0, Offset=0, **kwargs):
    """
    Writes a 'Bit Struct' type Tag_Block in 'Attr_Index' of
    'Parent' to the supplied 'Write_Buffer'. All attributes of
    the Bit_Struct are converted to unsigned integers, merged
    together on the bit level, and the result is written.
    Returns the offset this function finished writing at.

    Required arguments:
        Parent(Tag_Block)
        Write_Buffer(buffer)
    Optional arguments:
        Attr_Index(int, str) = None
        Root_Offset(int) = 0
        Offset(int) = 0

    If Attr_Index is None, 'Parent' is expected to be
    the Tag_Block being written, rather than its parent.
    """
    
    try:
        Bit_Struct_Block = Parent[Attr_Index]
    except AttributeError:
        Bit_Struct_Block = Parent
    except TypeError:
        Bit_Struct_Block = Parent
    except IndexError:
        Bit_Struct_Block = Parent
        
    if hasattr(Bit_Struct_Block, CHILD):
        kwargs['Parents'].append(Bit_Struct_Block)
        
    Data = 0
    Desc = Bit_Struct_Block.DESC
    Struct_Size = Desc[SIZE]
    
    #get a list of everything as unsigned
    #ints with their masks and offsets
    for i in range(len(Bit_Struct_Block)):
        Bit_Int = Desc[i][TYPE].Encoder(Bit_Struct_Block[i],Bit_Struct_Block,i)

        #combine with the other data
        #0 = actual U_Int, 1 = bit offset of int
        Data += Bit_Int[0] << Bit_Int[1]
    
    Write_Buffer.seek(Root_Offset+Offset)
    
    if self.Endian == '<':
        Write_Buffer.write(Data.to_bytes(Struct_Size, 'little'))
    else:
        Write_Buffer.write(Data.to_bytes(Struct_Size, 'big'))


    return Offset + Struct_Size






def Decode_Numeric(self, Bytes, Parent=None, Attr_Index=None):
    """
    Converts a bytes object into a python int
    Decoding is done using struct.unpack
    
    Returns an int decoded represention of the "Bytes" argument.

    Required arguments:
        Bytes(Bytes)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    """
    
    return unpack(self.Enc, Bytes)[0]
                

def Decode_String(self, Bytes, Parent=None, Attr_Index=None):
    """
    Decodes a bytes object into a python string
    with the delimiter character sliced off the end.
    Decoding is done using bytes.decode
    
    Returns a string decoded represention of the "Bytes" argument.

    Required arguments:
        Bytes(Bytes)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    """
    
    return Bytes.decode(encoding=self.Enc).strip(self.Str_Delimiter)


def Decode_Raw_String(self, Bytes, Parent=None, Attr_Index=None):
    """
    Decodes a bytes object into a python string.
    Decoding is done using bytes.decode
    
    Returns a string decoded represention of the "Bytes" argument.

    Required arguments:
        Bytes(Bytes)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    """
    
    return Bytes.decode(encoding=self.Enc)


def Decode_Big_Int(self, Bytes, Parent=None, Attr_Index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Decoding is done using int.from_bytes
    
    Returns an int represention of the "Bytes" argument.
    
    Required arguments:
        Bytes(object)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    '''

    if len(Bytes):
        if self.Endian == '<':
            Endian = 'little'
        else:
            Endian = 'big'
    
        if self.Enc.endswith('s'):
            #ones compliment
            Big_Int = int.from_bytes(Bytes, Endian, signed=True)
            if Big_Int < 0:
                return Big_Int + 1
            else:
                return Big_Int
        elif self.Enc.endswith('S'):
            #twos compliment
            return int.from_bytes(Bytes, Endian, signed=True)
        else:
            return int.from_bytes(Bytes, Endian)
    else:
        #If an empty bytes object was provided, return a zero.
        '''Not sure if this should be an exception instead.'''
        return 0


def Decode_Bit_Int(self, Raw_Int, Parent, Attr_Index):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment
    
    Returns an int represention of the "Raw_Int" argument
    after masking and bit-shifting.
    
    Required arguments:
        Raw_Int(int)
        Parent(Tag_Block)
        Attr_Index(int)
    '''
    
    Bit_Count = Parent.Get_Size(Attr_Index)
    
    if Bit_Count:
        Offset = Parent.ATTR_OFFS[Parent.DESC[Attr_Index][NAME]]
        Mask   = (1<<Bit_Count)-1

        #mask and shift the int out of the Raw_Int
        Bit_Int = (Raw_Int >> Offset) & Mask
        
        #if the number would be negative if signed
        if Bit_Int&(1<<(Bit_Count-1)):
            if self.Enc.endswith('s'):
                #get the ones compliment and change the sign
                Int_Mask = ((1 << (Bit_Count-1))-1)
                Bit_Int = -1*((~Bit_Int)&Int_Mask)
            elif self.Enc.endswith('S'):
                #get the twos compliment and change the sign
                Int_Mask = ((1 << (Bit_Count-1))-1)
                Bit_Int = -1*((~Bit_Int+1)&Int_Mask)
                
        return Bit_Int
    else:
        #If the bit count is zero, return a zero
        '''Not sure if this should be an exception instead.'''
        return 0





def Encode_Numeric(self, Block, Parent=None, Attr_Index=None):
    '''
    Encodes a python int into a bytes representation.
    Encoding is done using struct.pack
    
    Returns a bytes object encoded represention of the "Block" argument.

    Required arguments:
        Block(object)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    '''
    
    return pack(self.Enc, Block)

def Encode_String(self, Block, Parent=None, Attr_Index=None):
    """
    Encodes a python string into a bytes representation,
    making sure there is a delimiter character on the end.
    Encoding is done using str.encode
    
    Returns a bytes object encoded represention of the "Block" argument.

    Required arguments:
        Block(object)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    """
    
    if self.Is_Delimited and not Block.endswith(self.Str_Delimiter):
        Block += self.Str_Delimiter
        
    return str.encode(Block, self.Enc)

def Encode_Raw_String(self, Block, Parent=None, Attr_Index=None):
    """
    Encodes a python string into a bytes representation.
    Encoding is done using str.encode
    
    Returns a bytes object encoded represention of the "Block" argument.
    
    Required arguments:
        Block(object)
    Optional arguments:
        Parent(Tag_Block) = None
        Attr_Index(int) = None
    """
    return str.encode(Block, self.Enc)

def Encode_Big_Int(self, Block, Parent, Attr_Index):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Encoding is done using int.to_bytes
    
    Returns a bytes object encoded represention of the "Block" argument.
    
    Required arguments:
        Block(object)
        Parent(Tag_Block)
        Attr_Index(int)
    '''
    
    Byte_Count = Parent.Get_Size(Attr_Index)
    
    if Byte_Count:
        if self.Endian == '<':
            Endian = 'little'
        else:
            Endian = 'big'
    
        if self.Enc.endswith('S'):
            #twos compliment
            return Block.to_bytes(Byte_Count, Endian, signed=True)
        elif self.Enc.endswith('s'):
            #ones compliment
            if Block < 0:
                return (Block-1).to_bytes(Byte_Count, Endian, signed=True)
            
            return Block.to_bytes(Byte_Count, Endian, signed=True)
        else:
            return Block.to_bytes(Byte_Count, Endian)
    else:
        return bytes()


def Encode_Bit_Int(self, Block, Parent, Attr_Index):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment
    
    Returns the encoded 'Block', bit offset, and bit mask.
    This is done so they can be combined with the rest of a Bit_Struct.
    
    Required arguments:
        Block(object)
        Parent(Tag_Block)
        Attr_Index(int)
    '''
    
    Offset    = Parent.ATTR_OFFS[Parent.DESC[Attr_Index][NAME]]
    Bit_Count = Parent.Get_Size(Attr_Index)
    Mask      = (1<<Bit_Count)-1
    
    #if the number is signed
    if Block < 0:
        Sign_Mask = 1<<(Bit_Count-1)

        #because of the inability to efficiently
        #access the Bit_Count of the int directly, this
        #is the best workaround I can come up with
        if self.Enc.endswith('S'):
            return( 2*Sign_Mask + Block, Offset, Mask)
        else:
            return(   Sign_Mask - Block, Offset, Mask)
    else:
        return(Block, Offset, Mask)



'''These next methods are exclusively used for the Null Field_Type.'''
def No_Read(self, Parent, Raw_Data=None, Attr_Index=None,
            Root_Offset=0, Offset=0, *args, **kwargs):
    '''Reads nothing, returns the provided argument 'Offset'.'''
    return Offset
def No_Write(self, Parent, Write_Buffer=None, Attr_Index=None,
            Root_Offset=0, Offset=0, *args, **kwargs):
    '''Writes nothing, returns the provided argument 'Offset'.'''
    return Offset
def No_Decode(*args, **kwargs):
    '''Returns an empty bytes object'''
    return bytes()
def No_Encode(*args, **kwargs):
    '''Returns an empty bytes object'''
    return bytes()
