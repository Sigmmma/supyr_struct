'''
Parser, serializer, encoder, and decoder functions for all standard FieldTypes.

Parsers are responsible for reading bytes from a buffer and calling their
associated decoder on the bytes to turn them into a python object.

Serializers are responsible for calling their associated encoder, using it to
encode a python object, and writing the encoded bytes to the writebuffer.

If the FieldType the parser/serializer is meant for is not actually data,
but rather a form of hierarchy(like a Struct or Container) then
they wont have an encoder/decoder to call, but instead will be
responsible for calling the parser/serializer functions of their
attributes and possibly the parser/serializer functions of their
steptree and the steptrees of all nested children.

Parsers and serializers must also return an integer specifying
what offset the last data was read from or written to.

Decoders are responsible for converting bytes into a python object*
Encoders are responsible for converting a python object into bytes*

Some functions do not require all of the arguments they are given,
but many of them do, and it is easier to provide extra arguments
that are ignored than to provide exactly what is needed.

*Not all encoders and decoders receive/return bytes objects.
FieldTypes that operate on the bit level cant be expected to return
even byte sized amounts of bits, so they operate differently.
A FieldTypes parser/serializer and decoder/encoder simply need to
be working with the same parameter and return data types.
'''

from decimal import Decimal
from math import ceil, log
from struct import pack, pack_into, unpack
from sys import byteorder
from time import mktime, ctime, strptime

from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.buffer import *

# linked to through supyr_struct.__init__
blocks = None
common_descs = None
field_types = None

__all__ = [
    'byteorder_char',
    # Basic routines

    # Parsers
    'container_parser', 'array_parser',
    'struct_parser', 'bit_struct_parser', 'py_array_parser',
    'data_parser', 'cstring_parser', 'bytes_parser',
    # Serializers
    'container_serializer', 'array_serializer',
    'struct_serializer', 'bit_struct_serializer', 'py_array_serializer',
    'f_s_data_serializer', 'data_serializer',
    'cstring_serializer', 'bytes_serializer',
    # Decoders
    'decode_numeric', 'decode_string', 'no_decode',
    'decode_big_int', 'decode_bit_int', 'decode_raw_string',
    # Encoders
    'encode_numeric', 'encode_string', 'no_encode',
    'encode_big_int', 'encode_bit_int',
    # size calculators
    'no_sizecalc', 'def_sizecalc', 'len_sizecalc',
    'delim_str_sizecalc', 'str_sizecalc',

    # wrapper functions
    'sizecalc_wrapper', 'encoder_wrapper', 'decoder_wrapper',

    # Specialized routines

    # Parsers
    'default_parser', 'f_s_data_parser', 'computed_parser',
    'switch_parser', 'while_array_parser',
    'void_parser', 'pad_parser', 'union_parser',
    'stream_adapter_parser', 'quickstruct_parser',
    # Serializers
    'computed_serializer',
    'void_serializer', 'pad_serializer', 'union_serializer',
    'stream_adapter_serializer', 'quickstruct_serializer',
    # Decoders
    'decode_24bit_numeric', 'decode_decimal', 'decode_bit',
    'decode_timestamp', 'decode_string_hex',
    # Encoders
    'encode_24bit_numeric', 'encode_decimal', 'encode_bit', 'encode_raw_string',
    'encode_int_timestamp', 'encode_float_timestamp', 'encode_string_hex',
    # size calculators
    'delim_utf_sizecalc', 'utf_sizecalc', 'array_sizecalc',
    'big_sint_sizecalc', 'big_uint_sizecalc', 'str_hex_sizecalc',
    'bit_sint_sizecalc', 'bit_uint_sizecalc', 'computed_sizecalc',

    # Sanitizer functions
    'bool_sanitizer', 'enum_sanitizer', 'switch_sanitizer',
    'sequence_sanitizer', 'standard_sanitizer',
    'struct_sanitizer', 'quickstruct_sanitizer',
    'union_sanitizer', 'stream_adapter_sanitizer',

    # Exception string formatters
    'format_parse_error', 'format_serialize_error'
    ]

# for use in byteswapping arrays
byteorder_char = {'little': '<', 'big': '>'}[byteorder]

PARSE_ERROR_HEAD = "\nError occurred while parsing:"
SERIALIZE_ERROR_HEAD = "\nError occurred while serializing:"

QSTRUCT_ALLOWED_ENC = set('bB')
for c in 'HhIiQqfd':
    QSTRUCT_ALLOWED_ENC.add('<' + c)
    QSTRUCT_ALLOWED_ENC.add('>' + c)


def adapter_no_encode(parent, buffer, **kwargs):
    '''
    Returns the supplied 'buffer' argument.
    This function is used as the ENCODER entry in the descriptor
    for StreamAdapter FieldTypes when an ENCODER is not present.
    '''
    return buffer


# These next functions are for wrapping sizecalcs/encoders/decoders
# in functions which properly work with FieldTypes where is_block and
# is_data are both True. This is because the node will be a Block
# with some attribute that stores the "data" of the node.
def sizecalc_wrapper(sc):
    '''
    '''
    def sizecalc(self, node, _sizecalc=sc, *a, **kw):
        return _sizecalc(self, node.data, *a, **kw)

    return sizecalc


def decoder_wrapper(de):
    '''
    '''
    def decoder(self, rawdata, desc=None, parent=None,
                attr_index=None, _decode=de):
        return self.node_cls(desc, parent, initdata=_decode(
            self, rawdata, desc, parent, attr_index))

    return decoder


def encoder_wrapper(en):
    '''
    '''
    def encoder(self, node, parent=None, attr_index=None, _encode=en):
        return _encode(self, node.data, parent, attr_index)

    return encoder


def format_parse_error(e, **kwargs):
    '''
    Returns a FieldParseError which details the hierarchy
    of the field in which the parse error occurred.

    If the 'error' provided is not a FieldParseError, then
    one will be created. If it is, it will have the current
    level of hierarchy inserted into its last args string.

    keyword arguments:
    desc --------- defaults to dict()
    field_type --- defaults to desc.get('TYPE')
    parent ------- defaults to None
    attr_index --- defaults to None
    offset ------- defaults to 0
    root_offset -- defaults to 0
    '''
    e_str0 = e_str1 = ''
    desc = kwargs.get('desc', {})
    field_type = kwargs.get('field_type', desc.get('TYPE'))
    parent = kwargs.get('parent')
    attr_index = kwargs.get('attr_index')
    offset = kwargs.get('offset', 0)
    root_offset = kwargs.get('root_offset', 0)
    try:
        name = desc.get(NAME, UNNAMED)
    except Exception:
        name = UNNAMED
    if not isinstance(e, FieldParseError):
        e = FieldParseError()
        e_str0 = PARSE_ERROR_HEAD
        e.seen = set()

    # get a copy of all but the last of the arguments
    a = e.args[:-1]
    try:
        e_str0 = str(e.args[-1])
        e_str0, e_str1 = (e_str0[:len(PARSE_ERROR_HEAD)],
                          e_str0[len(PARSE_ERROR_HEAD):])
    except IndexError:
        pass

    # make sure this node hasnt already been seen
    seen_id = (id(parent), id(field_type), attr_index)
    if seen_id in e.seen:
        return e
    e.seen.add(seen_id)

    # remake the args with the new data
    e.args = a + (
        e_str0 + "\n    %s, index:%s, offset:%s, field_type:%s" %
        (name, attr_index, offset + root_offset, field_type) + e_str1,)

    # add the extra data pertaining to this hierarchy level to e.error_data
    e.error_data.insert(0, kwargs)
    return e


