'''
A module that implements WhileBlock and PWhileBlock, subclasses of ListBlock.
WhileBlocks are used where an array is needed which does not have a size
stored anywhere and must be parsed until some function says to stop.
'''
from .list_block import *


class WhileBlock(ListBlock):
    '''
    A Block class meant to be used with Fields that have an
    open ended size which must be deduced while parsing it.

    WhileBlocks function identically to ListBlocks, except that
    they have been optimized to only work with array Fields and
    all code regarding setting their size has been removed.
    This is because WhileArrays are designed to only be used with
    Fields that are open-ended and dont store their size anywhere.

    For example, WhileBlocks are used with WhileArrays, which continue
    to build array entries until a "case" function returns False.
    '''
    __slots__ = ('desc', 'parent')

    def __setitem__(self, index, new_value):
        '''
        Places 'new_value' into this Block at 'index'.

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

        elif isinstance(index, slice):
            # if this is an array, dont worry about the descriptor since
            # its list indexes aren't attributes, but instanced objects
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step

            assert hasattr(new_value, '__iter__'), ("must assign iterable " +
                                                    "to extended slice")

            slice_size = (stop - start)//step

            if step != -1 and slice_size > len(new_value):
                raise ValueError("Attempt to assign sequence of size " +
                                 "%s to extended slice of size %s" %
                                 (len(new_value), slice_size))

            list.__setitem__(self, index, new_value)
        else:
            self.__setattr__(index, new_value)

    def __delitem__(self, index):
        '''
        Deletes an attribute from this Block located in 'index'.

        If 'index' is a string, calls:
            self.__delattr__(index)
        '''
        if isinstance(index, str):
            self.__delattr__(index)
            return
        elif isinstance(index, int) and index < 0:
            index += len(self)
        list.__delitem__(self, index)

    def append(self, new_attr=None, new_desc=None):
        '''
        Appends 'new_attr' to this Block.

        If new_attr is None or not supplied, appends a new Block
        defined by the descriptor in:  self.desc[SUB_STRUCT]
        '''
        # create a new, empty index
        list.append(self, None)

        # if this block is an array and "new_attr" is None
        # then it means to append a new block to the array
        if new_attr is None:
            attr_desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
            attr_desc['TYPE'].reader(attr_desc, self, None, len(self) - 1)
            return

        try:
            list.__setitem__(self, -1, new_attr)
        except Exception:
            list.__delitem__(self, -1)
            raise
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def extend(self, new_attrs):
        '''Allows extending this ListBlock with new attributes.
        Provided argument must be a ListBlock so that a descriptor
        can be found for all attributes, whether they carry it or
        the provided block does.
        Provided argument may also be an int if this block type is an Array.
        Doing so will extend the array with that amount of fresh structures
        (as defined by the Array's SUB_STRUCT descriptor value)'''
        if isinstance(new_attrs, ListBlock):
            desc = new_attrs.desc
            for i in range(len(ListBlock)):
                self.append(new_attrs[i], desc[i])
        elif isinstance(new_attrs, int):
            # if this block is an array and "new_attr" is an int it means
            # that we are supposed to append this many of the SUB_STRUCT
            for i in range(new_attrs):
                self.append()
        else:
            raise TypeError("Argument type for 'extend' must be an " +
                            "instance of ListBlock or int, not %s" %
                            type(new_attrs))

    def insert(self, index, new_attr=None, new_desc=None):
        '''Allows inserting objects into this ListBlock while
        taking care of all descriptor related details.
        Function may be called with only "index" if this block type is a Array.
        Doing so will insert a fresh structure to the array at "index"
        (as defined by the Array's SUB_STRUCT descriptor value)'''

        # create a new, empty index
        list.insert(self, index, None)

        new_desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
        new_field = new_desc['TYPE']

        try:
            # if the type of the default object is a type of Block
            # then we can create one and just append it to the array
            if new_attr is None and issubclass(new_field.py_type, Block):
                new_field.reader(new_desc, self, None, index)
                # finished, so return
                return
        except Exception:
            list.__delitem__(self, index)
            raise

        # if new_attr has its own desc, use that instead of a provided one
        try:
            new_desc = new_attr.desc
        except Exception:
            pass

        if new_desc is None:
            list.__delitem__(self, index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(new_attr)) + "\nCannot insert " +
                                 "without a descriptor for the new item.")
        try:
            list.__setitem__(self, index, new_attr)
        except Exception:
            list.__delitem__(self, index)
            raise
        try:
            object.__setattr__(new_attr, 'parent', self)
        except Exception:
            pass

    def pop(self, index=-1):
        '''Pops the attribute at 'index' out of the ListBlock
        and returns a tuple containing it and its descriptor.'''

        desc = object.__getattribute__(self, "desc")

        if isinstance(index, int):
            if index < 0:
                return (list.pop(self, index + len(self)), desc['SUB_STRUCT'])
            return (list.pop(self, index), desc['SUB_STRUCT'])
        elif index in desc.get('NAME_MAP', ()):
            return (list.pop(self, desc['NAME_MAP'][index]),
                    self.get_desc('SUB_STRUCT'))
        elif 'NAME' in desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc['NAME'], type(self), index))
        else:
            raise AttributeError("'%s' has no attribute '%s'" %
                                 (type(self), index))

    def set_size(self, new_value=None, attr_index=None, op=None, **kwargs):

        desc = object.__getattribute__(self, 'desc')

        if isinstance(attr_index, int):
            block = self[attr_index]
            size = desc['SUB_STRUCT'].get('SIZE')
            field = self.get_desc(TYPE, attr_index)
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)

            error_num = 0
            # try to get the size directly from the block
            try:
                # do it in this order so desc doesnt get
                # overwritten if SIZE can't be found in desc
                size = block.desc['SIZE']
                desc = block.desc
            except Exception:
                # if that fails, try to get it from the desc of the parent
                try:
                    desc = desc[desc['NAME_MAP'][attr_index]]
                except Exception:
                    desc = desc[attr_index]

                try:
                    size = desc['SIZE']
                except Exception:
                    # its parent cant tell us the size, raise this error
                    error_num = 1
                    if 'TYPE' in desc and not desc['TYPE'].is_var_size:
                        # the size is not variable so it cant be set
                        # without changing the type. raise this error
                        error_num = 2

            attr_name = desc.get('NAME')
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            if error_num == 1:
                raise AttributeError(("Could not determine size for " +
                                      "attribute '%s' in block '%s'.") %
                                     (attr_name, object.__getattribute__
                                      (self, 'desc')['NAME']))
            elif error_num == 2:
                raise AttributeError(("Can not set size for attribute " +
                                      "'%s' in block '%s'.\n'%s' has a " +
                                      "fixed size  of '%s'.\nTo change the " +
                                      "size of '%s' you must change its " +
                                      "data type.") %
                                     (attr_name, object.__getattribute__
                                      (self, 'desc')['NAME'], desc['TYPE'],
                                      desc['TYPE'].size, attr_name))
            field = desc['TYPE']
        else:
            # cant set size of WhileArrays
            return

        # raise exception if the size is None
        if size is None:
            attr_name = desc['NAME']
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            raise AttributeError("'SIZE' does not exist in '%s'." % attr_name)

        # if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            op = None
            if hasattr(block, 'parent'):
                parent = block.parent
            else:
                parent = self

            newsize = field.sizecalc(parent=parent, block=block,
                                     attr_index=attr_index)
        else:
            newsize = new_value

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
            self.set_neighbor(size, newsize, block, op)
        elif hasattr(size, "__call__"):
            # set size by calling the provided function
            if hasattr(block, 'parent'):
                parent = block.parent
            else:
                parent = self

            if op is None:
                pass
            elif op == '+':
                newsize += size(attr_index=attr_index, parent=parent,
                                block=block, **kwargs)
            elif op == '-':
                newsize = (size(attr_index=attr_index, parent=parent,
                                block=block, **kwargs) - newsize)
            elif op == '*':
                newsize *= size(attr_index=attr_index, parent=parent,
                                block=block, **kwargs)
            else:
                raise TypeError("Unknown operator '%s' for setting size" % op)

            size(attr_index=attr_index, new_value=newsize,
                 op=op, parent=parent, block=block, **kwargs)
        else:
            attr_name = object.__getattribute__(self, 'desc')['NAME']
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index

            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (attr_name, type(size)) +
                            "Cannot determine how to set the size.")

    def build(self, **kwargs):
        '''This function will initialize all of a WhileBlocks attributes to
        their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

        attr_index = kwargs.get('attr_index')
        desc = object.__getattribute__(self, "desc")

        if attr_index is not None:
            # reading/initializing just one attribute
            if isinstance(attr_index, str):
                attr_index = desc['NAME_MAP'][attr_index]

            attr_desc = desc[attr_index]
            rawdata = kwargs.get('rawdata')

            # read the attr_index and return
            if isinstance(attr_desc[TYPE].py_type, Block):
                del kwargs['attr_index']
                self[attr_index].build(**kwargs)
            elif rawdata is not None:
                attr_desc[TYPE].reader(attr_desc, self, rawdata, attr_index,
                                       kwargs.get('root_offset', 0),
                                       kwargs.get('offset', 0),
                                       int_test=kwargs.get('int_test', 0))
            return
        elif not kwargs.get('init_attrs', True):
            # we are rebuilding all attributes
            list.__delitem__(self, slice(None, None, None))

        rawdata = self.get_rawdata(**kwargs)

        if rawdata is not None:
            # build the structure from raw data
            try:
                desc['TYPE'].reader(desc, self, rawdata, attr_index,
                                    kwargs.get('root_offset', 0),
                                    kwargs.get('offset', 0),
                                    int_test=kwargs.get('int_test', False))
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
            # this ListBlock is an array, so the type
            # of each element should be the same
            try:
                attr_desc = desc['SUB_STRUCT']
                attr_field = attr_desc['TYPE']
            except Exception:
                raise TypeError("Could not locate the sub-struct descriptor." +
                                "\nCould not initialize array")

            # loop through each element in the array and initialize it
            for i in range(len(self)):
                attr_field.reader(attr_desc, self, None, i)

            # only initialize the child if the block has a child
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
            # initdata is not None, so use it to populate the WhileBlock
            list.extend(self, [None]*(len(initdata) - len(self)))
            for i in range(len(self)):
                self[i] = initdata[i]

            # if the initdata has a CHILD block, copy it to
            # this block if this block can hold a CHILD.
            try:
                self.CHILD = initdata.CHILD
            except AttributeError:
                pass


class PWhileBlock(WhileBlock):
    '''
    A subclass of WhileBlock which adds a slot for a CHILD attribute.

    Uses __init__, __sizeof__, __setattr__, and __delattr__ from PListBlock.
    '''
    __slots__ = ('CHILD')

    __init__ = PListBlock.__init__

    __sizeof__ = PListBlock.__sizeof__

    __setattr__ = PListBlock.__setattr__

    __delattr__ = PListBlock.__delattr__

WhileBlock.PARENTABLE = PWhileBlock
PWhileBlock.UNPARENTABLE = WhileBlock
