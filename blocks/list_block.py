'''
'''
from copy import deepcopy
from .block import *


class ListBlock(list, Block):
    """
    ListBlocks are the primary method of storing hierarchial
    data, and can be seen as a mutable version of namedtuples.
    They function as a list where each entry can be accessed
    by its attribute name defined in the descriptor.

    For example: If the value in key "0" in the descriptor of the
    object "block" has a key:value pair of "NAME":"data", then doing:

    block[0] = "here's a string"
        is the same as doing:
    block.data = "here's a string"
        or
    block['data'] = "here's a string"
    """

    __slots__ = ('desc', 'parent')

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes a ListBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'NAME_MAP', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'NAME_MAP' in desc and 'ENTRIES' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, 'parent', parent)

        if kwargs:
            self.rebuild(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this ListBlock.

        Optional keywords arguments:
        # int:
        attr_index - The index this block is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
        indent ----- The number of spaces of indent added per indent level.
        precision -- The number of decimals to round floats to.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

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
            children - Attributes parented to a block as children
        '''
        # set the default things to show
        seen = kwargs['seen'] = set(kwargs.get('seen', ()))
        seen.add(id(self))

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        indent = kwargs.get('indent', BLOCK_PRINT_INDENT)
        attr_index = kwargs.get('attr_index', None)
        kwargs.setdefault('level', 0)

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.remove('all')
            show.update(ALL_SHOW)
        kwargs['show'] = show

        # used to display different levels of indention
        indent_str0 = ' '*indent*kwargs['level']
        indent_str1 = ' '*indent*(kwargs['level'] + 1)

        tag_str = indent_str0 + '['
        kwargs['level'] += 1

        tempstr = ''

        desc = object.__getattribute__(self, 'desc')

        if "index" in show and attr_index is not None:
            tempstr = ', %s' % attr_index
        if "field" in show and hasattr(self, 'TYPE'):
            tempstr += ', %s' % desc['TYPE'].name
        if "offset" in show:
            if hasattr(self, POINTER):
                tempstr += ', pointer:%s' % self.get_meta('POINTER')
            else:
                try:
                    tempstr += (', offset:%s' %
                                self.parent['ATTR_OFFS'][attr_index])
                except Exception:
                    pass
        if "unique" in show:
            tempstr += ', unique:%s' % ('ORIG_DESC' in desc)
        if "py_id" in show:
            tempstr += ', py_id:%s' % id(self)
        if "py_type" in show:
            tempstr += ', py_type:%s' % desc['TYPE'].py_type
        if "size" in show:
            if hasattr(self, 'SIZE') and not desc['TYPE'].is_container:
                tempstr += ', size:%s' % self.get_size()
            tempstr += ', entries:%s' % len(self)
        if "name" in show and 'NAME' in desc:
            attr_name = kwargs.get('attr_name', UNNAMED)
            if attr_name == UNNAMED:
                attr_name = desc.get('NAME', UNNAMED)
            tempstr += ', %s' % attr_name

        tag_str += tempstr.replace(',', '', 1) + '\n'

        # make an inverse mapping. index:name instead of name:index
        inv_name_map = {v: k for k, v in desc.get(NAME_MAP, {}).items()}

        # Print all this ListBlock's indexes
        for i in range(len(self)):
            kwargs['attr_name'] = inv_name_map.get(i, UNNAMED)
            kwargs['attr_index'] = i

            tag_str += self.attr_to_str(**kwargs)

        # Print this ListBlock's child if it has one
        if hasattr(self, 'CHILD') and (self.CHILD is not None and
                                       "children" in show):
            kwargs['attr_name'] = inv_name_map.get('CHILD', UNNAMED)
            kwargs['attr_index'] = CHILD

            tag_str += self.attr_to_str(**kwargs)

        tag_str += indent_str1 + ']'

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

        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               initdata=self, parent=parent)

        if hasattr(self, 'CHILD'):
            object.__setattr__(dup_block, 'CHILD',
                               object.__getattribute__(self, 'CHILD'))

        return dup_block

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
        # make sure the attributes arent initialized. it'll just waste time.
        memo[id(self)] = dup_block = type(self)(object.__getattribute__
                                                (self, 'desc'), parent=parent,
                                                init_attrs=False)

        # clear the block so it can be populated
        list.__delitem__(dup_block, slice(None, None, None))
        list.extend(dup_block, [None]*len(self))

        # populate the duplicate
        for i in range(len(self)):
            list.__setitem__(dup_block, i, deepcopy(list.__getitem__(self, i),
                                                    memo))

        # CHILD has to be done last as its structure
        # likely relies on attributes of this, its parent
        if hasattr(self, 'CHILD'):
            object.__setattr__(dup_block, 'CHILD',
                               deepcopy(object.__getattribute__(self, 'CHILD'),
                                        memo))

        return dup_block

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this ListBlock, all its
        attributes, and all its list elements take up in memory.

        If this Blocks descriptor is unique(denoted by it having an
        'ORIG_DESC' key) then the size of the descriptor and all its
        entries will be included in the byte size total.

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
        bytes_total = list.__sizeof__(self)

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

        for i in range(len(self)):
            item = list.__getitem__(self, i)
            if not id(item) in seenset:
                if isinstance(item, Block):
                    bytes_total += item.__sizeof__(seenset)
                else:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def __getitem__(self, index):
        '''
        Returns the object located at index in this Block.
        index may be the string name of an attribute.

        If index is a string, returns self.__getattr__(index)
        '''
        if isinstance(index, str):
            return self.__getattr__(index)
        return list.__getitem__(self, index)

    def __setitem__(self, index, new_value):
        '''
        Places new_value into this ListBlock at index.
        index may be the string name of an attribute, a slice, or an integer.

        If index is an int or slice, calls:
            list.__setitem__(self, index, new_value)
        If index is neither, calls:
            self.__setattr__(index, new_value)

        If new_value has an attribute named 'parent', it will be set to
        this ListBlock after it is set. If index is a slice, new_value
        will be instead iterated over and each object in it will have
        its 'parent' attribute set to this ListBlock if 'parent' exists.

        If this ListBlocks descriptor has a SIZE entry that is not an int, its
        set_size method will be called with no arguments to update its size.

        If index is a slice, this ListBlocks set_size will be called for
        each of the indexes being updated with the contents of new_value.

        Raises AssertionError if index is a slice and new_value isnt iterable.
        Raises ValueError if index is a slice and the length of new_value is
        less than the length of the slice or the slice step is not 1 or -1.
        '''
        if isinstance(index, int):
            # handle accessing negative indexes
            if index < 0:
                index += len(self)
            list.__setitem__(self, index, new_value)

            # if the object being placed in the Block has
            # a 'parent' attribute, set this block to it
            if hasattr(new_value, 'parent'):
                object.__setattr__(new_value, 'parent', self)

            desc = object.__getattribute__(self, 'desc')

            # if the new attribute is a Block, dont even try to set
            # its size. This is mainly because it will break the way
            # the readers build a Block. For example, if an empty array
            # is created and placed into a Block when the reader makes
            # it, and the parent Block sets its size, it'll change
            # the size to 0(since thats what its currently at).
            # When the reader tries to build the number of
            # entries its size says to, it wont make any.
            if isinstance(new_value, Block):
                return

            try:
                # set the size of the attribute
                self.set_size(None, index)
            except (NotImplementedError, AttributeError,
                    DescEditError, DescKeyError):
                pass
            if not isinstance(desc.get(SIZE, 0), int):
                # set the size of this Block
                self.set_size()

        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step

            assert hasattr(new_value, '__iter__'), (
                "must assign iterable to extended slice")

            slice_size = (stop - start)//step

            if step != -1 and slice_size > len(new_value):
                raise ValueError("attempt to assign sequence of size " +
                                 "%s to extended slice of size %s" %
                                 (len(new_value), slice_size))

            list.__setitem__(self, index, new_value)
            __osa__ = object.__setattr__
            for block in new_value:
                # if the objects being placed in the Block have
                # 'parent' attributes, set them to this Block.
                if hasattr(block, 'parent'):
                    __osa__(block, 'parent', self)

            set_size = self.set_size
            desc = object.__getattribute__(self, 'desc')

            # update the size of each attribute set to this Block
            for i in range(start, stop):
                try:
                    set_size(None, i)
                except (NotImplementedError, AttributeError,
                        DescEditError, DescKeyError):
                    pass

            # update the size of this Block
            if not isinstance(desc.get(SIZE, 0), int):
                set_size()
        else:
            self.__setattr__(index, new_value)

    def __delitem__(self, index):
        '''
        Deletes attributes from this Block located in index.
        index may be the string name of an attribute, a slice, or an integer.

        If index is an int or slice, calls:
            list.__delitem__(self, index)
        If index is neither, calls:
            self.__delattr__(index)

        If index is a slice or int, this ListBlocks set_size will be called
        for each of the indexes being deleted to set their sizes to 0.

        Calls self.del_desc(index) to delete the removed elements descriptor.
        If index is a slice, calls self.del_desc(i) for each i in the slice.

        If this ListBlocks descriptor has a SIZE entry that is not an int, its
        set_size method will be called with no arguments to update its size.
        '''
        if isinstance(index, int):
            # handle accessing negative indexes
            if index < 0:
                index += len(self)

            # set the size of the block to 0 since it's being deleted
            try:
                self.set_size(0, index)
            except (NotImplementedError, AttributeError,
                    DescEditError, DescKeyError):
                pass

            # set the size of this Block
            if not isinstance(desc.get(SIZE, 0), int):
                self.set_size()

            self.del_desc(index)

            list.__delitem__(self, index)
        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step

            for i in range(start-1, stop-1, step):
                # set the size of the block to 0 since it's being deleted
                try:
                    self.set_size(0, i)
                except (NotImplementedError, AttributeError,
                        DescEditError, DescKeyError):
                    pass

                self.del_desc(i)
                list.__delitem__(self, i)

            # set the size of this Block
            if not isinstance(desc.get(SIZE, 0), int):
                self.set_size()
        else:
            self.__delattr__(index)

    def __binsize__(self, block, substruct=False):
        '''Does NOT protect against recursion'''
        size = 0
        if isinstance(block, Block):
            field = object.__getattribute__(block, 'desc')['TYPE']
            if field.name == 'Void':
                return 0

            if field.is_struct:
                if field.is_bit_based:
                    # return the size of this bit_struct
                    # since the block contains no substructs
                    if substruct:
                        return 0
                    return block.get_size()
                elif not substruct:
                    # get the size of this structure if it's not a substruct
                    size = block.get_size()
                    substruct = True

            # loop for each of the attributes
            for i in range(len(block)):
                sub_block = block[i]
                if isinstance(sub_block, Block):
                    size += sub_block.__binsize__(sub_block, substruct)
                elif not substruct:
                    size += block.get_size(i)

            # add the size of the child
            if hasattr(block, 'CHILD'):
                child = object.__getattribute__(block, 'CHILD')
                if isinstance(child, Block):
                    size += child.__binsize__(child)
                else:
                    size += block.get_size('CHILD')
        return size

    def append(self, new_attr, new_desc=None):
        '''
        Appends new_attr to this ListBlock and adds new_desc to self.desc
        using the index new_attr will be located in as the key.

        new_desc will be added to self.desc using the self.ins_desc method.
        If new_desc is None, new_attr.desc will be used(if it exists).

        Is self.TYPE.is_struct is True, this ListBlocks set_size method will
        be called to update the size of the ListBlock after it is appended to.
        If new_attr has an attribute named 'parent', it will be set to
        this ListBlock after it is appended.

        Raises AttributeError is new_desc is not provided and
        new_attr does not have an attribute named 'desc'.
        '''
        # create a new, empty index
        list.append(self, None)

        # if the new_attr has its own descriptor, use that if not provided one
        if new_desc is None:
            try:
                new_desc = new_attr.desc
            except Exception:
                pass

        if new_desc is None:
            list.__delitem__(self, -1)
            raise AttributeError(("Descriptor was not provided and could " +
                                  "not locate descriptor in object of type " +
                                  "%s\nCannot append without a descriptor " +
                                  "for the new item.") % type(new_attr))

        # try and insert the new descriptor and set the new attribute value,
        # raise the last error if it fails and remove the new empty index
        try:
            list.__setitem__(self, -1, new_attr)
            self.ins_desc(len(self) - 1, new_desc)
            if object.__getattribute__(self, 'desc')['TYPE'].is_struct:
                # increment the size of the struct
                # by the size of the new attribute
                self.set_size(self.get_size() + self.get_size(len(self) - 1))
        except Exception:
            list.__delitem__(self, -1)
            raise

        # if the object being placed in the ListBlock
        # has a 'parent' attribute, set this block to it
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def extend(self, new_attrs):
        '''
        Extends this ArrayBlock with new_attrs.

        new_attrs must be an instance of ListBlock

        Each element in new_attrs will be appended
        to this ListBlock using its append method.

        Raises TypeError if new_attrs is not an instance of ListBlock.
        '''
        if isinstance(new_attrs, ListBlock):
            desc = new_attrs.desc
            for i in range(desc['ENTRIES']):
                self.append(new_attrs[i], desc[i])
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of ListBlock or int, not %s" %
                            type(new_attrs))

    def index_by_id(self, block):
        '''
        Checks the id of every entry in this ListBlock to locate
        which index 'block' is in. This differs from list.index
        as it selects a match by id(block) rather than content.

        Returns the index that 'block' is in.
        Raises ValueError if 'block' can not be found.
        '''
        return [id(list.__getitem__(self, i)) for
                i in range(len(self))].index(id(block))

    def insert(self, index, new_attr=None, new_desc=None):
        '''
        Allows inserting objects into this ListBlock while
        taking care of all descriptor related details.
        Function may be called with only "index" if this block type is a Array.
        Doing so will insert a fresh structure to the array at "index"
        (as defined by the Array's SUB_STRUCT descriptor value)
        '''

        # create a new, empty index
        list.insert(self, index, None)
        desc = object.__getattribute__(self, 'desc')

        # if the new_attr has its own descriptor,
        # use that instead of any provided one
        try:
            new_desc = new_attr.desc
        except Exception:
            pass

        if new_desc is None:
            list.__delitem__(self, index)
            raise AttributeError(("Descriptor was not provided and could " +
                                  "not locate descriptor in object of type " +
                                  "%s\nCannot append without a descriptor " +
                                  "for the new item.") % type(new_attr))

        # try and insert the new descriptor and set the new
        # attribute value, raise the last error if it fails
        try:
            list.__setitem__(self, index, new_attr)
            self.ins_desc(index, new_desc)
        except Exception:
            list.__delitem__(self, index)
            raise

        # if the object being placed in the ListBlock
        # has a 'parent' attribute, set this block to it
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def pop(self, index=-1):
        '''
        Pops 'index' out of this Block.
        index may be either the string name of an attribute or an int.

        Returns a tuple containing it and its descriptor.

        self.del_desc(index) will be called to remove the descriptor
        of the specified attribute from self.desc

        Raises TypeError if index is not an int or string
        Raises AttributeError if index cannot be found in self.desc['NAME_MAP']
        '''
        desc = object.__getattribute__(self, "desc")

        if isinstance(index, int):
            if index < 0:
                index += len(self)
            attr = list.pop(self, index)
            desc = desc[index]
            self.del_desc(index)
        elif index in desc['NAME_MAP']:
            i = desc['NAME_MAP'][index]
            attr = list.pop(self, i)
            desc = desc[i]
            self.del_desc(index)
        elif isinstance(index, str):
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get(NAME, UNNAMED), type(self), index))
        else:
            raise TypeError("index must be an instance of %s or %s, not %s" %
                            (int, str, type(index)))
        return(attr, desc)

    def get_size(self, attr_index=None, **context):
        '''
        Returns the size of self[attr_index] or self if attr_index == None.
        Checks the data type and descriptor for the size.

        Size units are dependent on the data type being measured.
        Variables and structs will be measured in bytes and
        arrays and containers will be measured in entries.
        The descriptor may specify size in terms of already parsed fields.
        '''
        self_desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, int):
            block = self[attr_index]
            desc = self_desc[attr_index]
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)
            # try to get the size directly from the block
            try:
                desc = block.desc
            except Exception:
                # if that fails, try to get it from the desc of the parent
                try:
                    desc = self_desc[self_desc['NAME_MAP'][attr_index]]
                except Exception:
                    desc = self_desc[attr_index]
        else:
            desc = self_desc
            block = self

        # determine how to get the size
        if 'SIZE' in desc:
            size = desc['SIZE']

            if isinstance(size, int):
                return size
            elif isinstance(size, str):
                # get the pointed to size data by traversing the tag
                # structure along the path specified by the string
                return self.get_neighbor(size, block)
            elif hasattr(size, '__call__'):
                # find the pointed to size data by calling the function
                try:
                    return size(attr_index=attr_index, parent=block.parent,
                                block=block, **context)
                except AttributeError:
                    return size(attr_index=attr_index, parent=self,
                                block=block, **context)

            self_name = self_desc.get('NAME', UNNAMED)
            if isinstance(attr_index, (int, str)):
                self_name = attr_index
            raise TypeError(("size specified in '%s' is not a valid type." +
                             "\nExpected int, str, or function. Got %s.") %
                            (self_name, type(size)))
        # use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(block)

    def set_size(self, new_value=None, attr_index=None, **context):
        '''
        Sets the size of this Block to 'new_value' using the SIZE entry
        in the descriptor. If 'attr_index' is not None, uses the descriptor
        of the attribute 'attr_index'. If the attribute has a descriptor,
        uses its descriptor instead of the one in self.desc[attr_index]

        If new_value isnt supplied, uses the value returned by the
        sizecalc method of the TYPE entry in the descriptor.
        If attr_index is None, calculates the size of this Block,
        otherwise calculates the size of the specified attribute.

        If the SIZE entry is a string, the size will be set with:
            self.set_neighbor(pathstring, new_value, block)
        where 'block' is this Block(or its attribute if attr_index is not
        None), and pathstring is the value in the descriptor under 'SIZE'.

        If the SIZE entry is a function, 

        If attr_index is an int, sets the size of self[attr_index].
        If attr_index is a str, sets the size of self.__getattr__(attr_index).

        Raises a DescEditError if the descriptor 'SIZE' entry is an int



        FINISH WRITING THIS DOCSTRING



        Size units are dependent on the data type being measured.
        Variables and structs will be measured in bytes and
        arrays and containers will be measured in entries.
        The descriptor may specify size in terms of already parsed fields.
        '''

        self_desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, int):
            block = self[attr_index]
            desc = self_desc[attr_index]
            size = desc.get('SIZE')
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)

            error_num = 0
            # try to get the size directly from the block
            try:
                desc = block.desc
                size = desc['SIZE']
            except Exception:
                # if that fails, try to get it from the desc of the parent
                try:
                    desc = self_desc[self_desc['NAME_MAP'][attr_index]]
                except Exception:
                    desc = self_desc[attr_index]

                try:
                    size = desc['SIZE']
                except Exception:
                    # its parent cant tell us the size, raise this error
                    error_num = 1
                    if 'TYPE' in desc and not desc['TYPE'].is_var_size:
                        # the size is not variable so it cant be set
                        # without changing the type. raise this error
                        error_num = 2

            attr_name = desc.get('NAME', UNNAMED)
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            if error_num == 1:
                raise DescKeyError(("Could not determine size for " +
                                    "attribute '%s' in block '%s'.") %
                                   (attr_name, object.__getattribute__
                                    (self, 'desc')['NAME']))
            elif error_num == 2:
                raise DescKeyError(("Can not set size for attribute '%s' " +
                                    "in block '%s'.\n'%s' has a fixed " +
                                    "size of '%s'.\nTo change the size of " +
                                    "'%s' you must change its Field.") %
                                   (attr_name, object.__getattribute__
                                    (self, 'desc')['NAME'], desc['TYPE'],
                                    desc['TYPE'].size, attr_name))
        else:
            block = self
            desc = self_desc
            size = desc.get('SIZE')

        field = desc['TYPE']

        # raise exception if the size is None
        if size is None:
            attr_name = desc.get('NAME', UNNAMED)
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            raise DescKeyError("'SIZE' does not exist in '%s'." % attr_name)

        # if a new size wasnt provided then it needs to be calculated
        if new_value is not None:
            newsize = new_value
        elif hasattr(block, 'parent'):
            newsize = field.sizecalc(parent=block.parent, block=block,
                                     attr_index=attr_index)
        else:
            newsize = field.sizecalc(parent=self, block=block,
                                     attr_index=attr_index)

        if isinstance(size, int):
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if new_value is None and newsize <= size:
                return
            raise DescEditError("Changing a size statically defined in a " +
                                "descriptor is not supported through " +
                                "set_size. Use the 'set_desc' method instead.")
        elif isinstance(size, str):
            # set size by traversing the tag structure
            # along the path specified by the string
            self.set_neighbor(size, newsize, block)
            return
        elif hasattr(size, '__call__'):
            # set size by calling the provided function
            if hasattr(block, 'parent'):
                size(attr_index=attr_index, new_value=newsize,
                     parent=block.parent, block=block, **context)
            else:
                size(attr_index=attr_index, new_value=newsize,
                     parent=self, block=block, **context)
            return

        self_name = self_desc['NAME']
        if isinstance(attr_index, (int, str)):
            self_name = attr_index

        raise TypeError(("size specified in '%s' is not a valid type." +
                         "\nExpected int, str, or function. Got %s.\n") %
                        (self_name, type(size)))

    def collect_pointers(self, offset=0, seen=None, pointed_blocks=None,
                         substruct=False, root=False, attr_index=None):
        '''
        '''
        if seen is None:
            seen = set()

        if attr_index is None:
            desc = object.__getattribute__(self, 'desc')
            block = self
        else:
            desc = self.get_desc(attr_index)
            block = self.__getitem__(attr_index)

        if id(block) in seen:
            return offset

        if 'POINTER' in desc:
            pointer = desc['POINTER']
            if isinstance(pointer, int):
                # if the next blocks are to be located directly after
                # this one then set the current offset to its location
                offset = pointer

            # if this is a block within the root block
            if not root:
                pointed_blocks.append((self, attr_index, substruct))
                return offset

        field = desc['TYPE']
        if field.is_block:
            seen.add(id(block))

        if desc.get('ALIGN'):
            align = desc['ALIGN']
            offset += (align - (offset % align)) % align

        # increment the offset by this blocks size if it isn't a substruct
        if not(substruct or field.is_container):
            offset += self.get_size(attr_index)
            substruct = True

        # If the block isn't a Block it means that this is being run
        # on a non-Block that happens to have its location specified by
        # pointer. The offset must still be incremented by the size of this
        # block, but the block can't contain other blocks, so return early.
        if not field.is_block:
            return offset

        if hasattr(self, 'CHILD'):
            indexes = list(range(len(self)))
            indexes.append('CHILD')
        else:
            indexes = range(len(self))

        align = 0

        for i in indexes:
            block = self[i]
            if isinstance(block, Block):
                # if "i" is an integer it means this object still
                # exists within the structure, or is "substruct".
                # If it isn't it means its a linked block, which
                # (as of writing this) means its a child block.
                offset = block.collect_pointers(offset, seen, pointed_blocks,
                                                (isinstance(i, int) and
                                                 substruct), False)
            elif not substruct and isinstance(i, int):
                # It's pointless to check if this block is in seen
                # or not because the block may be an integer, float,
                # or string that is shared across multiple blocks.
                # The check would succeed or fail at random.
                b_desc = desc[i]
                align = b_desc.get('ALIGN')

                pointer = b_desc.get('POINTER')
                if isinstance(pointer, int):
                    offset = pointer
                elif pointer is not None:
                    # if the block has a variable pointer, add it to the
                    # list and break early so its id doesnt get added
                    pointed_blocks.append((self, i, substruct))
                    continue
                elif align:
                    # align the block
                    offset += (align - (offset % align)) % align

                # add the size of the block to the current offset
                offset += self.get_size(i)
                seen.add(id(block))
        return offset

    def rebuild(self, **kwargs):
        '''
        '''
        attr_index = kwargs.pop('attr_index', None)
        desc = object.__getattribute__(self, "desc")

        rawdata = get_rawdata(**kwargs)

        if attr_index is not None:
            # reading/initializing just one attribute
            if isinstance(attr_index, str):
                attr_index = desc['NAME_MAP'][attr_index]

            attr_desc = desc[attr_index]

            if 'initdata' in kwargs:
                # if initdata was provided for this attribute
                # then just place it in this WhileBlock.
                self[attr_index] = kwargs['initdata']
            else:
                # we are either reading the attribute from rawdata or nothing
                kwargs.update(desc=attr_desc, parent=self, rawdata=rawdata,
                              attr_index=attr_index)
                kwargs.pop('filepath', None)
                attr_desc['TYPE'].reader(**kwargs)
            return
        else:
            # reading/initializing all attributes, so clear the block
            # and create as many elements as it needs to hold
            list.__init__(self, [None]*desc['ENTRIES'])

        if rawdata is not None:
            # rebuild the ListBlock from raw data
            try:
                # we are either reading the attribute from rawdata or nothing
                kwargs.update(desc=desc, parent=self, rawdata=rawdata)
                kwargs.pop('filepath', None)
                desc['TYPE'].reader(**kwargs)
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
            # initialize the attributes
            for i in range(len(self)):
                desc[i]['TYPE'].reader(desc[i], self, None, i)

            # Only initialize the child if the block has a child
            c_desc = desc.get('CHILD')
            if c_desc:
                c_desc['TYPE'].reader(c_desc, self, None, 'CHILD')

        # if an initdata was provided, make sure it can be used
        initdata = kwargs.get('initdata')
        assert (initdata is None or
                (hasattr(initdata, '__iter__') and
                 hasattr(initdata, '__len__'))), (
                     "initdata must be an iterable with a length")

        if initdata is not None:
            if isinstance(initdata, Block):
                # copy the attributes from initdata into self
                # by name for each of the attributes, but do
                # this only if the name exists in both blocks
                i_name_map = initdata.desc.get(NAME_MAP, ())
                name_map = desc.get(NAME_MAP, ())

                for name in i_name_map:
                    if name in name_map:
                        self[name_map[name]] = initdata[i_name_map[name]]

                # if the initdata has a CHILD block, copy it to
                # this block if this block can hold a CHILD.
                try:
                    self.CHILD = initdata.CHILD
                except AttributeError:
                    pass
            else:
                # loop over the ListBlock and copy the entries
                # from initdata into the ListBlock. Make sure to
                # loop as many times as the shortest length of the
                # two so as to prevent IndexErrors.'''
                for i in range(min(len(self), len(initdata))):
                    self[i] = initdata[i]


class PListBlock(ListBlock):
    '''
    This ListBlock allows a reference to the child
    block it describes to be stored as well as a
    reference to whatever block it is parented to.
    '''
    __slots__ = ('CHILD')

    def __init__(self, desc, parent=None, child=None, **kwargs):
        '''
        Initializes a PListBlock. Sets its desc, parent,
        and CHILD to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'CHILD', 'NAME_MAP', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'CHILD' in desc and
                'NAME_MAP' in desc and 'ENTRIES' in desc)

        object.__setattr__(self, 'desc',   desc)
        object.__setattr__(self, 'CHILD',  child)
        object.__setattr__(self, 'parent', parent)

        if kwargs:
            self.rebuild(**kwargs)

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this PListBlock, all its
        attributes, and all its list elements take up in memory.

        If this Blocks descriptor is unique(denoted by it having an
        'ORIG_DESC' key) then the size of the descriptor and all its
        entries will be included in the byte size total.

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
        bytes_total = list.__sizeof__(self)

        if hasattr(self, 'CHILD'):
            child = object.__getattribute__(self, 'CHILD')
            if isinstance(child, Block):
                bytes_total += child.__sizeof__(seenset)
            else:
                seenset.add(id(child))
                bytes_total += getsizeof(child)

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

        for i in range(len(self)):
            item = list.__getitem__(self, i)
            if not id(item) in seenset:
                if isinstance(item, Block):
                    bytes_total += item.__sizeof__(seenset)
                else:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def __setattr__(self, attr_name, new_value):
        '''
        '''
        try:
            object.__setattr__(self, attr_name, new_value)
            if attr_name == 'CHILD':
                field = object.__getattribute__(self, 'desc')['CHILD']['TYPE']
                if field.is_var_size and field.is_data:
                    # try to set the size of the attribute
                    try:
                        self.set_size(None, 'CHILD')
                    except(NotImplementedError, AttributeError,
                           DescEditError, DescKeyError):
                        pass

                # if this object is being given a child then try to
                # automatically give the child this object as a parent
                try:
                    if object.__getattribute__(new_value, 'parent') != self:
                        object.__setattr__(new_value, 'parent', self)
                except Exception:
                    pass
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                self.__setitem__(desc['NAME_MAP'][attr_name], new_value)
            elif attr_name in desc:
                self.set_desc(attr_name, new_value)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        '''
        '''
        try:
            object.__delattr__(self, attr_name)
            if attr_name == 'CHILD':
                # set the size of the block to 0 since it's being deleted
                try:
                    self.set_size(0, 'CHILD')
                except(NotImplementedError, AttributeError,
                       DescEditError, DescKeyError):
                    pass
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                # set the size of the block to 0 since it's being deleted
                try:
                    self.set_size(0, attr_name=attr_name)
                except(NotImplementedError, AttributeError,
                       DescEditError, DescKeyError):
                    pass
                self.del_desc(attr_name)
                list.__delitem__(self, desc['NAME_MAP'][attr_name])
            elif attr_name in desc:
                self.del_desc(attr_name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

ListBlock.PARENTABLE = PListBlock
ListBlock.UNPARENTABLE = ListBlock

PListBlock.PARENTABLE = PListBlock
PListBlock.UNPARENTABLE = ListBlock
