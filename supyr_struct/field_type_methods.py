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

from supyr_struct.defs.constants import (
    DEFAULT, NODE_CLS, COMPUTE_READ, COMPUTE_WRITE, STEPTREE, TYPE, SIZE,
    ATTR_OFFS, ALIGN, POINTER, SUB_STRUCT, CASE, CASE_MAP, ENCODER, DECODER,
    byteorder_char
    )
from supyr_struct.exceptions import FieldParseError, FieldSerializeError
from supyr_struct.buffer import BytearrayBuffer

__all__ = [
    # Parsers
    'container_parser', 'array_parser',
    'struct_parser', 'bit_struct_parser', 'py_array_parser',
    'data_parser', 'cstring_parser', 'bytes_parser',
    # Serializers
    'container_serializer', 'array_serializer',
    'struct_serializer', 'bit_struct_serializer', 'py_array_serializer',
    'f_s_data_serializer', 'data_serializer',
    'cstring_serializer', 'bytes_serializer',

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

    # Exception string formatters
    'format_parse_error', 'format_serialize_error'
    ]


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
    if not isinstance(e, FieldParseError):
        e = FieldParseError()
    e.add_stack_layer(**kwargs)
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
    if not isinstance(e, FieldSerializeError):
        e = FieldSerializeError()
    e.add_stack_layer(**kwargs)
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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            error = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            error = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            error = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            error = format_parse_error(e, field_type=a_desc['TYPE'], desc=a_desc,
                                   parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            error = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            error = format_parse_error(e, field_type=a_desc['TYPE'], desc=a_desc,
                                   parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        try:
            index = case_i
        except NameError:
            index = None
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, buffer=rawdata,
                               attr_index=index, root_offset=root_offset,
                               offset=offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
            # If there is a specific pointer to read the node from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this node is being built
            # without a parent(such as from an exported block) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and 'POINTER' in desc:
                offset = node.get_meta('POINTER', **kwargs)
            elif 'ALIGN' in desc:
                align = desc['ALIGN']
                offset += (align - (offset % align)) % align

            # loop once for each field in the node
            for i, off in enumerate(desc['ATTR_OFFS']):
                desc[i]['TYPE'].parser(desc[i], None, node, i, rawdata,
                                       root_offset, offset + off, **kwargs)

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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            error = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                   parent=p_node, attr_index=STEPTREE,
                                   offset=offset, **kwargs)
        elif 'i' in locals():
            error = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


def quickstruct_parser(self, desc, node=None, parent=None, attr_index=None,
                       rawdata=None, root_offset=0, offset=0, **kwargs):
    """
    """

    try:
        # we wanna go as fast as possible, so we completely skip over the
        # nodes __setitem__ magic method by calling the lists one directly
        __lsi__ = list.__setitem__

        orig_offset = offset
        if node is None:
            parent[attr_index] = node = desc.get(NODE_CLS, self.node_cls)\
                (desc, parent=parent)

        # If there is rawdata to build the structure from
        if rawdata is not None:
            # If there is a specific pointer to read the node from
            # then go to it. Only do this, however, if the POINTER can
            # be expected to be accurate. If the pointer is a path to
            # a previously parsed field, but this node is being built
            # without a parent(such as from an exported block) then
            # the path wont be valid. The current offset will be used instead.
            if attr_index is not None and 'POINTER' in desc:
                offset = node.get_meta('POINTER', **kwargs)
            elif 'ALIGN' in desc:
                align = desc['ALIGN']
                offset += (align - (offset % align)) % align

            struct_off = root_offset + offset

            f_endian = self.f_endian
            # loop once for each field in the node
            for i, off in enumerate(desc['ATTR_OFFS']):
                off += struct_off
                typ = desc[i]['TYPE']
                # check the forced endianness of the typ being parsed
                # before trying to use the endianness of the struct
                if f_endian == "=" and typ.f_endian == "=":
                    pass
                elif typ.f_endian == ">":
                    typ = typ.big
                elif typ.f_endian == "<" or f_endian == "<":
                    typ = typ.little
                else:
                    typ = typ.big

                __lsi__(node, i, typ.struct_unpacker(
                    rawdata[off:off + typ.size])[0])

            # increment offset by the size of the struct
            offset += desc['SIZE']
        else:
            for i in range(len(node)):
                __lsi__(node, i,
                        desc[i].get(DEFAULT, desc[i]['TYPE'].default()))

        if 'STEPTREE' in desc:
            s_desc = desc['STEPTREE']
            if 'steptree_parents' not in kwargs:
                offset = s_desc['TYPE'].parser(s_desc, None, node, 'STEPTREE',
                                               rawdata, root_offset, offset,
                                               **kwargs)
            else:
                kwargs['steptree_parents'].append(node)

        # pass the incremented offset to the caller
        return offset
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 's_desc' in locals():
            error = format_parse_error(e, field_type=s_desc.get(TYPE), desc=s_desc,
                                  parent=node, attr_index=STEPTREE,
                                  offset=offset, **kwargs)
        elif 'i' in locals():
            error = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        adapted_stream = locals().get('adapted_stream', rawdata)
        kwargs.update(field_type=self, desc=desc, parent=parent,
                      buffer=adapted_stream, attr_index=attr_index,
                      root_offset=orig_root_offset, offset=orig_offset)
        error = format_parse_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'case_i' in locals() and case_i in desc:
            error = format_parse_error(
                e, field_type=desc[case_i].get(TYPE), desc=desc[case_i],
                parent=node, attr_index=case_i, offset=offset, **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=orig_offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        kwargs.update(buffer=rawdata, root_offset=root_offset)
        if 'i' in locals():
            error = format_parse_error(e, field_type=desc[i].get(TYPE),
                                   desc=desc[i], parent=node, attr_index=i,
                                   offset=desc['ATTR_OFFS'][i], **kwargs)
        error = format_parse_error(e, field_type=self, desc=desc,
                               parent=parent, attr_index=attr_index,
                               offset=offset, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            error = format_serialize_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            error = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        error = format_serialize_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            error = format_serialize_error(e, **kwargs)
        elif 'i' in locals():
            try:
                a_desc = node[i].desc
            except (TypeError, AttributeError):
                a_desc = desc['SUB_STRUCT']
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            error = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        error = format_serialize_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


def struct_serializer(self, node, parent=None, attr_index=None,
                      writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    """

    try:
        orig_offset = offset
        desc = node.desc
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
        for i, off in enumerate(desc['ATTR_OFFS']):
            # structs usually dont contain Blocks, so check
            attr = node[i]
            if hasattr(attr, 'desc'):
                a_desc = attr.desc
            else:
                a_desc = desc[i]
            a_desc['TYPE'].serializer(attr, node, i, writebuffer, root_offset,
                                      offset + off, **kwargs)

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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=p_node, attr_index=STEPTREE, offset=offset)
            error = format_serialize_error(e, **kwargs)
        elif 'a_desc' in locals():
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            error = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        error = format_serialize_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
        
        f_endian = self.f_endian
        # loop once for each field in the node
        for i, off in enumerate(desc['ATTR_OFFS']):
            typ = desc[i]['TYPE']
            # check the forced endianness of the typ being serialized
            # before trying to use the endianness of the struct
            if f_endian == "=" and typ.f_endian == "=":
                pass
            elif typ.f_endian == ">":
                typ = typ.big
            elif typ.f_endian == "<" or f_endian == "<":
                typ = typ.little
            else:
                typ = typ.big

            writebuffer.seek(struct_off + off)
            writebuffer.write(typ.struct_packer(__lgi__(node, i)))

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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc', None)
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 's_desc' in locals():
            kwargs.update(field_type=s_desc.get(TYPE), desc=s_desc,
                          parent=node, attr_index=STEPTREE, offset=offset)
            error = format_serialize_error(e, **kwargs)
        elif 'i' in locals():
            kwargs.update(field_type=desc[i].get(TYPE), desc=desc[i],
                          parent=node, attr_index=i, offset=offset)
            error = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=orig_offset)
        error = format_serialize_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        desc = locals().get('desc', None)
        error = format_serialize_error(
            e, field_type=self, desc=desc, parent=parent, buffer=temp_buffer,
            attr_index=attr_index, root_offset=root_offset, offset=offset,
            **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
    except (Exception, KeyboardInterrupt) as e:
        desc = locals().get('desc', None)
        error = format_serialize_error(
            e, field_type=self, desc=desc, parent=parent, buffer=writebuffer,
            attr_index=attr_index, root_offset=root_offset, offset=offset,
            **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


def f_s_data_serializer(self, node, parent=None, attr_index=None,
                        writebuffer=None, root_offset=0, offset=0, **kwargs):
    """
    Serializer for fixed size data types.
    Increments the offset exactly by the size of the field.
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
    except (Exception, KeyboardInterrupt) as e:
        # if the error occurred while parsing something that doesnt have an
        # error report routine built into the function, do it for it.
        desc = locals().get('desc')
        kwargs.update(buffer=writebuffer, root_offset=root_offset)
        if 'i' in locals():
            a_desc = desc[i]
            kwargs.update(field_type=a_desc.get(TYPE), desc=a_desc,
                          parent=node, attr_index=i, offset=offset)
            error = format_serialize_error(e, **kwargs)

        kwargs.update(field_type=self, desc=desc, parent=parent,
                      attr_index=attr_index, offset=offset)
        error = format_serialize_error(e, **kwargs)
        # raise a new error if it was replaced, otherwise reraise
        if error is e:
            raise
        raise error from e


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
