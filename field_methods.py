'''
Reader, writer, encoder, and decoder functions for all standard Fields.

Readers are responsible for reading bytes from a buffer and calling their
associated decoder on the bytes to turn them into a python object.

Writers are responsible for calling their associated encoder, using it to
encode a python object, and writing the encoded bytes to the writebuffer.

If the Field the reader/writer is meant for is not actually data,
but rather a form of hierarchy(like a Struct or Container) then
they wont have an encoder/decoder to call, but instead will be
responsible for calling the reader/writer functions of their
attributes and possibly the reader/writer routines of their
child and the children of all nested sub-structs.

Readers and writers must also return an integer specifying
what offset the last data was read from or written to.

Decoders are responsible for converting bytes into a python object*
Encoders are responsible for converting a python object into bytes*

Some functions do not require all of the arguments they are given,
but many of them do, and it is easier to provide extra arguments
that are ignored than to provide exactly what is needed.

*Not all encoders and decoders receive/return bytes objects.
Fields that operate on the bit level cant be expected to return
even byte sized amounts of bits, so they operate differently.
A fields reader/writer and decoder/encoder simply need to
be working with the same parameter and return data types.
'''

from math import ceil
from struct import pack, pack_into, unpack
from sys import byteorder
from time import mktime, ctime, strptime

from supyr_struct.defs.constants import *
from supyr_struct.buffer import *

# linked to through supyr_struct.__init__
blocks = None
common_descs = None
fields = None

__all__ = [
    'byteorder_char',
    # Basic routines

    # readers
    'container_reader', 'array_reader',
    'struct_reader', 'bit_struct_reader', 'py_array_reader',
    'data_reader', 'cstring_reader', 'bytes_reader',
    # writers
    'container_writer', 'array_writer',
    'struct_writer', 'bit_struct_writer', 'py_array_writer',
    'data_writer', 'cstring_writer', 'bytes_writer',
    # Decoders
    'decode_numeric', 'decode_string', 'no_decode',
    'decode_big_int', 'decode_bit_int', 'decode_raw_string',
    # Encoders
    'encode_numeric', 'encode_string', 'no_encode',
    'encode_big_int', 'encode_bit_int',
    # size calculators
    'no_sizecalc', 'def_sizecalc', 'len_sizecalc',
    'delim_str_sizecalc', 'str_sizecalc',

    # Specialized routines

    # readers
    'default_reader', 'f_s_data_reader',
    'switch_reader', 'while_array_reader',
    'void_reader', 'pad_reader', 'union_reader',
    'stream_adapter_reader', 'quickstruct_reader',
    # writers
    'void_writer', 'pad_writer', 'union_writer',
    'stream_adapter_writer', 'quickstruct_writer',
    # Decoders
    'decode_24bit_numeric', 'decode_bit',
    'decode_timestamp', 'decode_string_hex',
    # Encoders
    'encode_24bit_numeric', 'encode_bit', 'encode_raw_string',
    'encode_int_timestamp', 'encode_float_timestamp', 'encode_string_hex',
    # size calculators
    'delim_utf_sizecalc', 'utf_sizecalc', 'array_sizecalc',
    'big_sint_sizecalc', 'big_uint_sizecalc', 'str_hex_sizecalc',
    'bit_sint_sizecalc', 'bit_uint_sizecalc',

    # Sanitizer routines
    'bool_enum_sanitizer', 'switch_sanitizer',
    'sequence_sanitizer', 'standard_sanitizer',
    'struct_sanitizer', 'quickstruct_sanitizer',
    'union_sanitizer', 'stream_adapter_sanitizer',

    # Exception string formatters
    'format_read_error', 'format_write_error'
    ]

# for use in byteswapping arrays
byteorder_char = {'little': '<', 'big': '>'}[byteorder]

READ_ERROR_HEAD = "\nError occurred while reading:"
WRITE_ERROR_HEAD = "\nError occurred while writing:"

QSTRUCT_ALLOWED_ENC = set('bB')
for end in '<>':
    for c in 'HhIiQqfd':
        QSTRUCT_ALLOWED_ENC.add(end + c)


def adapter_no_encode(parent, buffer, **kwargs):
    '''
    Returns the supplied 'buffer' argument.
    This function is used as the ENCODER entry in the descriptor
    for StreamAdapter Fields when an ENCODER is not present.
    '''
    return buffer


def format_read_error(e, **kwargs):
    '''
    Returns a FieldReadError which details the hierarchy
    of the field in which the read error occurred.

    If the 'error' provided is not a FieldReadError, then
    one will be created. If it is, it will have the current
    level of hierarchy inserted into its last args string.

    keyword arguments:
    desc --------- defaults to dict()
    field -------- defaults to desc.get('TYPE')
    parent ------- defaults to None
    attr_index --- defaults to None
    offset ------- defaults to 0
    root_offset -- defaults to 0
    '''
    e_str0 = e_str1 = ''
    desc = kwargs.get('desc', {})
    field = kwargs.get('field', desc.get('TYPE'))
    parent = kwargs.get('parent')
    attr_index = kwargs.get('attr_index')
    offset = kwargs.get('offset', 0)
    root_offset = kwargs.get('root_offset', 0)
    try:
        name = desc.get(NAME, UNNAMED)
    except Exception:
        name = UNNAMED
    if not isinstance(e, FieldReadError):
        e = FieldReadError()
        e_str0 = READ_ERROR_HEAD
        e.seen = set()

    # get a copy of all but the last of the arguments
    a = e.args[:-1]
    try:
        e_str0 = str(e.args[-1])
        e_str0, e_str1 = (e_str0[:len(READ_ERROR_HEAD)],
                          e_str0[len(READ_ERROR_HEAD):])
    except IndexError:
        pass

    # make sure this block hasnt already been seen
    seen_id = (id(parent), id(field), attr_index)
    if seen_id in e.seen:
        return e
    e.seen.add(seen_id)

    # remake the args with the new data
    e.args = a + (e_str0 + "\n    %s, index:%s, offset:%s, field:%s" %
                  (name, attr_index, offset + root_offset, field) + e_str1,)

    # add the extra data pertaining to this hierarchy level to e.error_data
    e.error_data.insert(0, kwargs)
    return e


def format_write_error(e, **kwargs):
    '''
    Returns an FieldWriteError which details the hierarchy
    of the field in which the write error occurred.

    If the 'error' provided is not a FieldWriteError, then
    one will be created. If it is, it will have the current
    level of hierarchy inserted into its last args string.

    keyword arguments:
    desc --------- defaults to dict()
    field -------- defaults to desc.get('TYPE')
    parent ------- defaults to None
    attr_index --- defaults to None
    offset ------- defaults to 0
    root_offset -- defaults to 0
    '''
    e_str0 = e_str1 = ''
    desc = kwargs.get('desc', {})
    field = kwargs.get('field', desc.get('TYPE'))
    parent = kwargs.get('parent')
    attr_index = kwargs.get('attr_index')
    offset = kwargs.get('offset', 0)
    root_offset = kwargs.get('root_offset', 0)
    try:
        name = desc.get(NAME, UNNAMED)
    except Exception:
        name = UNNAMED
    if not isinstance(e, FieldWriteError):
        e = FieldWriteError()
        e_str0 = WRITE_ERROR_HEAD
        e.seen = set()

    # get a copy of all but the last of the arguments
    a = e.args[:-1]
    try:
        e_str0 = str(e.args[-1])
        e_str0, e_str1 = (e_str0[:len(WRITE_ERROR_HEAD)],
                          e_str0[len(WRITE_ERROR_HEAD):])
    except IndexError:
        pass

    # make sure this block hasnt already been seen
    seen_id = (id(parent), id(field), attr_index)
    if seen_id in e.seen:
        return e
    else:
        e.seen.add(seen_id)

    # remake the args with the new data
    e.args = a + (e_str0 + "\n    %s, index:%s, offset:%s, field:%s" %
                  (name, attr_index, offset + root_offset, field) + e_str1,)

    # add the extra data pertaining to this hierarchy level to e.error_data
    e.error_data.insert(0, kwargs)
    return e


# ################################################
'''############  Reader functions  ############'''
# ################################################


