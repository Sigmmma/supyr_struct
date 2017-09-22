'''
A module that implements WhileBlock and PWhileBlock, subclasses of ArrayBlock.
WhileBlocks are used where an array is needed which does not have a size
stored anywhere and must be parsed until some function says to stop.
'''
from .array_block import *


class WhileBlock(ArrayBlock):
    '''
    A Block class meant to be used with fields that have an
    open ended size which must be deduced while parsing it.

    WhileBlocks function identically to ArrayBlocks, except that
    all code regarding setting their size has been removed.
    This is because WhileArrays are designed to only be used for
    fields that are open-ended and dont store their size anywhere.

    For example, WhileBlocks are used with WhileArrays, which continue
    to build array entries until a "case" function returns False.
    '''
    __slots__ = ()

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
            # if the object being placed in the Block is itself
            # a Block, set its parent attribute to this Block.
            if isinstance(new_value, Block):
                new_value.parent = self

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
            for node in new_value:
                # if the object being placed in the Block is itself
                # a Block, set its parent attribute to this Block.
                if isinstance(node, Block):
                    node.parent = self
        else:
            self.__setattr__(index, new_value)

    def __delitem__(self, index):
        '''
        Deletes an attribute from this Block located in 'index'.
        index may be the string name of an attribute.

        If 'index' is a string, calls:
            self.__delattr__(index)
        '''
        if isinstance(index, str):
            self.__delattr__(index)
            return
        elif isinstance(index, int) and index < 0:
            index += len(self)
        list.__delitem__(self, index)

    def append(self, new_attr=None, new_desc=None, **kwargs):
        '''
        Appends new_attr to this WhileBlock.

        If new_attr is None or not provided, this method will create
        an empty index on the end of the array and run the parser
        function of new_desc['TYPE'] to create a new default
        object of the proper python type to place in it.

        If new_desc is not provided, uses self.desc['SUB_STRUCT'] as it.
        '''
        # create a new, empty index
        list.append(self, new_attr)

        # if this Block is an array and "new_attr" is None
        # then it means to append a new node to the array
        if new_attr is None:
            if new_desc is None:
                new_desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
            new_desc['TYPE'].parser(new_desc, parent=self,
                                    attr_index=len(self) - 1, **kwargs)
            return

        # if the object being placed in the Block is itself
        # a Block, set its parent attribute to this Block.
        if isinstance(new_attr, Block):
            new_attr.parent = self

    def extend(self, new_attrs, **kwargs):
        '''
        Extends this Block with 'new_attrs'.

        If new_attrs is a ListBlock, calls the below code:
            desc = new_attrs.desc[SUB_STRUCT]
            for i in range(len(new_attrs)):
                self.append(new_attrs[i], desc)

        If new_attrs is an int, appends 'new_attrs' count of new nodes
        defined by the descriptor in:  self.desc[SUB_STRUCT].
        '''
        if isinstance(new_attrs, ListBlock):
            assert SUB_STRUCT in new_attrs.desc, (
                'Can only extend a WhileArray with another array type Block.')
            for node in new_attrs:
                self.append(node)

        elif isinstance(new_attrs, int):
            # if this Block is an array and "new_attr" is an int it means
            # that we are supposed to append this many of the SUB_STRUCT
            for i in range(new_attrs):
                self.append(**kwargs)
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of ListBlock or int, not %s" %
                            type(new_attrs))

    def insert(self, index, new_attr=None, new_desc=None, **kwargs):
        '''
        Inserts 'new_attr' into this Block at 'index'.
        index may be the string name of an attribute.

        If new_attr is None, inserts a new node defined by new_desc.
        If new_desc is None, uses self.desc[SUB_STRUCT] as new_desc.
        '''
        # create a new, empty index
        list.insert(self, index, new_attr)

        if new_attr is None:
            if new_desc is None:
                new_desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
            new_desc['TYPE'].parser(new_desc, parent=self,
                                    attr_index=index, **kwargs)
            # finished, so return
            return

        # if the object being placed in the Block is itself
        # a Block, set its parent attribute to this Block.
        if isinstance(new_attr, Block):
            new_attr.parent = self

    def pop(self, index=-1):
        '''
        Pops 'index' out of this Block.
        index may be the string name of an attribute.

        Returns a tuple containing it and its descriptor.
        '''
        desc = object.__getattribute__(self, "desc")

        if isinstance(index, int):
            if index < 0:
                return (list.pop(self, index + len(self)), desc['SUB_STRUCT'])
            return (list.pop(self, index), desc['SUB_STRUCT'])
        elif index in desc.get('NAME_MAP', ()):
            return (list.pop(self, desc['NAME_MAP'][index]),
                    self.get_desc('SUB_STRUCT'))

        raise AttributeError("'%s' of type %s has no attribute '%s'" %
                             (desc.get(NAME, UNNAMED), type(self), index))

    def set_size(self, new_value=None, attr_index=None, **context):
        '''
        Sets the size of the 'attr_index' element in this Block to
        'new_value' using the SIZE entry in self.desc[attr_index].
        If the attribute itself has a descriptor, uses its
        descriptor instead of the one in self.desc[attr_index]

        If 'new_value' isnt supplied, calculates it using the
        sizecalc method of the 'TYPE' entry in the descriptor.

        If the SIZE entry is a string, the size will be set using
        self.set_neighbor and providing the SIZE entry as the nodepath.

        If the SIZE entry is a function, the size will be set by doing:
            size_setter(attr_index=attr_index, new_value=new_value,
                        parent=self, node=node, **context)
        where size_setter is the function under the descriptors SIZE key,
        new_value is the calculated or provided value to set the size to,
        context is a dictionary of the remaining supplied keyword arguments,
        node is the attribute whose size is being set,
        and attr_index is the provided attr_index argument.

        If attr_index is an int, sets the size of self[attr_index].
        If attr_index is a str, sets the size of self.__getattr__(attr_index).
        If attr_index is None, this method will do nothing. This is because
        WhileBlocks are designed to express data which doesnt store a size.

        Raises DescEditError if the descriptor 'SIZE' entry
        is an int and the value the size is being set to is
        greater than what is currently in the descriptor.
        Raises DescKeyError if 'SIZE' doesnt exist in the descriptor.
        Raises TypeError if the 'SIZE' entry isnt an int, string, or function.
        '''
        self_desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, str):
            attr_index = self_desc['NAME_MAP'][attr_index]
        elif not isinstance(attr_index, int):
            # cant set size of WhileArrays
            return

        node = self[attr_index]
        # try to get the size directly from the node
        try:
            desc = node.desc
            size = self_desc['SIZE']
            error_num = 0
        except Exception:
            # if that fails, try to get it from the desc of the parent
            desc = self_desc[attr_index]

            try:
                size = desc['SIZE']
                error_num = 0
            except Exception:
                # its parent cant tell us the size, raise this error
                error_num = 1
                if 'TYPE' in desc and not desc['TYPE'].is_var_size:
                    # the size is not variable so it cant be set
                    # without changing the type. raise this error
                    error_num = 2

        if error_num:
            f_type = desc['TYPE']
            if error_num == 1:
                raise DescKeyError("Could not locate size for " +
                                   "attribute '%s' in block '%s'." %
                                   (desc.get('NAME', UNNAMED),
                                    self_desc.get('NAME', UNNAMED)))
            raise DescKeyError(("Can not set size for attribute " +
                                "'%s' in block '%s'.\n'%s' has a " +
                                "fixed size  of '%s'.\nTo change its " +
                                "size you must change its FieldType.") %
                               (desc.get('NAME', attr_index),
                                self_desc.get('NAME', UNNAMED),
                                f_type, f_type.size, attr_name))

        if isinstance(size, int):
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if new_value is None and newsize <= size:
                return
            raise DescEditError("Changing a size statically defined in a " +
                                "descriptor is not supported through " +
                                "set_size. Make a new descriptor instead.")

        # if a new size wasnt provided then it needs to be calculated
        if new_value is not None:
            newsize = new_value
        else:
            newsize = desc['TYPE'].sizecalc(parent=self, node=node,
                                            attr_index=attr_index, **context)

        if isinstance(size, str):
            # set size by traversing the tag structure
            # along the path specified by the string
            self.set_neighbor(size, newsize, node)
        elif hasattr(size, "__call__"):
            # set size by calling the provided function
            size(attr_index=attr_index, new_value=newsize,
                 parent=self, node=node, **context)
        else:
            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (desc.get('NAME', attr_index), type(size)) +
                            "Cannot determine how to set the size.")

    def parse(self, **kwargs):
        '''
        Parses this WhileBlock in the way specified by the keyword arguments.

        If rawdata or a filepath is supplied, it will be used to parse
        this WhileBlock. If not, and initdata is supplied, it will be
        used to replace the entries in this WhileBlock.

        If rawdata, initdata, filepath, and init_attrs are all unsupplied,
        all entries in this array will be deleted and replaced with new ones.

        If rawdata, initdata, and filepath are all unsupplied or
        None and init_attrs is False, this method will do nothing.

        If this WhileBlock also has a STEPTREE attribute, it will be
        initialized in the same way as the array elements.

        If attr_index is supplied, the initialization will only be
        done to only the specified attribute or array element.

        Raises AssertionError if attr_index is None and initdata
        does not have __iter__ or __len__ methods.
        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.

        Optional keywords arguments:
        # bool:
        init_attrs --- Whether or not to clear the contents of the WhileBlock.
                       Defaults to True. If True, and 'rawdata' and 'filepath'
                       are None, all the cleared array elements will be rebuilt
                       using the desciptor in this Blocks SUB_STRUCT entry.

        # buffer:
        rawdata ------ A peekable buffer that will be used for parsing
                       elements of this WhileBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the parser of each elements FieldType when
                       they are rebuilt using the given filepath or rawdata.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the parser of each elements FieldType when
                       they are rebuilt using the given filepath or rawdata.

        # int/str:
        attr_index --- The specific attribute index to initialize. Operates on
                       all indices if unsupplied or None. Defaults to None.

        # object:
        initdata ----- An iterable of objects to replace the contents of
                       this WhileBlock if attr_index is None.
                       If attr_index is not None, this is instead an object
                       to replace self[attr_index]

        #str:
        filepath ----- An absolute path to a file to use as rawdata to parse
                       this WhileBlock. If supplied, do not supply 'rawdata'.
        '''
        attr_index = kwargs.pop('attr_index', None)
        desc = object.__getattribute__(self, "desc")

        rawdata = get_rawdata(**kwargs)

        if attr_index is not None:
            # parsing/initializing just one attribute
            if isinstance(attr_index, str) and attr_index not in desc:
                attr_index = desc['NAME_MAP'][attr_index]

            attr_desc = desc[attr_index]

            if 'initdata' in kwargs:
                # if initdata was provided for this attribute
                # then just place it in this WhileBlock.
                self[attr_index] = kwargs['initdata']
            elif rawdata or kwargs.get('init_attrs', False):
                # we are either parsing the attribute from rawdata or nothing
                kwargs.update(desc=attr_desc, parent=self,
                              rawdata=rawdata, attr_index=attr_index)
                kwargs.pop('filepath', None)
                attr_desc['TYPE'].parser(**kwargs)
            return

        old_len = len(self)
        if kwargs.get('init_attrs', True):
            # parsing/initializing all array elements, so clear the Block
            list.__delitem__(self, slice(None, None, None))

        # if an initdata was provided, make sure it can be used
        initdata = kwargs.pop('initdata', None)
        assert (initdata is None or
                (hasattr(initdata, '__iter__') and
                 hasattr(initdata, '__len__'))), (
                     "initdata must be an iterable with a length")

        if rawdata is not None:
            # parse the structure from raw data
            try:
                # we are either parsing the attribute from rawdata or nothing
                kwargs.update(desc=desc, node=self, rawdata=rawdata)
                kwargs.pop('filepath', None)
                desc['TYPE'].parser(**kwargs)
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
        elif initdata is not None:
            # initdata is not None, so use it to populate the WhileBlock
            list.extend(self, [None]*(len(initdata) - len(self)))
            for i in range(len(initdata)):
                self[i] = initdata[i]

            # if the initdata has a STEPTREE node, copy it to
            # this Block if this Block can hold a STEPTREE.
            try:
                self.STEPTREE = initdata.STEPTREE
            except AttributeError:
                pass
        elif kwargs.get('init_attrs', True):
            # this ListBlock is an array, so the FieldType
            # of each element should be the same
            try:
                attr_desc = desc['SUB_STRUCT']
                attr_f_type = attr_desc['TYPE']
            except Exception:
                raise TypeError("Could not locate the sub-struct descriptor." +
                                "\nCould not initialize array")

            # if initializing the array elements, extend this Block with
            # elements so its length is what it was before it was cleared.
            list.extend(self, [None]*(old_len - len(self)))

            # loop through each element in the array and initialize it
            for i in range(old_len):
                attr_f_type.parser(attr_desc, parent=self, attr_index=i)

            # only initialize the STEPTREE if this Block has a STEPTREE
            s_desc = desc.get('STEPTREE')
            if s_desc:
                s_desc['TYPE'].parser(s_desc, parent=self,
                                      attr_index='STEPTREE')


class PWhileBlock(WhileBlock):
    '''
    A subclass of WhileBlock which adds a slot for a STEPTREE attribute.

    Uses __init__, __sizeof__, __setattr__, and __delattr__ from PArrayBlock.

    See supyr_struct.blocks.while_block.WhileBlock.__doc__ for more help.
    '''
    __slots__ = ('STEPTREE')

    __init__ = PArrayBlock.__init__

    __sizeof__ = PArrayBlock.__sizeof__

    __setattr__ = PArrayBlock.__setattr__

    __delattr__ = PArrayBlock.__delattr__

WhileBlock.PARENTABLE = PWhileBlock
WhileBlock.UNPARENTABLE = WhileBlock

WhileBlock.PARENTABLE = PWhileBlock
WhileBlock.UNPARENTABLE = WhileBlock
