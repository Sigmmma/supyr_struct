from copy import deepcopy
from .list_block import *


class ArrayBlock(ListBlock):
    """
    ArrayBlocks are similar to ListBlocks, except that while they
    are able to store a NAME_MAP to give alias's to each list index,
    they are intended to store arrays of identical structures.
    The arrayed descriptors are stored in the SUB_STRUCT descriptor entry.
    """

    __slots__ = ()

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes an ArrayBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'SUB_STRUCT', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'SUB_STRUCT' in desc and 'ENTRIES' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, 'parent', parent)

        if kwargs:
            self.rebuild(**kwargs)

    def __sizeof__(self, seenset=None):
        '''docstring'''
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

        __lgi__ = list.__getitem__
        if desc['SUB_STRUCT']['TYPE'].is_block:
            # the entries in this ArrayBlock are Blocks, so call
            # their __getsize__ method directly with the seenset
            for i in range(len(self)):
                item = __lgi__(self, i)
                if not id(item) in seenset:
                    bytes_total += item.__sizeof__(seenset)
        else:
            for i in range(len(self)):
                item = __lgi__(self, i)
                if not id(item) in seenset:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def __setitem__(self, index, new_value):
        '''
        Places 'new_value' into this Block at 'index'.
        index may be the string name of an attribute.

        If 'index' is a string, calls:
            self.__setattr__(index, new_value)
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
        elif isinstance(index, slice):
            # if this is an array, dont worry about
            # the descriptor since its list indexes
            # aren't attributes, but instanced objects
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step

            assert hasattr(new_value, '__iter__'), ("must assign iterable " +
                                                    "to extended slice")

            slice_size = (stop - start)//step

            if step != -1 and slice_size > len(new_value):
                raise ValueError("attempt to assign sequence of size " +
                                 "%s to extended slice of size %s" %
                                 (len(new_value), slice_size))

            list.__setitem__(self, index, new_value)
            try:
                self.set_size()
            except (NotImplementedError, AttributeError,
                    DescEditError, DescKeyError):
                pass
        else:
            self.__setattr__(index, new_value)

    def __delitem__(self, index):
        '''
        Deletes an attribute from this Block located in 'index'.
        index may be the string name of an attribute.

        If 'index' is a string, calls:
            self.__delattr__(index)
        '''
        if isinstance(index, int):
            # handle accessing negative indexes
            if index < 0:
                index += len(self)
            self.set_size()
            list.__delitem__(self, index)
        elif isinstance(index, slice):
            # if this is an array, dont worry about
            # the descriptor since its list indexes
            # aren't attributes, but instanced objects
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step

            self.set_size()
            list.__delitem__(self, index)
        else:
            self.__delattr__(index)

    def append(self, new_attr=None):
        '''Allows appending objects to this Block while taking
        care of all descriptor related details.
        Function may be called with no arguments if this block type is
        an Array. Doing so will append a fresh structure to the array
        (as defined by the Array's SUB_STRUCT descriptor value).'''

        # get the index we'll be appending into
        index = len(self)
        # create a new, empty index
        list.append(self, None)

        desc = object.__getattribute__(self, 'desc')

        try:
            # if this block is an array and "new_attr" is None
            # then it means to append a new block to the array
            if new_attr is None:
                attr_desc = desc['SUB_STRUCT']

                attr_desc['TYPE'].reader(attr_desc, self, None, index)
                self.set_size()
                # finished, so return
                return
        except Exception:
            list.__delitem__(self, index)
            raise

        # try and insert the new descriptor and set the new attribute value,
        # raise the last error if it fails and remove the new empty index
        try:
            list.__setitem__(self, index, new_attr)

            # set the new size of the array
            self.set_size()
        except Exception:
            list.__delitem__(self, index)
            raise

        # if the object being placed in the ArrayBlock
        # has a 'parent' attribute, set this block to it
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def extend(self, new_attrs):
        '''
        '''
        if hasattr(new_attrs, '__iter__'):
            for attr in new_attrs:
                self.append(attr)
        elif isinstance(new_attrs, int):
            # if "new_attr" is an int it means that we are
            # supposed to append this many of the SUB_STRUCT
            attr_desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
            attr_field = attr_desc['TYPE']

            # get the index we'll be inserting entries into
            index = len(self)

            # create new, empty indices
            list.extend(self, [None]*new_attrs)

            # read new sub_structs into the empty indices
            for i in range(index, index + new_attrs):
                attr_field.reader(attr_desc, self, None, i)

            # set the new size of this ArrayBlock
            self.set_size()
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of ArrayBlock or int, not %s" %
                            type(new_attrs))

    def insert(self, index, new_attr=None, new_desc=None):
        '''
        '''

        # create a new, empty index
        list.insert(self, index, None)
        desc = object.__getattribute__(self, 'desc')

        # if this block is an array and "new_attr" is None
        # then it means to append a new block to the array
        new_desc = desc['SUB_STRUCT']
        new_field = new_desc['TYPE']

        # if the Field is a Block then we can
        # create one and just append it to the array
        if new_attr is None and new_field.is_block:
            new_field.reader(new_desc, self, None, index)
            self.set_size()
            # finished, so return
            return

        # try and insert the new descriptor and set the new
        # attribute value, raise the last error if it fails
        try:
            list.__setitem__(self, index, new_attr)
            # set the newsize of the array
            self.set_size()
        except Exception:
            list.__delitem__(self, index)
            raise

        # if the object being placed in the ArrayBlock
        # has a 'parent' attribute, set this block to it
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def pop(self, index=-1):
        '''
        Pops 'index' out of this Block.
        index may be the string name of an attribute.

        Returns a tuple containing it and its descriptor.
        '''
        desc = object.__getattribute__(self, "desc")

        if isinstance(index, int):
            if index < 0:
                index += len(self)
            attr = list.pop(self, index)

            # if this is an array, dont worry about the descriptor since
            # its list indexes aren't attributes, but instanced objects
            desc = desc['SUB_STRUCT']
            self.set_size()
        elif index in desc['NAME_MAP']:
            attr = list.pop(self, desc['NAME_MAP'][index])
            desc = self.get_desc(index)
            self.del_desc(index)
        else:
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get(NAME, UNNAMED), type(self), index))
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
            desc = self_desc['SUB_STRUCT']
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
            desc = self_desc['SUB_STRUCT']
            size = desc.get('SIZE')
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)

            error_num = 0
            # try to get the size directly from the block
            try:
                desc = block.desc[attr_index]
                size = desc['SIZE']
            except Exception:
                # if that fails, try to get it from the desc of the parent
                try:
                    desc = self_desc[attr_index]
                except Exception:
                    desc = self_desc[self_desc['NAME_MAP'][attr_index]]

                try:
                    size = desc['SIZE']
                except Exception:
                    # its parent cant tell us the size, raise this error
                    error_num = 1

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
        '''docstring'''
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
            if isinstance(pointer, int) and desc.get('CARRY_OFF', True):
                # if the next blocks are to be located directly after
                # this one then set the current offset to its location
                offset = pointer

            # if this is a block within the root block
            if not root:
                pointed_blocks.append((self, attr_index, substruct))
                return offset

        field = desc['TYPE']
        b_desc = desc['SUB_STRUCT']
        if field.is_block:
            seen.add(id(block))

        # align the start of the array of structs
        align = desc.get('ALIGN', 1)
        offset += (align - (offset % align)) % align

        if hasattr(self, 'CHILD'):
            indexes = list(range(len(self)))
            indexes.append('CHILD')
        else:
            indexes = range(len(self))

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
                pointer = b_desc.get('POINTER')
                if pointer is not None:
                    if not isinstance(pointer, int):
                        # if the block has a variable pointer, add it to the
                        # list and break early so its id doesnt get added
                        pointed_blocks.append((self, i, substruct))
                        continue
                    elif b_desc.get('CARRY_OFF'):
                        offset = pointer
                # add the size of the block to the current offset
                offset += self.get_size(i)
                seen.add(id(block))
        return offset

    def rebuild(self, **kwargs):
        '''This function will initialize all of a ListBlocks attributes to
        their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

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
            # reading/initializing all array elements, so clear the block
            list.__init__(self, [None]*self.get_size())

        if rawdata is not None:
            # rebuild the ArrayBlock from raw data
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

            try:
                attr_desc = desc['SUB_STRUCT']
                attr_field = attr_desc['TYPE']
            except Exception:
                raise TypeError("Could not locate the sub-struct " +
                                "descriptor.\nCould not initialize array")

            # loop through each element in the array and initialize it
            for i in range(len(self)):
                attr_field.reader(attr_desc, self, None, i)

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
                # loop over the ArrayBlock and copy the entries
                # from initdata into the ArrayBlock. Make sure to
                # loop as many times as the shortest length of the
                # two so as to prevent IndexErrors.'''
                for i in range(min(len(self), len(initdata))):
                    self[i] = initdata[i]


