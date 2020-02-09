'''
Serializer functions for all standard FieldTypes.

Serializers are responsible for calling their associated encoder, using it to
encode a python object, and writing the encoded bytes to the writebuffer.

If the FieldType the serializer is meant for is not actually data,
but rather a form of hierarchy(like a Struct or Container) then
they wont have an encoder to call, but instead will be
responsible for calling the serializer functions of their
attributes and possibly the serializer functions of their
steptree and the steptrees of all nested children.

Serializers must also return an integer specifying what offset the
last data was written to.

Some functions do not require all of the arguments they are given,
but many of them do, and it is easier to provide extra arguments
that are ignored than to provide exactly what is needed.
'''

__all__ = [
    'container_serializer', 'array_serializer',
    'struct_serializer', 'bit_struct_serializer', 'py_array_serializer',
    'f_s_data_serializer', 'data_serializer',
    'cstring_serializer', 'bytes_serializer',

    # specialized serializers
    'computed_serializer',
    'void_serializer', 'pad_serializer', 'union_serializer',
    'stream_adapter_serializer', 'quickstruct_serializer',

    # util functions
    'format_serialize_error'
    ]

from supyr_struct.defs.constants import (
    COMPUTE_WRITE, STEPTREE, TYPE, SIZE, ATTR_OFFS, ALIGN, POINTER,
    SUB_STRUCT, ENCODER, byteorder_char
    )
from supyr_struct.exceptions import FieldSerializeError
from supyr_struct.buffer import BytearrayBuffer


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


def void_serializer(self, node, parent=None, attr_index=None,
                    writebuffer=None, root_offset=0, offset=0, **kwargs):
    return offset


def pad_serializer(self, node, parent=None, attr_index=None,
                   writebuffer=None, root_offset=0, offset=0, **kwargs):
    
    pad_size = node.get_size(offset=offset, root_offset=root_offset, **kwargs)
    writebuffer.seek(offset + root_offset)
    writebuffer.write(b'\x00'*pad_size)
    if parent is not None:
        return offset + pad_size
    return offset
