'''
A module that implements UnionBlock, a subclass of Block and BytearrayBuffer.
UnionBlocks are used in the same situations one would use them in
while programming in C or C++. They allow multiple structures to
be stored in the space of one, but only one may be active at a time.
'''
from sys import getsizeof

from supyr_struct.blocks.block import Block
from supyr_struct.defs.constants import DEF_SHOW, SHOW_SETS, UNNAMED,\
     NODE_PRINT_INDENT, TYPE, NAME, SIZE, NoneType
from supyr_struct.exceptions import DescEditError, BinsizeError
from supyr_struct.buffer import BytesBuffer, BytearrayBuffer,\
     get_rawdata_context


class UnionBlock(Block, BytearrayBuffer):
    '''
    A Block class meant to be used with Union fields or any fields that
    work similarly to Unions.

    This Block is designed to emulate the 'union' types found in C and C++
    by allowing it to switch between multiple descriptors for its 'u_node'
    attribute and having only one of them able to be set active at a time.

    The Block currently in self.u_node is the 'active' member, and is able
    to be accessed by its alias name in the CASE_MAP descriptor entry.
    self.u_index is set to the descriptor key of the active member.
    When an 'inactive' union member is accessed it is set as active and
    self.u_node is replaced with the newly active member. The current
    member is first serialized to the UnionBlocks internal bytearray
    before the UnionBlock is provided as rawdata to build the new member.
    The previously active member is not deleted, just de-referenced.

    A union member may be set as active by calling self.set_active and
    passing either the members name or its descriptor key as the argument.
    If no argument is given, the active member will be set to None.
    If the active member is None, there is no member active.
    This effectively turns the Block into just a BytearrayBuffer, which
    is how it should be treated when no member is active.

    If the internal bytearray is accessed through index notation(ex. self[i])
    the active member will be set to None. This is because when getting
    data from the bytearray, the active member will need to be serialized
    to update it. When writing to it, any changes would cause the active
    member to no longer share the same serialized value as the bytearray.

    Because of certain complexities introduced by having multiple
    descriptors, this Block does not allow its descriptors SIZE entry
    to be anything other than an int literal. The u_node entry also
    must be a Block, UnionBlocks can not be used inside a bitstruct,
    and nothing within a UnionBlock can be pointered or have steptrees.
    '''

    __slots__ = ('desc', '_parent', '__weakref__', 'u_node', 'u_index')

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes a UnionBlock. Sets its desc and parent to those supplied.
        Sets the currently active union member to None. This means that
        no member is active, and that the UnionBlock should be treated
        as a regular BytearrayBuffer when parsing or writing its data.

        Raises AssertionError is desc is missing
        'TYPE', 'NAME', or 'CASE_MAP' keys.
        If kwargs are supplied, calls self.parse and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'CASE_MAP' in desc)

        object.__setattr__(self, 'desc',   desc)
        self.parent = parent
        object.__setattr__(self, 'u_node', None)
        object.__setattr__(self, 'u_index', None)

        if kwargs:
            self.parse(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this UnionBlock.

        Optional keywords arguments:
        # int:
        indent ----- The number of spaces of indent added per indent level
        precision -- The number of decimals to round floats to

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located at in its parent
            name ------ The name of the field
            value ----- The field value(the node)
            type ------ The FieldType of the field
            size ------ The size of the field
            offset ---- The offset(or pointer) of the field
            parent_id - The id() of self.parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
            endian ---- The endianness of the field
            flags ----- The individual flags(offset, name, value) in a bool
            trueonly -- Limit flags shown to only the True flags
        '''
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        level = kwargs.get('level', 0)
        indent = kwargs.get('indent', NODE_PRINT_INDENT)

        u_node = self.u_node
        u_index = self.u_index

        tag_str = Block.__str__(self, **kwargs)[:-2].replace(',', '', 1)

        kwargs['level'] = level + 1
        indent_str = ' '*indent*(level + 1)

        if not isinstance(u_node, Block) and u_index is None:
            tag_str += ('\n' + indent_str + '[ RAWDATA:%s ]' %
                        bytearray.__str__(self))
        else:
            kwargs['attr_name'] = None
            kwargs['attr_index'] = 'u_node'
            del kwargs['attr_name']

            tag_str += '\n' + self.attr_to_str(**kwargs)

        tag_str += '\n%s]' % indent_str

        return tag_str

    def __copy__(self):
        '''
        Creates a copy of this Block which references
        the same descriptor and parent.

        Returns the copy.
        '''
        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self, 'desc'),
                          parent=parent, initdata=self)

    def __deepcopy__(self, memo):
        '''
        Creates a deepcopy of this Block which references
        the same descriptor and parent.

        Returns the deepcopy.
        '''
        # if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
            parent = memo.get(id(parent), parent)
        except AttributeError:
            parent = None

        # make a new Block sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               parent=parent, initdata=self)
        memo[id(self)] = dup_block

        return dup_block

    def __getattr__(self, attr_name):
        '''
        Returns the attribute specified by the supplied 'attr_name'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['CASE_MAP'], or in self.desc.

        If object.__getattribute__(self, attr_name) raises an AttributeError,
        then self.desc['CASE_MAP'] will be checked for attr_name in its keys.
        If it exists, activates and returns the member specified by attr_name.
        If not, self.desc will be checked for attr_name in its keys.
        If it exists, returns self.desc[attr_index]

        Raises AttributeError if attr_name cant be found in the Block,
        its CASE_MAP desc entry, or the descriptor itself.
        '''
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['CASE_MAP']:
                return self.set_active(desc['CASE_MAP'][attr_name])
            elif attr_name in desc:
                return desc[attr_name]
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_name))

    def __setattr__(self, attr_name, new_value):
        '''
        Sets the attribute specified by 'attr_name' to the given 'new_value'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['CASE_MAP'], or in self.desc.

        If object.__setattr__(self, attr_name, new_value) raises an
        AttributeError, then self.desc['CASE_MAP'] will be checked for
        attr_name in its keys.
        If it exists, sets the currently active member to the one specified
        by 'attr_name' and sets self.u_node to the new_value.
        If not, self.desc will be checked for attr_name in its keys.

        Raises AttributeError if attr_name cant be found in the Block,
        its CASE_MAP desc entry, or the descriptor itself.
        '''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['CASE_MAP']:
                assert not self.assert_is_valid_field_value(
                    desc['CASE_MAP'][attr_name], new_value)
                self.u_index = desc['CASE_MAP'][attr_name]
                self.u_node = new_value
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        '''
        Deletes the attribute specified by 'attr_name'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['CASE_MAP'], or in self.desc.

        If object.__delattr__(self, attr_name) raises an AttributeError,
        then self.desc['CASE_MAP'] will be checked for attr_name in its keys.
        If it exists and is active, sets the currently active member to
        None without serializing self.u_node to the internal bytearray.
        If it doesn't exist, self.desc will be checked for attr_name
        in its keys.

        Raises AttributeError if attr_name cant be found in the Block,
        its CASE_MAP desc entry, or the descriptor itself.
        '''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['CASE_MAP']:
                if desc['CASE_MAP'][attr_name] == self.u_index:
                    self.u_index = self.u_node = None
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __getitem__(self, index):
        '''
        Returns bytes in this UnionBlocks internal bytearray at the
        location specified by 'index'. index may be an int or slice.

        If self.u_index is not None, changes the unions active state to None.
        '''
        if isinstance(index, str):
            return self.__getattr__(index)
        elif self.u_index is not None:
            # flush self.u_node to the buffer if it is currently active
            self.flush()
        return bytearray.__getitem__(self, index)

    def __setitem__(self, index, new_value):
        '''
        Replaces bytes in this UnionBlocks internal bytearray with 'new_value'
        at the location specified by 'index'. index may be an int or slice.

        If 'index' is a string, calls self.__setattr__(index, new_value)
            This is a kludge to fix some stuff related to parsers,
            and hopefully I can make a not kludgy fix soon.

        If self.u_index is not None, sets the currently active member to None.
        '''
        if isinstance(index, str):
            return self.__setattr__(index, new_value)
        elif self.u_index is not None:
            # flush self.u_node to the buffer if it is currently active
            self.set_active(None)
        bytearray.__setitem__(self, index, new_value)

    def __delitem__(self, index):
        '''
        Replaces bytes in this UnionBlocks internal bytearray with b'\x00'
        at the location specified by 'index'. index may be an int or slice.

        If self.u_index is not None, sets the currently active member to None.
        '''
        if isinstance(index, str):
            return self.__delattr__(index)
        elif self.u_index is not None:
            # flush self.u_node to the buffer if it is currently active
            self.set_active(None)

        # set the bytearray indexes to 0
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            slice_size = (max(start, stop)-min(start, stop))//abs(step)

            bytearray.__setitem__(self, index, b'\x00'*slice_size)
        else:
            bytearray.__setitem__(self, index, 0)

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this Block and all its attributes and
        nodes take up in memory.

        'seen_set' is a set of python object ids used to keep track
        of whether or not an object has already been added to the byte
        total at some earlier point. This was added for more accurate
        measurements that dont count descriptor sizes multiple times.
        '''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = object.__sizeof__(self) + getsizeof(self.u_node)

        desc = object.__getattribute__(self, 'desc')

        return bytes_total

    def __binsize__(self, node, substruct=False):
        '''
        Returns the byte size of this UnionBlock if written to a buffer.

        This method is intended to only be called by other binsize methods
        and will return 0 if this UnionBlock is inside a Struct.
        This is to account for the fact that Structs already know
        the combined size of all their members and padding.
        '''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''Returns the byte size of this UnionBlock if written to a buffer.'''
        try:
            return self.get_size()
        except Exception as exc:
            raise BinsizeError("Could not calculate binary size.") from exc

    def flush(self):
        '''
        '''
        u_node = object.__getattribute__(self, 'u_node')
        u_index = object.__getattribute__(self, 'u_index')
        desc = object.__getattribute__(self, 'desc')
        assert u_index is not None, (
            "Cannot flush a UnionBlock that has no active member.")

        # get the proper descriptor to use to serialize the data
        try:
            u_desc = u_node.desc
        except AttributeError:
            u_desc = desc[u_index]

        u_type = u_desc['TYPE']
        self._pos = 0  # reset the write position

        # temporarily set the u_index to None so it can be used as a writebuffer
        object.__setattr__(self, 'u_index', None)
        if u_type.endian == '>' and u_type.f_endian in '=>':
            # If the Union is big_endian then the offset the bytes
            # should be written to may not be 0. This is because the
            # members of a union are only guaranteed to be no larger
            # than the Union as a whole, and may in fact be smaller.
            # If they are smaller, some of the most significant bytes
            # arent used, which in big endian are the first bytes.
            u_type.serializer(u_node, self, None, self, 0,
                              desc.get(SIZE) - u_desc.get(SIZE))
        else:
            u_type.serializer(u_node, self, None, self)

        object.__setattr__(self, 'u_index', u_index)

    def get_size(self, attr_index=None, **context):
        '''
        Returns the value in self.desc['SIZE']
        Raises TypeError if the value isn't an int.
        '''
        desc = object.__getattribute__(self, 'desc')

        # It's faster to try to bitshift the size by 0 and return it
        # than to check if it's an int using isinstance(size, int)
        try:
            return desc.get('SIZE') >> 0
        except TypeError:
            pass
        raise TypeError(("Size specified in '%s' is not a valid type.\n" +
                         "Expected int, got %s.") % (desc['NAME'],
                                                     type(desc.get('SIZE'))))

    def set_size(self, new_value=None, attr_index=None, **context):
        '''
        Raises DescEditError when called.

        Unions must have a fixed size and thus the SIZE value in their
        descriptor must be an int.
        Setting fixed sizes is disallowed because of the
        possibility of unintended descriptor modification.
        '''
        raise DescEditError('Union sizes are int literals and cannot be set ' +
                            'using set_size. Make a new descriptor instead.')

    def set_active(self, new_index=None):
        '''
        Sets the currently active union member to the one given by 'new_index'
        and returns the newly active member. If new_index is self.u_index,
        this function will do nothing except return self.u_node

        The new_index must be either the string name of the member, None, or
        the int index in the descriptor that the members descriptor is under.
        If new_index is a string, self.desc['CASE_MAP'] will be checked for
        new_index in its keys. If it exists, the keyed value will be used
        as new_index. Raises an AttributeError if it doesnt exist.

        If new_index is None, self.u_index and self.u_node will both
        be set to None.

        If the currently active member is not None, it will be serialized to
        this UnionBlocks internal bytearray before changing the active member.

        If new_index is not None, the descriptor in self.desc[new_index]
        will be used to build the newly active union member.

        Returns self.u_node after changing the active member.
        '''
        u_index = object.__getattribute__(self, 'u_index')
        u_node = object.__getattribute__(self, 'u_node')
        desc = object.__getattribute__(self, 'desc')

        # make sure that new_index is an int or string
        assert isinstance(new_index, (int, str, NoneType)), (
            "'new_index' must be an int or str, not %s" % type(new_index))

        # make sure that new_index is a valid index
        if isinstance(new_index, str):
            if new_index not in desc['CASE_MAP']:
                name = desc.get(NAME, UNNAMED)
                raise AttributeError(
                    ("'%s' is not a valid member of the union '%s'") %
                    (new_index, name))
            new_index = desc['CASE_MAP'][new_index]

        # Return the current u_node if the new and current index are equal
        # and they are either both None, or neither one is None. The second
        # condition is to make sure there is no chance of None == 0 occuring
        # CHECK FAILS IF PARANTHESES ARE NOT AROUND BOTH xxxx is None
        if new_index == u_index and ((u_index is None) == (new_index is None)):
            return u_node

        # serialize the node to the buffer if it is active
        if u_index is not None:
            self.flush()

        # temporarily set the u_index to None so it can be used as rawdata
        object.__setattr__(self, 'u_index', None)

        # make a new u_node if the new u_index is not None
        if new_index is not None:
            # get the descriptor to use to build the node
            u_desc = desc[new_index]
            u_desc[TYPE].parser(
                u_desc, parent=self, rawdata=self, attr_index='u_node')
            object.__setattr__(self, 'u_index', new_index)
            return object.__getattribute__(self, 'u_node')
        else:
            # u_index is already None, so dont need to change it
            object.__setattr__(self, 'u_node', None)

    def parse(self, **kwargs):
        '''
        Parses this UnionBlock in the way specified by the keyword arguments.

        If initdata is supplied, it will be used to replace the contents
        of this UnionBlocks bytearray. If not, and rawdata or a filepath
        is supplied, it will be used to parse this UnionBlock.

        If rawdata, initdata, filepath, and init_attrs are all unsupplied,
        the contents of this UnionBlocks bytearray will be replaced with
        the DEFAULT value in the descriptor. If one doesnt exist, the
        contents will be replaced with    b'\x00'*desc['SIZE']

        If rawdata, initdata, and filepath are all unsupplied or None and
        init_attrs is False, this method will do nothing.

        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.

        Optional keywords arguments:
        # bool:
        init_attrs --- Whether or not to replace the contents of this
                       UnionBlocks bytearray with the DEFAULT descriptor value,
                       or with b'\x00'*desc['SIZE'] if DEFAULT doesnt exist.
                       Changes the active state to None.

        # buffer:
        rawdata ------ A peekable buffer that will be used for parsing
                       this UnionBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the parser of this UnionBlocks FieldType.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the parser of this UnionBlocks FieldType.

        # iterable:
        initdata ----- An iterable capable of being assigned to a bytearray
                       using the slice notation    self[:] = initdata

        #str:
        filepath ----- An absolute path to a file to use as rawdata to parse
                       this UnionBlock. If supplied, do not supply 'rawdata'.
        '''
        initdata = kwargs.pop('initdata', None)

        if initdata is not None:
            self[:] = initdata
            return  # return early

        desc = object.__getattribute__(self, "desc")
        writable = kwargs.pop('writable', False)
        with get_rawdata_context(writable=writable, **kwargs) as rawdata:
            if rawdata is not None:
                # parse the block from rawdata
                try:
                    kwargs.update(parent=self.parent, desc=desc,
                                  node=self, rawdata=rawdata)
                    kwargs.pop('filepath', None)
                    desc['TYPE'].parser(**kwargs)
                    return  # return early
                except Exception as e:
                    a = e.args[:-1]
                    e_str = "\n"
                    try:
                        e_str = e.args[-1] + e_str
                    except IndexError:
                        pass
                    e.args = a + (e_str + "Error occurred while " +
                                  "attempting to parse %s." % type(self),)
                    raise e
            elif kwargs.get('init_attrs', True):
                # initialize the UnionBlock's bytearray data
                self[:] = desc.get('DEFAULT', b'\x00'*desc['SIZE'])

    # overriding BytearrayBuffer methods with ones that work for a UnionBlock
    def read(self, count=None):
        '''
        Reads and returns 'count' number of bytes as a bytes
        object from this UnionBlocks internal bytearray.
        '''
        try:
            if self._pos + count < len(self):
                old_pos = self._pos
                self._pos += count
            else:
                old_pos = self._pos
                self._pos = len(self)

            return bytearray.__getitem__(self, slice(old_pos, self._pos))
        except TypeError:
            pass

        assert count is None

        old_pos = self._pos
        self._pos = len(self)
        return bytes(bytearray.__getitem__(self, slice(old_pos, self._pos)))

    def write(self, s):
        '''
        Uses memoryview().tobytes() to convert the supplied object
        into bytes and writes those bytes to this UnionBlocks internal
        bytearray at the current location of the read/write pointer.
        Attempting to write outside the buffer will force
        the buffer to be extended to fit the written data.

        Updates the read/write pointer by the length of the bytes.
        '''
        s = memoryview(s).tobytes()
        str_len = len(s)
        if len(self) < str_len + self._pos:
            self.extend(b'\x00' * (str_len - len(self) + self._pos))
        bytearray.__setitem__(self, slice(self._pos, self._pos + str_len), s)
        self._pos += str_len
