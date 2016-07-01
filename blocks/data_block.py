from copy import deepcopy
from .block import *

_INVALID_NAME_DESC = {NAME: INVALID}


class DataBlock(Block):
    '''Does not allow specifying a size as anything other than an
    int literal in the descriptor/Field. Specifying size as
    a string path or a function was deemed to be unlikely to ever
    be required and is faster without having to account for it.'''

    __slots__ = ("desc", "parent", "data")

    def __init__(self, desc, parent=None, **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, 'parent', parent)

        self.data = desc['TYPE'].data_type()

        if kwargs:
            self.build(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this DataBlock.

        Optional keywords arguments:
        # int:
        indent ------ The number of spaces of indent added per indent level
        precision --- The number of decimals to round floats to

        # set:
        show -------- An iterable containing strings specifying what to
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
        '''docstring'''
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
        '''Creates a shallow copy, keeping the same descriptor.'''
        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self, 'desc'),
                          parent=parent, initdata=self.data)

    def __deepcopy__(self, memo):
        '''Creates a deep copy, keeping the same descriptor.'''
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

    def _binsize(self, block, substruct=False):
        '''Returns the size of this Block.
        This size is how many bytes it would take up if written to a buffer.'''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''Returns the size of this Block.
        This size is how many bytes it would take up if written to a buffer.'''
        return self.get_size()

    def get_size(self, attr_index=None, **kwargs):
        '''docstring'''
        desc = object.__getattribute__(self, 'desc')

        # determine how to get the size
        if 'SIZE' in desc:
            try:
                return desc['SIZE'] >> 0
            except TypeError:
                raise TypeError(("Size specified in '%s' is not a " +
                                 "valid type.\nExpected int, got %s.") %
                                (desc['NAME'], type(desc['SIZE'])))
        # use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(self)

    def set_size(self, new_value=None, attr_index=None, op=None, **kwargs):
        '''docstring.'''
        desc = object.__getattribute__(self, 'desc')
        size = desc.get('SIZE')

        # raise exception if the size is None
        if size is None:
            raise AttributeError("'SIZE' does not exist in '%s'." %
                                 desc['NAME'])

        # if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            newsize = desc['TYPE'].sizecalc(block=self.data)
        else:
            newsize = new_value

        # Its faster to try to bitshift the size
        # by 0 and return it than to check if it's
        # an int using isinstance(size, int).
        try:
            # Because literal descriptor sizes are supposed to be static
            # (unless you're changing the structure), we don't even try to
            # change the size if the new size is less than the current one.
            if newsize >> 0 <= size and new_value is None:
                return
        except TypeError:
            raise TypeError(("Size specified in '%s' is not a valid type.\n" +
                             "Expected int, got %s.\nCannot determine how " +
                             "to set the size.") % (desc['NAME'], type(size)))

        self.set_desc('SIZE', newsize)

    def build(self, **kwargs):
        '''This function will initialize all of a DataBlocks attributes to
        their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

        initdata = kwargs.get('initdata')
        rawdata = self.get_rawdata(**kwargs)
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
            assert (hasattr(rawdata, 'read') and hasattr(rawdata, 'seek')), (
                'Cannot build %s without an input path or a readable buffer' %
                type(self))
            # build the block from raw data
            try:
                try:
                    parent = object.__getattribute__(self, "parent")
                except AttributeError:
                    parent = None

                desc['TYPE'].reader(desc, parent, rawdata, None,
                                    kwargs.get('root_offset', 0),
                                    kwargs.get('offset', 0))
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
            # Initialize self.data to its default value
            self.data = desc.get('DEFAULT', desc.get('TYPE').data_type())