def format_serialize_error(e, **kwargs):
    '''
    Returns an FieldSerializeError which details the hierarchy
    of the field in which the serialize error occurred.

    If the 'error' provided is not a FieldSerializeError, then
    one will be created. If it is, it will have the current
    level of hierarchy inserted into its last args string.

    keyword arguments:
    desc --------- defaults to dict()
    field_type --- defaults to desc.get('TYPE')
    parent ------- defaults to None
    attr_index --- defaults to None
    offset ------- defaults to 0
    root_offset -- defaults to 0
    '''
    e_str0 = e_str1 = ''
    desc = kwargs.get('desc', {})
    field_type = kwargs.get('field_type', desc.get('TYPE'))
    parent = kwargs.get('parent')
    attr_index = kwargs.get('attr_index')
    offset = kwargs.get('offset', 0)
    root_offset = kwargs.get('root_offset', 0)
    try:
        name = desc.get(NAME, UNNAMED)
    except Exception:
        name = UNNAMED
    if not isinstance(e, FieldSerializeError):
        e = FieldSerializeError()
        e_str0 = SERIALIZE_ERROR_HEAD
        e.seen = set()

    # get a copy of all but the last of the arguments
    a = e.args[:-1]
    try:
        e_str0 = str(e.args[-1])
        e_str0, e_str1 = (e_str0[:len(SERIALIZE_ERROR_HEAD)],
                          e_str0[len(SERIALIZE_ERROR_HEAD):])
    except IndexError:
        pass

    # make sure this node hasnt already been seen
    seen_id = (id(parent), id(field_type), attr_index)
    if seen_id in e.seen:
        return e
    else:
        e.seen.add(seen_id)

    # remake the args with the new data
    e.args = a + (
        e_str0 + "\n    %s, index:%s, offset:%s, field_type:%s" %
        (name, attr_index, offset + root_offset, field_type) + e_str1,)

    # add the extra data pertaining to this hierarchy level to e.error_data
    e.error_data.insert(0, kwargs)
    return e


# ################################################
'''############  Parser functions  ############'''
# ################################################


