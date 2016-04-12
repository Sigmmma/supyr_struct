'''
Read, write, encode, and decode functions for all standard fields.

Readers are responsible for reading bytes from a file that are to be turned
into a python object and calling their associated decoder on the bytes.

Writers are responsible for calling their associated encoder, using it
to encode the python object, and writing the encoded bytes to a file.

Readers and Writers are also responsible for calling the reader/writer
functions of their attributes and potentially the reader routines of their
Child and the children of all nested sub-structs. They also must return an
integer specifying what offset the last data was read from or written to.

Decoders are responsible for converting bytes into a python object*
Encoders are responsible for converting a python object into bytes*

Some functions do not require all of the arguments they are given, but many
of them do and it is easier to provide extra arguments that are ignored
than to provide exactly what is needed.

*Not all encoders and decoders receive/return bytes objects. fields that
operate on the bit level cant be expected to return even byte sized amounts
of bits, so they instead receive an unsigned python integer and return an
unsigned integer, an offset, and a mask. A fields reader, writer, encoder,
and decoder simply need to be working with the same arg and return data types.
'''

__all__ = [ 'byteorder_char',
            #Basic routines
    
            #Readers
            'container_reader', 'array_reader', 'no_read',
            'struct_reader', 'bit_struct_reader', 'py_array_reader',
            'data_reader', 'cstring_reader', 'bytes_reader',
            #Writers
            'container_writer', 'array_writer', 'no_write',
            'struct_writer', 'bit_struct_writer', 'py_array_writer',
            'data_writer', 'cstring_writer', 'bytes_writer',
            #Decoders
            'decode_numeric', 'decode_string', 'no_decode',
            'decode_big_int', 'decode_bit_int',
            #Encoders
            'encode_numeric', 'encode_string', 'no_encode',
            'encode_big_int', 'encode_bit_int',
            #size calculators
            'no_sizecalc', 'def_sizecalc', 'len_sizecalc',
            'delim_str_sizecalc', 'str_sizecalc',

            #Specialized routines
            
            #Readers
            'default_reader', 'f_s_data_reader', 'void_reader',
            'switch_reader', 'while_array_reader',
            #Writers
            'void_writer',
            #Decoders
            'decode_24bit_numeric', 'decode_bit', 'decode_timestamp',
            #Encoders
            'encode_24bit_numeric', 'encode_bit', 'encode_raw_string',
            'encode_int_timestamp', 'encode_float_timestamp',
            #size calculators
            'delim_utf_sizecalc', 'utf_sizecalc', 'array_sizecalc',
            'big_sint_sizecalc', 'big_uint_sizecalc',
            'bit_sint_sizecalc', 'bit_uint_sizecalc',
            ]

import shutil

from math import log, ceil
from struct import pack, unpack
from sys import byteorder
from time import mktime, ctime, strptime

#for use in byteswapping arrays
byteorder_char = {'little':'<','big':'>'}[byteorder]

from supyr_struct.defs.constants import *


def default_reader(self, desc, parent, rawdata=None, attr_index=None, 
                   root_offset=0, offset=0, **kwargs):
    """
    This function exists so that blocks which dont actually set
    themselves can still have their default value set properly.
    This applies to fields such as the "bitint" types since
    their value is set by their parent BitStruct.

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    """
    
    if rawdata is None and attr_index is not None:
        if not issubclass(self.py_type, blocks.Block):
            parent[attr_index] = desc.get('DEFAULT', self.default())
        elif self.data_type is type(None):
            parent[attr_index] = desc.get('DEFAULT', self.py_type)(desc)
        else:
            parent[attr_index] = self.py_type(desc, init_attrs=True)
        
    return offset



