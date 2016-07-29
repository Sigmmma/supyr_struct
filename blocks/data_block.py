'''
A module that implements DataBlock, EnumBlock, BoolBlock, and WrapperBlock.
These Block subclasses are used with 'data' Fields which need
extra methods and a descriptor to properly operate on the data.
'''
from copy import deepcopy
from .block import *

_INVALID_NAME_DESC = {NAME: INVALID}


class DataBlock(Block):
    '''
    A Block class for Fields which are 'data', but which need to hold
    a reference to a descriptor and need to be able to use it properly.

    For a Field to be considered 'data' it needs to be describing
    a type of information(like a string or integer) rather than a
    type of structure or hierarchy(such as a struct or array).
    A DataBlock is not intended to be used as is, but rather have
    specialized subclasses made from it. Examples of such include
    EnumBlock and BoolBlock, which(respectively) act as a wrappers
    for data that may be set to one of several enumerations and
    integer data that treats each of the bits as a named boolean.

    DataBlocks use their descriptor for storing information about
    their data and employ methods to manipulate it using the descriptor.
    For BoolBlocks such methods include ones to get/set specified flags.
    EnumBlocks add methods for changing the data to a named setting.

    DataBlocks do not allow specifying a size as anything other than
    an int literal in their descriptor/Field. Specifying size with a
    pathstring or a function was deemed unlikely to ever be used and
    the resulting code is faster without having to account for it.
    '''

    __slots__ = ("desc", "parent", "data")

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes a DataBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE' or 'NAME' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, 'parent', parent)

        self.data = desc['TYPE'].data_type()

        if kwargs:
            self.rebuild(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this DataBlock.

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
            index ---- The index the attribute is located at in its parent
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
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        tag_str = Block.__str__(self, **kwargs)[:-2]

        if "value" in show:
            tag_str += ', %s' % self.data

        # remove the first comma
        tag_str = tag_str.replace(',', '', 1) + ' ]'

        return tag_str

    def __sizeof__(self, seenset=None):
        '''
        Returns the number of bytes this Block and all its attributes and
        sub-Blocks take up in memory.

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
        data = self.data
        if isinstance(data, Block):
            bytes_total = object.__sizeof__(self) + data.__sizeof__(seenset)
        else:
            bytes_total = object.__sizeof__(self) + getsizeof(data)

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
                          parent=parent, initdata=self.data)

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
        except AttributeError:
            parent = None

        # make a new block object sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               parent=parent, initdata=deepcopy(self.data,
                                                                memo))
        memo[id(self)] = dup_block

        return dup_block

    def __binsize__(self, block, substruct=False):
        '''
        Returns the size of this DataBlock.
        This size is how many bytes it would take up if written to a buffer.
        '''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''
        Returns the size of this DataBlock.
        This size is how many bytes it would take up if written to a buffer.
        '''
        return self.get_size()

    def get_size(self, attr_index=None, **context):
        '''
        Returns the size in bytes of this Block if it were serialized.

        This byte size either exists directly in the descriptor under the
        'SIZE' key, or must be calculated using self.TYPE.sizecalc(self)

        The attr_index and additional keyword arguments do nothing,
        and are only there so this method's parameters match those
        of all other get_size methods.

        Raises TypeError if the 'SIZE' entry isnt an int.
        '''
        desc = object.__getattribute__(self, 'desc')

        # determine how to get the size
        if 'SIZE' in desc:
            try:
                return desc['SIZE'] >> 0
            except TypeError:
                pass
            raise TypeError(("Size specified in '%s' is not a " +
                             "valid type.\nExpected int, got %s.") %
                            (desc['NAME'], type(desc['SIZE'])))
        # use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(self)

    def set_size(self, new_value=None, attr_index=None, **context):
        '''
        Runs a series of checks to ensure that the size this Block is being
        set to is less than or equal to the size it is currently set to.

        This method doesnt actually change this Blocks size because DataBlocks
        are expected to have explicit integer sizes, which are not allowed to
        be changed through their set_size method. This method exists mainly to
        fit the interface expected of a Block, but also ensures that self.data
        is not set to a value too large to be serialized.

        If 'new_value' isnt supplied, calculates it using:
            self.desc['TYPE'].sizecalc(self.data)

        The attr_index argument does nothing, and is only there so this
        method's parameters match those of all other set_size methods.

        Raises DescEditError if the descriptor 'SIZE' entry is an int
        and the the size is being set to a value greater than what is
        currently in the descriptor.
        Raises DescKeyError if 'SIZE' doesnt exist in the descriptor.
        Raises TypeError if the 'SIZE' entry isnt an int.
        '''
        desc = object.__getattribute__(self, 'desc')
        size = desc.get('SIZE')

        # raise exception if the size is None
        if size is None:
            raise DescKeyError("'SIZE' does not exist in '%s'." % desc['NAME'])

        # if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            newsize = desc['TYPE'].sizecalc(self.data)
        else:
            newsize = new_value

        # Its faster to try to bitshift the size by 0 and return it
        # than to check if it's an int using isinstance(size, int).
        try:
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if newsize > size >> 0:
                raise DescEditError(
                    "Changing a size statically defined in a " +
                    "descriptor is not supported through set_size. " +
                    "Use the 'set_desc' method instead.")
            return
        except TypeError:
            pass
        raise TypeError(("Size specified in '%s' is not a valid type.\n" +
                         "Expected int, got %s.\nCannot determine how " +
                         "to set the size.") % (desc['NAME'], type(size)))

    def rebuild(self, **kwargs):
        '''
        Rebuilds this DataBlock in the way specified by the keyword arguments.

        If initdata is supplied, it will be used to replace self.data.
        If initdata is not supplied and rawdata or a filepath is, they
        will be used when reparsing this DataBlock. 

        If rawdata, initdata, filepath, and init_attrs are all unsupplied,
        init_attrs will default to True, setting self.data to a default value.

        If rawdata, initdata, and filepath are all unsupplied or None and
        init_attrs is False, this method will do nothing.

        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.
        
        Optional keywords arguments:
        # bool:
        init_attrs --- Whether or not to reset self.data to a default value.
                       If DEFAULT exists in self.desc, it will be cast to the
                       type specified by self.desc['TYPE'].data_type and
                       self.data will be set to it. If it instead doesnt exist,
                       self.data will be set to self.desc['TYPE'].data_type()

        # buffer:
        rawdata ------ A peekable buffer that will be used for rebuilding
                       this DataBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the reader of this DataBlocks Field.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the reader of this DataBlocks Field.

        # iterable:
        initdata ----- An object able to be cast to the python type located
                       at self.TYPE.data_type using the following line:
                           self.data = desc.get('TYPE').data_type(initdata)

        #str:
        filepath ----- An absolute path to a file to use as rawdata to rebuild
                       this DataBlock. If supplied, do not supply 'rawdata'.
        '''
        initdata = kwargs.pop('initdata', None)
        rawdata = get_rawdata(**kwargs)
        desc = object.__getattribute__(self, "desc")

        if initdata is not None:
            try:
                self.data = desc.get('TYPE').data_type(initdata)
            except ValueError:
                d_type = desc.get('TYPE').data_type
                raise ValueError("'initdata' must be a value able to be " +
                                 "cast to a %s. Got %s" % (d_type, initdata))
            except TypeError:
                d_type = desc.get('TYPE').data_type
                raise ValueError("Invalid type for 'initdata'. Must be a " +
                                 "%s, not %s" % (d_type, type(initdata)))
        elif rawdata is not None:
            # rebuild the block from raw data
            try:
                try:
                    parent = object.__getattribute__(self, "parent")
                except AttributeError:
                    parent = None

                kwargs.update(desc=desc, parent=parent, rawdata=rawdata,
                              attr_index=None)
                kwargs.pop('filepath', None)
                desc['TYPE'].reader(**kwargs)
            except Exception as e:
                a = e.args[:-1]
                try:
                    e_str = e.args[-1] + e_str
                except IndexError:
                    e_str = ''
                e.args = a + (
                    "%sError occurred while attempting to rebuild %s." %
                    (e_str + '\n', type(self)),)
                raise e
        elif kwargs.get('init_attrs', True):
            # Initialize self.data to its default value
            if 'DEFAULT' in desc:
                self.data = desc.get('TYPE').data_type(desc['DEFAULT'])
            else:
                self.data = desc.get('TYPE').data_type()


class WrapperBlock(DataBlock):
    '''
    A Block class for Fields which must decode rawdata before the
    wrapped SUB_STRUCT can be built using it, and must encode the
    wrapped SUB_STRUCT before it is serialized to the writebuffer.

    The main function of this class is for it to hold a descriptor
    and a reference to the SUB_STRUCT attribute so that when the
    Block is serialized it can be encoded before being written.

    The get_size and set_size methods of this class will pass all
    supplied arguments over to the method with the same name in
    self.data if self.data is an instance of Block.
    '''
    __slots__ = ()

    def __init__(self, desc, parent=None, **kwargs):
        '''
        Initializes a WrapperBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE' or 'NAME' keys.
        If kwargs are supplied, calls self.rebuild and passes them to it.
        '''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, "parent", parent)

        self.data = None

        if kwargs:
            self.rebuild(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this WrapperBlock.

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
        show -------- An iterable containing strings specifying what to
                      include in the string. Valid strings are as follows:
            index ---- The index the attribute is located at in its parent
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
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        tag_str = Block.__str__(self, **kwargs)[:-2].replace(',', '', 1) + '\n'

        kwargs['attr_name'] = None
        kwargs['attr_index'] = SUB_STRUCT
        del kwargs['attr_name']
        kwargs['level'] = level = kwargs.get('level', 0) + 1

        indent_str = ' ' * level * kwargs.get('indent', BLOCK_PRINT_INDENT)

        return (tag_str + self.attr_to_str(**kwargs) + indent_str + ']')

    def get_size(self, attr_index=None, **context):
        '''
        Returns the size in bytes of self.data using the SIZE entry
        in self.desc['SUB_STRUCT'] if self.data were serialized.
        
        If self.data is an instance of Block, calls self.data.get_size
        with all of the supplied arguments and returns that instead.

        This is the byte size of the stream before it has been adapted, such
        as before an ENCODER function zlib compresses a serialized stream.
        This means the size returned is not guaranteed to be the size of the
        final serialized data. This must be kept in mind when sizing a buffer.

        The attr_index argument does nothing, and is only there so this
        method's parameters match those of all other get_size methods.

        If the SIZE entry is a string, returns self.get_neighbor
        while providing the SIZE entry as the pathstring.
        If the SIZE entry is a function, returns:
            size_getter(attr_index='SUB_STRUCT', parent=self,
                        block=self.data, **context)
        where size_getter is the function under the descriptors SIZE key and
        context is a dictionary of the remaining supplied keyword arguments.

        Raises TypeError if the 'SIZE' entry isnt an int, string, or function.
        '''
        if isinstance(self.data, Block):
            return self.data.get_size(**context)

        desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']

        # determine how to get the size
        if 'SIZE' in desc:
            size = desc['SIZE']

            if isinstance(size, int):
                return size
            elif isinstance(size, str):
                # get the pointed to size data by traversing the tag
                # structure along the path specified by the string
                return self.get_neighbor(size, self.data)
            elif hasattr(size, '__call__'):
                # find the pointed to size data by calling the function
                return size(attr_index='SUB_STRUCT', parent=self,
                            block=self.data, **context)

            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "\nExpected str or function. Got %s.") %
                            (SUB_STRUCT, type(size)))
        # use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(object.__getattribute__(self, 'data'))

    def set_size(self, new_value=None, attr_index=None, **context):
        '''
        Sets the size of self.data to 'new_value' using the SIZE
        entry in self.desc['SUB_STRUCT'].
        
        If self.data is an instance of Block, calls self.data.set_size
        with all of the supplied arguments instead.

        The size being set is the byte size of the stream before it
        has been adapted, such as before an ENCODER function zlib
        compresses a serialized stream.
        This means the size returned is not guaranteed to be the size of the
        final serialized data. This must be kept in mind when sizing a buffer.

        If 'new_value' isnt supplied, calculates it using the
        sizecalc method of self.desc['SUB_STRUCT']['TYPE']

        The attr_index argument does nothing, and is only there so this
        method's parameters match those of all other set_size methods.

        If the SIZE entry is a string, the size will be set using
        self.set_neighbor and providing the SIZE entry as the pathstring.

        If the SIZE entry is a function, the size will be set by doing:
            size_setter(attr_index='data', new_value=new_value,
                        parent=self, block=self.data, **context)
        where size_setter is the function under the descriptors SIZE key,
        new_value is the calculated or provided value to set the size to, and
        context is a dictionary of the remaining supplied keyword arguments.

        Raises DescEditError if the descriptor 'SIZE' entry
        is an int and the value the size is being set to is
        greater than what is currently in the descriptor.
        Raises DescKeyError if 'SIZE' doesnt exist in the descriptor.
        Raises TypeError if the 'SIZE' entry isnt an int, string, or function.
        '''
        data = object.__getattribute__(self, 'data')

        if isinstance(data, Block):
            return data.set_size(new_value, attr_index, **context)

        desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
        size = desc.get('SIZE')
        field = desc['TYPE']

        # raise exception if the size is None
        if size is None:
            raise DescKeyError("'SIZE' does not exist in '%s'." % desc['NAME'])

        # if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            newsize = field.sizecalc(parent=self, block=data,
                                     attr_index='data')
        else:
            newsize = new_value

        if isinstance(size, int):
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if newsize > size:
                raise DescEditError(
                    "Changing a size statically defined in a " +
                    "descriptor is not supported through set_size. " +
                    "Use the 'set_desc' method instead.")
        elif isinstance(size, str):
            # set size by traversing the tag structure
            # along the path specified by the string
            self.set_neighbor(size, newsize, data)
        elif hasattr(size, '__call__'):
            # set size by calling the provided function
            size(attr_index='data', new_value=newsize,
                 parent=self, block=data, **context)
        else:
            raise TypeError(("size specified in '%s' is not a valid type.\n" +
                             "Expected str or function, got %s.\nCannot " +
                             "determine how to set the size.") %
                            (desc['NAME'], type(size)))

    def rebuild(self, **kwargs):
        '''
        Rebuilds this WrapperBlock as specified by the keyword arguments.

        If initdata is supplied and not None, this WrapperBlock 'data'
        attribute will be set to it.
        If initdata is not supplied and rawdata or a filepath is, they
        will be used to reparse this WrapperBlock. 

        If rawdata, initdata, and filepath are all unsupplied or None and
        init_attrs is False, this method will do nothing.

        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.
        
        Optional keywords arguments:
        # buffer:
        rawdata ------ A peekable buffer that will be used for
                       rebuilding this WrapperBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the reader of this WrapperBlocks Field.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the reader of this WrapperBlocks Field.

        # object:
        initdata ----- If supplied and not None, self.data will be set to a
                       copy of it and the method will return. WrapperBlocks
                       can hold either Blocks or data in their data attribute,
                       so initdata can really be just about anything.

        #str:
        filepath ----- An absolute path to a file to use as rawdata to rebuild
                       this WrapperBlock. If supplied, do not supply 'rawdata'.
        '''
        initdata = kwargs.pop('initdata', None)

        if initdata is not None:
            # set the data attribute to the initdata
            self.data = initdata
            return

        desc = object.__getattribute__(self, "desc")

        # rebuild the block from raw data
        try:
            rawdata = get_rawdata(**kwargs)
            if kwargs.get('init_attrs', True) or rawdata is not None:
                kwargs.update(desc=desc, parent=self,
                              rawdata=rawdata, attr_index='data')
                kwargs.pop('filepath', None)
                desc['TYPE'].reader(**kwargs)
        except Exception as e:
            a = e.args[:-1]
            try:
                e_str = e.args[-1] + e_str
            except IndexError:
                e_str = ''
            e.args = a + ("%sError occurred while attempting to rebuild %s." %
                          (e_str + '\n', type(self)),)