def default_parser(self, desc, node=None, parent=None, attr_index=None,
                   rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    A parser meant specifically for setting the default value
    of a field whose parser is not called by its parents parser.

    This parser is currently for fields used inside bitstructs since
    their parser is not called by their parent bitstructs parser.

    When "rawdata" is not provided to a bitstructs parser, the parser will
    call its Blocks parse method to initialize its attributes, which in
    turn calls the parser of each attribute, which should be this function.
    """
    if parent is not None and attr_index is not None:
        if not self.is_block:
            # non-Block node
            parent[attr_index] = desc.get(DEFAULT, self.default())
        elif isinstance(None, self.data_cls):
            # Block node_cls without a 'data_cls'
            parent[attr_index] = desc.get(NODE_CLS, self.node_cls)(desc)
        else:
            # Block node_cls with a 'data_cls'
            # the node is likely either an EnumBlock or BoolBlock
            parent[attr_index] = self.node_cls(desc, init_attrs=True)

    return offset


def computed_parser(self, desc, node=None, parent=None, attr_index=None,
                    rawdata=None, root_offset=0, offset=0, **kwargs):
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a computed field.")
    if desc.get(COMPUTE_READ):
        new_offset = desc[COMPUTE_READ](
            desc=desc, node=node, parent=parent, attr_index=attr_index,
            rawdata=rawdata, root_offset=root_offset, offset=offset, **kwargs)
        if new_offset is not None:
            return new_offset

    return offset


def container_parser(self, desc, node=None, parent=None, attr_index=None,
                     rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                                 (desc, parent=parent)

        is_steptree_root = (desc.get('STEPTREE_ROOT') or
                           'steptree_parents' not in kwargs)
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if 'STEPTREE' in desc:
            kwargs['steptree_parents'].append(node)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # loop once for each field in the node
        for i in range(len(node)):
            offset = desc[i]['TYPE'].parser(desc[i], None, node, i, rawdata,
                                            root_offset, offset, **kwargs)

        if is_steptree_root:
            # build the steptrees for all the nodes within this one
            del kwargs['steptree_parents']
            for p_node in parents:
                s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].parser(s_desc, None, p_node,
                                               'STEPTREE', rawdata,
                                               root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            e = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def array_parser(self, desc, node=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent)

        is_steptree_root = (desc.get('STEPTREE_ROOT') or
                           'steptree_parents' not in kwargs)
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if 'STEPTREE' in desc:
            kwargs['steptree_parents'].append(node)
        a_desc = desc['SUB_STRUCT']
        a_parser = a_desc['TYPE'].parser

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # loop once for each field in the node
        for i in range(node.get_size(**kwargs)):
            offset = a_parser(a_desc, None, node, i, rawdata,
                              root_offset, offset, **kwargs)

        if is_steptree_root:
            # build the children for all the field within this node
            del kwargs['steptree_parents']
            for p_node in parents:
                s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].parser(s_desc, None, p_node,
                                               'STEPTREE', rawdata,
                                               root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            e = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_parse_error(e, field_type=a_desc['TYPE'], desc=a_desc,
                                   parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def while_array_parser(self, desc, node=None, parent=None, attr_index=None,
                       rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent)

        is_steptree_root = (desc.get('STEPTREE_ROOT') or
                           'steptree_parents' not in kwargs)
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if 'STEPTREE' in desc:
            kwargs['steptree_parents'].append(node)
        a_desc = desc['SUB_STRUCT']
        a_parser = a_desc['TYPE'].parser

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        i = 0
        decider = desc.get('CASE')
        if decider is not None:
            temp_kwargs = dict(kwargs)
            temp_kwargs.update(parent=node, rawdata=rawdata, attr_index=i,
                               root_offset=root_offset, offset=offset)
            while decider(**temp_kwargs):
                # make a new slot in the new array for the new array element
                node.append(None)
                offset = a_parser(a_desc, **temp_kwargs)
                i += 1
                temp_kwargs.update(attr_index=i, offset=offset)

        if is_steptree_root:
            del kwargs['steptree_parents']
            for p_node in parents:
                s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].parser(s_desc, None, p_node,
                                               'STEPTREE', rawdata,
                                               root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            e = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_parse_error(e, field_type=a_desc['TYPE'], desc=a_desc,
                                   parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def switch_parser(self, desc, node=None, parent=None, attr_index=None,
                  rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        # A case may be provided through kwargs.
        # This is to allow overriding behavior of the switch and
        # to allow creating a node specified by the user
        case = case_i = desc['CASE']
        case_map = desc['CASE_MAP']

        if 'case' in kwargs:
            case_i = kwargs['case']
            del kwargs['case']
            if isinstance(case_i, (list, tuple)):
                # this way we can provide nested switch cases
                if len(case_i) > 1:
                    kwargs['case'] = case_i[1:]
                case_i = case_i.pop(0)
        else:
            if isinstance(attr_index, int):
                node = parent[attr_index]
            elif isinstance(attr_index, str):
                node = parent.__getattr__(attr_index)
            else:
                node = parent

            try:
                parent = node.parent
            except AttributeError:
                pass

            if isinstance(case, str):
                # get the pointed to meta data by traversing the tag
                # structure along the path specified by the string'
                case_i = parent.get_neighbor(case, node)
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
                              rawdata=rawdata, node=node,
                              offset=offset, **kwargs)

        # get the descriptor to use to build the node
        # based on what the CASE meta data says
        desc = desc.get(case_map.get(case_i, DEFAULT))

        return desc['TYPE'].parser(desc, None, parent, attr_index,
                                   rawdata, root_offset, offset, **kwargs)
    except Exception as e:
        try:
            index = case_i
        except NameError:
            index = None
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, buffer=rawdata,
                               attr_index=index, root_offset=root_offset,
                               offset=offset, **kwargs)
        raise e


def struct_parser(self, desc, node=None, parent=None, attr_index=None,
                  rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent, init_attrs=rawdata is None)

        is_steptree_root = 'steptree_parents' not in kwargs
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if 'STEPTREE' in desc:
            kwargs['steptree_parents'].append(node)

        # If there is rawdata to build the structure from
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the node from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this node is being built
            # without a parent(such as from an exported block) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = node.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            offsets = desc['ATTR_OFFS']
            # loop once for each field in the node
            for i in range(len(node)):
                desc[i]['TYPE'].parser(desc[i], None, node, i, rawdata,
                                       root_offset, offset + offsets[i],
                                       **kwargs)

            # increment offset by the size of the struct
            offset += desc['SIZE']

        if is_steptree_root:
            del kwargs['steptree_parents']
            for p_node in parents:
                s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].parser(s_desc, None, p_node,
                                               'STEPTREE', rawdata,
                                               root_offset, offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            e = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def quickstruct_parser(self, desc, node=None, parent=None, attr_index=None,
                       rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        __lsi__ = list.__setitem__
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent)

        # If there is rawdata to build the structure from
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the node from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this node is being built
            # without a parent(such as from an exported block) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = node.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            offsets = desc['ATTR_OFFS']
            struct_off = root_offset + offset

            if self.f_endian == '=':
                # loop once for each field in the node
                for i in range(len(node)):
                    off = struct_off + offsets[i]
                    typ = desc[i]['TYPE']
                    __lsi__(node, i,
                            unpack(typ.enc, rawdata[off:off + typ.size])[0])
            elif self.f_endian == '<':
                # loop once for each field in the node
                for i in range(len(node)):
                    off = struct_off + offsets[i]
                    typ = desc[i]['TYPE']
                    __lsi__(node, i, unpack(typ.little.enc,
                                            rawdata[off:off + typ.size])[0])
            else:
                # loop once for each field in the node
                for i in range(len(node)):
                    off = struct_off + offsets[i]
                    typ = desc[i]['TYPE']
                    __lsi__(node, i, unpack(typ.big.enc,
                                            rawdata[off:off + typ.size])[0])

            # increment offset by the size of the struct
            offset += desc['SIZE']
        else:
            for i in range(len(node)):
                __lsi__(node, i,
                        desc[i].get(DEFAULT, desc[i]['TYPE'].default()))

        s_desc = desc.get('STEPTREE')
        if s_desc:
            if 'steptree_parents' not in kwargs:
                offset = s_desc['TYPE'].parser(s_desc, None, node, 'STEPTREE',
                                               rawdata, root_offset, offset,
                                               **kwargs)
            else:
                kwargs['steptree_parents'].append(node)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            e = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                  parent=node, attr_index=STEPTREE,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            e = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def stream_adapter_parser(self, desc, node=None, parent=None, attr_index=None,
                          rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        orig_root_offset = root_offset
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = (
                desc.get(NODE_CLS, self.node_cls)(desc, parent=parent))

        sub_desc = desc['SUB_STRUCT']

        # If there is rawdata to build from
        if rawdata is not None:
            align = desc.get('ALIGN')

            # If there is a specific pointer to read the node from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this node is being built
            # without a parent(such as from an exported block) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and desc.get('POINTER') is not None:
                offset = node.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            # use the decoder method to get a decoded stream and
            # the length of the stream before it was decoded
            adapted_stream, length_read = desc['DECODER'](
                node, rawdata, root_offset, offset, **kwargs)
        else:
            adapted_stream = None
            length_read = 0

        sub_desc['TYPE'].parser(sub_desc, None, node, 'SUB_STRUCT',
                                adapted_stream, 0, 0, **kwargs)

        # pass the incremented offset to the caller
        return offset + length_read
    except Exception as e:
        adapted_stream = locals().get('adapted_stream', rawdata)
        kwargs.update(field_type=self, desc=desc, parent=parent,
                      buffer=adapted_stream, attr_index=attr_index,
                      root_offset=orig_root_offset, offset=orig_offset)
        e = format_parse_error(e, **kwargs)
        raise e


def union_parser(self, desc, node=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    try:
        orig_offset = offset
        if node is None:
            parent[attr_index] = node = (
                desc.get(NODE_CLS, self.node_cls)(desc, parent=parent))

        size = desc['SIZE']

        if rawdata is not None:
            # A case may be provided through kwargs.
            # This is to allow overriding behavior of the union and
            # to allow creating a node specified by the user
            case_i = case = desc.get('CASE')
            case_map = desc['CASE_MAP']
            align = desc.get('ALIGN')

            if attr_index is not None and desc.get('POINTER') is not None:
                offset = node.get_meta('POINTER', **kwargs)
            elif align:
                offset += (align - (offset % align)) % align

            # read and store the rawdata to the new node
            rawdata.seek(root_offset + offset)
            node[:] = rawdata.read(size)

            if 'case' in kwargs:
                case_i = kwargs['case']
            elif isinstance(case, str):
                # get the pointed to meta data by traversing the tag
                # structure along the path specified by the string
                case_i = parent.get_neighbor(case, node)
            elif hasattr(case, "__call__"):
                try:
                    # try to reposition the rawdata if it needs to be peeked
                    rawdata.seek(root_offset + offset)
                except AttributeError:
                    pass
                case_i = case(parent=parent, node=node,
                              attr_index=attr_index, rawdata=rawdata,
                              root_offset=root_offset, offset=offset, **kwargs)
            offset += size
            case_i = case_map.get(case_i)

            if case_i is not None:
                try:
                    node.set_active(case_i)
                except AttributeError:
                    # this case doesnt exist, but this can be intentional, so
                    # allow this error to pass. Maybe change this later on.
                    pass
        else:
            # if no rawdata is provided, set the union data to its default
            node[:] = desc.get(DEFAULT, b'\x00'*size)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'case_i' in locals() and case_i in desc:
            e = format_parse_error(
                e, field_type=desc[case_i].get(TYPE), desc=desc[case_i],
                parent=node, attr_index=i, offset=offset, **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        raise e


def f_s_data_parser(self, desc, node=None, parent=None, attr_index=None,
                    rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    f_s means fixed_size.
    """
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a data field.")
    if rawdata:
        # read and store the node
        rawdata.seek(root_offset + offset)
        parent[attr_index] = self.decoder(rawdata.read(self.size), desc=desc,
                                          parent=parent, attr_index=attr_index)
        return offset + self.size
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf', 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = desc.get(NODE_CLS, self.node_cls)\
            (desc, initdata=desc.get(DEFAULT), init_attrs=True)
    else:
        # this is not a Block
        parent[attr_index] = desc.get(DEFAULT, self.default())

    return offset


def data_parser(self, desc, node=None, parent=None, attr_index=None,
                rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a data field.")
    if rawdata:
        # read and store the node
        rawdata.seek(root_offset + offset)
        size = parent.get_size(attr_index, root_offset=root_offset,
                               offset=offset, rawdata=rawdata, **kwargs)
        parent[attr_index] = self.decoder(rawdata.read(size), desc=desc,
                                          parent=parent, attr_index=attr_index)
        return offset + size
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf', 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = desc.get(NODE_CLS, self.node_cls)(
            desc, initdata=desc.get(DEFAULT), init_attrs=True)
    else:
        # this is not a Block
        parent[attr_index] = desc.get(DEFAULT, self.default())

    return offset


def cstring_parser(self, desc, node=None, parent=None, attr_index=None,
                   rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a data field.")

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
        # read and store the node
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
        parent[attr_index] = desc.get(NODE_CLS, self.node_cls)(
            desc, initdata=desc.get(DEFAULT), init_attrs=True)
    return offset


def py_array_parser(self, desc, node=None, parent=None, attr_index=None,
                    rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a data field.")

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

        # if the system the array is being created on
        # has a different endianness than what the array is
        # packed as, swap the endianness after reading it.
        if self.endian != byteorder_char and self.endian != '=':
            parent[attr_index] = py_array = self.node_cls(
                self.enc, rawdata.read(bytecount))
            py_array.byteswap()
            return offset

        parent[attr_index] = self.node_cls(self.enc, rawdata.read(bytecount))

        # pass the incremented offset to the caller
        return offset
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = desc.get(NODE_CLS, self.node_cls)(
            desc, initdata=desc.get(DEFAULT), init_attrs=True)
    elif DEFAULT in desc:
        parent[attr_index] = self.node_cls(self.enc, desc[DEFAULT])
    else:
        bytecount = parent.get_size(attr_index, offset=offset,
                                    root_offset=root_offset,
                                    rawdata=rawdata, **kwargs)
        parent[attr_index] = self.node_cls(self.enc, b'\x00'*bytecount)
    return offset


def bytes_parser(self, desc, node=None, parent=None, attr_index=None,
                 rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    assert parent is not None and attr_index is not None, (
        "parent and attr_index must be provided " +
        "and not None when reading a data field.")
    if rawdata is not None:
        orig_offset = offset
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)

        bytecount = parent.get_size(attr_index, offset=offset,
                                    rawdata=rawdata, **kwargs)
        rawdata.seek(root_offset + offset)
        offset += bytecount

        parent[attr_index] = self.node_cls(rawdata.read(bytecount))

        # pass the incremented offset to the caller
        return offset
    elif self.is_block:
        # this is a 'data' Block, so it needs a descriptor and the
        # DEFAULT is expected to be some kind of literal data(like
        # 'asdf' or 42, or 5234.4) rather than a subclass of Block
        parent[attr_index] = desc.get(NODE_CLS, self.node_cls)(
            desc, initdata=desc.get(DEFAULT), init_attrs=True)
    elif DEFAULT in desc:
        parent[attr_index] = self.node_cls(desc[DEFAULT])
    else:
        parent[attr_index] = self.node_cls(
            b'\x00'*(parent.get_size(attr_index, offset=offset,
                                     rawdata=rawdata, **kwargs)))
    return offset


def bit_struct_parser(self, desc, node=None, parent=None, attr_index=None,
                      rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent, init_attrs=rawdata is None)

        """If there is file data to build the structure from"""
        if rawdata is not None:
            rawdata.seek(root_offset + offset)
            structsize = desc['SIZE']
            if self.endian == '<':
                rawint = int.from_bytes(rawdata.read(structsize), 'little')
            else:
                rawint = int.from_bytes(rawdata.read(structsize), 'big')

            # loop once for each field in the node
            for i in range(len(node)):
                node[i] = desc[i]['TYPE'].decoder(
                    rawint, desc=desc[i], parent=node, attr_index=i)

            # increment offset by the size of the struct
            offset += structsize

        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'i' in locals():
            e = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=desc['ATTR_OFFS'][i], **kwargs)
        e = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=offset, **kwargs)
        raise e


# ####################################################
'''############  Serializer functions  ############'''
# ####################################################


def computed_serializer(self, node, parent=None, attr_index=None,
                        writebuffer=None, root_offset=0, offset=0, **kwargs):
    p_desc = parent.desc
    if p_desc['TYPE'].is_array:
        desc = p_desc['SUB_STRUCT']
    else:
        desc = p_desc[attr_index]

    if desc.get(COMPUTE_WRITE):
        new_offset = desc[COMPUTE_WRITE](
            desc=desc, node=node, parent=parent, attr_index=attr_index,
            writebuffer=writebuffer, root_offset=root_offset, offset=offset, **kwargs)
        if new_offset is not None:
            return new_offset

    return offset


def container_serializer(self, node, parent=None, attr_index=None,
                         writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        desc = node.desc

        is_steptree_root = (desc.get('STEPTREE_ROOT') or
                           'steptree_parents' not in kwargs)
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if hasattr(node, 'STEPTREE'):
            kwargs['steptree_parents'].append(node)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # loop once for each node in the node
        for i in range(len(node)):
            # Trust that each of the nodes in the container is a Block
            attr = node[i]
            try:
                a_desc = attr.desc
            except AttributeError:
                a_desc = desc[i]
            offset = a_desc['TYPE'].serializer(attr, node, i, writebuffer,
                                               root_offset, offset, **kwargs)

        if is_steptree_root:
            del kwargs['steptree_parents']

            for p_node in parents:
                attr = p_node.STEPTREE
                try:
                    s_desc = attr.desc
                except AttributeError:
                    s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].serializer(attr, p_node, 'STEPTREE',
                                                   writebuffer, root_offset,
                                                   offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            e = format_serialize_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            e = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_serialize_error(e, **kwargs)
        raise e


def array_serializer(self, node, parent=None, attr_index=None,
                     writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        desc = node.desc
        a_desc = desc['SUB_STRUCT']
        a_serializer = a_desc['TYPE'].serializer

        is_steptree_root = (desc.get('STEPTREE_ROOT') or
                           'steptree_parents' not in kwargs)
        if is_steptree_root:
            kwargs['steptree_parents'] = parents = []
        if hasattr(node, 'STEPTREE'):
            kwargs['steptree_parents'].append(node)

        align = desc.get('ALIGN')
        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # loop once for each node in the node
        for i in range(len(node)):
            # Trust that each of the nodes in the container is a Block
            attr = node[i]
            try:
                serializer = attr.desc['TYPE'].serializer
            except AttributeError:
                serializer = a_serializer
            offset = serializer(attr, node, i, writebuffer,
                                root_offset, offset, **kwargs)

        del kwargs['steptree_parents']

        if is_steptree_root:
            for p_node in parents:
                attr = p_node.STEPTREE
                try:
                    s_desc = attr.desc
                except AttributeError:
                    s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].serializer(attr, p_node, 'STEPTREE',
                                                   writebuffer, root_offset,
                                                   offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            e = format_serialize_error(e, **kwargs)
        elif 'i' in locals():
            try:
                a_desc = node[i].desc
            except (TypeError, AttributeError):
                a_desc = desc['SUB_STRUCT']
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            e = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_serialize_error(e, **kwargs)
        raise e


def struct_serializer(self, node, parent=None, attr_index=None,
                      writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        orig_offset = offset
        desc = node.desc
        offsets = desc['ATTR_OFFS']
        structsize = desc['SIZE']
        is_tree_root = 'steptree_parents' not in kwargs

        if is_tree_root:
            kwargs['steptree_parents'] = parents = []
        if hasattr(node, 'STEPTREE'):
            kwargs['steptree_parents'].append(node)

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the whole size of the node so
        # any padding is filled in properly
        writebuffer.seek(root_offset + offset)
        writebuffer.write(bytes(structsize))

        # loop once for each node in the node
        for i in range(len(node)):
            # structs usually dont contain Blocks, so check
            attr = node[i]
            if hasattr(attr, 'desc'):
                a_desc = attr.desc
            else:
                a_desc = desc[i]
            a_desc['TYPE'].serializer(attr, node, i, writebuffer, root_offset,
                                      offset + offsets[i], **kwargs)

        # increment offset by the size of the struct
        offset += structsize

        if is_tree_root:
            del kwargs['steptree_parents']

            for p_node in parents:
                attr = p_node.STEPTREE
                try:
                    s_desc = attr.desc
                except AttributeError:
                    s_desc = p_node.desc['STEPTREE']
                offset = s_desc['TYPE'].serializer(attr, p_node, 'STEPTREE',
                                                   writebuffer, root_offset,
                                                   offset, **kwargs)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            e = format_serialize_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            e = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_serialize_error(e, **kwargs)
        raise e


def quickstruct_serializer(self, node, parent=None, attr_index=None,
                           writebuffer=None, root_offset=0, offset=0,
                           **kwargs):
    """
    """
    try:
        __lgi__ = list.__getitem__
        orig_offset = offset
        desc = node.desc
        offsets = desc['ATTR_OFFS']
        structsize = desc['SIZE']

        align = desc.get('ALIGN')

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the whole size of the node so
        # any padding is filled in properly
        writebuffer.seek(root_offset + offset)
        writebuffer.write(bytes(structsize))

        struct_off = root_offset + offset

        # loop once for each node in the node
        if self.f_endian == '=':
            for i in range(len(node)):
                writebuffer.seek(struct_off + offsets[i])
                writebuffer.write(pack(desc[i]['TYPE'].enc, __lgi__(node, i)))
        elif self.f_endian == '<':
            for i in range(len(node)):
                writebuffer.seek(struct_off + offsets[i])
                writebuffer.write(
                    pack(desc[i]['TYPE'].little.enc, __lgi__(node, i)))
        else:
            for i in range(len(node)):
                writebuffer.seek(struct_off + offsets[i])
                writebuffer.write(
                    pack(desc[i]['TYPE'].big.enc, __lgi__(node, i)))

        # increment offset by the size of the struct
        offset += structsize

        if hasattr(node, 'STEPTREE'):
            if 'steptree_parents' not in kwargs:
                attr = node.STEPTREE
                try:
                    s_desc = attr.desc
                except AttributeError:
                    s_desc = node.desc['STEPTREE']
                offset = s_desc['TYPE'].serializer(attr, node, 'STEPTREE',
                                                   writebuffer, root_offset,
                                                   offset, **kwargs)
            else:
                kwargs['steptree_parents'].append(node)

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=node, attr_index=STEPTREE, offset=offset)
            e = format_serialize_error(e, **kwargs)
        elif 'i' in locals():
            kwargs.update(field_type=desc[i].get(TYPE), desc=desc[i],
                          parent=node, attr_index=i, offset=offset)
            e = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_serialize_error(e, **kwargs)
        raise e


def stream_adapter_serializer(self, node, parent=None, attr_index=None,
                              writebuffer=None, root_offset=0, offset=0,
                              **kwargs):
    '''
    '''
    try:
        # make a new buffer to write the data to
        temp_buffer = BytearrayBuffer()
        orig_offset = offset
        desc = node.desc
        align = desc.get('ALIGN')

        try:
            sub_desc = node.data.desc
        except AttributeError:
            sub_desc = desc['SUB_STRUCT']

        # If there is a specific pointer to read the node from then go to it.
        # Only do this, however, if the POINTER can be expected to be accurate.
        # If the pointer is a path to a previously parsed field, but this node
        # is being built without a parent(such as from an exported block)
        # then the path wont be valid. The current offset will be used instead.
        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # write the sub_struct to the temp buffer
        sub_desc['TYPE'].serializer(node.data, node, 'SUB_STRUCT',
                                temp_buffer, 0, 0, **kwargs)

        # use the decoder method to get a decoded stream and
        # the length of the stream before it was decoded
        adapted_stream = desc['ENCODER'](node, temp_buffer, **kwargs)

        # write the adapted stream to the writebuffer
        writebuffer.seek(root_offset + offset)
        writebuffer.write(adapted_stream)

        # pass the incremented offset to the caller
        return offset + len(adapted_stream)
    except Exception as e:
        desc = locals().get('desc', None)
        e = format_serialize_error(
            e, field_type=self, desc=desc, parent=parent, buffer=temp_buffer,
            attr_index=attr_index, root_offset=root_offset, offset=offset,
            **kwargs)
        raise e


def union_serializer(self, node, parent=None, attr_index=None,
                     writebuffer=None, root_offset=0, offset=0, **kwargs):
    '''
    '''
    try:
        orig_offset = offset
        desc = node.desc
        align = desc.get('ALIGN')

        if attr_index is not None and desc.get('POINTER') is not None:
            offset = node.get_meta('POINTER', **kwargs)
        elif align:
            offset += (align - (offset % align)) % align

        # if the u_node is not flushed to the UnionBlock, do it
        # before writing the UnionBlock to the writebuffer
        if node.u_index is not None:
            node.flush()

        # write the UnionBlock to the writebuffer
        writebuffer.seek(root_offset + offset)
        writebuffer.write(node)

        # increment offset by the size of the UnionBlock
        offset += desc['SIZE']

        # pass the incremented offset to the caller
        return offset
    except Exception as e:
        desc = locals().get('desc', None)
        e = format_serialize_error(
            e, field_type=self, desc=desc, parent=parent, buffer=temp_buffer,
            attr_index=attr_index, root_offset=root_offset, offset=offset,
            **kwargs)
        raise e


def f_s_data_serializer(self, node, parent=None, attr_index=None,
                        writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    node_bytes = self.encoder(node, parent, attr_index)
    writebuffer.seek(root_offset + offset)
    writebuffer.write(node_bytes)
    return offset + len(node_bytes)


def data_serializer(self, node, parent=None, attr_index=None,
                    writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    node_bytes = self.encoder(node, parent, attr_index)
    writebuffer.seek(root_offset + offset)
    writebuffer.write(node_bytes)
    size = parent.get_size(attr_index, root_offset=root_offset,
                           offset=offset, **kwargs)
    if size - len(node_bytes):
        writebuffer.write(b'\x00'*(size - len(node_bytes)))
    return offset + size


def cstring_serializer(self, node, parent=None, attr_index=None,
                       writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
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

    node = self.encoder(node, parent, attr_index)
    writebuffer.seek(root_offset + offset)
    writebuffer.write(node)

    # pass the incremented offset to the caller
    return offset + len(node)


def py_array_serializer(self, node, parent=None, attr_index=None,
                        writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
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

    # This is the only method I can think of to tell if
    # the endianness of an array needs to be changed since
    # the array.array objects dont know their own endianness'''
    if self.endian != byteorder_char and self.endian != '=':
        # if the system the array exists on has a different
        # endianness than what the array should be written as,
        # then the endianness is swapped before writing it.
        node.byteswap()
        writebuffer.write(node)
        node.byteswap()
    else:
        writebuffer.write(node)

    size = parent.get_size(attr_index, root_offset=root_offset,
                           offset=offset, **kwargs)
    node_size = len(node)*node.itemsize
    if size - node_size:
        writebuffer.write(b'\x00'*(size - node_size))
    return offset + size


def bytes_serializer(self, node, parent=None, attr_index=None,
                     writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    orig_offset = offset

    if parent and attr_index is not None:
        p_desc = parent.desc
        if p_desc['TYPE'].is_array:
            desc = p_desc['SUB_STRUCT']
        else:
            desc = p_desc[attr_index]

        if desc.get('POINTER') is not None:
            offset = parent.get_meta('POINTER', attr_index, **kwargs)

    writebuffer.seek(root_offset + offset)
    writebuffer.write(node)
    size = parent.get_size(attr_index, root_offset=root_offset,
                           offset=offset, **kwargs)
    if size - len(node):
        writebuffer.write(b'\x00'*(size - len(node)))
    return offset + size


def bit_struct_serializer(self, node, parent=None, attr_index=None,
                          writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        data = 0
        desc = node.desc
        structsize = desc['SIZE']

        # get a list of everything as unsigned
        # ints with their masks and offsets
        for i in range(len(node)):
            try:
                bitint = node[i].desc[TYPE].encoder(node[i], node, i)
            except AttributeError:
                bitint = desc[i][TYPE].encoder(node[i], node, i)

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
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            e = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        e = format_serialize_error(e, **kwargs)
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


def decode_decimal(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Converts a bytes object into a python Decimal.

    Returns a Decimal represention of the "rawdata" argument.
    '''
    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'
    d_exp = parent.get_meta('DECIMAL_EXP', attr_index)
    bigint = str(int.from_bytes(
        rawdata, endian, signed=self.enc.endswith('S')))

    return Decimal(bigint[:len(bigint)-d_exp] + '.' +
                   bigint[len(bigint)-d_exp:])


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
    if rawint & 0x800000 and self.enc[1] == 't':
        return rawint - 0x1000000  # 0x1000000 == 0x800000 * 2
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
    node = hex(int.from_bytes(rawdata, 'big'))[2:]
    return '0'*(len(rawdata)*2 - len(node)) + node


def decode_big_int(self, rawdata, desc=None, parent=None, attr_index=None):
    '''
    Decodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Decoding is done using int.from_bytes

    Returns an int represention of the "rawdata" argument.
    '''
    # If an empty bytes object was provided, return a zero.
    if not len(rawdata):
        return 0

    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'

    if self.enc[-1] == 's':
        # ones compliment
        bigint = int.from_bytes(rawdata, endian, signed=True)
        if bigint < 0:
            return bigint + 1
        return bigint
    elif self.enc[-1] == 'S':
        # twos compliment
        return int.from_bytes(rawdata, endian, signed=True)

    return int.from_bytes(rawdata, endian)


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

    # If the bit count is zero, return a zero
    if not bitcount:
        return 0

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


# #################################################
'''############  Encoder functions  ############'''
# #################################################


def encode_numeric(self, node, parent=None, attr_index=None):
    '''
    Encodes a python int into a bytes representation.
    Encoding is done using struct.pack

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return pack(self.enc, node)


def encode_decimal(self, node, parent=None, attr_index=None):
    '''
    Encodes a python Decimal into a bytes representation.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    raise NotImplementedError('Encoding Decimal objects is not supported yet.')


def encode_24bit_numeric(self, node, parent=None, attr_index=None):
    '''
    Encodes a python int to a signed or unsigned 24-bit bytes representation.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    if self.enc[1] == 't':
        # int can be signed
        assert node >= -0x800000 and node <= 0x7fffff, (
            '%s is too large to pack as a 24bit signed int.' % node)
        if node < 0:
            # int IS signed
            node += 0x1000000
    else:
        assert node >= 0 and node <= 0xffffff, (
            '%s is too large to pack as a 24bit unsigned int.' % node)

    # pack and return the int
    if self.endian == '<':
        return pack('<I', node)[0:3]
    return pack('>I', node)[1:4]


def encode_int_timestamp(self, node, parent=None, attr_index=None):
    '''
    '''
    return pack(self.enc, int(mktime(strptime(node))))


def encode_float_timestamp(self, node, parent=None, attr_index=None):
    '''
    '''
    return pack(self.enc, float(mktime(strptime(node))))


def encode_string(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation,
    making sure there is a delimiter character on the end.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "node" argument.
    '''
    if not node.endswith(self.str_delimiter):
        return (node + self.str_delimiter).encode(self.enc)
    return node.encode(self.enc)


def encode_raw_string(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string into a bytes representation.
    Encoding is done using str.encode

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return node.encode(self.enc)


def encode_string_hex(self, node, parent=None, attr_index=None):
    '''
    Encodes a python string formatted as a hex string into a bytes object.

    Returns a bytes object encoded represention of the "node" argument.
    '''
    return int(node, 16).to_bytes((len(node) + 1)//2, 'big')


def encode_big_int(self, node, parent=None, attr_index=None):
    '''
    Encodes arbitrarily sized signed or unsigned integers
    on the byte level in either ones or twos compliment.
    Encoding is done using int.to_bytes

    Returns a bytes object encoded represention of the "node" argument.
    '''
    bytecount = parent.get_size(attr_index)

    if not bytecount:
        return b''

    if self.endian == '<':
        endian = 'little'
    else:
        endian = 'big'

    if self.enc[-1] == 'S':
        # twos compliment
        return node.to_bytes(bytecount, endian, signed=True)
    elif self.enc[-1] == 's':
        # ones compliment
        if node < 0:
            return (node-1).to_bytes(bytecount, endian, signed=True)
        return node.to_bytes(bytecount, endian, signed=False)

    return node.to_bytes(bytecount, endian)


def encode_bit(self, node, parent=None, attr_index=None):
    '''
    Encodes an int to a single bit.
    Returns the encoded int, the offset it should be
    shifted to, and a mask that covers its range.
    '''
    # return the int with the bit offset and a mask of 1
    return(node, parent.ATTR_OFFS[attr_index], 1)


def encode_bit_int(self, node, parent=None, attr_index=None):
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
    if node < 0:
        signmask = 1 << (bitcount - 1)
        if self.enc == 'S':
            # twos signed
            return(2*signmask + node, offset, mask)
        # ones signed
        return(2*signmask + (node-1), offset, mask)
    return(node, offset, mask)


# ##########################################################
'''#########  Void and Pad FieldType functions  #########'''
# ##########################################################


# These next methods are exclusively used for the Void FieldType.
def void_parser(self, desc, node=None, parent=None, attr_index=None,
                rawdata=None, root_offset=0, offset=0, **kwargs):
    if node is None:
        parent[attr_index] = (desc.get(NODE_CLS, self.node_cls)
                              (desc, parent=parent))
    return offset


def void_serializer(self, node, parent=None, attr_index=None,
                    writebuffer=None, root_offset=0, offset=0, **kwargs):
    return offset


def pad_parser(self, desc, node=None, parent=None, attr_index=None,
               rawdata=None, root_offset=0, offset=0, **kwargs):
    ''''''
    if node is None:
        parent[attr_index] = node = (desc.get(NODE_CLS, self.node_cls)
                                     (desc, parent=parent))
        return offset + node.get_size(offset=offset, root_offset=root_offset,
                                       rawdata=rawdata, **kwargs)
    return offset


def pad_serializer(self, node, parent=None, attr_index=None,
                   writebuffer=None, root_offset=0, offset=0, **kwargs):
    ''''''
    pad_size = node.get_size(offset=offset, root_offset=root_offset, **kwargs)
    writebuffer.seek(offset + root_offset)
    writebuffer.write(b'\x00'*pad_size)
    if parent is not None:
        return offset + pad_size
    return offset


def no_decode(self, rawdata, desc=None, parent=None, attr_index=None):
    ''''''
    return rawdata


def no_encode(self, node, parent=None, attr_index=None):
    ''''''
    return node


# ##################################################
'''############  Sizecalc functions  ############'''
# ##################################################


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


# ###################################################
'''############  Sanitizer functions  ############'''
# ###################################################


def bool_sanitizer(blockdef, src_dict, **kwargs):
    kwargs['is_bool'] = True
    return bool_enum_sanitize_main(blockdef, src_dict, **kwargs)


def enum_sanitizer(blockdef, src_dict, **kwargs):
    kwargs['is_bool'] = False
    return bool_enum_sanitize_main(blockdef, src_dict, **kwargs)


def bool_enum_sanitize_main(blockdef, src_dict, **kwargs):
    '''
    '''
    p_f_type = src_dict[TYPE]
    is_bool = kwargs.pop('is_bool', False)

    nameset = set()
    src_dict[NAME_MAP] = dict(src_dict.get(NAME_MAP, ()))
    src_dict[VALUE_MAP] = {}

    # Need to make sure there is a value for each element
    blockdef.set_entry_count(src_dict)
    blockdef.find_entry_gaps(src_dict)
    sanitize_option_values(blockdef, src_dict, p_f_type,
                           is_bool=is_bool, **kwargs)

    if not isinstance(src_dict.get(SIZE, 0), int):
        blockdef._e_str += (
            ("ERROR: INVALID TYPE FOR SIZE IN '%s'.\n    EXPECTED %s, GOT %s" +
             ".\n") % (src_dict.get(NAME, UNNAMED), int, type(src_dict[SIZE])))
        blockdef._bad = True

    for i in range(src_dict[ENTRIES]):
        name = blockdef.sanitize_name(
            src_dict, i, allow_reserved=not is_bool,
            p_f_type=p_f_type, p_name=src_dict.get(NAME),
            reserved_names=reserved_bool_enum_names, key_name=i)

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


def sanitize_option_values(blockdef, src_dict, f_type, **kwargs):
    '''
    '''
    is_bool = kwargs.get('is_bool')
    p_name = kwargs.get('p_name', UNNAMED)
    p_f_type = kwargs.get('p_f_type', None)
    pad_size = removed = 0
    def_val = 0

    for i in range(src_dict.get(ENTRIES, 0)):
        opt = src_dict[i]

        if isinstance(opt, dict):
            if opt.get(TYPE) is field_types.Pad:
                # subtract 1 from the pad size because the pad itself is 1
                pad_size += opt.get(SIZE, 1) - 1
                removed += 1
                del src_dict[i]
                def_val += 1
                continue

            # make a copy to make sure the original is intact
            opt = dict(opt)
        elif isinstance(opt, str):
            opt = {NAME: opt}
        elif isinstance(opt, (list, tuple)):
            if len(opt) == 1:
                opt = {NAME: opt[0]}
            elif len(opt) == 2:
                opt = {NAME: opt[0], VALUE: opt[1]}
            else:
                blockdef._e_str += (
                    "ERROR: EXPECTED TUPLE OR LIST OF LENGTH 1 or 2 " +
                    "FOR\nOPTION NUMBER %s IN FIELD %s OF NAME '%s', " +
                    "GOT LENGTH OF %s.\n") % (i, p_f_type, p_name, len(opt))
                blockdef._bad = True
                continue
        else:
            continue

        # remove any keys that aren't descriptor keywords
        for key in tuple(opt.keys()):
            if not(isinstance(key, int) or key in desc_keywords):
                opt.pop(key)

        if removed:
            del src_dict[i]

        if VALUE in opt:
            if isinstance(opt[VALUE], int):
                if is_bool:
                    if opt[VALUE] <= 0:
                        blockdef._e_str += (
                            "ERROR: VALUE OF BOOLEAN WAS <= 0 FOR OPTION NUMBER" +
                            "%s IN FIELD %s OF NAME '%s'") % (i, p_f_type, p_name)
                        blockdef._bad = True
                        continue
                    def_val = int(log(opt[VALUE], 2))
                else:
                    def_val = opt[VALUE]
                pad_size = 0
        elif is_bool:
            opt[VALUE] = 2**(def_val + pad_size)
        else:
            opt[VALUE] = def_val + pad_size

        if p_f_type:
            opt[VALUE] = blockdef.decode_value(
                opt[VALUE], key=i, p_name=p_name, p_f_type=p_f_type,
                end=kwargs.get('end'))
        src_dict[i-removed] = opt
        def_val += 1

    src_dict[ENTRIES] -= removed


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

    # if a field doesnt have a specified offset then
    # this will be used as the starting offset and will
    # be incremented by the size of each field after it
    def_offset = 0
    # the largest alignment size requirement of any entry in this block
    l_align = 1

    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # ATTR_OFFS stores the offsets of each attribute by index.
    attr_offs = [0]*src_dict.get(ENTRIES, 0)
    nameset = set()  # contains the name of each entriy in the desc
    rem = 0  # number of dict entries removed
    key = 0
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in (i for i in range(src_dict[ENTRIES])
                if isinstance(src_dict.get(i), dict)):
        # Make sure to shift upper indexes down by how many
        # were removed and make a copy to preserve the original
        this_d = src_dict[key-rem] = dict(src_dict[key])
        key -= rem

        f_type = this_d.get(TYPE)

        if f_type is field_types.Pad:
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
                     "IS MISSING A SIZE KEY.\n") % (p_name, p_f_type, key))
            if ATTR_OFFS in src_dict:
                blockdef._e_str += (
                    ("ERROR: ATTR_OFFS ALREADY EXISTS IN '%s' OF TYPE " +
                     "%s, BUT A Pad ENTRY WAS FOUND AT INDEX %s.\n" +
                     "    CANNOT INCLUDE Pad FIELDS WHEN ATTR_OFFS " +
                     "ALREADY EXISTS.\n") % (p_name, p_f_type, key + rem))
                blockdef._bad = True
            rem += 1
            src_dict[ENTRIES] -= 1
            continue
        elif f_type is not None:
            # make sure the node has an offset if it needs one
            if OFFSET not in this_d:
                this_d[OFFSET] = def_offset
        elif p_f_type:
            blockdef._bad = True
            blockdef._e_str += (
                "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                "TYPE '%s' AT INDEX %s.\n" % (p_name, p_f_type, key))

        kwargs["key_name"] = key
        this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

        if f_type:
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
                if not p_f_type.is_bit_based:
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
                         "INDEX %s.\n    EXPECTED %s, GOT %s. \n    NAME " +
                         "OF OFFENDING ELEMENT IS '%s' OF TYPE %s.\n") %
                        (p_name, key + rem, int, type(size), name, f_type))
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

    # if the f_type is a struct and the ATTR_OFFS isnt already in it
    if ATTR_OFFS not in src_dict:
        src_dict[ATTR_OFFS] = attr_offs

    # Make sure all structs have a defined SIZE
    if p_f_type and calc_size:
        if p_f_type.is_bit_based:
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
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # make sure nothing exists in the QuickStruct that cant be in it.
    for key, this_d in ((i, src_dict[i]) for i in range(src_dict[ENTRIES])):
        if isinstance(this_d, dict) and this_d.get(TYPE):
            f_type = this_d[TYPE]
            name = this_d.get(NAME, UNNAMED)

            if f_type.is_block:
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CANNOT CONTAIN BLOCKS.\n    " +
                    "OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n    " +
                    "OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (f_type, name, p_name, p_f_type, key)
            elif (f_type.enc not in QSTRUCT_ALLOWED_ENC or
                  f_type.node_cls not in (float, int)):
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CAN ONLY CONTAIN INTEGER AND/OR " +
                    "FLOAT DATA WHOSE ENCODING IS ONE OF THE FOLLOWING:\n" +
                    ("    %s\n" % sorted(QSTRUCT_ALLOWED_ENC)) +
                    "    OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n" +
                    "    OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (f_type, name, p_name, p_f_type, key)

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

    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    nameset = set()  # contains the name of each entry in the desc
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in (i for i in range(src_dict[ENTRIES])
                if isinstance(src_dict[i], dict)):
        this_d = src_dict[key] = dict(src_dict[key])
        f_type = this_d.get(TYPE)

        if f_type is field_types.Pad:
            size = this_d.get(SIZE)

            if size is None:
                blockdef._bad = True
                blockdef._e_str += (
                    ("ERROR: Pad ENTRY IN '%s' OF TYPE %s AT INDEX %s " +
                     "IS MISSING A SIZE KEY.\n") % (p_name, p_f_type, key))
            # make sure the padding follows convention and has a name
            this_d.setdefault(NAME, 'pad_entry_%s' % pad_count)
            if NAME_MAP in src_dict:
                src_dict[NAME_MAP][this_d[NAME]] = key
            pad_count += 1
            continue
        elif f_type is None and p_f_type:
            blockdef._bad = True
            blockdef._e_str += (
                "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                "TYPE '%s' AT INDEX %s.\n" % (p_name, p_f_type, key))

        kwargs["key_name"] = key
        this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

        if f_type:
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
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # create a NAME_MAP, which maps the name of
    # each attribute to the key it's stored under
    if p_f_type.is_block:
        name_map = src_dict.get(NAME_MAP)

        # if the NAME_MAP is a list of names, turn it into a mapping
        if isinstance(name_map, (list, tuple)):
            name_list = name_map
            name_map = {}
            for i in range(len(name_list)):
                name_map[name_list[i]] = i

        if isinstance(name_map, dict):
            src_dict[NAME_MAP] = dict(name_map)
        else:
            src_dict[NAME_MAP] = {}
        blockdef.set_entry_count(src_dict, kwargs["key_name"])
        blockdef.find_entry_gaps(src_dict)

    # The non integer entries aren't substructs, so set it to False.
    kwargs['substruct'] = False

    # if the node cant hold a STEPTREE, but the descriptor
    # requires that it have a STEPTREE attribute, try to
    # set the NODE_CLS to one that can hold a STEPTREE.
    # Only do this though, if there isnt already a default set.
    if (not hasattr(p_f_type.node_cls, STEPTREE) and
        STEPTREE in src_dict and NODE_CLS not in src_dict):
        try:
            src_dict[NODE_CLS] = p_f_type.node_cls.PARENTABLE
        except AttributeError:
            blockdef._bad = True
            blockdef._e_str += (
                ("ERROR: FOUND DESCRIPTOR WHICH SPECIFIES A STEPTREE, BUT " +
                 "THE CORROSPONDING Block\nHAS NO SLOT FOR A STEPTREE " +
                 "AND DOES NOT SPECIFY A BLOCK THAT HAS A SLOT.\n    " +
                 "OFFENDING ELEMENT IS %s OF TYPE %s\n") % (p_name, p_f_type))

    # loops through the descriptors non-integer keyed sub-sections
    for key in (i for i in tuple(src_dict.keys()) if not isinstance(i, int)):
        if key not in desc_keywords:
            #blockdef._e_str += (
            #    ("ERROR: FOUND ENTRY IN DESCRIPTOR OF '%s' UNDER " +
            #     "UNKNOWN STRING KEY '%s'.\n") % (p_name, key))
            #blockdef._bad = True
            src_dict.pop(key)
            continue
        if isinstance(src_dict[key], dict) and key != ADDED:
            kwargs["key_name"] = key
            f_type = src_dict[key].get(TYPE)
            this_d = dict(src_dict[key])

            # replace with the modified copy so the original is intact
            src_dict[key] = this_d = blockdef.sanitize_loop(this_d,
                                                            **kwargs)

            if f_type:
                # if this is the repeated substruct of an array
                # then we need to calculate and set its alignment
                if ((key == SUB_STRUCT or f_type.is_str) and
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
    p_f_type = src_dict[TYPE]
    size = src_dict.get(SIZE)
    p_name = src_dict.get(NAME, UNNAMED)
    pointer = src_dict.get(POINTER)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if src_dict.get(CASE) is None:
        blockdef._e_str += (
            "ERROR: CASE MISSING IN '%s' OF TYPE %s\n" % (p_name, p_f_type))
        blockdef._bad = True
    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += (
            "ERROR: CASES MISSING IN '%s' OF TYPE %s\n" % (p_name, p_f_type))
        blockdef._bad = True

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

    for case in cases:
        case_map[case] = c_index
        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])
        c_f_type = case_desc.get(TYPE, field_types.Void)
        if not c_f_type.is_block:
            blockdef._e_str += (
                ("ERROR: Switch CASE DESCRIPTORS MUST HAVE THEIR " +
                 "'TYPE' ENTRIES is_block ATTRIBUTE BE True.\n" +
                 "    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "IN '%s'.\n") % (case, c_f_type, p_name))
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
    if isinstance(src_dict, dict) and src_dict.get(TYPE) is not None:
        p_f_type = src_dict[TYPE]
        p_name = src_dict.get(NAME, UNNAMED)
        if STEPTREE in src_dict:
            blockdef._e_str += (
                "ERROR: Union fields CANNOT CONTAIN STEPTREE BLOCKS AT " +
                "ANY POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                "IS '%s' OF TYPE %s." % (p_name, p_f_type))
            blockdef._bad = True

        if POINTER in src_dict:
            blockdef._e_str += (
                "ERROR: Union fields CANNOT BE POINTERED AT ANY " +
                "POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                "IS '%s' OF TYPE %s." % (p_name, p_f_type))
            blockdef._bad = True

        # re-run this check on entries in the dict
        for key in src_dict:
            _find_union_errors(blockdef, src_dict[key])


def union_sanitizer(blockdef, src_dict, **kwargs):
    ''''''
    # If the descriptor is a switch, the individual cases need to
    # be checked and setup as well as the pointer and defaults.
    p_f_type = src_dict[TYPE]
    size = src_dict.get(SIZE, 0)
    p_name = src_dict.get(NAME, UNNAMED)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += ("ERROR: CASES MISSING IN '%s' OF TYPE %s\n" %
                            (p_name, p_f_type))
        blockdef._bad = True
    if not isinstance(size, int):
        blockdef._e_str += (
            ("ERROR: Union 'SIZE' MUST BE AN INT LITERAL OR UNSPECIFIED, " +
             "NOT %s.\n    OFFENDING BLOCK IS '%s' OF TYPE %s\n") %
            (type(size), p_name, p_f_type))
        blockdef._bad = True
    if p_f_type.is_bit_based:
        blockdef._e_str += (
            "ERROR: Unions CANNOT BE INSIDE A bit_based field.\n    " +
            "OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

    # loop over all union cases and sanitize them
    for case in sorted(cases):
        case_map[case] = c_index

        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])

        c_f_type = case_desc.get(TYPE, field_types.Void)
        c_size = blockdef.get_size(case_desc)

        kwargs['key_name'] = case

        # sanitize the name and gui_name of the descriptor
        blockdef.sanitize_name(case_desc, **kwargs)
        c_name = case_desc.get(NAME, UNNAMED)

        if not c_f_type.is_block:
            blockdef._e_str += (
                ("ERROR: Union CASE DESCRIPTORS MUST HAVE THEIR " +
                 "'TYPE' ENTRIES is_block ATTRIBUTE BE True.\n" +
                 "    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_f_type, case, p_name))
            blockdef._bad = True
        if not c_f_type.is_struct and c_f_type.is_bit_based:
            blockdef._e_str += (
                ("ERROR: Structs ARE THE ONLY bit_based fields ALLOWED IN A " +
                 "Union.\n    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_f_type, case, p_name))
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
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    if SUB_STRUCT not in src_dict:
        blockdef._e_str += (
            "ERROR: MISSING SUB_STRUCT ENTRY.\n" +
            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True
        return src_dict
    if DECODER not in src_dict:
        blockdef._e_str += (
            "ERROR: MISSING STREAM DECODER.\n" +
            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True
    if ENCODER not in src_dict:
        # if no encoder was provided, use a dummy one
        src_dict[ENCODER] = adapter_no_encode

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

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