def default_reader(self, desc, block=None, parent=None, attr_index=None,
                   rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    A reader meant specifically for setting the default value
    of Fields whose reader is not called by its parents reader.

    This function is currently for the fields used inside bitstructs
    since their reader is not called by their parent bitstructs reader.

    When "rawdata" is not provided to a bitstructs reader, the reader will
    call its Blocks rebuild method to initialize its attributes, which in
    turn calls the reader of each attribute, which should be this function.
    """
    if parent is not None and attr_index is not None:
        if not self.is_block:
            # non-Block py_type
            parent[attr_index] = desc.get(DEFAULT, self.default())
        elif isinstance(None, self.data_type):
            # Block py_type without a 'data_type'
            parent[attr_index] = desc.get(BLOCK_CLS, self.py_type)(desc)
        else:
            # Block py_type with a 'data_type'
            # the Block is likely either an EnumBlock or BoolBlock
            parent[attr_index] = self.py_type(desc, init_attrs=True)

    return offset


def container_reader(self, desc, block=None, parent=None, attr_index=None,
                     rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a 'container' type Block and places it into the 'parent' Block
    at 'attr_index' and calls the readers of each of its attributes.

    If a list keyed under 'parents' is not in kwargs, then one will
    be created, passed to the reader of all attributes, and this Block
    will be considered to be the build_root of those attributes.
    If this Block is considered to be the build_root, all of the
    child blocks of each of its elements will be built from here.

    Returns the offset this function finished reading at.

    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        parents = kwargs['parents'] = []
        if 'CHILD' in desc:
            kwargs['parents'].append(block)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # loop once for each block in the object block
        for i in range(len(block)):
            offset = desc[i]['TYPE'].reader(desc[i], None, block, i, rawdata,
                                            root_offset, offset, **kwargs)

        # build the children for all the blocks within this one
        del kwargs['parents']
        for p_block in parents:
            c_desc = p_block.desc['CHILD']
            offset = c_desc['TYPE'].reader(c_desc, None, p_block,
                                           'CHILD', rawdata, root_offset,
                                           offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'c_desc' in locals():
            e = format_read_error(e, field=c_desc.get(TYPE), desc=c_desc,
                                  parent=p_block, attr_index=CHILD,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_read_error(e, field=desc[i].get(TYPE), desc=desc[i],
                                  parent=block, attr_index=i,
                                  offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def array_reader(self, desc, block=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds an 'array' type Block and places it into the 'parent' Block at
    'attr_index' and calls the SUB_STRUCT reader for each of its entries.

    If a list keyed under 'parents' is not in kwargs, then one will
    be created, passed to the reader of all attributes, and this Block
    will be considered to be the build_root of those attributes.
    If this Block is considered to be the build_root, all of the
    child blocks of each of its elements will be built from here.

    Returns the offset this function finished reading at.

    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        parents = kwargs['parents'] = []
        if 'CHILD' in desc:
            kwargs['parents'].append(block)
        a_desc = desc['SUB_STRUCT']
        a_reader = a_desc['TYPE'].reader

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        for i in range(block.get_size(**kwargs)):
            offset = a_reader(a_desc, None, block, i, rawdata,
                              root_offset, offset, **kwargs)

        # build the children for all the blocks within this one
        del kwargs['parents']
        for p_block in parents:
            c_desc = p_block.desc['CHILD']
            offset = c_desc['TYPE'].reader(c_desc, None, p_block,
                                           'CHILD', rawdata, root_offset,
                                           offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'c_desc' in locals():
            e = format_read_error(e, field=c_desc.get(TYPE), desc=c_desc,
                                  parent=p_block, attr_index=CHILD,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_read_error(e, field=a_desc['TYPE'], desc=a_desc,
                                  parent=block, attr_index=i,
                                  offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def while_array_reader(self, desc, block=None, parent=None, attr_index=None,
                       rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds an 'oe_size' 'array' type Block, places it into the 'parent' Block
    at 'attr_index' and calls the SUB_STRUCT reader for each of its entries.

    Calls the CASE entry of 'desc' as the condition in a while
    loop to determine whether or not to keep building Blocks.

    If a list keyed under 'parents' is not in kwargs, then one will
    be created, passed to the reader of all attributes, and this Block
    will be considered to be the build_root of those attributes.
    If this Block is considered to be the build_root, all of the
    child blocks of each of its elements will be built from here.

    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        parents = kwargs['parents'] = []
        if 'CHILD' in desc:
            kwargs['parents'].append(block)
        a_desc = desc['SUB_STRUCT']
        a_reader = a_desc['TYPE'].reader

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        i = 0
        decider = desc.get('CASE')
        if decider is not None:
            temp_kwargs = dict(kwargs)
            temp_kwargs.update(parent=block, rawdata=rawdata, attr_index=i,
                               root_offset=root_offset, offset=offset)
            while decider(**temp_kwargs):
                # make a new slot in the new array for the new array element
                block.append(None)
                offset = a_reader(a_desc, **temp_kwargs)
                i += 1
                temp_kwargs.update(attr_index=i, offset=offset)

        del kwargs['parents']
        for p_block in parents:
            c_desc = p_block.desc['CHILD']
            offset = c_desc['TYPE'].reader(c_desc, None, p_block,
                                           'CHILD', rawdata, root_offset,
                                           offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'c_desc' in locals():
            e = format_read_error(e, field=c_desc.get(TYPE), desc=c_desc,
                                  parent=p_block, attr_index=CHILD,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_read_error(e, field=a_desc['TYPE'], desc=a_desc,
                                  parent=block, attr_index=i,
                                  offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def switch_reader(self, desc, block=None, parent=None, attr_index=None,
                  rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Selects a descriptor to build by using desc['CASE']
    and using that value to select a descriptor from desc['CASE_MAP'].
    Passes all supplied arg and kwargs onto the selected descriptors
    Field.reader() with the desc arg changed to the selected desc.

    Returns the return value of the selected desc['TYPE'].reader()

    Optional kwargs:
        case(str, int)
    """
    try:
        # A case may be provided through kwargs.
        # This is to allow overriding behavior of the switch and
        # to allow creating a Block specified by the user
        case = case_i = desc['CASE']
        case_map = desc['CASE_MAP']

        if 'case' in kwargs:
            case_i = kwargs['case']
            del kwargs['case']
        else:
            if isinstance(attr_index, int):
                block = parent[attr_index]
            elif isinstance(attr_index, str):
                block = parent.__getattr__(attr_index)
            else:
                block = parent

            try:
                parent = block.parent
            except AttributeError:
                pass

            if isinstance(case, str):
                # get the pointed to meta data by traversing the tag
                # structure along the path specified by the string'
                case_i = parent.get_neighbor(case, block)
            elif hasattr(case, "__call__"):

                align = desc.get('ALIGN')
                if align:
                    offset += (align - (offset % align)) % align
                try:
                    # try to reposition the rawdata if it needs to be peeked
                    rawdata.seek(root_offset + offset)
                except AttributeError:
                    pass
                case_i = case(parent=parent, attr_index=attr_index,
                              rawdata=rawdata, block=block,
                              offset=offset, **kwargs)

        # get the descriptor to use to build the block
        # based on what the CASE meta data says
        desc = desc.get(case_map.get(case_i, DEFAULT))

        return desc['TYPE'].reader(desc, None, parent, attr_index,
                                   rawdata, root_offset, offset, **kwargs)
    except Exception as e:
        try:
            index = case_i
        except NameError:
            index = None
        e = format_read_error(e, field=self, desc=desc, parent=parent,
                              buffer=rawdata, attr_index=index,
                              root_offset=root_offset, offset=offset, **kwargs)
        raise e


def struct_reader(self, desc, block=None, parent=None, attr_index=None,
                  rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a 'struct' type Block and places it into the 'parent' Block
    at 'attr_index' and calls the readers of each of its attributes.

    If a list keyed under 'parents' is not in kwargs, then one will
    be created, passed to the reader of all attributes, and this Block
    will be considered to be the build_root of those attributes.
    If this Block is considered to be the build_root, all of the
    child blocks of each of its elements will be built from here.

    Returns the offset this function finished reading at.

    Optional kwargs:
        parents(list)

    If rawdata is None, the Block will be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        is_build_root = 'parents' not in kwargs
        if is_build_root:
            kwargs["parents"] = parents = []
        if 'CHILD' in desc:
            kwargs['parents'].append(block)

        """If there is rawdata to build the structure from"""
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the block from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this block is being built
            # without a parent(such as from an exported .blok file) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = block.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            offsets = desc['ATTR_OFFS']
            # loop for each attribute in the struct
            for i in range(len(block)):
                desc[i]['TYPE'].reader(desc[i], None, block, i, rawdata,
                                       root_offset, offset + offsets[i],
                                       **kwargs)

            # increment offset by the size of the struct
            offset += desc['SIZE']

        if is_build_root:
            del kwargs['parents']
            for p_block in parents:
                c_desc = p_block.desc['CHILD']
                offset = c_desc['TYPE'].reader(c_desc, None, p_block,
                                               'CHILD', rawdata, root_offset,
                                               offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'c_desc' in locals():
            e = format_read_error(e, field=c_desc.get(TYPE), desc=c_desc,
                                  parent=p_block, attr_index=CHILD,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_read_error(e, field=desc[i].get(TYPE), desc=desc[i],
                                  parent=block, attr_index=i,
                                  offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def quickstruct_reader(self, desc, block=None, parent=None, attr_index=None,
                       rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        """If there is rawdata to build the structure from"""
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the block from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this block is being built
            # without a parent(such as from an exported .blok file) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = block.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            offsets = desc['ATTR_OFFS']
            __lsi__ = list.__setitem__
            struct_off = root_offset + offset

            # loop for each attribute in the struct
            for i in range(len(block)):
                off = struct_off + offsets[i]
                typ = desc[i]['TYPE']
                __lsi__(block, i,
                        unpack(typ.enc, rawdata[off:off + typ.size])[0])

            # increment offset by the size of the struct
            offset += desc['SIZE']
        else:
            __lsi__ = list.__setitem__
            for i in range(len(block)):
                __lsi__(block, i,
                        desc[i].get(DEFAULT, desc[i]['TYPE'].default()))

        c_desc = desc.get('CHILD')
        if c_desc:
            if 'parents' not in kwargs:
                offset = c_desc['TYPE'].reader(c_desc, None, block, rawdata,
                                               'CHILD', root_offset, offset,
                                               **kwargs)
            else:
                kwargs['parents'].append(block)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'c_desc' in locals():
            e = format_read_error(e, field=c_desc.get(TYPE), desc=c_desc,
                                  parent=p_block, attr_index=CHILD,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_read_error(e, field=desc[i].get(TYPE), desc=desc[i],
                                  parent=block, attr_index=i,
                                  offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def stream_adapter_reader(self, desc, block=None, parent=None, attr_index=None,
                          rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        orig_root_offset = root_offset
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (
                desc.get(BLOCK_CLS, self.py_type)(desc, parent=parent))

        sub_desc = desc['SUB_STRUCT']

        # If there is rawdata to build from
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the block from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this block is being built
            # without a parent(such as from an exported .blok file) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = block.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            # use the decoder method to get a decoded stream and
            # the length of the stream before it was decoded
            adapted_stream, length_read = desc['DECODER'](
                block, rawdata, root_offset, offset, **kwargs)
        else:
            adapted_stream = None
            length_read = 0

        sub_desc['TYPE'].reader(sub_desc, None, block, 'SUB_STRUCT',
                                adapted_stream, 0, 0, **kwargs)

        # pass the incremented offset to the caller
        return offset + length_read
    except Exception as e:
        adapted_stream = locals().get('adapted_stream', rawdata)
        kwargs.update(field=self, desc=desc, parent=parent,
                      buffer=adapted_stream, attr_index=attr_index,
                      root_offset=orig_root_offset, offset=orig_offset)
        e = format_read_error(e, **kwargs)
        raise e


def union_reader(self, desc, block=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        orig_offset = offset
        if block is None:
            parent[attr_index] = block = (
                desc.get(BLOCK_CLS, self.py_type)(desc, parent=parent))

        if rawdata is not None:
            # A case may be provided through kwargs.
            # This is to allow overriding behavior of the union and
            # to allow creating a Block specified by the user
            case_i = case = desc.get('CASE')
            case_map = desc['CASE_MAP']
            align = desc.get('ALIGN')
            size = desc['SIZE']

            if attr_index is not None and desc.get('POINTER') is not None:
                offset = block.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            # read and store the rawdata to the new block
            rawdata.seek(root_offset + offset)
            block[:] = rawdata.read(size)

            if 'case' in kwargs:
                case_i = kwargs['case']
            elif isinstance(case, str):
                # get the pointed to meta data by traversing the tag
                # structure along the path specified by the string
                case_i = parent.get_neighbor(case, block)
            elif hasattr(case, "__call__"):
                try:
                    # try to reposition the rawdata if it needs to be peeked
                    rawdata.seek(root_offset + offset)
                except AttributeError:
                    pass
                case_i = case(parent=parent, block=block,
                              attr_index=attr_index, rawdata=rawdata,
                              root_offset=root_offset, offset=offset, **kwargs)
            offset += size
            case_i = case_map.get(case_i)

            if case_i is not None:
                try:
                    block.set_active(case_i)
                except AttributeError:
                    # this case doesnt exist, but this can be intentional, so
                    # allow this error to pass. Maybe change this later on.
                    pass

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'case_i' in locals() and case_i in desc:
            e = format_read_error(
                e, field=desc[case_i].get(TYPE), desc=desc[case_i],
                parent=block, attr_index=i, offset=offset, **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=orig_offset, **kwargs)
        raise e


def f_s_data_reader(self, desc, block=None, parent=None, attr_index=None,
                    rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    f_s means fixed_size.
    Builds a python object determined by the decoder and
    places it into the 'parent' Block at 'attr_index'.
    Returns the offset this function finished reading at.

    This function differs from data_reader in that it is expected that
    the size of the Field has a fixed size, which is determined
    specifically in the Field. A costly Block.get_size() isnt needed.
    """
    assert parent is not None and attr_index is not None, (
        "'parent' and 'attr_index' must be provided " +
        "and not None when reading a 'data' Field.")
    if rawdata:
        # read and store the variable
        rawdata.seek(root_offset + offset)
        parent[attr_index] = self.decoder(rawdata.read(self.size), desc=desc,
                                          parent=parent, attr_index=attr_index)
        return offset + self.size
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)(
            desc, initdata=desc.get(DEFAULT), init_attrs=True))
    else:
        # this is not a Block
        parent[attr_index] = desc.get(DEFAULT, self.default())

    return offset


def data_reader(self, desc, block=None, parent=None, attr_index=None,
                rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a python object determined by the decoder and
    places it into the 'parent' Block at 'attr_index'.
    Returns the offset this function finished reading at.
    """
    assert parent is not None and attr_index is not None, (
        "'parent' and 'attr_index' must be provided " +
        "and not None when reading a 'data' Field.")
    if rawdata:
        # read and store the variable
        rawdata.seek(root_offset + offset)
        size = parent.get_size(attr_index, root_offset=root_offset,
                               offset=offset, rawdata=rawdata, **kwargs)
        parent[attr_index] = self.decoder(rawdata.read(size), desc=desc,
                                          parent=parent, attr_index=attr_index)
        return offset + size
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)
                              (desc, initdata=desc.get(DEFAULT),
                               init_attrs=True))
    else:
        # this is not a Block
        parent[attr_index] = desc.get(DEFAULT, self.default())

    return offset


def cstring_reader(self, desc, block=None, parent=None, attr_index=None,
                   rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a python string determined by the decoder and
    places it into the 'parent' Block at 'attr_index'.

    The strings length is unknown before hand, thus this
    function relies on locating the null terminator.
    Returns the offset this function finished reading at.
    """
    assert parent is not None and attr_index is not None, (
        "'parent' and 'attr_index' must be provided and " +
        "not None when reading a 'data' Field.")

    if rawdata is not None:
        orig_offset = offset
        align = desc.get('ALIGN')
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        start = root_offset + offset
        charsize = self.size
        delimiter = self.delimiter

        # if the character size is greater than 1 we need to do special
        # checks to ensure the position the null terminator was found at
        # is not overlapping the boundary between individual characters.
        size = rawdata.find(delimiter, start) - start

        # if length % char_size is not zero, it means the location lies
        # between individual characters. Try again from this spot + 1
        while size % charsize:
            size = rawdata.find(delimiter, start + size + 1) - start

            if size + start < 0:
                raise LookupError("Reached end of raw data and could not " +
                                  "locate null terminator for string.")
        rawdata.seek(start)
        # read and store the variable
        parent[attr_index] = self.decoder(rawdata.read(size), desc=desc,
                                          parent=parent, attr_index=attr_index)

        # pass the incremented offset to the caller
        return offset + size + charsize
    elif not self.is_block:
        parent[attr_index] = desc.get(DEFAULT, self.default())
    else:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)
                              (desc, initdata=desc.get(DEFAULT),
                               init_attrs=True))
    return offset


def py_array_reader(self, desc, block=None, parent=None, attr_index=None,
                    rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a python array.array object and places it
    into the 'parent' Block at 'attr_index'.
    Returns the offset this function finished reading at.

    If rawdata is None, the array will be initialized with a default value.
    """
    assert parent is not None and attr_index is not None, (
        "'parent' and 'attr_index' must be provided and " +
        "not None when reading a 'data' Field.")

    if rawdata is not None:
        orig_offset = offset
        align = desc.get('ALIGN')
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        bytecount = parent.get_size(attr_index, offset=offset,
                                    rawdata=rawdata, **kwargs)

        rawdata.seek(root_offset + offset)

        offset += bytecount

        # If the tag is only being test loaded we skip
        # loading any raw data to save on RAM and speed.
        # When we do we make sure to set it's bytes size to 0
        py_array = self.py_type(self.enc, rawdata.read(bytecount))

        # if the system the array is being created on
        # has a different endianness than what the array is
        # packed as, swap the endianness after reading it.
        if self.endian != byteorder_char and self.endian != '=':
            py_array.byteswap()
        parent[attr_index] = py_array

        # pass the incremented offset to the caller
        return offset
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)
                              (desc, initdata=desc.get(DEFAULT),
                               init_attrs=True))
    elif DEFAULT in desc:
        parent[attr_index] = self.py_type(self.enc, desc[DEFAULT])
    else:
        bytecount = parent.get_size(attr_index, offset=offset,
                                    root_offset=root_offset,
                                    rawdata=rawdata, **kwargs)
        parent[attr_index] = self.py_type(self.enc, b'\x00'*bytecount)
    return offset


def bytes_reader(self, desc, block=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a python bytes or bytearray object and places
    it into the 'parent' Block at 'attr_index'.
    Returns the offset this function finished reading at.

    If rawdata is None, the Block will be initialized with default values.
    """
    assert parent is not None and attr_index is not None, (
        "'parent' and 'attr_index' must be provided and " +
        "not None when reading a 'data' Field.")
    if rawdata is not None:
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)

        bytecount = parent.get_size(attr_index, offset=offset,
                                    rawdata=rawdata, **kwargs)
        rawdata.seek(root_offset + offset)
        offset += bytecount

        # If the tag is only being test loaded we skip
        # loading any raw data to save on RAM and speed.
        # When we do we make sure to set it's bytes size to 0
        parent[attr_index] = self.py_type(rawdata.read(bytecount))

        # pass the incremented offset to the caller
        return offset
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)
                              (desc, initdata=desc.get(DEFAULT),
                               init_attrs=True))
    elif DEFAULT in desc:
        parent[attr_index] = self.py_type(desc[DEFAULT])
    else:
        bytecount = parent.get_size(attr_index, offset=offset,
                                    rawdata=rawdata, **kwargs)
        parent[attr_index] = self.py_type(b'\x00'*bytecount)
    return offset


def bit_struct_reader(self, desc, block=None, parent=None, attr_index=None,
                      rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Struct' type Block and places it into the
    'parent' Block at 'attr_index' and calls the readers
    of each of its attributes.
    Returns the offset this function finished reading at.

    If rawdata is None, the Block will be initialized with default values.
    If attr_index is None, 'parent' is expected to be
    the Block being built, rather than its parent.
    """
    try:
        if block is None:
            parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)(
                desc, parent=parent, init_attrs=rawdata is None))

        """If there is file data to build the structure from"""
        if rawdata is not None:
            rawdata.seek(root_offset + offset)
            structsize = desc['SIZE']
            if self.endian == '<':
                rawint = int.from_bytes(rawdata.read(structsize), 'little')
            else:
                rawint = int.from_bytes(rawdata.read(structsize), 'big')

            # loop for each attribute in the struct
            for i in range(len(block)):
                block[i] = desc[i]['TYPE'].decoder(
                    rawint, desc=desc[i], parent=block, attr_index=i)

            # increment offset by the size of the struct
            offset += structsize

        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'i' in locals():
            e = format_read_error(e, field=desc[i].get(TYPE), desc=desc[i],
                                  parent=block, attr_index=i,
                                  offset=desc['ATTR_OFFS'][i], **kwargs)
        e = format_read_error(e, field=self, desc=desc,
                              parent=parent, attr_index=attr_index,
                              offset=offset, **kwargs)
        raise e


# ################################################
'''############  Writer functions  ############'''
# ################################################


def container_writer(self, block, parent=None, attr_index=None,
                     writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Container' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer' and calls the writers
    of each of its attributes.
    Returns the offset this function finished writing at.

    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    try:
        orig_offset = offset
        desc = block.desc
        kwargs.setdefault('parents', [])
        parents = kwargs['parents']
        if hasattr(block, 'CHILD'):
            kwargs['parents'].append(block)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        for i in range(len(block)):
            # Trust that each of the entries in the container is a Block
            attr = block[i]
            try:
                a_desc = attr.desc
            except AttributeError:
                a_desc = desc[i]
            offset = a_desc['TYPE'].writer(attr, block, i, writebuffer,
                                           root_offset, offset, **kwargs)
        del kwargs['parents']

        for p_block in parents:
            attr = p_block.CHILD
            try:
                c_desc = attr.desc
            except AttributeError:
                c_desc = p_block.desc['CHILD']
            offset = c_desc['TYPE'].writer(attr, p_block, 'CHILD', writebuffer,
                                           root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'c_desc' in locals():
            kwargs.update(field=c_desc.get(TYPE), desc=c_desc,
                          parent=p_block, attr_index=CHILD, offset=offset)
            e = format_write_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field=a_desc.get(TYPE), desc=a_desc,
                          parent=block, attr_index=i, offset=offset)
            e = format_write_error(e, **kwargs)

        kwargs.update(field=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_write_error(e, **kwargs)
        raise e


def array_writer(self, block, parent=None, attr_index=None,
                 writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes an 'Array' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer' and calls the writers
    of each of its arrayed elements.
    Returns the offset this function finished writing at.

    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    try:
        orig_offset = offset
        desc = block.desc
        a_desc = desc['SUB_STRUCT']
        a_writer = a_desc['TYPE'].writer
        kwargs.setdefault('parents', [])
        parents = kwargs['parents']
        if hasattr(block, 'CHILD'):
            kwargs['parents'].append(block)

        align = desc.get('ALIGN')
        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        for i in range(len(block)):
            # Trust that each of the entries in the container is a Block
            attr = block[i]
            try:
                writer = attr.desc['TYPE'].writer
            except AttributeError:
                writer = a_writer
            offset = writer(attr, block, i, writebuffer,
                            root_offset, offset, **kwargs)

        del kwargs['parents']

        for p_block in parents:
            attr = p_block.CHILD
            try:
                c_desc = attr.desc
            except AttributeError:
                c_desc = p_block.desc['CHILD']
            offset = c_desc['TYPE'].writer(attr, p_block, 'CHILD', writebuffer,
                                           root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'c_desc' in locals():
            kwargs.update(field=c_desc.get(TYPE), desc=c_desc,
                          parent=p_block, attr_index=CHILD, offset=offset)
            e = format_write_error(e, **kwargs)
        elif 'i' in locals():
            try:
                a_desc = block[i].desc
            except (TypeError, AttributeError):
                a_desc = desc['SUB_STRUCT']
            kwargs.update(field=a_desc.get(TYPE), desc=a_desc,
                          parent=block, attr_index=i, offset=offset)
            e = format_write_error(e, **kwargs)

        kwargs.update(field=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_write_error(e, **kwargs)
        raise e


def struct_writer(self, block, parent=None, attr_index=None,
                  writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Struct' type Block in 'attr_index' of 'parent'
    to the supplied 'writebuffer' and calls the writers of
    each of its attributes.
    Returns the offset this function finished writing at.

    Optional kwargs:
        parents(list)

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    try:
        orig_offset = offset
        desc = block.desc
        offsets = desc['ATTR_OFFS']
        structsize = desc['SIZE']
        is_build_root = 'parents' not in kwargs

        if is_build_root:
            kwargs['parents'] = parents = []
        if hasattr(block, 'CHILD'):
            kwargs['parents'].append(block)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the whole size of the block so
        # any padding is filled in properly
        writebuffer.seek(root_offset + offset)
        writebuffer.write(bytes(structsize))

        for i in range(len(block)):
            # structs usually dont contain blocks, so check
            attr = block[i]
            try:
                a_desc = block[i].desc
            except AttributeError:
                a_desc = desc[i]
            a_desc['TYPE'].writer(attr, block, i, writebuffer,
                                  root_offset, offset + offsets[i], **kwargs)

        # increment offset by the size of the struct
        offset += structsize

        if is_build_root:
            del kwargs['parents']

            for p_block in parents:
                attr = p_block.CHILD
                try:
                    c_desc = attr.desc
                except AttributeError:
                    c_desc = p_block.desc['CHILD']
                offset = c_desc['TYPE'].writer(attr, p_block, 'CHILD',
                                               writebuffer, root_offset,
                                               offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'c_desc' in locals():
            kwargs.update(field=c_desc.get(TYPE), desc=c_desc,
                          parent=p_block, attr_index=CHILD, offset=offset)
            e = format_write_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field=a_desc.get(TYPE), desc=a_desc,
                          parent=block, attr_index=i, offset=offset)
            e = format_write_error(e, **kwargs)

        kwargs.update(field=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_write_error(e, **kwargs)
        raise e


def quickstruct_writer(self, block, parent=None, attr_index=None,
                       writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        desc = block.desc
        offsets = desc['ATTR_OFFS']
        structsize = desc['SIZE']

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the whole size of the block so
        # any padding is filled in properly
        writebuffer.seek(root_offset + offset)
        writebuffer.write(bytes(structsize))

        __lgi__ = list.__getitem__
        struct_off = root_offset + offset

        # loop for each attribute in the struct
        for i in range(len(block)):
            writebuffer.seek(struct_off + offsets[i])
            writebuffer.write(pack(desc[i]['TYPE'].enc, __lgi__(block, i)))

        # increment offset by the size of the struct
        offset += structsize

        if hasattr(block, 'CHILD'):
            if 'parents' not in kwargs:
                attr = block.CHILD
                try:
                    c_desc = attr.desc
                except AttributeError:
                    c_desc = block.desc['CHILD']
                offset = c_desc['TYPE'].writer(attr, block, 'CHILD',
                                               writebuffer, root_offset,
                                               offset, **kwargs)
            else:
                kwargs['parents'].append(block)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'c_desc' in locals():
            kwargs.update(field=c_desc.get(TYPE), desc=c_desc,
                          parent=p_block, attr_index=CHILD, offset=offset)
            e = format_write_error(e, **kwargs)
        elif 'i' in locals():
            kwargs.update(field=desc[i].get(TYPE), desc=desc[i],
                          parent=block, attr_index=i, offset=offset)
            e = format_write_error(e, **kwargs)

        kwargs.update(field=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_write_error(e, **kwargs)
        raise e


def stream_adapter_writer(self, block, parent=None, attr_index=None,
                          writebuffer=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        # make a new buffer to write the data to
        temp_buffer = BytearrayBuffer()
        orig_offset = offset
        desc = block.desc
        align = desc.get('ALIGN')

        # structs usually dont contain blocks, so check
        try:
            sub_desc = block.data.desc
        except AttributeError:
            sub_desc = desc['SUB_STRUCT']

        # If there is a specific pointer to read the block from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this block
        # is being built without a parent(such as from an exported .blok file)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the sub_struct to the temp buffer
        sub_desc['TYPE'].writer(block.data, block, 'SUB_STRUCT',
                                temp_buffer, 0, 0, **kwargs)

        # use the decoder method to get a decoded stream and
        # the length of the stream before it was decoded
        adapted_stream = desc['ENCODER'](block, temp_buffer, **kwargs)

        # write the adapted stream to the writebuffer
        writebuffer.seek(root_offset + offset)
        writebuffer.write(adapted_stream)

        # pass the incremented offset to the caller
        return offset + len(adapted_stream)
    except Exception as e:
        desc = locals().get('desc', None)
        e = format_write_error(e, field=self, desc=desc, parent=parent,
                               buffer=temp_buffer, attr_index=attr_index,
                               root_offset=root_offset, offset=offset,
                               **kwargs)
        raise e


def union_writer(self, block, parent=None, attr_index=None,
                 writebuffer=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        orig_offset = offset
        desc = block.desc
        size = desc['SIZE']
        align = desc.get('ALIGN')

        if attr_index is not None and desc.get('POINTER') is not None:
            offset = block.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # if the u_block is not flushed to the UnionBlock, do it
        # before writing the UnionBlock to the writebuffer
        if block.u_index is not None:
            block.flush()

        # write the UnionBlock to the writebuffer
        writebuffer.seek(root_offset + offset)
        writebuffer.write(block)

        # increment offset by the size of the UnionBlock
        offset += size

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        desc = locals().get('desc', None)
        e = format_write_error(e, field=self, desc=desc, parent=parent,
                               buffer=temp_buffer, attr_index=attr_index,
                               root_offset=root_offset, offset=offset,
                               **kwargs)
        raise e


def data_writer(self, block, parent=None, attr_index=None,
                writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    block = self.encoder(block, parent, attr_index)
    writebuffer.seek(root_offset + offset)
    writebuffer.write(block)
    return offset + len(block)


def cstring_writer(self, block, parent=None, attr_index=None,
                   writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python object in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    orig_offset = offset
    p_desc = parent.desc
    if p_desc['TYPE'].is_array:
        desc = p_desc['SUB_STRUCT']
    else:
        desc = p_desc[attr_index]

    if attr_index is not None:
        if parent is not None:
            # if the parent and attr_index arent
            # None, pointers may need to be used
            align = desc.get('ALIGN')
            if desc.get('POINTER') is not None:
                offset = parent.get_meta('POINTER', attr_index, **kwargs)
            elif align:
                offset += (align - (offset % align)) % align
        elif align:
            offset += (align - (offset % align)) % align

    block = self.encoder(block, parent, attr_index)
    writebuffer.seek(root_offset + offset)
    writebuffer.write(block)

    # pass the incremented offset to the caller
    return offset + len(block)


def py_array_writer(self, block, parent=None, attr_index=None,
                    writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a bytes representation of the python array in
    'attr_index' of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    orig_offset = offset
    p_desc = parent.desc
    if p_desc['TYPE'].is_array:
        desc = p_desc['SUB_STRUCT']
    else:
        desc = p_desc[attr_index]

    if attr_index is not None:
        if parent is not None:
            # if the parent and attr_index arent
            # None, pointers may need to be used
            align = desc.get('ALIGN')
            if desc.get('POINTER') is not None:
                offset = parent.get_meta('POINTER', attr_index, **kwargs)
            elif align:
                offset += (align - (offset % align)) % align
        elif align:
            offset += (align - (offset % align)) % align

    writebuffer.seek(root_offset + offset)

    # if the system the array exists on has a different
    # endianness than what the array should be written as,
    # then the endianness is swapped before writing it.

    # This is the only method I can think of to tell if
    # the endianness of an array needs to be changed since
    # the array.array objects dont know their own endianness'''

    if self.endian != byteorder_char and self.endian != '=':
        block.byteswap()
        writebuffer.write(block)
        block.byteswap()
    else:
        writebuffer.write(block)

    # pass the incremented offset to the caller
    return offset + len(block)*block.itemsize


def bytes_writer(self, block, parent=None, attr_index=None,
                 writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes the bytes or bytearray object in 'attr_index'
    of 'parent' to the supplied 'writebuffer'.
    Returns the offset this function finished writing at.

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    orig_offset = offset

    if parent is not None and attr_index is not None:
        p_desc = parent.desc
        if p_desc['TYPE'].is_array:
            desc = p_desc['SUB_STRUCT']
        else:
            desc = p_desc[attr_index]

        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)

    writebuffer.seek(root_offset + offset)
    writebuffer.write(block)

    # pass the incremented offset to the caller
    return offset + len(block)


def bit_struct_writer(self, block, parent=None, attr_index=None,
                      writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Writes a 'Bit Struct' type Block in 'attr_index' of
    'parent' to the supplied 'writebuffer'. All attributes of
    the BitStruct are converted to unsigned integers, merged
    together on the bit level, and the result is written.
    Returns the offset this function finished writing at.

    If attr_index is None, 'parent' is expected to be
    the Block being written, rather than its parent.
    """
    try:
        if hasattr(block, CHILD):
            kwargs['parents'].append(block)

        data = 0
        desc = block.desc
        structsize = desc['SIZE']

        # get a list of everything as unsigned
        # ints with their masks and offsets
        for i in range(len(block)):
            try:
                bitint = block[i].desc[TYPE].encoder(block[i], block, i)
            except AttributeError:
                bitint = desc[i][TYPE].encoder(block[i], block, i)

            # combine with the other data
            # 0=U_Int being written,  1=bit offset of U_Int,  2=U_Int mask
            data += (bitint[0] & bitint[2]) << bitint[1]

        writebuffer.seek(root_offset + offset)

        if self.endian == '<':
            writebuffer.write(data.to_bytes(structsize, 'little'))
        else:
            writebuffer.write(data.to_bytes(structsize, 'big'))

        return offset + structsize
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc')
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'i' in locals():
            a_desc = desc[i]
            kwargs.update(field=a_desc.get(TYPE), desc=a_desc,
                          parent=block, attr_index=i, offset=offset)
            e = format_write_error(e, **kwargs)

        kwargs.update(field=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_write_error(e, **kwargs)
        raise e


# #################################################
'''############  Decoder functions  ############'''
# #################################################


def decode_numeric(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Converts a bytes object into a python int.
    Decoding is done using struct.unpack

    Returns an int decoded represention of the "rawdata" argument.
    '''
    return unpack(self.enc, rawdata)[0]


def decode_24bit_numeric(self, rawdata, desc=None,
                         parent=None, attr_index=None):
    '''
    Converts a 24-bit bytes object into a python int.
    Decoding is done using struct.unpack and a manual twos-signed check.

    Returns an int decoded represention of the "rawdata" argument.
    '''
    if self.endian == '<':
        rawint = unpack('<I', rawdata + b'\x00')[0]
    else:
        rawint = unpack('>I', b'\x00' + rawdata)[0]

    # if the int can be signed and IS signed then take care of that
    if rawint & 0x800000 and self.enc[1] == 'i':
        return rawint - 0x10000000  # 0x10000000 == 0x800000 * 2
    return rawint


def decode_timestamp(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    '''
    return ctime(unpack(self.enc, rawdata)[0])


def decode_string(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string
    with the delimiter character sliced off the end.
    Decoding is done using bytes.decode

    Returns a string decoded represention of the "rawdata" argument.
    '''
    return rawdata.decode(encoding=self.enc).split(self.str_delimiter)[0]


def decode_raw_string(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string that can contain delimiters.
    Decoding is done using bytes.decode

    Returns a string decoded represention of the "rawdata" argument.
    '''
    return rawdata.decode(encoding=self.enc)


def decode_string_hex(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a bytes object into a python string representing
    the original bytes object in a hexadecimal form.

    Returns a string decoded represention of the "rawdata" argument.
    '''
    # slice off the first 2 characters since they are '0x'
    return hex(int.from_bytes(rawdata, 'big'))[2:]


def decode_big_int(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Decoding is done using int.from_bytes

    Returns an int represention of the "rawdata" argument.
    '''
    if len(rawdata):
        if self.endian == '<':
            endian = 'little'
        else:
            endian = 'big'

        if self.enc.endswith('s'):
            # ones compliment
            bigint = int.from_bytes(rawdata, endian, signed=True)
            if bigint < 0:
                return bigint + 1
            return bigint
        elif self.enc.endswith('S'):
            # twos compliment
            return int.from_bytes(rawdata, endian, signed=True)

        return int.from_bytes(rawdata, endian)
    # If an empty bytes object was provided, return a zero.
    # Not sure if this should be an exception instead.
    return 0


def decode_bit(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes a single bit from the given int into an int.
    Returns a 1 if the bit is set, or a 0 if it isnt.
    '''
    # mask and shift the int out of the rawdata
    return (rawdata >> parent.ATTR_OFFS[attr_index]) & 1


def decode_bit_int(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the bit level in either ones or twos compliment

    Returns an int represention of the "rawdata" argument
    after masking and bit-shifting.
    '''
    bitcount = parent.get_size(attr_index)

    if bitcount:
        offset = parent.ATTR_OFFS[attr_index]
        mask = (1 << bitcount) - 1

        # mask and shift the int out of the rawdata
        bitint = (rawdata >> offset) & mask

        # if the number would be negative if signed
        if bitint & (1 << (bitcount - 1)):
            intmask = ((1 << (bitcount - 1)) - 1)
            if self.enc == 's':
                # get the ones compliment and change the sign
                return -1*((~bitint) & intmask)
            elif self.enc == 'S':
                # get the twos compliment and change the sign
                bitint = -1*((~bitint + 1) & intmask)
                # if only the negative sign was set, the bitint will be
                # masked off to 0, and end up as 0 rather than the max
                # negative number it should be. instead, return negative max
                if not bitint:
                    return -(1 << (bitcount - 1))

        return bitint
    # If the bit count is zero, return a zero
    # Not sure if this should be an exception instead.
    return 0


# #################################################
'''############  Encoder functions  ############'''
# #################################################


def encode_numeric(self, block, parent=None, attr_index=None):
    '''
    Encodes a python int into a bytes representation.
    Encoding is done using struct.pack

    Returns a bytes object encoded represention of the "block" argument.
    '''
    return pack(self.enc, block)


def encode_24bit_numeric(self, block, parent=None, attr_index=None):
    '''
    Encodes a python int to a signed or unsigned 24-bit bytes representation.

    Returns a bytes object encoded represention of the "block" argument.
    '''
    if self.enc[1] == 'i':
        # int can be signed
        assert block >= -0x800000 and block <= 0x7fffff, (
            '%s is too large to pack as a 24bit signed int.' % block)
        if block < 0:
            # int IS signed
            block += 0x10000000
    else:
        assert block >= 0 and block <= 0xffffff (
            '%s is too large to pack as a 24bit unsigned int.' % block)

    # pack and return the int
    if self.endian == '<':
        return pack('<I', block)[0:3]
    return pack('>I', block)[1:4]


def encode_int_timestamp(self, block, parent=None, attr_index=None):
    '''
    '''
    return pack(self.enc, int(mktime(strptime(block))))


def encode_float_timestamp(self, block, parent=None, attr_index=None):
    '''
    '''
    return pack(self.enc, float(mktime(strptime(block))))


def encode_string(self, block, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation,
    making sure there is a delimiter character on the end.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "block" argument.
    '''
    if not block.endswith(self.str_delimiter):
        return (block + self.str_delimiter).encode(self.enc)
    return block.encode(self.enc)


def encode_raw_string(self, block, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "block" argument.
    '''
    return block.encode(self.enc)


def encode_string_hex(self, block, parent=None, attr_index=None):
    '''
    Encodes a python string formatted as a hex string into a bytes object.

    Returns a bytes object encoded represention of the "block" argument.
    '''
    return int(block, 16).to_bytes((len(block) + 1)//2, 'big')


def encode_big_int(self, block, parent=None, attr_index=None):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Encoding is done using int.to_bytes

    Returns a bytes object encoded represention of the "block" argument.
    '''
    bytecount = parent.get_size(attr_index)

    if bytecount:
        if self.endian == '<':
            endian = 'little'
        else:
            endian = 'big'

        if self.enc.endswith('S'):
            # twos compliment
            return block.to_bytes(bytecount, endian, signed=True)
        elif self.enc.endswith('s'):
            # ones compliment
            if block < 0:
                return (block-1).to_bytes(bytecount, endian, signed=True)
            return block.to_bytes(bytecount, endian, signed=True)

        return block.to_bytes(bytecount, endian)
    return bytes()


def encode_bit(self, block, parent=None, attr_index=None):
    '''
    Encodes an int to a single bit.
    Returns the encoded int, the offset it should be
    shifted to, and a mask that covers its range.
    '''
    # return the int with the bit offset and a mask of 1
    return(block, parent.ATTR_OFFS[attr_index], 1)


def encode_bit_int(self, block, parent=None, attr_index=None):
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
    if block < 0:
        signmask = 1 << (bitcount - 1)
        if self.enc == 'S':
            return(2*signmask + block, offset, mask)
        return(signmask - block, offset, mask)
    return(block, offset, mask)


# ##################################################
'''###########  Void Field functions  ###########'''
# ##################################################


# These next methods are exclusively used for the Void Field.
def void_reader(self, desc, block=None, parent=None, attr_index=None,
                rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    Builds a 'Void' type Block and places it into the
    'parent' Block at 'attr_index'.
    Returns the provided argument 'offset'.

    Optional kwargs:
        parents(list)
    """
    if block is None:
        parent[attr_index] = (desc.get(BLOCK_CLS, self.py_type)
                              (desc, parent=parent))
    return offset


def void_writer(self, block, parent=None, attr_index=None,
                writebuffer=None, root_offset=0, offset=0, **kwargs):
    '''
    Writes nothing.
    Returns the provided 'offset' argument
    '''
    return offset


def pad_reader(self, desc, block=None, parent=None, attr_index=None,
               rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    if block is None:
        parent[attr_index] = block = (desc.get(BLOCK_CLS, self.py_type)
                                      (desc, parent=parent))
        return offset + block.get_size(offset=offset, root_offset=root_offset,
                                       rawdata=rawdata, **kwargs)
    return offset


def pad_writer(self, block, parent=None, attr_index=None,
               writebuffer=None, root_offset=0, offset=0, **kwargs):
    ''''''
    pad_size = block.get_size(offset=offset, root_offset=root_offset, **kwargs)
    writebuffer.seek(offset + root_offset)
    writebuffer.write(b'\x00'*pad_size)
    if parent is not None:
        return offset + pad_size
    return offset


def no_decode(self, rawdata, desc=None, parent=None, attr_index=None):
    ''''''
    return rawdata


def no_encode(self, block, parent=None, attr_index=None):
    ''''''
    return block


# ##################################################
'''############  Sizecalc functions  ############'''
# ##################################################


def no_sizecalc(self, block, **kwargs):
    '''
    If a sizecalc routine wasnt provided for this Field and one can't
    be decided upon as a default, then the size can't be calculated.
    Returns 0 when called.
    '''
    return 0


def def_sizecalc(self, block, **kwargs):
    '''
    Only used if the self.var_size == False.
    Returns the byte size specified by the Field.
    '''
    return self.size


def len_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of an object whose length is its
    size if it were converted to bytes(bytes, bytearray).
    '''
    return len(block)


def str_sizecalc(self, block, **kwargs):
    '''Returns the byte size of a string if it were encoded to bytes.'''
    return len(block)*self.size


def str_hex_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a string of hex characters if it were encoded
    to a bytes object. Add 1 to round up to the nearest multiple of 2.
    '''
    return (len(block) + 1)//2


def delim_str_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a delimited string if it were encoded to bytes.
    '''
    # dont add the delimiter size if the string is already delimited
    if block.endswith(self.str_delimiter):
        return len(block) * self.size
    return (len(block) + 1) * self.size


def delim_utf_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were encoded to bytes.

    Only use this for UTF8 and UTF16 as it is slower than delim_str_sizecalc.
    '''
    blocklen = len(block.encode(encoding=self.enc))

    # dont add the delimiter size if the string is already delimited
    if block.endswith(self.str_delimiter):
        return blocklen
    return blocklen + self.size


def utf_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of a UTF string if it were encoded to bytes.

    Only use this for UTF8 and UTF16 as it is slower than str_sizecalc.
    '''
    # return the length of the entire string of bytes
    return len(block.encode(encoding=self.enc))


def array_sizecalc(self, block, **kwargs):
    '''
    Returns the byte size of an array if it were encoded to bytes.
    '''
    return len(block)*block.itemsize


def big_sint_sizecalc(self, block, **kwargs):
    '''
    Returns the number of bytes required to represent a twos signed integer.
    NOTE: returns a byte size of 1 for the int 0
    '''
    # add 8 bits for rounding up, and 1 for the sign bit
    return (block.bit_length() + 9) // 8


def big_uint_sizecalc(self, block, **kwargs):
    '''
    Returns the number of bytes required to represent an unsigned integer.
    NOTE: returns a byte size of 1 for the int 0
    '''
    # add 8 bits for rounding up
    return (block.bit_length() + 8) // 8


def bit_sint_sizecalc(self, block, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    return block.bit_length() + 1


def bit_uint_sizecalc(self, block, **kwargs):
    '''
    Returns the number of bits required to represent an integer
    of arbitrary size, whether ones signed, twos signed, or unsigned.
    '''
    return block.bit_length()


# ###################################################
'''############  Sanitizer functions  ############'''
# ###################################################


def bool_enum_sanitizer(blockdef, src_dict, **kwargs):
    '''
    '''
    p_field = src_dict[TYPE]

    nameset = set()
    src_dict[NAME_MAP] = dict(src_dict.get(NAME_MAP, ()))
    src_dict[VALUE_MAP] = {}

    # Need to make sure there is a value for each element
    blockdef.sanitize_entry_count(src_dict)
    blockdef.sanitize_element_ordering(src_dict)
    blockdef.sanitize_option_values(src_dict, p_field, **kwargs)

    if not isinstance(src_dict.get(SIZE, 0), int):
        blockdef._e_str += (
            ("ERROR: INVALID TYPE FOR SIZE IN '%s'.\n    EXPECTED %s, GOT %s" +
             ".\n") % (src_dict.get(NAME, UNNAMED), int, type(src_dict[SIZE])))
        blockdef._bad = True

    for i in range(src_dict[ENTRIES]):
        name = blockdef.sanitize_name(src_dict, i,
                                      allow_reserved=not p_field.is_bool)
        if name in nameset:
            blockdef._e_str += (
                ("ERROR: DUPLICATE NAME FOUND IN '%s'.\nNAME OF OFFENDING " +
                 "ELEMENT IS '%s'\n") % (src_dict.get(NAME, UNNAMED), name))
            blockdef._bad = True
            continue
        src_dict[NAME_MAP][name] = i
        src_dict[VALUE_MAP][src_dict[i][VALUE]] = i
        nameset.add(name)
    return src_dict


def struct_sanitizer(blockdef, src_dict, **kwargs):
    """
    """
    # whether or not to calculate a size based on the element sizes
    calc_size = SIZE not in src_dict

    # make sure there is a size(it'll trip error catching routines otherwise)
    if calc_size:
        src_dict[SIZE] = 0

    # do the standard sanitization routine on the non-numbered entries
    src_dict = standard_sanitizer(blockdef, src_dict, **kwargs)

    # if a variable doesnt have a specified offset then
    # this will be used as the starting offset and will
    # be incremented by the size of each variable after it
    def_offset = 0
    # the largest alignment size requirement of any entry in this block
    l_align = 1

    p_field = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # ATTR_OFFS stores the offsets of each attribute by index.
    attr_offs = [0]*src_dict.get(ENTRIES, 0)
    nameset = set()  # contains the name of each entriy in the desc
    rem = 0  # number of dict entries removed
    key = 0
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in range(src_dict[ENTRIES]):
        this_d = src_dict[key]

        if isinstance(this_d, dict):
            # Make sure to shift upper indexes down by how many
            # were removed and make a copy to preserve the original
            this_d = src_dict[key-rem] = dict(this_d)
            key -= rem

            field = this_d.get(TYPE)

            if field is fields.Pad:
                # the dict was found to be padding, so increment
                # the default offset by it, remove the entry from the
                # dict, and adjust the removed and entry counts.
                size = this_d.get(SIZE)

                if size is not None:
                    def_offset += size
                else:
                    blockdef._bad = True
                    blockdef._e_str += (
                        ("ERROR: Pad ENTRY IN '%s' OF TYPE %s AT INDEX %s " +
                         "IS MISSING A SIZE KEY.\n") % (p_name, p_field, key))
                if ATTR_OFFS in src_dict:
                    blockdef._e_str += (
                        ("ERROR: ATTR_OFFS ALREADY EXISTS IN '%s' OF TYPE " +
                         "%s, BUT A Pad ENTRY WAS FOUND AT INDEX %s.\n" +
                         "    CANNOT INCLUDE Pad Fields WHEN ATTR_OFFS " +
                         "ALREADY EXISTS.\n") % (p_name, p_field, key + rem))
                    blockdef._bad = True
                rem += 1
                src_dict[ENTRIES] -= 1
                continue
            elif field is not None:
                # make sure the block has an offset if it needs one
                if OFFSET not in this_d:
                    this_d[OFFSET] = def_offset
            elif p_field:
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                    "TYPE '%s' AT INDEX %s.\n" % (p_name, p_field, key))

            kwargs["key_name"] = key
            this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

            if field:
                sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
                if NAME_MAP in src_dict:
                    src_dict[NAME_MAP][sani_name] = key

                    name = this_d[NAME]
                    if name in nameset:
                        blockdef._e_str += (
                            ("ERROR: DUPLICATE NAME FOUND IN '%s' AT INDEX " +
                             "%s.\n    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                            (p_name, key, name))
                        blockdef._bad = True
                    nameset.add(name)

                # get the size of the entry(if the parent dict requires)
                if OFFSET in this_d:
                    # add the offset to ATTR_OFFS in the parent dict
                    offset = this_d[OFFSET]
                    size = blockdef.get_size(src_dict, key)

                    # make sure not to align within bit structs
                    if not p_field.is_bit_based:
                        align = blockdef.get_align(src_dict, key)

                        if align > ALIGN_MAX:
                            align = l_align = ALIGN_MAX
                        elif align > l_align:
                            l_align = align

                        if align > 1:
                            offset += (align - (offset % align)) % align

                    if isinstance(size, int):
                        def_offset = offset + size
                    else:
                        blockdef._e_str += (
                            ("ERROR: INVALID TYPE FOR SIZE FOUND IN '%s' AT " +
                             "INDEX %s.\n    EXPECTED %s, GOT %s. \n    NAME" +
                             " OF OFFENDING ELEMENT IS '%s' OF TYPE %s.\n") %
                            (p_name, key + rem, int, type(size), name, field))
                        blockdef._bad = True

                    # set the offset and delete the OFFSET entry
                    attr_offs[key] = offset
                    del this_d[OFFSET]

    # if there were any removed entries (padding) then the
    # ones above where the last key was need to be deleted
    entry_count = src_dict[ENTRIES]
    for i in range(entry_count, entry_count + rem):
        del src_dict[i]

    # prune potentially extra entries from the attr_offs list
    attr_offs = attr_offs[:entry_count]

    # if the field is a struct and the ATTR_OFFS isnt already in it
    if ATTR_OFFS not in src_dict:
        src_dict[ATTR_OFFS] = attr_offs

    # Make sure all structs have a defined SIZE
    if p_field and calc_size:
        if p_field.is_bit_based:
            def_offset = int(ceil(def_offset / 8))

        # calculate the padding based on the largest alignment
        padding = (l_align - (def_offset % l_align)) % l_align
        src_dict[SIZE] = def_offset + padding

    return src_dict


def quickstruct_sanitizer(blockdef, src_dict, **kwargs):
    """
    """
    # do the struct sanitization routine on the src_dict
    src_dict = struct_sanitizer(blockdef, src_dict, **kwargs)
    p_field = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # make sure nothing exists in the QuickStruct that cant be in it.
    for key, this_d in ((i, src_dict[i]) for i in range(src_dict[ENTRIES])):
        if isinstance(this_d, dict) and this_d.get(TYPE):
            field = this_d[TYPE]
            name = this_d.get(NAME, UNNAMED)

            if field.is_block:
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CANNOT CONTAIN BLOCKS.\n    " +
                    "OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n    " +
                    "OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (field, name, p_name, p_field, key)
            elif (field.enc not in QSTRUCT_ALLOWED_ENC or
                  field.py_type not in (float, int)):
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CAN ONLY CONTAIN INTEGER AND/OR " +
                    "FLOAT DATA WHOSE ENCODING IS ONE OF THE FOLLOWING:\n" +
                    ("    %s\n" % sorted(QSTRUCT_ALLOWED_ENC)) +
                    "    OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n" +
                    "    OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (field, name, p_name, p_field, key)

    return src_dict


def sequence_sanitizer(blockdef, src_dict, **kwargs):
    """
    Loops through each of the numbered entries in the descriptor.
    This is done separate from the non-integer dict entries because
    a check to sanitize offsets needs to be done from 0 up to ENTRIES.
    Looping over a dictionary by its keys will do them in a non-ordered
    way and the offset sanitization requires them to be done in order.
    """

    # do the standard sanitization routine on the non-numbered entries
    src_dict = standard_sanitizer(blockdef, src_dict, **kwargs)

    p_field = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    nameset = set()  # contains the name of each entry in the desc
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in range(src_dict[ENTRIES]):
        this_d = src_dict[key]

        if isinstance(this_d, dict):
            this_d = src_dict[key] = dict(this_d)
            field = this_d.get(TYPE)

            if field is fields.Pad:
                size = this_d.get(SIZE)

                if size is None:
                    blockdef._bad = True
                    blockdef._e_str += (
                        ("ERROR: Pad ENTRY IN '%s' OF TYPE %s AT INDEX %s " +
                         "IS MISSING A SIZE KEY.\n") % (p_name, p_field, key))
                # make sure the padding follows convention and has a name
                this_d.setdefault(NAME, 'pad_entry_%s' % pad_count)
                if NAME_MAP in src_dict:
                    src_dict[NAME_MAP][this_d[NAME]] = key
                pad_count += 1
                continue
            elif field is None and p_field:
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                    "TYPE '%s' AT INDEX %s.\n" % (p_name, p_field, key))

            kwargs["key_name"] = key
            this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

            if field:
                sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
                if NAME_MAP in src_dict:
                    src_dict[NAME_MAP][sani_name] = key

                    name = this_d[NAME]
                    if name in nameset:
                        blockdef._e_str += (
                            ("ERROR: DUPLICATE NAME FOUND IN '%s' AT INDEX " +
                             "%s.\n    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                            (p_name, key, name))
                        blockdef._bad = True
                    nameset.add(name)

    return src_dict


def standard_sanitizer(blockdef, src_dict, **kwargs):
    ''''''
    p_field = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # create a NAME_MAP, which maps the name of
    # each attribute to the key it's stored under
    if p_field.is_block:
        src_dict[NAME_MAP] = dict(src_dict.get(NAME_MAP, ()))
        blockdef.sanitize_entry_count(src_dict, kwargs["key_name"])
        blockdef.sanitize_element_ordering(src_dict)

    # The non integer entries aren't substructs, so set it to False.
    kwargs['substruct'] = False

    # if the block cant hold a child, but the descriptor
    # requires that it have a CHILD attribute, try to
    # set the BLOCK_CLS to one that can hold a CHILD.
    # Only do this though, if there isnt already a default set.
    if (not hasattr(p_field.py_type, CHILD) and
        CHILD in src_dict and BLOCK_CLS not in src_dict):
        try:
            src_dict[BLOCK_CLS] = p_field.py_type.PARENTABLE
        except AttributeError:
            blockdef._bad = True
            blockdef._e_str += (
                ("ERROR: FOUND DESCRIPTOR WHICH SPECIFIES A CHILD, BUT " +
                 "THE CORROSPONDING Block\nHAS NO SLOT FOR A CHILD " +
                 "AND DOES NOT SPECIFY A BLOCK THAT HAS A SLOT.\n    " +
                 "OFFENDING ELEMENT IS %s OF TYPE %s\n") % (p_name, p_field))

    # loops through the descriptors non-integer keyed sub-sections
    for key in src_dict:
        if not isinstance(key, int):
            if key not in desc_keywords:
                blockdef._e_str += (
                    ("ERROR: FOUND ENTRY IN DESCRIPTOR OF '%s' UNDER " +
                     "UNKNOWN STRING KEY '%s'.\n") % (p_name, key))
                blockdef._bad = True
            if isinstance(src_dict[key], dict) and key != ADDED:
                kwargs["key_name"] = key
                field = src_dict[key].get(TYPE)
                this_d = dict(src_dict[key])

                # replace with the modified copy so the original is intact
                src_dict[key] = this_d = blockdef.sanitize_loop(this_d,
                                                                **kwargs)

                if field:
                    # if this is the repeated substruct of an array
                    # then we need to calculate and set its alignment
                    if ((key == SUB_STRUCT or field.is_str) and
                        ALIGN not in this_d):
                        align = blockdef.get_align(src_dict, key)
                        # if the alignment is 1 then adjustments arent needed
                        if align > 1:
                            this_d[ALIGN]

                    sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
                    if key != SUB_STRUCT:
                        src_dict[NAME_MAP][sani_name] = key
    return src_dict


def switch_sanitizer(blockdef, src_dict, **kwargs):
    ''''''
    # The descriptor is a switch, so individual cases need to
    # be checked and setup as well as the pointer and defaults.
    p_field = src_dict[TYPE]
    size = src_dict.get(SIZE)
    p_name = src_dict.get(NAME, UNNAMED)
    pointer = src_dict.get(POINTER)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if src_dict.get(CASE) is None:
        blockdef._e_str += ("ERROR: CASE MISSING IN '%s' OF TYPE %s\n" %
                            (p_name, p_field))
        blockdef._bad = True
    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += ("ERROR: CASES MISSING IN '%s' OF TYPE %s\n" %
                            (p_name, p_field))
        blockdef._bad = True

    for case in cases:
        case_map[case] = c_index
        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])
        c_field = case_desc.get(TYPE, fields.Void)
        if not c_field.is_block:
            blockdef._e_str += ("ERROR: Switch CASES MUST HAVE THEIR " +
                                "Field BE A Block.\n    OFFENDING " +
                                "ELEMENT IS '%s' OF '%s' OF TYPE %s.\n" %
                                (case, p_name, c_field))
            blockdef._bad = True

        kwargs['key_name'] = case
        # copy the pointer and size from the switch into each case
        if pointer is not None:
            case_desc.setdefault(POINTER, pointer)
        if size is not None:
            case_desc.setdefault(SIZE, size)

        # need to sanitize the names of the descriptor
        blockdef.sanitize_name(case_desc, **kwargs)
        src_dict[c_index] = blockdef.sanitize_loop(case_desc, **kwargs)

        c_index += 1

    if CASES in src_dict:
        del src_dict[CASES]
    src_dict[CASE_MAP] = case_map

    # make sure there is a default case
    src_dict[DEFAULT] = dict(src_dict.get(DEFAULT, common_descs.void_desc))
    kwargs['key_name'] = DEFAULT

    # copy the pointer and size from the switch into the default
    if pointer is not None:
        src_dict[DEFAULT].setdefault(POINTER, pointer)
    if size is not None:
        src_dict[DEFAULT].setdefault(SIZE, size)
    src_dict[DEFAULT] = blockdef.sanitize_loop(src_dict[DEFAULT], **kwargs)

    return src_dict


def _find_union_errors(blockdef, src_dict):
    ''''''
    if isinstance(src_dict, dict):
        p_name = src_dict.get(NAME, UNNAMED)
        p_field = src_dict.get(TYPE)

        if p_field is not None:
            if CHILD in src_dict:
                blockdef._e_str += (
                    "ERROR: Union Fields CANNOT CONTAIN CHILD BLOCKS AT " +
                    "ANY POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                    "IS '%s' OF TYPE %s." % (p_name, p_field))
                blockdef._bad = True

            if POINTER in src_dict:
                blockdef._e_str += (
                    "ERROR: Union Fields CANNOT BE POINTERED AT ANY " +
                    "POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                    "IS '%s' OF TYPE %s." % (p_name, p_field))
                blockdef._bad = True

            # re-run this check on entries in the dict
            for key in src_dict:
                _find_union_errors(blockdef, src_dict[key])


def union_sanitizer(blockdef, src_dict, **kwargs):
    ''''''
    # If the descriptor is a switch, the individual cases need to
    # be checked and setup as well as the pointer and defaults.
    p_field = src_dict[TYPE]
    size = src_dict.get(SIZE, 0)
    p_name = src_dict.get(NAME, UNNAMED)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += ("ERROR: CASES MISSING IN '%s' OF TYPE %s\n" %
                            (p_name, p_field))
        blockdef._bad = True
    if not isinstance(size, int):
        blockdef._e_str += (
            ("ERROR: Union 'SIZE' MUST BE AN INT LITERAL OR UNSPECIFIED, " +
             "NOT %s.\n    OFFENDING BLOCK IS '%s' OF TYPE %s\n") %
            (type(size), p_name, p_field))
        blockdef._bad = True
    if p_field.is_bit_based:
        blockdef._e_str += (
            "ERROR: Unions CANNOT BE INSIDE A bit_based Field.\n    " +
            "OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_field))
        blockdef._bad = True

    # loop over all union cases and sanitize them
    for case in cases:
        case_map[case] = c_index

        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])

        c_field = case_desc.get(TYPE, fields.Void)
        c_size = blockdef.get_size(case_desc)

        kwargs['key_name'] = case

        # sanitize the name and gui_name of the descriptor
        blockdef.sanitize_name(case_desc, **kwargs)
        c_name = case_desc.get(NAME, UNNAMED)

        if not c_field.is_block:
            blockdef._e_str += (
                ("ERROR: Union CASES MUST HAVE THEIR Field.py_type BE A " +
                 "Block.\n    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_field, case, p_name))
            blockdef._bad = True
        if not c_field.is_struct and c_field.is_bit_based:
            blockdef._e_str += (
                ("ERROR: Structs ARE THE ONLY bit_based Fields ALLOWED IN A " +
                 "Union.\n    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_field, case, p_name))
            blockdef._bad = True

        # sanitize the case descriptor
        src_dict[c_index] = blockdef.sanitize_loop(case_desc, **kwargs)

        # check for any nested errors specific to unions
        _find_union_errors(blockdef, case_desc)

        # set size to the largest size out of all the cases
        size = max(size, c_size)
        c_index += 1

    if CASES in src_dict:
        del src_dict[CASES]
    src_dict[CASE_MAP] = case_map
    src_dict[SIZE] = size

    return src_dict


def stream_adapter_sanitizer(blockdef, src_dict, **kwargs):
    ''''''
    p_field = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    if SUB_STRUCT not in src_dict:
        blockdef._e_str += ("ERROR: MISSING SUB_STRUCT ENTRY.\n" +
                            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" %
                            (p_name, p_field))
        blockdef._bad = True
        return src_dict
    if DECODER not in src_dict:
        blockdef._e_str += ("ERROR: MISSING STREAM DECODER.\n" +
                            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" %
                            (p_name, p_field))
        blockdef._bad = True
    if ENCODER not in src_dict:
        # if no encoder was provided, use a dummy one
        src_dict[ENCODER] = adapter_no_encode

    # copy the substruct desc so it can be modified
    substruct_desc = dict(src_dict[SUB_STRUCT])
    kwargs['key_name'] = SUB_STRUCT

    # sanitize the name and gui_name of the descriptor
    blockdef.sanitize_name(substruct_desc, **kwargs)

    a_name = substruct_desc.get(NAME, UNNAMED)

    # sanitize the case descriptor
    src_dict[SUB_STRUCT] = blockdef.sanitize_loop(substruct_desc, **kwargs)
    src_dict[NAME_MAP] = {SUB_STRUCT: 'data', a_name: 'data'}

    return src_dict
