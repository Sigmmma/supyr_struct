from .block import *
from ..buffer import BytesBuffer, BytearrayBuffer


class UnionBlock(Block, BytearrayBuffer):
    '''This block doesnt allow specifying a size as anything
    other than an int literal in the descriptor.'''

    __slots__ = ('DESC', 'PARENT', "u_block", "u_index")

    def __new__(typ, desc, parent=None, initdata=b'', **kwargs):
        '''docstring'''
        self = BytearrayBuffer.__new__(typ, initdata)
        return self

    def __init__(self, desc, parent=None, initdata=b'', **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc
                                           and 'CASE_MAP' in desc)

        osa = object.__setattr__
        osa(self, 'DESC',   desc)
        osa(self, 'PARENT', parent)
        osa(self, 'u_block', None)
        osa(self, 'u_index', None)

        if 'rawdata' in kwargs:
            self.build(**kwargs)

    def __str__(self, **kwargs):
        '''docstring'''
        show = kwargs.get('show', def_show)
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
            kwargs['attr_index'] = u_index
            kwargs['attr_name'] = None
            kwargs['attr'] = u_block
            del kwargs['attr_name']

            tag_str += '\n' + self.attr_to_str(**kwargs)

        tag_str += '\n%s]' % indent_str

        return tag_str

    def __copy__(self):
        '''Creates a shallow copy, keeping the same descriptor.'''
        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'PARENT')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self, 'DESC'),
                          parent=parent, initdata=self)

    def __deepcopy__(self, memo):
        '''Creates a deep copy, keeping the same descriptor.'''
        # if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'PARENT')
        except AttributeError:
            parent = None

        # make a new block object sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self, 'DESC'),
                               parent=parent, initdata=self)
        memo[id(self)] = dup_block

        return dup_block

    def __getattr__(self, attr_name):
        '''docstring'''
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")

            if attr_name in desc['CASE_MAP']:
                return self.set_active(desc['CASE_MAP'][attr_name])
            elif attr_name in desc:
                return desc[attr_name]
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_name))

    def __setattr__(self, attr_name, new_value):
        '''docstring'''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")

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
        '''docstring'''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")

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
        '''docstring'''
        # serialize self.u_block to the buffer if it is currently active
        if self.u_index is not None:
            self.set_active(None)
        return bytearray.__getitem__(self, index)

    def __setitem__(self, index, new_value):
        '''docstring'''
        if isinstance(index, str):
            return self.__setattr__(index, new_value)

        # serialize self.u_block to the buffer if it is currently active
        if self.u_index is not None:
            self.set_active(None)
        bytearray.__setitem__(self, index, new_value)

    def __delitem__(self, index):
        '''docstring'''
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
        '''docstring'''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = object.__sizeof__(self) + getsizeof(self.u_block)

        desc = object.__getattribute__(self, 'DESC')

        if 'ORIG_DESC' in desc and id(desc) not in seenset:
            seenset.add(id(desc))
            bytes_total += getsizeof(desc)
            for key in desc:
                item = desc[key]
                if (not isinstance(key, int) and key != 'ORIG_DESC' and
                    id(item) not in seenset):
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def _binsize(self, block, substruct=False):
        '''Returns the size of this UnionBlock.
        This size is how many bytes it would take up if written to a buffer.'''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''Returns the size of this UnionBlock.
        This size is how many bytes it would take up if written to a buffer.'''
        return self.get_size()

    def get_size(self, attr_index=None, **kwargs):
        '''docstring'''
        desc = object.__getattribute__(self, 'DESC')

        # It's faster to try to bitshift the size by 0 and return it
        # than to check if it's an int using isinstance(size, int)
        try:
            return desc.get('SIZE') >> 0
        except TypeError:
            raise TypeError(("Size specified in '%s' is not a valid type.\n" +
                "Expected int, got %s.") % (desc['NAME'], type(desc['SIZE'])))

    def set_size(self, new_value=None, **kwargs):
        '''docstring.'''
        raise TypeError('Union fields cannot have their size changed.')

    def set_active(self, new_index=None):
        u_index = object.__getattribute__(self, 'u_index')
        u_block = object.__getattribute__(self, 'u_block')
        desc = object.__getattribute__(self, 'DESC')

        # make sure that new_index is an int and that it is a valid index
        if isinstance(new_index, str):
            new_index = desc['CASE_MAP'].get(new_index)
            if new_index is None:
                name = desc.get(NAME, desc.get(GUI_NAME, UNNAMED))
                raise AttributeError(("'%s' is not a valid member of the " +
                                      "union '%s'") % (new_index, name))

        # Return the current block if the new and current index are equal
        # and they are either both None, or neither one is None. The second
        # condition is to make sure there is no chance of None == 0 occuring
        if new_index == u_index and (u_index is None == new_index is None):
            return u_block

        # serialize the block to the buffer if it is active
        if u_index is not None:
            # get the proper descriptor to use to write the data
            try:
                u_desc = u_block.DESC
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

    def build(self, **kwargs):
        '''This function will initialize all of a UnionBlocks attributes to
        their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

        initdata = kwargs.get('initdata', None)

        if initdata is not None:
            if not isinstance(initdata, (bytes, bytearray)):
                raise TypeError("Invalid type for initdata. Expected one of " +
                                "the following: %s\n Got %s" %
                                ((bytes, bytearray, BytesBuffer,
                                  BytearrayBuffer), type(initdata)))
            self[:] = initdata
            return  # return early

        rawdata = self.get_rawdata(**kwargs)
        desc = object.__getattribute__(self, "DESC")

        if rawdata is not None:
            assert (hasattr(rawdata, 'read') and hasattr(rawdata, 'seek')), (
                'Cannot build %s without an input path or a readable buffer' %
                type(self))
            # build the block from rawdata
            try:
                try:
                    parent = object.__getattribute__(self, "PARENT")
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
                              "attempting to build %s." % type(self),)
                raise e
        elif kwargs.get('init_attrs', True):
            # initialize the UnionBlock's bytearray data
            self[:] = desc.get('DEFAULT', b'\x00'*desc.get('SIZE'))

    # overriding BytearrayBuffer methods with ones that work for a UnionBlock
    def read(self, count=None):
        '''docstring'''
        try:
            if self._pos + count < len(self):
                old_pos = self._pos
                self._pos += count
            else:
                old_pos = self._pos
                self._pos = len(self)

            return bytearray.__getitem__(self, slice(old_pos, self._pos, None))
        except TypeError:
            pass

        assert count is None

        old_pos = self._pos
        self._pos = len(self)
        return bytes(bytearray.__getitem__(self, slice(old_pos,
                                                       self._pos,
                                                       None)))

    def write(self, s):
        '''docstring'''
        s = memoryview(s).tobytes()
        str_len = len(s)
        if len(self) < str_len + self._pos:
            self.extend(b'\x00' * (str_len - len(self) + self._pos))
        bytearray.__setitem__(self, slice(self._pos,
                                          self._pos + str_len,
                                          None), s)
        self._pos += str_len
