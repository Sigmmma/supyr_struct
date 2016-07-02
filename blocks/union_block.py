'''
A module that implements UnionBlock, a subclass of Block and BytearrayBuffer.
UnionBlocks are used in the same situations one would use them in
while programming in C or C++. They allow multiple structures to
be stored in the space of one, but only one may be active at a time.
'''
from .block import *
from ..buffer import BytesBuffer, BytearrayBuffer


class UnionBlock(Block, BytearrayBuffer):
    '''


    This block doesnt allow specifying a size as anything
    other than an int literal in the descriptor.
    '''

    __slots__ = ('desc', 'parent', 'u_block', 'u_index')

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes a UnionBlock. Sets its desc and parent to those supplied.
        Initializes self.u_block and self.u_index to None.

        Raises AssertionError is desc is missing
        'TYPE', 'NAME', or 'CASEMAP' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'CASE_MAP' in desc)

        osa = object.__setattr__
        osa(self, 'desc',   desc)
        osa(self, 'parent', parent)
        osa(self, 'u_block', None)
        osa(self, 'u_index', None)

        if kwargs:
            self.rebuild(**kwargs)

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
            index ---- The index the attribute is located in in its parent
            name ----- The name of the attribute
            value ---- The attribute value
            field ---- The Field of the attribute
            size ----- The size of the attribute
            offset --- The offset(or pointer) of the attribute
            py_id ---- The id() of the attribute
            py_type -- The type() of the attribute
            endian --- The endianness of the Field
            flags ---- The individual flags(offset, name, value) in a bool
            trueonly - Limit flags shown to only the True flags
        '''
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        level = kwargs.get('level', 0)
        indent = kwargs.get('indent', BLOCK_PRINT_INDENT)

        u_block = self.u_block
        u_index = self.u_index

        tag_str = Block.__str__(self, **kwargs)[:-2].replace(',', '', 1)

        kwargs['level'] = level + 1
        indent_str = ' '*indent*(level + 1)

        if not isinstance(u_block, Block) and u_index is None:
            tag_str += ('\n' + indent_str + '[ RAWDATA:%s ]' %
                        bytearray.__str__(self))
        else:
            kwargs['attr_name'] = None
            kwargs['attr_index'] = 'u_block'
            del kwargs['attr_name']

            tag_str += '\n' + self.attr_to_str(**kwargs)

        tag_str += '\n%s]' % indent_str

        return tag_str

    def __copy__(self):
        '''
        Creates a copy of this block which references
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
        Creates a deepcopy of this block which references
        the same descriptor and parent.

        Returns the deepcopy.
        '''
        # if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
        except AttributeError:
            parent = None

        # make a new block object sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               parent=parent, initdata=self)
        memo[id(self)] = dup_block

        return dup_block

    def __getattr__(self, attr_name):
        ''''''
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
        ''''''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['CASE_MAP']:
                self.u_index = desc['CASE_MAP'][attr_name]
                self.u_block = new_value
            elif attr_name in desc:
                self.set_desc(attr_name, new_value)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        ''''''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['CASE_MAP']:
                if desc['CASE_MAP'][attr_name] == self.u_index:
                    self.u_index = self.u_block = None
            elif attr_name in desc:
                self.del_desc(attr_name)
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
        # serialize self.u_block to the buffer if it is currently active
        if self.u_index is not None:
            self.set_active(None)
        return bytearray.__getitem__(self, index)

    def __setitem__(self, index, new_value):
        '''
        Replaces bytes in this UnionBlocks internal bytearray with 'new_value'
        at the location specified by 'index'. index may be an int or slice.

        If 'index' is a string, calls self.__setattr__(index, new_value)
            This is a kludge to fix some stuff related to readers,
            and hopefully I can make a not kludgy fix soon.

        If self.u_index is not None, changes the unions active state to None.
        '''
        if isinstance(index, str):
            return self.__setattr__(index, new_value)

        # serialize self.u_block to the buffer if it is currently active
        if self.u_index is not None:
            self.set_active(None)
        bytearray.__setitem__(self, index, new_value)

    def __delitem__(self, index):
        '''
        Replaces bytes in this UnionBlocks internal bytearray with b'\x00'
        at the location specified by 'index'. index may be an int or slice.

        If self.u_index is not None, changes the unions active state to None.
        '''
        # serialize self.u_block to the buffer if it is currently active
        if self.u_index is not None:
            self.set_active(None)

        # set the bytearray indexes to 0
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            slice_size = (max(start, stop)-min(start, stop))//abs(step)

            bytearray.__setitem__(self, index, b'\x00'*slice_size)
        else:
            bytearray.__setitem__(self, index, 0)

    def __sizeof__(self, seenset=None):
        ''''''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = object.__sizeof__(self) + getsizeof(self.u_block)

        desc = object.__getattribute__(self, 'desc')

        if 'ORIG_DESC' in desc and id(desc) not in seenset:
            seenset.add(id(desc))
            bytes_total += getsizeof(desc)
            for key in desc:
                item = desc[key]
                if not isinstance(key, int) and (key != 'ORIG_DESC' and
                                                 id(item) not in seenset):
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def _binsize(self, block, substruct=False):
        '''
        Returns the byte size of this UnionBlock.
        This size is how many bytes it would take up if written to a buffer.
        '''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''
        Returns the byte size of this UnionBlock.
        This size is how many bytes it would take up if written to a buffer.
        '''
        return self.get_size()

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
            raise TypeError(("Size specified in '%s' is not a valid type.\n" +
                             "Expected int, got %s.") % (desc['NAME'],
                                                         type(desc['SIZE'])))

    def set_size(self, new_value=None, **context):
        ''''''
        raise NotImplementedError('Unions cannot have their size changed.')

    def set_active(self, new_index=None):
        ''''''
        u_index = object.__getattribute__(self, 'u_index')
        u_block = object.__getattribute__(self, 'u_block')
        desc = object.__getattribute__(self, 'desc')

        # make sure that new_index is an int and that it is a valid index
        if isinstance(new_index, str):
            index = desc['CASE_MAP'].get(new_index)
            if index is None:
                name = desc.get(NAME, UNNAMED)
                raise AttributeError(("'%s' is not a valid member of the " +
                                      "union '%s'") % (new_index, name))
            new_index = index

        # Return the current block if the new and current index are equal
        # and they are either both None, or neither one is None. The second
        # condition is to make sure there is no chance of None == 0 occuring
        if new_index == u_index and (u_index is None == new_index is None):
            return u_block

        # serialize the block to the buffer if it is active
        if u_index is not None:
            # get the proper descriptor to use to write the data
            try:
                u_desc = u_block.desc
            except AttributeError:
                u_desc = desc[new_index]

            u_type = u_desc['TYPE']
            self._pos = 0  # reset the write position
            if u_type.endian == '>' and u_type.f_endian in '=>':
                # If the Union is big_endian then the offset the bytes
                # should be written to may not be 0. This is because the
                # members of a union are only guaranteed to be no larger
                # than the Union as a whole, and may in fact be smaller.
                # If they are smaller, some of the most significant bytes
                # arent used, which in big endian are the first bytes.

                # Do a right shift by 0 to make sure the offset is an int
                u_type.writer(u_block, self, None, 0,
                              (desc.get(size) - u_desc.get(size)) >> 0)
            else:
                u_type.writer(u_block, self)

        # make a new u_block if the new u_index is not None
        if new_index is not None:
            # get the descriptor to use to build the block
            u_desc = desc[new_index]
            u_desc[TYPE].reader(u_desc, self, self, 'u_block')
            object.__setattr__(self, 'u_index', new_index)
            return object.__getattribute__(self, 'u_block')
        else:
            object.__setattr__(self, 'u_index', None)
            object.__setattr__(self, 'u_block', None)

    def rebuild(self, **kwargs):
        '''
        Rebuilds this UnionBlock in the way specified by the keyword arguments.

        If initdata is supplied, it will be used to replace the contents
        of this UnionBlocks bytearray. If not, and rawdata or a filepath
        is supplied, it will be used to reparse this UnionBlock. 

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
        rawdata ------ A peekable buffer that will be used for rebuilding
                       this UnionBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the reader of this UnionBlocks Field.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the reader of this UnionBlocks Field.

        # iterable:
        initdata ----- An iterable capable of being assigned to a bytearray
                       using the slice notation    self[:] = initdata

        #str:
        filepath ----- An absolute path to a file to use as rawdata to rebuild
                       this UnionBlock. If supplied, do not supply 'rawdata'.
        '''

        initdata = kwargs.get('initdata', None)

        if initdata is not None:
            self[:] = initdata
            return  # return early

        rawdata = self.get_rawdata(**kwargs)
        desc = object.__getattribute__(self, "desc")

        if rawdata is not None:
            # rebuild the block from rawdata
            try:
                try:
                    parent = object.__getattribute__(self, "parent")
                except AttributeError:
                    parent = None

                desc['TYPE'].reader(desc, parent, rawdata, None,
                                    kwargs.get('root_offset', 0),
                                    kwargs.get('offset', 0))
                return  # return early
            except Exception as e:
                a = e.args[:-1]
                e_str = "\n"
                try:
                    e_str = e.args[-1] + e_str
                except IndexError:
                    pass
                e.args = a + (e_str + "Error occurred while " +
                              "attempting to rebuild %s." % type(self),)
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