class WrapperBlock(DataBlock):

    __slots__ = ()

    def __init__(self, desc, parent=None, **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, "parent", parent)

        self.data = None

        if kwargs:
            self.build(**kwargs)

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this WrapperBlock.

        Optional keywords arguments:
        # int:
        indent ------ The number of spaces of indent added per indent level
        precision --- The number of decimals to round floats to

        # set:
        show -------- An iterable containing strings specifying what to
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
        show = kwargs.get('show', DEF_SHOW)
        if isinstance(show, str):
            show = [show]
        show = set(show)

        tag_str = Block.__str__(self, **kwargs)[:-2].replace(',', '', 1) + '\n'

        kwargs['attr_name'] = None
        del kwargs['attr_name']
        kwargs['level'] = level = kwargs.get('level', 0) + 1

        indent_str = ' ' * level * kwargs.get('indent', BLOCK_PRINT_INDENT)

        return (tag_str + self.attr_to_str(SUB_STRUCT, **kwargs) +
                indent_str + ']')

    def get_size(self, attr_index=None, **kwargs):
        '''docstring'''
        if isinstance(self.data, Block):
            return self.data.get_size(**kwargs)

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
                            block=self.data, **kwargs)

            raise TypeError(("Size specified in '%s' is not a valid type." +
                             "\nExpected str or function. Got %s.") %
                            (attr_index, type(size)))
        # use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(object.__getattribute__(self, 'data'))

    def set_size(self, new_value=None, attr_index=None, op=None, **kwargs):
        '''docstring.'''
        desc = object.__getattribute__(self, 'desc')['SUB_STRUCT']
        size = desc.get('SIZE')
        field = desc['TYPE']

        # raise exception if the size is None
        if size is None:
            raise AttributeError("'SIZE' does not exist in '%s'." %
                                 desc['NAME'])

        # if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            op = None
            newsize = field.sizecalc(parent=self, block=self.data,
                                     attr_index='data')
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
            self.set_neighbor(size, newsize, self.data, op)
            return
        elif hasattr(size, '__call__'):
            # set size by calling the provided function
            if op is None:
                pass
            elif op == '+':
                newsize += size(attr_index='data', parent=self,
                                block=self.data, **kwargs)
            elif op == '-':
                newsize = (size(attr_index='data', parent=self,
                                block=self.data, **kwargs) - newsize)
            elif op == '*':
                newsize *= size(attr_index='data', parent=self,
                                block=self.data, **kwargs)
            else:
                raise TypeError("Unknown operator '%s' for setting size" % op)

            size(attr_index='data', new_value=newsize,
                 parent=self, block=self.data, **kwargs)
            return

        raise TypeError(("size specified in '%s' is not a valid type.\n" +
                         "Expected str or function, got %s.\nCannot " +
                         "determine how to set the size.") %
                        (desc['NAME'], type(size)))

    def build(self, **kwargs):
        '''This function will initialize all of a WrapperBlocks attributes
        to their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

        initdata = kwargs.get('initdata')

        if initdata is not None:
            # set the data attribute to the initdata
            self.data = initdata
            return

        desc = object.__getattribute__(self, "desc")

        # build the block from raw data
        try:
            desc['TYPE'].reader(desc, self, self.get_rawdata(**kwargs),
                                'data', kwargs.get('root_offset', 0),
                                kwargs.get('offset', 0))
        except Exception as e:
            a = e.args[:-1]
            e_str = "\n"
            try:
                e_str = e.args[-1] + e_str
            except IndexError:
                pass
            e.args = a + (e_str + "Error occurred while " +
                          "attempting to build %s." % type(self),)


class BoolBlock(DataBlock):

    __slots__ = ()

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this BoolBlock.

        Optional keywords arguments:
        # int:
        indent ------ The number of spaces of indent added per indent level

        # set:
        show -------- An iterable containing strings specifying what to
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
        '''docstring'''
        if not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int, not %s" %
                            type(attr_index))
        return self.data & (object.__getattribute__(self, "desc")
                            [attr_index]['VALUE'])

    def __setitem__(self, attr_index, new_val):
        '''docstring'''
        if not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int, not %s" %
                            type(attr_index))
        mask = object.__getattribute__(self, "desc")[attr_index]['VALUE']
        self.data = self.data - (self.data & mask) + (mask)*bool(new_val)

    def __delitem__(self, attr_index):
        '''docstring'''
        if not isinstance(attr_index, int):
            raise TypeError("'attr_index' must be an int, not %s" %
                            type(attr_index))
        self.data -= self.data & (object.__getattribute__(self, "desc")
                                  [attr_index]['VALUE'])

    def __getattr__(self, name):
        '''docstring'''
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if name in desc['NAME_MAP']:
                return self.data & desc[desc['NAME_MAP'][name]]['VALUE']
            elif name in desc:
                return desc[name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def __setattr__(self, name, new_val):
        '''docstring'''
        try:
            object.__setattr__(self, name, new_val)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            attr_index = desc['NAME_MAP'].get(name)
            if attr_index is not None:
                mask = desc[attr_index]['VALUE']
                self.data = (self.data - (self.data & mask) +
                             (mask)*bool(new_val))
            elif name in desc:
                self.set_desc(name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def __delattr__(self, name):
        '''docstring'''
        try:
            object.__delattr__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            attr_index = desc['NAME_MAP'].get(name)
            if attr_index is not None:
                # unset the flag and remove the option from the descriptor
                self.data -= self.data & desc[attr_index]['VALUE']
                self.del_desc(attr_index)
            elif name in desc:
                self.del_desc(name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def set(self, name):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s" % type(name))
        desc = object.__getattribute__(self, "desc")
        mask = desc[desc['NAME_MAP'][name]]['VALUE']
        self.data = self.data - (self.data & mask) + mask

    def set_to(self, name, value):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s" % type(name))
        desc = object.__getattribute__(self, "desc")
        mask = desc[desc['NAME_MAP'][name]]['VALUE']
        self.data = self.data - (self.data & mask) + mask*bool(value)

    def unset(self, name):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s" % type(name))
        desc = object.__getattribute__(self, "desc")
        self.data -= self.data & desc[desc['NAME_MAP'][name]]['VALUE']

    def build(self, **kwargs):
        '''This function will initialize all of a BoolBlocks attributes to
        their default value and add in ones that dont exist. An initdata
        can be provided with which to initialize the values of the block.'''

        initdata = kwargs.get('initdata')

        if initdata is not None:
            try:
                self.data = int(initdata)
                return  # return early
            except ValueError:
                raise ValueError("'initdata' must be a value able to be " +
                                 "cast to an integer. Got %s" % initdata)
            except TypeError:
                raise ValueError("Invalid type for 'initdata'. Must be a " +
                                 "string or a number, not %s" % type(initdata))

        rawdata = self.get_rawdata(**kwargs)
        if rawdata is not None:
            # build the block from raw data
            try:
                desc = object.__getattribute__(self, "desc")
                desc['TYPE'].reader(desc, self, rawdata, None,
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
            desc = object.__getattribute__(self, "desc")
            new_val = 0
            for i in range(desc['ENTRIES']):
                opt = desc[i]
                new_val += opt.get('VALUE') * bool(opt.get('DEFAULT', 0))
            self.data = new_val


class EnumBlock(DataBlock):

    __slots__ = ()

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this EnumBlock.

        Optional keywords arguments:
        # int:
        indent ------ The number of spaces of indent added per indent level
        precision --- The number of decimals to round floats to

        # set:
        show -------- An iterable containing strings specifying what to
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
        except AttributeError:
            index = None

        opt = desc.get(index, {})
        tag_str += indent_str + ' %s ]' % opt.get('NAME', INVALID)

        return tag_str

    def __getattr__(self, name):
        '''docstring'''
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if name in desc:
                return desc[name]
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot get enumerator option as an " +
                                     "attribute. Use Get() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def __setattr__(self, name, new_value):
        '''docstring'''
        try:
            object.__setattr__(self, name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if name in desc:
                if name == 'CHILD':
                    raise AttributeError(("'%s' of type %s has no " +
                                          "slot for a CHILD.") %
                                         (desc.get('NAME', UNNAMED),
                                          type(self)))
                self.set_desc(name, new_value)
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot set enumerator option as an " +
                                     "attribute. Use set() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def __delattr__(self, name):
        '''docstring'''
        try:
            object.__delattr__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "desc")

            if name in desc:
                self.del_desc(name)
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot delete enumerator option as " +
                                     "an attribute. Use del_desc() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME', UNNAMED),
                                      type(self), name))

    def get_index(self, value):
        '''docstring'''
        index = object.__getattribute__(self, "desc")['VALUE_MAP'].get(value)
        if index is not None:
            return index
        desc = object.__getattribute__(self, "desc")
        raise AttributeError(("'%s' of type %s has no option value " +
                              "matching '%s'") % (desc.get('NAME', UNNAMED),
                                                  type(self), value))

    def get_name(self, value):
        '''docstring'''
        desc = object.__getattribute__(self, "desc")
        index = desc['VALUE_MAP'].get(value)
        if index is not None:
            return desc[index]['NAME']

        raise AttributeError(("'%s' of type %s has no option value " +
                              "matching '%s'") % (desc.get('NAME', UNNAMED),
                                                  type(self), value))

    def get_data(self, name):
        '''docstring'''
        desc = object.__getattribute__(self, "desc")
        if isinstance(name, int):
            option = desc.get(name)
        else:
            option = desc.get(desc['NAME_MAP'].get(name))

        if option is None:
            raise AttributeError(("'%s' of type %s has no enumerator " +
                                  "option '%s'") % (desc.get('NAME', UNNAMED),
                                                    type(self), name))
        data = option['VALUE']
        return (self.data == data) and (type(self.data) == type(data))

    def set_data(self, name):
        '''docstring'''
        desc = object.__getattribute__(self, "desc")
        if isinstance(name, int):
            option = desc.get(name)
        else:
            option = desc.get(desc['NAME_MAP'].get(name))

        if option is None:
            raise AttributeError(("'%s' of type %s has no enumerator " +
                                  "option '%s'") % (desc.get('NAME', UNNAMED),
                                                    type(self), name))
        self.data = option['VALUE']

    @property
    def data_name(self):
        '''Exists as a property based way of determining
        the option name of the current value of self.data'''
        desc = object.__getattribute__(self, "desc")
        return (desc.get(desc['VALUE_MAP'].get(self.data),
                         _INVALID_NAME_DESC)[NAME])