class BoolBlock(DataBlock):
    '''
    A Block class meant to be used with data Fields where 'data' is expected
    to be an integer with some(or all) of the bits representing named flags.

    This Block is designed to provide an interface to set and unset
    a flag by its name or set a flag to a specific value by its name.
    '''
    __slots__ = ()

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this BoolBlock.

        Optional keywords arguments:
        # int:
        attr_index - The index this block is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
        indent ----- The number of spaces of indent added per indent level.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

        # set:
        show -------- An iterable containing strings specifying what to
                      include in the string. Valid strings are as follows:
            index ---- The index the attribute is located at in its parent
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

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(ALL_SHOW)

        # used to display different levels of indention
        indent_str = (' '*kwargs.get('indent', BLOCK_PRINT_INDENT) *
                      (kwargs.get('level', 0) + 1))

        desc = object.__getattribute__(self, 'desc')

        # build the main part of the string
        tag_str = DataBlock.__str__(self, **kwargs)[:-2]

        if "flags" in show:
            tag_str += '\n'

            trueonly = 'trueonly' in show
            entries = desc['ENTRIES']
            n_spc, m_spc, name, mask_str = [0]*entries, [0]*entries, '', ''

            if "name" in show:
                n_spc = [len(desc[i]['NAME']) for i in range(entries)]
            if "offset" in show:
                m_spc = [len(str(hex(desc[i]['VALUE'])))
                         for i in range(entries)]

            # if only printing set flags, remove the space sizes
            # that belong to flags which are currently False
            if trueonly:
                for i in range(entries-1, -1, -1):
                    if not self.data & desc[i].get('VALUE'):
                        n_spc.pop(i)
                        m_spc.pop(i)

            # get the largest spacing sizes out of all the shown flags
            n_spc = max(n_spc + [0])
            m_spc = max(m_spc + [0])

            # print each of the booleans
            for i in range(entries):
                tempstr = indent_str + '['
                mask = desc[i].get('VALUE')
                spc_str = ''

                if "offset" in show:
                    mask_str = str(hex(mask))
                    tempstr += ', mask:' + mask_str
                    spc_str = ' '*(m_spc - len(mask_str))
                if "name" in show:
                    name = desc[i].get('NAME')
                    tempstr += ', ' + spc_str + name
                    spc_str = ' '*(n_spc - len(name))
                if "value" in show:
                    tempstr += ', ' + spc_str + str(bool(self.data & mask))

                if not trueonly or (self.data & mask):
                    tag_str += tempstr.replace(',', '', 1) + ' ]\n'
            tag_str += indent_str + ']'
        else:
            tag_str += ' ]'

        return tag_str

    def __getitem__(self, attr_index):
        '''
        Returns the masked, unshifted value of the flag defined
        by the descriptor: self[DESC][attr_index].

        If attr_index is a string, uses self.desc['NAME_MAP'].get(attr_index)
        as attr_index.

        Being unshifted means that if the flag is(for example) the 5th bit
        in the integer and is set, this method will return 2**(5-1) or 16.
        attr_index must be an int.

        Raises AttributeError if attr_index does not exist in self.desc
        Raises TypeError if attr_index is not an int or string.
        '''
        desc = object.__getattribute__(self, "desc")
        if isinstance(attr_index, str):
            attr_index = desc['NAME_MAP'].get(attr_index)
        elif not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int or str, not %s" %
                            type(attr_index))
        if attr_index not in desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_index))
        return self.data & desc[attr_index]['VALUE']

    def __setitem__(self, attr_index, new_value):
        '''
        Sets the flag defined by the descriptor: self.desc[attr_index]
        The flag is set to bool(new_value)
        If attr_index is a string, uses self.desc['NAME_MAP'].get(attr_index)
        as attr_index.

        Raises AttributeError if attr_index does not exist in self.desc
        Raises TypeError if attr_index is not an int or string.
        '''
        desc = object.__getattribute__(self, "desc")
        if isinstance(attr_index, str):
            attr_index = desc['NAME_MAP'].get(attr_index)
        elif not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int or str, not %s" %
                            type(attr_index))
        if attr_index not in desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_index))
        mask = desc[attr_index]['VALUE']
        self.data = self.data - (self.data & mask) + (mask)*bool(new_value)

    def __delitem__(self, attr_index):
        '''
        Unsets the flag defined by the descriptor: self.desc[attr_index]
        If attr_index is a string, uses self.desc['NAME_MAP'].get(attr_index)
        as attr_index.

        Raises AttributeError if attr_index does not exist in self.desc
        Raises TypeError if attr_index is not an int or string.
        '''
        desc = object.__getattribute__(self, "desc")
        if isinstance(attr_index, str):
            attr_index = desc['NAME_MAP'].get(attr_index)
        elif not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int or str, not %s" %
                            type(attr_index))
        if attr_index not in desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                 (desc.get('NAME', UNNAMED),
                                  type(self), attr_index))
        self.data -= self.data & desc[attr_index]['VALUE']

    def __getattr__(self, attr_name):
        '''
        Returns the attribute specified by 'attr_name'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['NAME_MAP'], or in self.desc.

        If object.__getattribute__(self, attr_name) raises an AttributeError,
        then self.desc['NAME_MAP'] will be checked for attr_name in its keys.
        If it exists, uses desc[desc['NAME_MAP'][attr_name]]['VALUE'] as a
        bitmask to return   self.data & bitmask.
        If attr_name does not exist in self.desc['NAME_MAP'], self.desc will
        be checked for attr_name in its keys.
        If it exists, returns self.desc[attr_index]

        Raises AttributeError if attr_name cant be found in any of the above.
        '''
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc['NAME_MAP']:
                return self.data & desc[desc['NAME_MAP'][attr_name]]['VALUE']
            elif attr_name in desc:
                return desc[attr_name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __setattr__(self, attr_name, new_value):
        '''
        Sets the attribute specified by 'attr_name' to the given 'new_value'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['NAME_MAP'], or in self.desc.

        If object.__setattr__(self, attr_name, new_value) raises an
        AttributeError, then self.desc['NAME_MAP'] will be checked for
        attr_name in its keys.
        If it exists, uses desc[desc['NAME_MAP'][attr_name]]['VALUE'] as a
        bitmask to set the specified flag.
        If attr_name does not exist in self.desc['NAME_MAP'], self.desc will
        be checked for attr_name in its keys.
        If it exists, calls self.set_desc(attr_name)

        Raises AttributeError if attr_name cant be found in any of the above.
        '''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            attr_index = desc['NAME_MAP'].get(attr_name)
            if attr_index is not None:
                mask = desc[attr_index]['VALUE']
                self.data = (self.data - (self.data & mask) +
                             mask*bool(new_value))
            elif attr_name in desc:
                self.set_desc(attr_name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        '''
        Deletes the attribute specified by 'attr_name'.
        The attribute may either exist directly in this Block, in this Block
        under an alias name stored in self.desc['NAME_MAP'], or in self.desc.

        If object.__delattr__(self, attr_name) raises an AttributeError,
        then self.desc['NAME_MAP'] will be checked for attr_name in its keys.
        If it exists, uses desc[desc['NAME_MAP'][attr_name]]['VALUE'] as a
        bitmask to unset the specified flag.
        If attr_name does not exist in self.desc['NAME_MAP'], self.desc will
        be checked for attr_name in its keys.
        If it exists, calls self.del_desc(attr_name)

        Raises AttributeError if attr_name cant be found in any of the above.
        '''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            attr_index = desc['NAME_MAP'].get(attr_name)
            if attr_index is not None:
                # unset the flag and remove the option from the descriptor
                self.data -= self.data & desc[attr_index]['VALUE']
                self.del_desc(attr_index)
            elif attr_name in desc:
                self.del_desc(attr_name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def set(self, attr_name):
        '''
        Sets the flag specified by 'attr_name' to True.
        Raises TypeError if 'attr_name' is not a string.
        '''
        if not isinstance(attr_name, str):
            raise TypeError("'attr_name' must be a string, not %s" %
                            type(attr_name))
        desc = object.__getattribute__(self, "desc")
        mask = desc[desc['NAME_MAP'][attr_name]]['VALUE']
        self.data = self.data - (self.data & mask) + mask

    def set_to(self, attr_name, value):
        '''
        Sets the flag specified by 'attr_name' to bool(value).
        Raises TypeError if 'attr_name' is not a string.
        '''
        if not isinstance(attr_name, str):
            raise TypeError("'attr_name' must be a string, not %s" %
                            type(attr_name))
        desc = object.__getattribute__(self, "desc")
        mask = desc[desc['NAME_MAP'][attr_name]]['VALUE']
        self.data = self.data - (self.data & mask) + mask*bool(value)

    def unset(self, attr_name):
        '''
        Sets the flag specified by 'attr_name' to False.
        Raises TypeError if 'attr_name' is not a string.
        '''
        if not isinstance(attr_name, str):
            raise TypeError("'attr_name' must be a string, not %s" %
                            type(attr_name))
        desc = object.__getattribute__(self, "desc")
        self.data -= self.data & desc[desc['NAME_MAP'][attr_name]]['VALUE']

    def rebuild(self, **kwargs):
        '''
        Rebuilds this BoolBlock in the way specified by the keyword arguments.

        If initdata is supplied, it will be cast as an int and used for
        this BoolBlock 'data' attribute. If not, and rawdata or a filepath
        is supplied, it will be used to reparse this BoolBlock. 

        If rawdata, initdata, filepath, and init_attrs are all unsupplied,
        init_attrs will default to True, resetting all flags to their defaults.

        If rawdata, initdata, and filepath are all unsupplied or None and
        init_attrs is False, this method will do nothing.

        Raises TypeError if rawdata and filepath are both supplied.
        Raises TypeError if rawdata doesnt have read, seek, and peek methods.
        
        Optional keywords arguments:
        # bool:
        init_attrs --- If True, resets all flags to the values under the
                       DEFAULT descriptor key of each flags descriptor.
                       Flags default to False is no DEFAULT exists.

        # buffer:
        rawdata ------ A peekable buffer that will be used for rebuilding
                       this BoolBlock. Defaults to None.
                       If supplied, do not supply 'filepath'.

        # int:
        root_offset -- The root offset that all rawdata reading is done from.
                       Pointers and other offsets are relative to this value.
                       Passed to the reader of this BoolBlocks Field.
        offset ------- The initial offset that rawdata reading is done from.
                       Passed to the reader of this BoolBlocks Field.

        # iterable:
        initdata ----- An object able to be cast as an int using int(initdata).
                       Will be cast as an int and self.data will be set to it.

        #str:
        filepath ----- An absolute path to a file to use as rawdata to rebuild
                       this BoolBlock. If supplied, do not supply 'rawdata'.
        '''
        initdata = kwargs.pop('initdata', None)

        if initdata is not None:
            self.data = int(initdata)
            return  # return early

        rawdata = get_rawdata(**kwargs)
        if rawdata is not None:
            # rebuild the block from raw data
            try:
                desc = object.__getattribute__(self, "desc")
                kwargs.update(desc=desc, parent=self,
                              rawdata=rawdata, attr_index=None)
                kwargs.pop('filepath', None)
                desc['TYPE'].reader(**kwargs)
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
            desc = object.__getattribute__(self, "desc")
            new_value = 0
            for i in range(desc['ENTRIES']):
                opt = desc[i]
                new_value += opt.get('VALUE') * bool(opt.get('DEFAULT', 0))
            self.data = new_value


class EnumBlock(DataBlock):
    '''
    A Block class meant to be used with data Fields where 'data' is
    expected to be set to one of a collection of several enumerations.

    This Block is designed to provide an interface to change the data
    using the name of an enumeration(rather than its value), finding
    the name of a given enumeration value, and a property to return
    the name of the current enumeration.
    '''
    __slots__ = ()

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this EnumBlock.

        Optional keywords arguments:
        # int:
        attr_index - The index this block is stored at in its parent.
                     If supplied, this will be the 'index' that is printed.
        indent ----- The number of spaces of indent added per indent level.

        # set:
        seen ------- A set of the python id numbers of each object which
                     has already been printed. Prevents infinite recursion.

        # set:
        show -------- An iterable containing strings specifying what to
                      include in the string. Valid strings are as follows:
            index ---- The index the attribute is located at in its parent
            name ----- The name of the attribute
            value ---- The attribute value
            field ---- The Field of the attribute
            size ----- The size of the attribute
            offset --- The offset(or pointer) of the attribute
            py_id ---- The id() of the attribute
            py_type -- The type() of the attribute
            endian --- The endianness of the Field
        '''

        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        # if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(ALL_SHOW)

        # used to display different levels of indention
        indent_str = (' '*kwargs.get('indent', BLOCK_PRINT_INDENT) *
                      (kwargs.get('level', 0) + 1))

        desc = object.__getattribute__(self, 'desc')

        # build the main part of the string
        tag_str = DataBlock.__str__(self, **kwargs)[:-2] + '\n'

        # find which index the string matches to
        try:
            index = self.get_index(self.data)
        except (AttributeError, DescKeyError):
            index = None

        opt = desc.get(index, {})
        tag_str += indent_str + ' %s ]' % opt.get('NAME', INVALID)

        return tag_str

    def __getattr__(self, attr_name):
        '''
        Returns the attribute specified by 'attr_name'.
        The attribute may either exist directly in this Block or in self.desc.

        If object.__getattribute__(self, attr_name) raises an AttributeError,
        then self.desc['NAME_MAP'] will be checked for attr_name in its keys.
        If attr_name exists in self.desc, returns self.desc[attr_name]

        Raises AttributeError if attr_name cant be found in either of the above
        '''
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc:
                return desc[attr_name]
            elif attr_name in desc['NAME_MAP']:
                raise AttributeError("Cannot get enumerator option as an " +
                                     "attribute. Use get_option() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __setattr__(self, attr_name, new_value):
        '''
        Sets the attribute specified by 'attr_name' to the given 'new_value'.
        The attribute may either exist directly in this Block or in self.desc.

        If object.__setattr__(self, attr_name, new_value) raises an
        AttributeError, then self.desc['NAME_MAP'] will be checked for
        attr_name in its keys.
        If attr_name exists in self.desc, calls:
            self.set_desc(attr_name, new_value)

        Raises AttributeError if attr_name cant be found in either of the above
        '''
        try:
            object.__setattr__(self, attr_name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc:
                self.set_desc(attr_name, new_value)
            elif attr_name in desc['NAME_MAP']:
                raise AttributeError("Cannot set enumerator option as an " +
                                     "attribute. Use set_to() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        '''
        Deletes the attribute specified by 'attr_name'.
        The attribute may either exist directly in this Block or in self.desc.

        If object.__delattr__(self, attr_name) raises an AttributeError,
        then self.desc['NAME_MAP'] will be checked for attr_name in its keys.
        If attr_name exists in self.desc, calls:
            self.del_desc(attr_name)

        Raises AttributeError if attr_name cant be found in either of the above
        '''
        try:
            object.__delattr__(self, attr_name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if attr_name in desc:
                self.del_desc(attr_name)
            elif attr_name in desc['NAME_MAP']:
                raise AttributeError("Cannot delete enumerator option as " +
                                     "an attribute. Use del_desc() instead.")
            else:
                raise AttributeError(
                    "'%s' of type %s has no attribute '%s'" %
                    (desc.get('NAME', UNNAMED), type(self), attr_name))

    def get_index(self, value):
        '''
        Returns the key that the enumeration option
        with supplied value is under in the descriptor.

        Raises DescKeyError is there is no option with the given value.
        '''
        index = object.__getattribute__(self, "desc")['VALUE_MAP'].get(value)
        if index is not None:
            return index
        desc = object.__getattribute__(self, "desc")
        raise DescKeyError(
            "'%s' of type %s has no option value matching '%s'" %
            (desc.get('NAME', UNNAMED), type(self), value))

    def get_name(self, value):
        '''
        Returns the string name of the enumeration
        with a value equal to the supplied value.

        Raises DescKeyError is there is no option with the given value.
        '''
        desc = object.__getattribute__(self, "desc")
        index = desc['VALUE_MAP'].get(value)
        if index is not None:
            return desc[index]['NAME']

        raise DescKeyError(
            "'%s' of type %s has no option value matching '%s'" %
            (desc.get('NAME', UNNAMED), type(self), value))

    def set_to(self, name):
        '''
        Sets the current enumeration to the one with the supplied name.

        Raises DescKeyError is there is no option with the given name.
        '''
        desc = object.__getattribute__(self, "desc")
        if isinstance(name, int):
            option = desc.get(name)
        else:
            option = desc.get(desc['NAME_MAP'].get(name))

        if option is None:
            raise AttributeError(
                "'%s' of type %s has no enumerator option '%s'" %
                (desc.get('NAME', UNNAMED), type(self), name))
        self.data = option['VALUE']

    @property
    def enum_name(self):
        '''
        Returns the option name of the current enumeration.
        Returns '<INVALID>' if the current enumeration is not a valid option.
        '''
        desc = object.__getattribute__(self, "desc")
        return (desc.get(desc['VALUE_MAP'].get(self.data),
                         _INVALID_NAME_DESC)[NAME])
