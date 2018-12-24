'''
'''
from copy import deepcopy
from .block import *


class ListBlock(list, Block):
    """
    ListBlocks are the primary method of organizing nodes into
    trees, and can be seen as a mutable version of namedtuples.
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

    __slots__ = ('desc', '_parent', '__weakref__')

    def __init__(self, desc, parent=None, init_attrs=None, **kwargs):
        '''
        Initializes a ListBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'NAME_MAP', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.parse and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'NAME_MAP' in desc and 'ENTRIES' in desc)
        object.__setattr__(self, "desc",   desc)
        self.parent = parent

        if kwargs or init_attrs:
            self.parse(init_attrs=init_attrs, **kwargs)
        else:
            # populate the listblock with the right number of fields
            list.__init__(self, [None]*desc['ENTRIES'])

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this ListBlock.

        Optional keywords arguments:
        # int:
        attr_index - The index this Block is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
        indent ----- The number of spaces of indent added per indent level.
        precision -- The number of decimals to round floats to.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located in in its parent
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
            steptrees - Fields parented to the node as steptrees
        '''
        # set the default things to show
        seen = kwargs['seen'] = set(kwargs.get('seen', ()))
        seen.add(id(self))

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            if show in SHOW_SETS:
                show = SHOW_SETS[show]
            else:
                show = [show]
        show = set(show)

        indent = kwargs.get('indent', NODE_PRINT_INDENT)
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
        if "type" in show and hasattr(self, 'TYPE'):
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
        if "parent_id" in show:
            tempstr += ', parent_id:%s' % id(self.parent)
        if "node_id" in show:
            tempstr += ', node_id:%s' % id(self)
        if "node_cls" in show:
            tempstr += ', node_cls:%s' % desc['TYPE'].node_cls
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

        # Print this ListBlock's STEPTREE if it has one
        if hasattr(self, 'STEPTREE') and (self.STEPTREE is not None and
                                         "steptrees" in show):
            kwargs['attr_name'] = inv_name_map.get('STEPTREE', UNNAMED)
            kwargs['attr_index'] = STEPTREE

            tag_str += self.attr_to_str(**kwargs)

        tag_str += indent_str1 + ']'

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

        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               initdata=self, parent=parent)

        if hasattr(self, 'STEPTREE'):
            object.__setattr__(dup_block, 'STEPTREE',
                               object.__getattribute__(self, 'STEPTREE'))

        return dup_block

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
            parent = self.parent
            parent = memo.get(id(parent), parent)
        except AttributeError:
            parent = None

        # make a new block object sharing the same descriptor.
        # make sure the attributes arent initialized. it'll just waste time.
        memo[id(self)] = dup_block = type(self)(
            object.__getattribute__ (self, 'desc'),
            parent=parent, init_attrs=False)

        # clear the Block so it can be populated
        list.__delitem__(dup_block, slice(None, None, None))
        list.extend(dup_block, [None]*len(self))

        # populate the duplicate
        for i in range(len(self)):
            list.__setitem__(dup_block, i, deepcopy(list.__getitem__(self, i),
                                                    memo))

        # STEPTREE has to be done last as its structure
        # likely relies on attributes of this, its parent
        if hasattr(self, 'STEPTREE'):
            object.__setattr__(
                dup_block, 'STEPTREE',
                deepcopy(object.__getattribute__(self, 'STEPTREE'), memo))

        return dup_block

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this ListBlock, all its
        attributes, and all its list elements take up in memory.

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

            assert not self.assert_is_valid_field_value(index, new_value)
            list.__setitem__(self, index, new_value)
            # if the object being placed in the Block is itself
            # a Block, set its parent attribute to this Block.
            if isinstance(new_value, Block):
                new_value.parent = self

                # if the new attribute is a Block, dont even try to set
                # its size. This is mainly because it will break the way
                # the parsers build a Block. For example, if an empty array
                # is created and placed into a Block when the parser makes
                # it, and the parent Block sets its size, it'll change
                # the size to 0(since thats what its currently at).
                # When the parser tries to build the number of entries
                # its size says, it wont make any since the size is 0.
                return

            desc = object.__getattribute__(self, 'desc')

            if not isinstance(desc[index].get('SIZE', 0), int):
                try:
                    # set the size of the attribute
                    self.set_size(None, index)
                except (NotImplementedError, AttributeError,
                        DescEditError, DescKeyError):
                    pass

        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if start > stop:
                start, stop = stop, start
            if step < 0:
                step = -step

            assert hasattr(new_value, '__iter__'), (
                "must assign iterable to extended slice")

            slice_size = (stop - start)//step

            if step != 1 and slice_size > len(new_value):
                raise ValueError("attempt to assign sequence of size " +
                                 "%s to extended slice of size %s" %
                                 (len(new_value), slice_size))

            assert not self.assert_are_valid_field_values(
                range(start, stop, step), new_value)
            list.__setitem__(self, index, new_value)
            for node in new_value:
                # if the object being placed in the Block is itself
                # a Block, set its parent attribute to this Block.
                if isinstance(node, Block):
                    node.parent = self

            set_size = self.set_size
            desc = object.__getattribute__(self, 'desc')

            # update the size of each attribute set to this Block
            for i in range(start, stop, step):
                if 'SIZE' in desc[i]:
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
        raise DescEditError("ListBlocks do not support deletion of fields.")

    def __binsize__(self, node, substruct=False):
        '''Does NOT protect against recursion'''
        size = 0
        if isinstance(node, Block):
            f_type = object.__getattribute__(node, 'desc')['TYPE']
            if f_type.name == 'Void':
                return 0

            if f_type.is_struct:
                if f_type.is_bit_based:
                    # return the size of this bit_struct
                    # since the node contains no substructs
                    if substruct:
                        return 0
                    return node.get_size()
                elif not substruct:
                    # get the size of this structure if it's not a substruct
                    size = node.get_size()
                    substruct = True

            # loop for each of the attributes
            for i in range(len(node)):
                sub_node = node[i]
                if isinstance(sub_node, Block):
                    size += sub_node.__binsize__(sub_node, substruct)
                elif not substruct:
                    size += node.get_size(i)

            # add the size of the STEPTREE
            if hasattr(node, 'STEPTREE'):
                steptree = object.__getattribute__(node, 'STEPTREE')
                if isinstance(steptree, Block):
                    size += steptree.__binsize__(steptree)
                else:
                    size += node.get_size('STEPTREE')
        return size

    def index_by_id(self, node):
        '''
        Checks the id of every entry in this ListBlock to locate
        which index 'node' is in. This differs from list.index
        as it selects a match by id(node) rather than content.

        Returns the index that node is in.
        Raises ValueError if node can not be found.
        '''
        return [id(list.__getitem__(self, i)) for
                i in range(len(self))].index(id(node))

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
        parent = self
        if isinstance(attr_index, int):
            node = self[attr_index]
            # try to get the size directly from the node or the parent
            try:
                desc = node.desc
            except AttributeError:
                desc = self_desc[attr_index]
        elif isinstance(attr_index, str):
            node = self.__getattr__(attr_index)
            # try to get the size directly from the node
            try:
                desc = node.desc
            except Exception:
                # if that fails, try to get it from the desc of the parent
                try:
                    desc = self_desc[self_desc['NAME_MAP'][attr_index]]
                except Exception:
                    desc = self_desc[attr_index]
        else:
            desc = self_desc
            node = self
            parent = self.parent

        # determine how to get the size
        if 'SIZE' in desc:
            size = desc['SIZE']

            if isinstance(size, int):
                return size
            elif isinstance(size, str):
                # get the pointed to size data by traversing the tag
                # structure along the path specified by the string
                return self.get_neighbor(size, node)
            elif hasattr(size, '__call__'):
                # find the pointed to size data by calling the function
                return size(attr_index=attr_index, parent=parent,
                            node=node, **context)

            self_name = self_desc.get('NAME', UNNAMED)
            if isinstance(attr_index, (int, str)):
                self_name = attr_index
            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "\nExpected int, str, or function. Got %s.") %
                            (self_name, type(size)))
        # use the size calculation routine of the field
        return desc['TYPE'].sizecalc(node, parent=parent,
                                     attr_index=attr_index, **context)

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
            self.set_neighbor(nodepath, new_value, node)
        where 'node' is this Block(or its attribute if attr_index is not
        None), and nodepath is the value in the descriptor under 'SIZE'.

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
            node = self[attr_index]
            # try to get the size directly from the node or the parent
            try:
                desc = node.desc
            except AttributeError:
                desc = self_desc[attr_index]
            size = desc.get('SIZE')
        elif isinstance(attr_index, str):
            node = self.__getattr__(attr_index)

            error_num = 0
            # try to get the size directly from the node
            try:
                desc = node.desc
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

            if error_num:
                attr_name = desc.get('NAME', UNNAMED)
                if isinstance(attr_index, (int, str)):
                    attr_name = attr_index
                if error_num == 1:
                    raise DescKeyError(
                        "Could not determine size for attribute " +
                        "'%s' in block '%s'." % (attr_name, self_desc['NAME']))
                elif error_num == 2:
                    raise DescKeyError(
                        ("Can not set size for attribute '%s' in block '%s'." +
                         "\n'%s' has a fixed size of '%s'.\nTo change the " +
                         "size of '%s' you must change its FieldType.") %
                        (attr_name, self_desc['NAME'], desc['TYPE'],
                         desc['TYPE'].size, attr_name))
        else:
            node = self
            desc = self_desc
            size = desc.get('SIZE')

        # raise exception if the size is None
        if size is None:
            attr_name = desc.get('NAME', UNNAMED)
            if isinstance(attr_index, (int, str)):
                attr_name = attr_index
            raise DescKeyError("'SIZE' does not exist in '%s'." % attr_name)

        # if a new size wasnt provided then it needs to be calculated
        if new_value is not None:
            newsize = new_value
        elif hasattr(node, 'parent'):
            newsize = desc['TYPE'].sizecalc(parent=node.parent, node=node,
                                            attr_index=attr_index, **context)
        else:
            newsize = desc['TYPE'].sizecalc(parent=self, node=node,
                                            attr_index=attr_index, **context)

        if isinstance(size, int):
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if new_value is None and newsize <= size:
                return
            raise DescEditError("Changing a size statically defined in a " +
                                "descriptor is not supported through " +
                                "set_size. Make a new descriptor instead.")
        elif isinstance(size, str):
            # set size by traversing the tag structure
            # along the path specified by the string
            self.set_neighbor(size, newsize, node)
            return
        elif hasattr(size, '__call__'):
            # set size by calling the provided function
            if hasattr(node, 'parent'):
                size(attr_index=attr_index, new_value=newsize,
                     parent=node.parent, node=node, **context)
            else:
                size(attr_index=attr_index, new_value=newsize,
                     parent=self, node=node, **context)
            return

        self_name = self_desc['NAME']
        if isinstance(attr_index, (int, str)):
            self_name = attr_index

        raise TypeError(("size specified in '%s' is not a valid type." +
                         "\nExpected int, str, or function. Got %s.\n") %
                        (self_name, type(size)))

    def collect_pointers(self, offset=0, seen=None, pointed_nodes=None,
                         substruct=False, root=False, attr_index=None):
        '''
        '''
        if seen is None:
            seen = set()

        if attr_index is None:
            desc = object.__getattribute__(self, 'desc')
            node = self
        else:
            desc = self.get_desc(attr_index)
            node = self.__getitem__(attr_index)

        if id(node) in seen:
            return offset

        if 'POINTER' in desc:
            pointer = desc['POINTER']
            if isinstance(pointer, int):
                # if the next nodes are to be located directly after
                # this one then set the current offset to its location
                offset = pointer

            # if this is a node within the root node
            if not root:
                pointed_nodes.append((self, attr_index, substruct))
                return offset

        f_type = desc['TYPE']
        if f_type.is_block:
            seen.add(id(node))

        if desc.get('ALIGN'):
            align = desc['ALIGN']
            offset += (align - (offset % align)) % align

        # increment the offset by this nodes size if it isn't a substruct
        if not(substruct or f_type.is_container):
            offset += self.get_size(attr_index)
            substruct = True

        # If the node isn't a Block it means that this is being run
        # on a non-Block that happens to have its location specified by
        # pointer. The offset must still be incremented by the size of this
        # node, but the node can't contain other nodes, so return early.
        if not f_type.is_block:
            return offset

        if hasattr(self, 'STEPTREE'):
            indexes = list(range(len(self)))
            indexes.append('STEPTREE')
        else:
            indexes = range(len(self))

        align = 0

        for i in indexes:
            node = self[i]
            if isinstance(node, Block):
                # if "i" is an integer it means this object still
                # exists within the structure, or is "substruct".
                offset = node.collect_pointers(offset, seen, pointed_nodes,
                                                (isinstance(i, int) and
                                                 substruct), False)
            elif not substruct and isinstance(i, int):
                # It's pointless to check if this node is in seen
                # or not because the node may be an integer, float,
                # or string that is shared across multiple nodes.
                # The check would succeed or fail at random.
                b_desc = desc[i]
                align = b_desc.get('ALIGN')

                pointer = b_desc.get('POINTER')
                if isinstance(pointer, int):
                    offset = pointer
                elif pointer is not None:
                    # if the node has a variable pointer, add it to the
                    # list and break early so its id doesnt get added
                    pointed_nodes.append((self, i, substruct))
                    continue
                elif align:
                    # align the node
                    offset += (align - (offset % align)) % align

                # add the size of the node to the current offset
                offset += self.get_size(i)
                seen.add(id(node))
        return offset

    def parse(self, **kwargs):
        '''
        Parses this ListBlock in the way specified by the keyword arguments.

        If rawdata or a filepath is supplied, it will be used to parse
        this ListBlock(or the specified entry if attr_index is not None).

        If initdata is supplied and not rawdata nor a filepath, it will be
        used to replace the entries in this ListBlock if attr_index is None.
        If attr_index is instead not None, self[attr_index] will be replaced
        with init_data.

        If rawdata, initdata, filepath, and init_attrs are all unsupplied,
        all entries in this list will be initialized with a default value by
        calling the parser function of each entries 'TYPE' descriptor entry.

        If rawdata, initdata, and filepath are all unsupplied or None
        and init_attrs is False, this method will do nothing more than
        replace all index entries with None.

        Raises AssertionError if attr_index is None and initdata
        does not have __iter__ or __len__ methods.
        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.

        Optional keywords arguments:
        # bool:
        init_attrs --- Whether or not to clear the contents of the ListBlock.
                       Defaults to True. If True, and 'rawdata' and 'filepath'
                       are None, all the cleared array elements will be rebuilt
                       using their matching descriptors in self.desc

        # buffer:
        rawdata ------ A peekable buffer that will be used for parsing
                       elements of this ListBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the parser of this ListBlocks FieldType.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the parser of this ListBlocks FieldType.

        # int/str:
        attr_index --- The specific attribute index to initialize. Operates on
                       all indices if unsupplied or None. Defaults to None.

        # object:
        initdata ----- An iterable of objects to replace the contents of
                       this ListBlock if attr_index is None.
                       If attr_index is not None, this is instead an object
                       to replace self[attr_index]

        #str:
        filepath ----- An absolute path to a file to use as rawdata to parse
                       this ListBlock. If supplied, do not supply 'rawdata'.
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
            else:
                # we are either parsing the attribute from rawdata or nothing
                kwargs.update(desc=attr_desc, parent=self, rawdata=rawdata,
                              attr_index=attr_index)
                kwargs.pop('filepath', None)
                attr_desc['TYPE'].parser(**kwargs)
            return
        else:
            # parsing/initializing all attributes, so clear the block
            # and create as many elements as it needs to hold
            list.__init__(self, [None]*desc['ENTRIES'])

        if rawdata is not None:
            # parse the ListBlock from raw data
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
        elif kwargs.get('init_attrs', True):
            # initialize the attributes
            for i in range(len(self)):
                desc[i]['TYPE'].parser(desc[i], parent=self, attr_index=i)

            # Only initialize the STEPTREE if the block has a STEPTREE
            s_desc = desc.get('STEPTREE')
            if s_desc:
                s_desc['TYPE'].parser(s_desc, parent=self,
                                      attr_index='STEPTREE')

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

                # if the initdata has a STEPTREE node, copy it to
                # this Block if this Block can hold a STEPTREE.
                try:
                    self.STEPTREE = initdata.STEPTREE
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
    This ListBlock allows a reference to the STEPTREE
    node it describes to be stored as well as a
    reference to whatever Block it is parented to.
    '''
    __slots__ = ('STEPTREE')

    def __init__(self, desc, parent=None, steptree=None,
                 init_attrs=None, **kwargs):
        '''
        Initializes a PListBlock. Sets its desc, parent,
        and STEPTREE to those supplied.

        Raises AssertionError is desc is missing 'TYPE',
        'NAME', 'STEPTREE', 'NAME_MAP', or 'ENTRIES' keys.
        If kwargs are supplied, calls self.parse and passes them to it.
        '''
        assert (isinstance(desc, dict) and 'TYPE' in desc and
                'NAME' in desc and 'STEPTREE' in desc and
                'NAME_MAP' in desc and 'ENTRIES' in desc)

        object.__setattr__(self, 'desc',   desc)
        object.__setattr__(self, 'STEPTREE',  steptree)
        self.parent = parent

        if kwargs or init_attrs:
            self.parse(init_attrs=init_attrs, **kwargs)
        else:
            # populate the listblock with the right number of fields
            list.__init__(self, [None]*desc['ENTRIES'])

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this PListBlock, all its
        attributes, and all its list elements take up in memory.

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

        if hasattr(self, 'STEPTREE'):
            steptree = object.__getattribute__(self, 'STEPTREE')
            if isinstance(steptree, Block):
                bytes_total += steptree.__sizeof__(seenset)
            else:
                seenset.add(id(steptree))
                bytes_total += getsizeof(steptree)

        desc = object.__getattribute__(self, 'desc')

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
            if attr_name == 'STEPTREE':
                f_type = object.__getattribute__(self, 'desc')\
                        ['STEPTREE']['TYPE']
                if f_type.is_var_size and f_type.is_data:
                    # try to set the size of the attribute
                    try:
                        self.set_size(None, 'STEPTREE')
                    except(NotImplementedError, AttributeError,
                           DescEditError, DescKeyError):
                        pass

        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                self.__setitem__(desc['NAME_MAP'][attr_name], new_value)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

        # if the object being placed in the Block is itself
        # a Block, set its parent attribute to this Block.
        if attr_name != "parent" and isinstance(new_value, Block):
            new_value.parent = self

    def __delattr__(self, attr_name):
        '''
        '''
        try:
            object.__delattr__(self, attr_name)
            if attr_name == 'STEPTREE':
                # set the size of the node to 0 since it's being deleted
                try:
                    self.set_size(0, 'STEPTREE')
                except(NotImplementedError, AttributeError,
                       DescEditError, DescKeyError):
                    pass
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                # set the size of the node to 0 since it's being deleted
                try:
                    self.set_size(0, attr_name=attr_name)
                except(NotImplementedError, AttributeError,
                       DescEditError, DescKeyError):
                    pass
                list.__setitem__(self, desc['NAME_MAP'][attr_name], None)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

ListBlock.PARENTABLE = PListBlock
ListBlock.UNPARENTABLE = ListBlock

PListBlock.PARENTABLE = PListBlock
PListBlock.UNPARENTABLE = ListBlock