class PArrayBlock(ArrayBlock):
    '''This ArrayBlock allows a reference to the child
    block it describes to be stored as well as a
    reference to whatever block it is parented to'''
    __slots__ = ('CHILD')

    def __init__(self, desc, parent=None, child=None, **kwargs):
        '''
        Initializes a PListBlock. Sets its desc, parent,
        and CHILD to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'CHILD', 'SUB_STRUCT', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'CHILD' in desc and
                'SUB_STRUCT' in desc and 'ENTRIES' in desc)

        object.__setattr__(self, 'desc',   desc)
        object.__setattr__(self, 'CHILD',  child)
        object.__setattr__(self, 'parent', parent)

        if kwargs:
            self.rebuild(**kwargs)

    def __sizeof__(self, seenset=None):
        '''docstring'''
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

        __lgi__ = list.__getitem__
        if desc['SUB_STRUCT']['TYPE'].is_block:
            # the entries in this ArrayBlock are Blocks, so call
            # their __getsize__ method directly with the seenset
            for i in range(len(self)):
                item = __lgi__(self, i)
                if not id(item) in seenset:
                    bytes_total += item.__sizeof__(seenset)
        else:
            for i in range(len(self)):
                item = __lgi__(self, i)
                if not id(item) in seenset:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)

        return bytes_total

    def __setattr__(self, attr_name, new_value):
        '''docstring'''
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
        '''docstring'''
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

ArrayBlock.PARENTABLE = PArrayBlock
PArrayBlock.UNPARENTABLE = ArrayBlock