def container_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                     root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Container' type Block and places it into the
    Block 'parent' at 'attr_index' and calls the Readers
    of each of its attributes. All the child blocks of this
    containers attributes(including its own child if applicable)
    will be built from here.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
    Optional arguments:
        parent(Block)
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will
    be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    
    if attr_index is None and parent is not None:
        new_block = parent
    else:
        new_block = desc.get('DEFAULT',self.py_type)(desc, parent=parent,
                                                    init_attrs=rawdata is None)
        parent[attr_index] = new_block
        
    kwargs['parents'] = []
    if 'CHILD' in desc:
        kwargs['parents'].append(new_block)

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
        
    orig_offset = offset
    '''If there is a specific pointer to read the block from then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being built without a parent(such as from an exported .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = new_block.get_meta('POINTER', **kwargs)
    
    #loop once for each block in the object block
    for i in range(len(new_block)):
        b_desc = desc[i]
        offset = b_desc['TYPE'].reader(b_desc, new_block, rawdata, i,
                                       root_offset, offset, **kwargs)

    #build the children for all the blocks within this one
    for block in kwargs['parents']:
        c_desc = block.DESC['CHILD']
        offset = c_desc['TYPE'].reader(c_desc, block, rawdata, 'CHILD',
                                       root_offset, offset, **kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset


def array_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                 root_offset=0, offset=0, **kwargs):
    """
    Builds an 'Array' type Block and places it into the
    Block 'parent' at 'attr_index' and calls the shared
    SUB_STRUCT reader on each of the elements in the array.
    All the child blocks of this arrays structs(including its
    own child if applicable) will be built from here.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
    Optional arguments:
        parent(Block)
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will
    be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    
    if attr_index is None and parent is not None:
        new_block = parent
    else:
        new_block = desc.get('DEFAULT',self.py_type)(desc, parent=parent,
                                                    init_attrs=rawdata is None)
        parent[attr_index] = new_block
        
    kwargs['parents'] = []
    if 'CHILD' in desc:
        kwargs['parents'].append(new_block)
    b_desc = desc['SUB_STRUCT']
    b_field = b_desc['TYPE']

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
    
    orig_offset = offset
    '''If there is a specific pointer to read the block from then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being built without a parent(such as from an exported .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = new_block.get_meta('POINTER', **kwargs)
        
    for i in range(new_block.get_size()):
        offset = b_field.reader(b_desc, new_block, rawdata, i,
                                root_offset, offset,**kwargs)
    
    for block in kwargs['parents']:
        c_desc = block.DESC['CHILD']
        offset = c_desc['TYPE'].reader(c_desc, block, rawdata, 'CHILD',
                                       root_offset, offset, **kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset



def while_array_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                       root_offset=0, offset=0, **kwargs):
    """
    Builds a 'WhileArray' type Block and places it into
    the Block 'parent' at 'attr_index' and calls the shared
    SUB_STRUCT reader on each of the elements in the array.
    All the child blocks of this arrays structs(including its
    own child if applicable) will be built from here.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
    Optional arguments:
        parent(Block)
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will
    be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    
    if attr_index is None and parent is not None:
        new_block = parent
    else:
        new_block = desc.get('DEFAULT',self.py_type)(desc, parent=parent,
                                                    init_attrs=rawdata is None)
        parent[attr_index] = new_block
        
    kwargs['parents'] = []
    if 'CHILD' in desc:
        kwargs['parents'].append(new_block)
    b_desc = desc['SUB_STRUCT']
    b_field = b_desc['TYPE']

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
    
    orig_offset = offset
    '''If there is a specific pointer to read the block from then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being built without a parent(such as from an exported .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = new_block.get_meta('POINTER', **kwargs)

    decider = desc['CASE']
    i = 0
    while decider(parent=new_block, attr_index=i, rawdata=rawdata,
                  root_offset=root_offset, offset=offset):
        #make a new slot in the new array for the new array element
        new_block.append(None)
        offset = b_field.reader(b_desc, new_block, rawdata, i,
                                   root_offset, offset,**kwargs)
        i += 1
    
    for block in kwargs['parents']:
        c_desc = block.DESC['CHILD']
        offset = c_desc['TYPE'].reader(c_desc, block, rawdata, 'CHILD',
                                       root_offset, offset, **kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset



def switch_reader(self, desc, parent, rawdata=None, attr_index=None,
                  root_offset=0, offset=0, **kwargs):
    """
    Selects a descriptor to build by using  parent.get_meta('CASE')
    and using that value to select a descriptor from desc['CASE_MAP'].
    Passes all supplied arg and kwargs onto the selected descriptors
    Field.reader() with the desc arg changed to the selected desc.
    
    Returns the return value of the selected desc['TYPE'].reader()

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        case(str, int)
    """
    #A case may be provided through kwargs.
    #This is to allow overriding behavior of the switch and
    #to allow creating a Block specified by the user
    case     = desc['CASE']
    case_map = desc['CASE_MAP']

    if 'case' in kwargs:
        case = kwargs['case']
        del kwargs['case']
    else:
        if isinstance(attr_index, int):
            block = parent[attr_index]
        elif isinstance(attr_index, str):
            block = parent.__getattr__(attr_index)
        else:
            block = parent

        try:
            parent = block.PARENT
        except AttributeError:
            pass

        if isinstance(case, str):
            '''get the pointed to meta data by traversing the tag
            structure along the path specified by the string'''
            case = parent.get_neighbor(case, block)
        elif hasattr(case, "__call__"):
            try:
                #try to reposition the rawdata if it needs to be peeked
                rawdata.seek(root_offset + offset)
            except AttributeError:
                pass
            case = case(parent=parent, attr_index=attr_index, rawdata=rawdata,
                        block=block, offset=offset, root_offset=root_offset)

    #get the descriptor to use to build the block
    #based on what the CASE meta data says
    desc = desc.get(case_map.get(case, 'DEFAULT'))

    return desc['TYPE'].reader(desc, parent, rawdata, attr_index,
                               root_offset, offset, **kwargs)



def struct_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                  root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Struct' type Block and places it into the
    Block 'parent' at 'attr_index' and calls the Readers
    of each of its attributes. If the descriptor specifies
    that this block is a build_root, then all the child blocks
    of all its sub-structs will be built from here.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
    Optional arguments:
        parent(Block)
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will
    be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    
    if attr_index is None and parent is not None:
        new_block = parent
    else:
        new_block = desc.get('DEFAULT',self.py_type)(desc, parent=parent,
                                                    init_attrs=rawdata is None)
        parent[attr_index] = new_block
            
    build_root = 'parents' not in kwargs
    if build_root:
        kwargs["parents"] = []
    if 'CHILD' in desc:
        kwargs['parents'].append(new_block)

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
        
    orig_offset = offset

    """If there is file data to build the structure from"""
    if rawdata is not None:
        '''If there is a specific pointer to read the block from then go to it,
        Only do this, however, if the POINTER can be expected to be accurate.
        If the pointer is a path to a previously parsed field, but this block
        is being built without a parent(such as from an exported .blok file)
        then the path wont be valid. The current offset will be used instead.'''
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = new_block.get_meta('POINTER', **kwargs)
            
        offsets = desc['ATTR_OFFS']
        #loop for each attribute in the struct
        for i in range(len(new_block)):
            b_desc = desc[i]
            b_desc['TYPE'].reader(b_desc, new_block, rawdata, i, root_offset,
                                  offset+offsets[i], **kwargs)
            
        #increment offset by the size of the struct
        offset += desc['SIZE']
        
    if build_root:
        for block in kwargs['parents']:
            c_desc = block.DESC['CHILD']
            offset = c_desc['TYPE'].reader(c_desc, block, rawdata, 'CHILD',
                                           root_offset, offset, **kwargs)
            
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset



def f_s_data_reader(self, desc, parent, rawdata=None, attr_index=None,
                    root_offset=0, offset=0, **kwargs):
    """
    f_s == fixed_size
    Builds a python object determined by the decoder and
    places it into the Block 'parent' at 'attr_index'.
    Returns the offset this function finished reading at.

    This function differs from data_reader in that it is expected that
    the size of the Field has a fixed size, which is determined
    specifically in the Field. A costly Block.get_size() isnt needed. 

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    """
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and " + \
           "not None when reading a 'data' Field."
    if rawdata:
        #read and store the variable
        rawdata.seek(root_offset+offset)    
        parent[attr_index] = self.decoder(rawdata.read(self.size),
                                          parent, attr_index)
        return offset + self.size
    elif not issubclass(self.py_type, blocks.Block):
        parent[attr_index] = desc.get('DEFAULT', self.default())
    else:
        #this block is a Block, so it needs its descriptor
        parent[attr_index] = self.py_type(desc, init_attrs=True)
        
    return offset


def data_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                root_offset=0, offset=0, **kwargs):
    """
    Builds a python object determined by the decoder and
    places it into the Block 'parent' at 'attr_index'.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    """
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'data' Field."
    if rawdata:
        #read and store the variable
        rawdata.seek(root_offset+offset)
        size = parent.get_size(attr_index, offset = offset,
                               root_offset = root_offset,
                               rawdata = rawdata, **kwargs)
        parent[attr_index] = self.decoder(rawdata.read(size),
                                          parent, attr_index)
        return offset + size
    elif not issubclass(self.py_type, blocks.Block):
        parent[attr_index] = desc.get('DEFAULT', self.default())
    else:
        #this block is a Block, so it needs its descriptor
        parent[attr_index] = self.py_type(desc, init_attrs=True)
        
    return offset



def cstring_reader(self, desc, parent, rawdata=None, attr_index=None,
                   root_offset=0, offset=0, **kwargs):
    """
    Builds a python string determined by the decoder and
    places it into the Block 'parent' at 'attr_index'.
    
    The strings length is unknown before hand, thus this
    function relies on locating the null terminator.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    """
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'data' Field."
    
    if rawdata is not None:
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
            
        start = root_offset+offset
        charsize = self.size
        delimiter = self.delimiter
        
        #if the character size is greater than 1 we need to do special
        #checks to ensure the position the null terminator was found at
        #is not overlapping the boundary between individual characters.
        size = rawdata.find(delimiter, start)-start

        #if length % char_size is not zero, it means the location lies
        #between individual characters. Try again from this spot + 1
        while size % charsize:
            size = rawdata.find(delimiter, start+size+1)-start

            if size+start < 0:
                raise IOError("Reached end of raw data and could not "+
                              "locate null terminator for string.")
        rawdata.seek(start)
        #read and store the variable
        parent[attr_index] = self.decoder(rawdata.read(size),
                                          parent, attr_index)

        #pass the incremented offset to the caller, unless specified not to
        if desc.get('CARRY_OFF', True):
            return offset + size + charsize
        return orig_offset
    elif not issubclass(self.py_type, blocks.Block):
        parent[attr_index] = desc.get('DEFAULT', self.default())
    else:
        #this block is a Block, so it needs its descriptor
        parent[attr_index] = self.py_type(desc, init_attrs=True)
    return offset
        



def py_array_reader(self, desc, parent, rawdata=None, attr_index=None,
                    root_offset=0, offset=0, **kwargs):
    """
    Builds a python array.array object and places it
    into the Block 'parent' at 'attr_index'.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        int_test(bool)

    If rawdata is None, the array will
    be initialized with a default value.
    """
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'data' Field."
    
    if rawdata is not None:
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
        bytecount = parent.get_size(attr_index, offset = offset,
                                     root_offset = root_offset,
                                     rawdata = rawdata, **kwargs)
            
        rawdata.seek(root_offset+offset)
        
        offset += bytecount
        
        #If the tag is only being test loaded we skip
        #loading any raw data to save on RAM and speed.
        #When we do we make sure to set it's bytes size to 0
        if kwargs.get("int_test"):
            parent.set_size(0, attr_index)
            py_array = self.py_type(self.enc)
        else:
            py_array = self.py_type(self.enc, rawdata.read(bytecount))
            

        '''if the system the array is being created on
        has a different endianness than what the array is
        packed as, swap the endianness after reading it.'''
        if self.endian != byteorder_char and self.endian != '=':
            py_array.byteswap()
        parent[attr_index] = py_array
        
        #pass the incremented offset to the caller, unless specified not to
        if desc.get('CARRY_OFF', True):
            return offset
        return orig_offset
    elif not issubclass(self.py_type, blocks.Block):
        '''this may seem redundant, but it has to be done AFTER
        the offset is set to whatever the pointer may be, as
        such it has to come after the pointer getting code.'''
        if 'DEFAULT' in desc:
            parent[attr_index] = self.py_type(self.enc, desc.get('DEFAULT'))
        else:
            bytecount = parent.get_size(attr_index, offset = offset,
                                         root_offset = root_offset,
                                         rawdata = rawdata, **kwargs)
            parent[attr_index] = self.py_type(self.enc, b'\x00'*bytecount)
    else:
        #this block is a Block, so it needs its descriptor
        parent[attr_index] = self.py_type(desc, init_attrs=True)
    return offset



def bytes_reader(self, desc, parent, rawdata=None, attr_index=None,
                 root_offset=0, offset=0, **kwargs):
    """
    Builds a python bytes or bytearray object and places
    it into the Block 'parent' at 'attr_index'.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        int_test(bool)

    If rawdata is None, the Block will be
    initialized with default values.
    """
    assert parent is not None and attr_index is not None,\
           "'parent' and 'attr_index' must be provided and "+\
           "not None when reading a 'data' Field."
    if rawdata is not None:
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
            
        bytecount = parent.get_size(attr_index, offset = offset,
                                     root_offset = root_offset,
                                     rawdata = rawdata, **kwargs)
        rawdata.seek(root_offset+offset)
        offset += bytecount
        
        #If the tag is only being test loaded we skip
        #loading any raw data to save on RAM and speed.
        #When we do we make sure to set it's bytes size to 0
        if kwargs.get("int_test"):
            parent.set_size(0, attr_index)
            parent[attr_index] = self.py_type()
        else:
            parent[attr_index] = self.py_type(rawdata.read(bytecount))
                
        #pass the incremented offset to the caller, unless specified not to
        if desc.get('CARRY_OFF', True):
            return offset
        return orig_offset
    elif not issubclass(self.py_type, blocks.Block):
        '''this may seem redundant, but it has to be done AFTER
        the offset is set to whatever the pointer may be, as
        such it has to come after the pointer getting code.'''
        if 'DEFAULT' in desc:
            parent[attr_index] = self.py_type(desc.get('DEFAULT'))
        else:
            bytecount = parent.get_size(attr_index, offset = offset,
                                         root_offset = root_offset,
                                         rawdata = rawdata, **kwargs)
            parent[attr_index] = self.py_type(b'\x00'*bytecount)
    else:
        #this block is a Block, so it needs its descriptor
        parent[attr_index] = self.py_type(desc, init_attrs=True)
    return offset
    



def bit_struct_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                      root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Struct' type Block and places it into the
    Block 'parent' at 'attr_index' and calls the Readers
    of each of its attributes.
    Returns the offset this function finished reading at.

    Required arguments:
        desc
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If rawdata is None, the Block will
    be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    
    #if the attr_index is None it means that this
    #is the root of the tag, and parent is the
    #block we that this function is populating
    if attr_index is None and parent is not None:
        new_block = parent
    else:            
        new_block = desc.get('DEFAULT',self.py_type)(desc, parent=parent,
                                                    init_attrs=rawdata is None)
        parent[attr_index] = new_block

    """If there is file data to build the structure from"""
    if rawdata is not None:
        rawdata.seek(root_offset+offset)
        structsize = desc['SIZE']
        if self.endian == '<':
            rawint = int.from_bytes(rawdata.read(structsize), 'little')
        else:
            rawint = int.from_bytes(rawdata.read(structsize), 'big')
        

        #loop for each attribute in the struct
        for i in range(len(new_block)):
            new_block[i] = desc[i]['TYPE'].decoder(rawint, new_block, i)
            
        #increment offset by the size of the struct
        offset += structsize        

    return offset



def container_writer(self, parent, writebuffer, attr_index=None,
                     root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Container' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer' and calls the Writers
    of each of its attributes.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    try:
        block = parent[attr_index]
    except (AttributeError, TypeError, IndexError, KeyError):
        block = parent
        
    desc = block.DESC
    kwargs['parents'] = []
    if hasattr(block, 'CHILD'):
        kwargs['parents'].append(block)

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
    
    orig_offset = offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = block.get_meta('POINTER', **kwargs)
        
    for i in range(len(block)):
        #Trust that each of the entries in the container is a Block
        try:
            attr_desc = block[i].DESC
        except (TypeError,AttributeError):
            attr_desc = desc[i]
        offset = attr_desc['TYPE'].writer(block, writebuffer, i,
                                          root_offset, offset, **kwargs)

    for block in kwargs['parents']:
        try:
            c_desc = block.CHILD.DESC
        except AttributeError:
            c_desc = block.DESC['CHILD']
        offset = c_desc['TYPE'].writer(block, writebuffer, 'CHILD',
                                       root_offset ,offset, **kwargs)
        
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset



def array_writer(self, parent, writebuffer, attr_index=None,
                 root_offset=0, offset=0, **kwargs):
    """
    Writes an 'Array' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer' and calls the Writers
    of each of its arrayed elements.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    try:
        block = parent[attr_index]
    except (AttributeError,TypeError,IndexError,KeyError):
        block = parent
        
    desc = block.DESC
    element_writer = desc['SUB_STRUCT']['TYPE'].writer
    kwargs['parents'] = []
    if hasattr(block, 'CHILD'):
        kwargs['parents'].append(block)

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
    
    orig_offset = offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = block.get_meta('POINTER', **kwargs)
        
    for i in range(len(block)):
        #Trust that each of the entries in the container is a Block
        try:
            writer = block[i].DESC['TYPE'].writer
        except (TypeError, AttributeError):
            writer = element_writer
        offset = writer(block, writebuffer, i, root_offset, offset, **kwargs)

    for block in kwargs['parents']:
        try:
            c_desc = block.CHILD.DESC
        except AttributeError:
            c_desc = block.DESC['CHILD']
        offset = c_desc['TYPE'].writer(block, writebuffer, 'CHILD',
                                       root_offset ,offset, **kwargs)

    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset


def struct_writer(self, parent, writebuffer, attr_index=None,
                  root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Struct' type Block in 'attr_index' of 'parent'
    to the supplied 'writebuffer' and calls the Writers of
    each of its attributes.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    try:
        block = parent[attr_index]
    except (AttributeError,TypeError,IndexError,KeyError):
        block = parent
        
    desc = block.DESC
    offsets = desc['ATTR_OFFS']
    structsize = desc['SIZE']
    build_root = 'parents' not in kwargs
    
    if build_root:
        kwargs['parents'] = []
    if hasattr(block, 'CHILD'):
        kwargs['parents'].append(block)

    if 'ALIGN' in desc:
        align = desc['ALIGN']
        offset += (align-(offset%align))%align
    
    orig_offset = offset
    '''If there is a specific pointer to write the block to then go to it,
    Only do this, however, if the POINTER can be expected to be accurate.
    If the pointer is a path to a previously parsed field, but this block
    is being written without a parent(such as when exporting a .blok file)
    then the path wont be valid. The current offset will be used instead.'''
    if attr_index is not None and desc.get('POINTER') is not None:
        offset = block.get_meta('POINTER', **kwargs)

    #write the whole size of the block so
    #any padding is filled in properly
    writebuffer.seek(root_offset+offset)
    writebuffer.write(bytes(structsize))
    
    for i in range(len(block)):
        #structs usually dont contain blocks, so dont assume
        #each entry has a descriptor, but instead check
        if hasattr(block[i],'DESC'):
            attr_desc = block[i].DESC
        else:
            attr_desc = desc[i]
        attr_desc['TYPE'].writer(block, writebuffer, i, root_offset,
                                 offset+offsets[i], **kwargs)
        
    #increment offset by the size of the struct
    offset += structsize

    if build_root:
        for block in kwargs['parents']:
            try:
                c_desc = block.CHILD.DESC
            except AttributeError:
                c_desc = block.DESC['CHILD']
            offset = c_desc['TYPE'].writer(block, writebuffer, 'CHILD',
                                           root_offset, offset, **kwargs)

    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset
    return orig_offset


    
def data_writer(self, parent, writebuffer, attr_index=None,
                root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    try:
        block = parent[attr_index]
    except (AttributeError,TypeError,IndexError,KeyError):
        block = parent
            
    block = self.encoder(block, parent, attr_index)
    writebuffer.seek(root_offset+offset)
    writebuffer.write(block)
    return offset + len(block)


    
def cstring_writer(self, parent, writebuffer, attr_index=None,
                   root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    if parent is None or attr_index is None:
        block = parent
        desc = {}
    else:
        block = parent[attr_index]
        
        p_desc = parent.DESC
        if p_desc['TYPE'].is_array:
            desc = p_desc['SUB_STRUCT']
        else:
            desc = p_desc[attr_index]
            
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
            
    block = self.encoder(block, parent, attr_index)
    writebuffer.seek(root_offset+offset)
    writebuffer.write(block)
    
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset + len(block)
    return orig_offset


def py_array_writer(self, parent, writebuffer, attr_index=None,
                    root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python array in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """

    if parent is None or attr_index is None:
        block = parent
        desc = {}
    else:
        block = parent[attr_index]
        
        p_desc = parent.DESC
        if p_desc['TYPE'].is_array:
            desc = p_desc['SUB_STRUCT']
        else:
            desc = p_desc[attr_index]
            
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
        
    writebuffer.seek(root_offset+offset)

    #if the system the array exists on has a different
    #endianness than what the array should be written as,
    #then the endianness is swapped before writing it.
    '''This is the only method I can think of to tell if
    the endianness of an array needs to be changed since
    the array.array objects dont know their own endianness'''

    if self.endian != byteorder_char and self.endian != '=':
        block.byteswap()
        writebuffer.write(block)
        block.byteswap()
    else:
        writebuffer.write(block)
    
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset + len(block)*block.itemsize
    return orig_offset



def bytes_writer(self, parent, writebuffer, attr_index=None,
                 root_offset=0, offset=0, **kwargs):
    """
    Writes the bytes or bytearray object in 'attr_index'
    of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    
    if parent is None or attr_index is None:
        block = parent
        desc = {}
    else:
        block = parent[attr_index]
        
        p_desc = parent.DESC
        if p_desc['TYPE'].is_array:
            desc = p_desc['SUB_STRUCT']
        else:
            desc = p_desc[attr_index]
            
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
    
    writebuffer.seek(root_offset+offset)
    writebuffer.write(block)
    
    #pass the incremented offset to the caller, unless specified not to
    if desc.get('CARRY_OFF', True):
        return offset + len(block)
    return orig_offset



def bit_struct_writer(self, parent, writebuffer, attr_index=None,
                      root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Bit Struct' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer'. All attributes of
    the BitStruct are converted to unsigned integers, merged
    together on the bit level, and the result is written.
    Returns the offset this function finished writing at.

    Required arguments:
        parent(Block)
        writebuffer(buffer)
    Optional arguments:
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """

    try:
        block = parent[attr_index]
    except (AttributeError,TypeError,IndexError,KeyError):
        block = parent
        
    if hasattr(block, CHILD):
        kwargs['parents'].append(block)
        
    data = 0
    desc = block.DESC
    structsize = desc['SIZE']
    
    #get a list of everything as unsigned
    #ints with their masks and offsets
    for i in range(len(block)):
        bitint = desc[i][TYPE].encoder(block[i], block, i)

        #combine with the other data
        #0 = actual U_Int, 1 = bit offset of int
        data += bitint[0] << bitint[1]
    
    writebuffer.seek(root_offset+offset)
    
    if self.endian == '<':
        writebuffer.write(data.to_bytes(structsize, 'little'))
    else:
        writebuffer.write(data.to_bytes(structsize, 'big'))


    return offset + structsize






def decode_numeric(self, rawbytes, parent=None, attr_index=None):
    """
    Converts a bytes object into a python int
    Decoding is done using struct.unpack
    
    Returns an int decoded represention of the "rawbytes" argument.

    Required arguments:
        rawbytes(rawbytes)
    Optional arguments:
        parent(Block) = None
        attr_index(int) = None
    """
    return unpack(self.enc, rawbytes)[0]

def decode_24bit_numeric(self, rawbytes, parent=None, attr_index=None):
    if self.endian == '<':
        return unpack(self.enc, rawbytes+b'\x00')[0]
    return unpack(self.enc, b'\x00'+rawbytes)[0]

def decode_timestamp(self, rawbytes, parent=None, attr_index=None):
    return ctime(unpack(self.enc, rawbytes)[0])
                

def decode_string(self, rawbytes, parent=None, attr_index=None):
    """
    Decodes a bytes object into a python string
    with the delimiter character sliced off the end.
    Decoding is done using bytes.decode
    
    Returns a string decoded represention of the "rawbytes" argument.

    Required arguments:
        rawbytes(rawbytes)
    Optional arguments:
        parent(Block) = None
        attr_index(int) = None
    """
    return rawbytes.decode(encoding=self.enc).split(self.str_delimiter)[0]


def decode_big_int(self, rawbytes, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Decoding is done using int.from_bytes
    
    Returns an int represention of the "rawbytes" argument.
    
    Required arguments:
        rawbytes(object)
    Optional arguments:
        parent(Block) = None
        attr_index(int) = None
    '''

    if len(rawbytes):
        if self.endian == '<':
            endian = 'little'
        else:
            endian = 'big'
    
        if self.enc.endswith('s'):
            #ones compliment
            bigint = int.from_bytes(rawbytes, endian, signed=True)
            if bigint < 0:
                return bigint + 1
            else:
                return bigint
        elif self.enc.endswith('S'):
            #twos compliment
            return int.from_bytes(rawbytes, endian, signed=True)
        else:
            return int.from_bytes(rawbytes, endian)
    else:
        #If an empty bytes object was provided, return a zero.
        '''Not sure if this should be an exception instead.'''
        return 0


def decode_bit(self, rawint, parent, attr_index):
    '''docstring'''
    #mask and shift the int out of the rawint
    return (rawint >> parent.ATTR_OFFS[attr_index]) & 1


def decode_bit_int(self, rawint, parent, attr_index):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment
    
    Returns an int represention of the "rawint" argument
    after masking and bit-shifting.
    
    Required arguments:
        rawint(int)
        parent(Block)
        attr_index(int)
    '''
    
    bitcount = parent.get_size(attr_index)
    
    if bitcount:
        offset = parent.ATTR_OFFS[attr_index]
        mask   = (1<<bitcount)-1

        #mask and shift the int out of the rawint
        bitint = (rawint >> offset) & mask
        
        #if the number would be negative if signed
        if bitint&(1<<(bitcount-1)):
            if self.enc == 's':
                #get the ones compliment and change the sign
                intmask = ((1 << (bitcount-1))-1)
                bitint = -1*((~bitint)&intmask)
            elif self.enc == 'S':
                #get the twos compliment and change the sign
                intmask = ((1 << (bitcount-1))-1)
                bitint = -1*((~bitint+1)&intmask)
                
        return bitint
    else:
        #If the bit count is zero, return a zero
        '''Not sure if this should be an exception instead.'''
        return 0



def encode_numeric(self, block, parent=None, attr_index=None):
    '''
    Encodes a python int into a bytes representation.
    Encoding is done using struct.pack
    
    Returns a bytes object encoded represention of the "block" argument.

    Required arguments:
        block(object)
    Optional arguments:
        parent(block) = None
        attr_index(int) = None
    '''
    
    return pack(self.enc, block)

def encode_24bit_numeric(self, block, parent=None, attr_index=None):
    if self.endian == '<':
        return pack(self.enc, block)[0:3]
    return pack(self.enc, block)[1:4]

def encode_int_timestamp(self, block, parent=None, attr_index=None):
    return pack(self.enc, int(mktime(strptime(block))))

def encode_float_timestamp(self, block, parent=None, attr_index=None):
    return pack(self.enc, float(mktime(strptime(block))))

def encode_string(self, block, parent=None, attr_index=None):
    """
    Encodes a python string into a bytes representation,
    making sure there is a delimiter character on the end.
    Encoding is done using str.encode
    
    Returns a bytes object encoded represention of the "block" argument.

    Required arguments:
        block(object)
    Optional arguments:
        parent(block) = None
        attr_index(int) = None
    """
    
    if self.is_delimited and not block.endswith(self.str_delimiter):
        block += self.str_delimiter
        
    return block.encode(self.enc)

def encode_raw_string(self, block, parent=None, attr_index=None):
    """
    Encodes a python string into a bytes representation.
    Encoding is done using str.encode
    
    Returns a bytes object encoded represention of the "block" argument.
    
    Required arguments:
        block(object)
    Optional arguments:
        parent(block) = None
        attr_index(int) = None
    """
    return block.encode(self.enc)

def encode_big_int(self, block, parent, attr_index):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Encoding is done using int.to_bytes
    
    Returns a bytes object encoded represention of the "block" argument.
    
    Required arguments:
        block(object)
        parent(block)
        attr_index(int)
    '''
    
    bytecount = parent.get_size(attr_index)
    
    if bytecount:
        if self.endian == '<':
            endian = 'little'
        else:
            endian = 'big'
    
        if self.enc.endswith('S'):
            #twos compliment
            return block.to_bytes(bytecount, endian, signed=True)
        elif self.enc.endswith('s'):
            #ones compliment
            if block < 0:
                return (block-1).to_bytes(bytecount, endian, signed=True)
            
            return block.to_bytes(bytecount, endian, signed=True)
        else:
            return block.to_bytes(bytecount, endian)
    else:
        return bytes()


def encode_bit(self, block, parent, attr_index):
    '''docstring'''
    #return the int with the bit offset and a mask of 1
    return(block, parent.ATTR_OFFS[attr_index], 1)


def encode_bit_int(self, block, parent, attr_index):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment
    
    Returns the encoded 'block', bit offset, and bit mask.
    This is done so they can be combined with the rest of a BitStruct.
    
    Required arguments:
        block(object)
        parent(block)
        attr_index(int)
    '''
    
    offset   = parent.ATTR_OFFS[attr_index]
    bitcount = parent.get_size(attr_index)
    mask     = (1<<bitcount)-1
    
    #if the number is signed
    if block < 0:
        signmask = 1<<(bitcount-1)

        #because of the inability to efficiently
        #access the bitcount of the int directly, this
        #is the best workaround I can come up with
        if self.enc == 'S':
            return( 2*signmask + block, offset, mask)
        else:
            return(   signmask - block, offset, mask)
    else:
        return(block, offset, mask)
    

'''These next methods are exclusively used for the Void Field.'''
def void_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Void' type Block and places it into the
    Block 'parent' at 'attr_index'.
    Returns the provided argument 'offset'.

    Required arguments:
        parent(Block)
    Optional arguments:
        rawdata(buffer) = None
        attr_index(int, str) = None
        root_offset(int) = 0
        offset(int) = 0
    Optional kwargs:
        parents(list)
    """
    
    if attr_index is not None:
        parent[attr_index]=desc.get('DEFAULT',self.py_type)(desc, parent=parent)
    return offset

def no_read(self, desc, parent=None, rawdata=None, attr_index=None,
            root_offset=0, offset=0, **kwargs):
    if parent is not None:
        return offset + parent.get_size(attr_index, offset = offset,
                                        root_offset = root_offset,
                                        rawdata = rawdata, **kwargs)
    return offset

def void_writer(self, parent, writebuffer, attr_index=None,
                root_offset=0, offset=0, **kwargs):
    '''Writes nothing, returns the provided argument 'offset'.'''
    return offset

def no_write(self, parent, writebuffer, attr_index=None,
             root_offset=0, offset=0, **kwargs):
    if parent is not None:
        return offset + parent.get_size(attr_index, offset = offset,
                                        root_offset = root_offset, **kwargs)
    return offset

def no_decode(self, block, parent=None, attr_index=None):
    return block
def no_encode(self, rawbytes, parent=None, attr_index=None):
    return rawbytes


def no_sizecalc(self, block=None, **kwargs):
    '''
    If a sizecalc routine wasnt provided for this
    Field and one can't be decided upon as a
    default, then the size can't be calculated.
    Returns 0 when called
    '''
    
    return 0

def def_sizecalc(self, block=None, **kwargs):
    '''
    Returns the byte size specified by the Field.
    Only used if the self.varsize == False.
    '''
    return self.size

def delim_str_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a delimited string if it were converted to bytes.
    '''
    #dont add the delimiter size if the string is already delimited
    if block.endswith(self.str_delimiter):
        return len(block) * self.size
    return (len(block)+1) * self.size

def str_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a string if it were converted to bytes.
    '''
    return len(block)*self.size

def delim_utf_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were converted to bytes.
    This function is potentially slower than the above one, but is
    necessary to get an accurate byte length for UTF8/16 strings.
    
    This should only be used for UTF8 and UTF16. 
    '''
    blocklen = len(block.encode(encoding=self.enc))
    
    #dont add the delimiter size if the string is already delimited
    if block.endswith(self.str_delimiter):
        return blocklen
    return blocklen + self.size

def utf_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were converted to bytes.
    This function is potentially slower than the above one, but is
    necessary to get an accurate byte length for UTF8/16 strings.
    
    This should only be used for UTF8 and UTF16. 
    '''
    #return the length of the entire string of bytes
    return len(block.encode(encoding=self.enc))

    
def array_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the byte size of an array if it were converted to bytes.
    '''
    return len(block)*block.itemsize
    
def len_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the byte size of an object whose length is its
    size if it were converted to bytes(bytes, bytearray).
    '''
    return len(block)
    
def big_sint_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent a twos signed integer
    NOTE: returns a byte size of 1 for the int 0
    '''
    #add 8 bits for rounding up, and 1 for the sign bit
    return (int.bit_length(block) + 9) // 8
    
def big_uint_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the number of bytes required to represent an unsigned integer
    NOTE: returns a byte size of 1 for the int 0
    '''
    #add 8 bits for rounding up
    return (int.bit_length(block) + 8) // 8
    
def bit_sint_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    return int.bit_length(block)+1
    
def bit_uint_sizecalc(self, block, *args, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    return int.bit_length(block)

'''DEPRECIATED SLOW METHODS'''
#def big_1sint_sizecalc(self, block, *args, **kwargs):
#    '''
#    Returns the number of bytes required to represent a ones signed integer
#    '''
#    #ones compliment
#    return int(ceil( (log(abs(block)+1,2)+1.0)/8.0 ))
#
#def big_sint_sizecalc(self, block, *args, **kwargs):
#    '''
#    Returns the number of bytes required to represent a twos signed integer
#    '''
#    #twos compliment
#    if block >= 0:
#        return int(ceil( (log(block+1,2)+1.0)/8.0 ))
#    return int(ceil( (log(0-block,2)+1.0)/8.0 ))
#
#def bit_1sint_sizecalc(self, block, *args, **kwargs):
#    '''
#    Returns the number of bits required to represent an integer
#    of arbitrary size, whether ones signed, twos signed, or unsigned.
#    '''
#    #ones compliment
#    return int(ceil( log(abs(block)+1,2)+1.0 ))
#
#def bit_sint_sizecalc(self, block, *args, **kwargs):
#    '''
#    Returns the number of bits required to represent an integer
#    of arbitrary size, whether ones signed, twos signed, or unsigned.
#    '''
#    #twos compliment
#    if block >= 0:
#        return int(ceil( log(block+1,2)+1.0 ))
#    return int(ceil( log(0-block,2)+1.0 ))
