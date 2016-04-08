from .block import *

class DataBlock(Block):
    '''Does not allow specifying a size as anything other than an
    int literal in the descriptor/Field. Specifying size as
    a string path or a function was deemed to be unlikely to ever
    be required and is faster without having to acount for it.'''
    
    __slots__ = ("DESC", "PARENT", "data")

    def __init__(self, desc, parent=None, **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME')
        
        object.__setattr__(self, "DESC",   desc)
        object.__setattr__(self, 'PARENT', parent)

        self.data = desc['TYPE'].data_type()
        
        if kwargs:
            self.read(**kwargs)
    

    def __str__(self, **kwargs):
        '''docstring'''
        printout = kwargs.get('printout', False)
        show = kwargs.get('show', def_show)
        if isinstance(show, str):
            show = set([show])
        else:
            show = set(show)
            
        kwargs['printout'] = False
        tag_str = Block.__str__(self, **kwargs)[:-2]
        
        if "value" in show or 'all' in show:
            tag_str += ', %s' % self.data
            
        #remove the first comma
        tag_str = tag_str.replace(',','',1) + ' ]'
        
        if printout:
            print(tag_str)
            return ''
        return tag_str


    def __sizeof__(self, seenset=None):
        '''docstring'''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = object.__sizeof__(self) + getsizeof(self.data)
        
        desc = object.__getattribute__(self,'DESC')
        
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
    

    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''
        #if there is a parent, use it
        try:
            parent = object.__getattribute__(self,'PARENT')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self,'DESC'),
                          parent=parent, init_data=self.data)

    
    def __deepcopy__(self, memo):
        '''Creates a deep copy, but keeps the same descriptor.'''
        #if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        #if there is a parent, use it
        try:
            parent = object.__getattribute__(self,'PARENT')
        except AttributeError:
            parent = None

        #make a new block object sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self,'DESC'),
                               parent=parent, init_data=self.data)
        memo[id(self)] = dup_block
        
        return dup_block
       

    def _bin_size(self, block, substruct=False):
        '''Returns the size of this BoolBlock.
        This size is how many bytes it would take up if written to a buffer.'''
        if substruct:
            return 0
        return self.get_size()

    @property
    def binsize(self):
        '''Returns the size of this BoolBlock.
        This size is how many bytes it would take up if written to a buffer.'''
        return self.get_size()

        
    def get_size(self, attr_index=None, **kwargs):
        '''docstring'''
        desc = object.__getattribute__(self,'DESC')

        #determine how to get the size
        if 'SIZE' in desc:
            size = desc['SIZE']
            '''It's faster to try to add zero to size and return it than
            to try and check if it's an int using isinstance(size, int)'''
            try:
                return size+0
            except TypeError:
                raise TypeError(("size specified in '%s' is not a valid type. "+
                             "Expected int, got %s.")%(desc['NAME'],type(size)))
        #use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(self)
    

    def set_size(self, new_value=None, **kwargs):
        '''docstring.'''
        desc = object.__getattribute__(self,'DESC')
        size = desc.get('SIZE')

        #raise exception if the size is None
        if size is None:
            raise AttributeError("'SIZE' does not exist in '%s'." %desc['NAME'])

        #if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            newsize = desc['TYPE'].sizecalc(block=self.data)
        else:
            newsize = new_value

        '''It's faster to try to add zero to size and return it than
        to try and check if it's an int using isinstance(size, int)'''
        try:
            '''Because literal descriptor sizes are supposed to be
            static(unless you're changing the structure), we don't change
            the size if the new size is less than the current one.'''
            if newsize <= size+0 and new_value is None:
                return
        except TypeError:
            raise TypeError(("size specified in '%s' is not a valid type." +
                            "Expected int, got %s.")%(desc['NAME'],type(size))+
                            "\nCannot determine how to set the size." )
        
        self.set_desc('SIZE', newsize)


    def read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and add in ones that dont exist. An init_data
        can be provided with which to initialize the values of the block.'''

        init_data = kwargs.get('init_data', None)
        
        rawdata = self.get_raw_data(**kwargs)
            
        desc = object.__getattribute__(self, "DESC")
        
        if init_data is not None:
            try:
                self.data = desc.get('TYPE').data_type(init_data)
            except ValueError:
                data_type = desc.get('TYPE').data_type
                raise ValueError("'init_data' must be a value able to be "+
                                 "cast to a %s. Got %s" % (data_type,init_data))
            except TypeError:
                data_type = desc.get('TYPE').data_type
                raise ValueError("Invalid type for 'init_data'. Must be a "+
                                 "%s, not %s" % (data_type, type(init_data)))
        elif rawdata is not None:
            if not(hasattr(rawdata, 'read') and hasattr(rawdata, 'seek')):
                raise TypeError(('Cannot build %s without either an input ' +
                                 'path or a readable buffer') % type(self))
            #build the block from raw data
            try:
                try:
                    parent = object.__getattribute__(self, "PARENT")
                except AttributeError:
                    parent = None
                    
                desc['TYPE'].reader(desc, parent, rawdata, None,
                                    kwargs.get('root_offset', 0),
                                    kwargs.get('offset', 0) )
            except Exception:
                raise IOError('Error occurred while trying to read '+
                              '%s from file.' % type(self))
        else:
            #Initialize self.data to its default value
            self.data = desc.get('DEFAULT', desc.get('TYPE').data_type())


class BoolBlock(DataBlock):
    
    __slots__ = ("DESC", "PARENT", "data")

    def __str__(self, **kwargs):
        '''docstring'''
        
        printout = kwargs.get('printout', False)
        show = kwargs.get('show', def_show)
        if isinstance(show, str):
            show = set([show])
        else:
            show = set(show)
            
        #if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(all_show)

        #used to display different levels of indention
        indent_str = (' '*kwargs.get('indent', BLOCK_PRINT_INDENT)*
                         (kwargs.get('level',0)+1))
        
        desc = object.__getattribute__(self,'DESC')

        #build the main part of the string
        kwargs['printout'] = False
        tag_str = DataBlock.__str__(self, **kwargs)[:-2]
        
        if "flags" in show:
            if printout:
                if tag_str:
                    print(tag_str)
                tag_str = ''
            else:
                tag_str += '\n'

            n_spc, m_spc, name, mask_str = 0, 0, '', ''
            trueonly = 'trueonly' in show
            
            if "name" in show:
                for i in range(desc['ENTRIES']):
                    name_len = len(desc[i]['NAME'])
                    if name_len > n_spc:
                       n_spc = name_len
            if "offset" in show:
                for i in range(desc['ENTRIES']):
                    mask_len = len(str(hex(desc[i]['VALUE'])))
                    if mask_len > m_spc:
                       m_spc = mask_len
                   
            #print each of the booleans
            for i in range(desc['ENTRIES']):
                tempstr = indent_str + '['
                mask = desc[i].get('VALUE')
                spc_str = ''
                
                if "offset" in show:
                    mask_str = str(hex(mask))
                    tempstr += ', mask:' + mask_str
                    spc_str = ' '*(m_spc-len(mask_str))
                if "name" in show:
                    name = desc[i].get('NAME')
                    tempstr += ', ' + spc_str + name
                    spc_str = ' '*(n_spc-len(name))
                if "value" in show:
                    tempstr += ', ' + spc_str + str(bool(self.data&mask))

                if not trueonly or (self.data & mask):
                    tag_str += tempstr.replace(',','',1) + ' ]'
                    
                    if printout:
                        if tag_str:
                            print(tag_str)
                        tag_str = ''
                    else:
                        tag_str += '\n'
            tag_str += indent_str + ']'
        else:
            tag_str += ' ]'

        if printout:
            if tag_str:
                print(tag_str)
            return ''
        return tag_str


    def __getitem__(self, attr_index):
        '''docstring'''
        if not isinstance(name, int):
            raise TypeError("'attr_index' must be an int, not %s" % type(name))
        
        return self.data & object.__getattribute__(self, "DESC")\
               [attr_index]['VALUE']

    def __setitem__(self, attr_index, new_val):
        '''docstring'''
        if not isinstance(name, int):
            raise TypeError("'attr_index' must be an int, not %s" %type(name))
        
        mask = object.__getattribute__(self,"DESC")[attr_index]['VALUE']
        self.data = self.data - (self.data&mask) + (mask)*bool(new_val)

    def __delitem__(self, attr_index):
        '''docstring'''
        if not isinstance(name, int):
            raise TypeError("'attr_index' must be an int, not %s" % type(name))
        
        self.data -= self.data & object.__getattribute__(self,"DESC")\
                     [attr_index]['VALUE']

    def __getattr__(self, name):
        '''docstring'''
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if name in desc['NAME_MAP']:
                return self.data & desc[desc['NAME_MAP'][name]]['VALUE']
            elif name in desc:
                return desc[name]
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'"
                                     %(desc.get('NAME',UNNAMED),
                                       type(self),name))


    def __setattr__(self, name, new_val):
        '''docstring'''
        try:
            object.__setattr__(self, name, new_val)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            attr_index = desc['NAME_MAP'].get(name)
            if attr_index is not None:
                mask = desc[attr_index]['VALUE']
                self.data = self.data - (self.data&mask) + (mask)*bool(new_val)
            elif name in desc:
                self.set_desc(name)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (desc.get('NAME',UNNAMED),
                                      type(self),name))

    def __delattr__(self, name):
        '''docstring'''
        try:
            object.__delattr__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")

            attr_index = desc['NAME_MAP'].get(name)
            if attr_index is not None:
                #unset the flag and remove the option from the descriptor
                self.data -= self.data & desc[attr_index]['VALUE']
                self.del_desc(attr_index)
            elif name in desc:
                self.del_desc(name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME',UNNAMED),
                                      type(self),name))
        
    def set(self, name):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s"%type(name))
        desc = object.__getattribute__(self, "DESC")
        mask = desc[desc['NAME_MAP'][name]]['VALUE']
        self.data = (self.data-(self.data&mask))+mask

    
    def set_to(self, name, value):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s"%type(name))
        desc = object.__getattribute__(self, "DESC")
        mask = desc[desc['NAME_MAP'][name]]['VALUE']
        self.data = self.data - (self.data&mask) + (mask)*bool(value)
    

    def unset(self, name):
        '''docstring'''
        if not isinstance(name, str):
            raise TypeError("'name' must be a string, not %s"%type(name))
        desc = object.__getattribute__(self, "DESC")
        self.data -= self.data & desc[desc['NAME_MAP'][name]]['VALUE']

        
    def read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An init_data
        can be provided with which to initialize the values of the block.'''

        attr_index = kwargs.get('attr_index',None)
        init_data  = kwargs.get('init_data', None)
        
        rawdata = self.get_raw_data(**kwargs)
            
        if init_data is not None:
            try:
                self.data = int(init_data)
            except ValueError:
                raise ValueError("'init_data' must be a value able to be "+
                                 "converted to an integer. Got %s"%init_data)
            except TypeError:
                raise ValueError("Invalid type for 'init_data'. Must be a "+
                                 "string or a number, not %s"%type(init_data))
        elif kwargs.get('init_attrs', True):
            desc = object.__getattribute__(self, "DESC")
            new_val = 0
            for i in range(desc['ENTRIES']):
                opt = desc[i]
                new_val += bool(opt.get('VALUE') & opt.get('DEFAULT', 0))
                    
            self.data = new_val
                
        elif rawdata is not None:
            #build the block from raw data
            try:
                desc = object.__getattribute__(self, "DESC")
                desc['TYPE'].reader(desc, self, rawdata, None,
                                    kwargs.get('root_offset', 0),
                                    kwargs.get('offset', 0))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read BoolBlock from file.')
            

class EnumBlock(DataBlock):
    
    __slots__ = ("DESC", "PARENT", "data")
    
    def __str__(self, **kwargs):
        '''docstring'''
        
        printout = kwargs.get('printout', False)
        show = kwargs.get('show', def_show)
        if isinstance(show, str):
            show = set([show])
        else:
            show = set(show)
            
        #if the list includes 'all' it means to show everything
        if 'all' in show:
            show.update(all_show)

        #used to display different levels of indention
        indent_str = (' '*kwargs.get('indent', BLOCK_PRINT_INDENT)*
                         (kwargs.get('level',0)+1))
        
        desc = object.__getattribute__(self,'DESC')

        #build the main part of the string
        kwargs['printout'] = False
        tag_str = DataBlock.__str__(self, **kwargs)[:-2]

        if printout:
            if tag_str:
                print(tag_str)
            tag_str = ''
        else:
            tag_str += '\n'
            
        #find which index the string matches to
        try:
            index = self.get_index(self.data)
        except AttributeError:
            index = None
        
        opt = desc.get(index, {})
        tag_str += indent_str + ' %s ]' % opt.get('NAME',INVALID)

        if printout:
            if tag_str:
                print(tag_str)
            return ''
        return tag_str


    def __getattr__(self, name):
        '''docstring'''
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if name in desc:
                return desc[name]
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot get enumerator option as an "+
                                     "attribute. Use Get() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME',UNNAMED),
                                      type(self),name))
            

    def __setattr__(self, name, new_value):
        '''docstring'''
        try:
            object.__setattr__(self, name, new_value)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if name in desc:
                if name == 'CHILD':
                    raise AttributeError(("'%s' of type %s has no slot for a "+
                            "CHILD.")%(desc.get('NAME',UNNAMED),type(self)))
                self.set_desc(name, new_value)
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot set enumerator option as an "+
                                     "attribute. Use set() instead.")
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (desc.get('NAME',UNNAMED),
                                      type(self),name))


    def __delattr__(self, name):
        '''docstring'''
        try:
            object.__delattr__(self, name)
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if name in desc:
                self.del_desc(name)
            elif name in desc['NAME_MAP']:
                raise AttributeError("Cannot delete enumerator option as "+
                                     "an attribute. Use del_desc() instead.")
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME',UNNAMED),
                                      type(self),name))
        

    def get_index(self, value):
        '''docstring'''
        index = object.__getattribute__(self, "DESC")['VALUE_MAP'].get(value)
        if index is not None:
            return index
        desc = object.__getattribute__(self, "DESC")
        raise AttributeError("'%s' of type %s has no option value matching '%s'"
                             % (desc.get('NAME',UNNAMED),type(self),value))

    def get_name(self, value):
        '''docstring'''
        desc = object.__getattribute__(self, "DESC")
        index = desc['VALUE_MAP'].get(value)
        if index is not None:
            return desc[index]['NAME']
        
        raise AttributeError("'%s' of type %s has no option value matching '%s'"
                             % (desc.get('NAME',UNNAMED),type(self),value))

    
    def get_data(self, name):
        '''docstring'''
        desc = object.__getattribute__(self, "DESC")
        if isinstance(name, int):
            option = desc.get(name)
        else:
            option = desc.get(desc['NAME_MAP'].get(name))
        
        if option is None:
            raise AttributeError("'%s' of type %s has no enumerator option '%s'"
                                %(desc.get('NAME',UNNAMED),type(self),name))
        data = option['VALUE']
        return (self.data == data) and (type(self.data) == type(data))

        
    def set_data(self, name):
        '''docstring'''
        desc = object.__getattribute__(self, "DESC")
        if isinstance(name, int):
            option = desc.get(name)
        else:
            option = desc.get(desc['NAME_MAP'].get(name))
        
        if option is None:
            raise AttributeError("'%s' of type %s has no enumerator option '%s'"
                                %(desc.get('NAME',UNNAMED),type(self),name))
        self.data = option['VALUE']

    @property
    def data_name(self):
        '''Exists as a property based way of determining
        the option name of the current value of self.data'''
        desc = object.__getattribute__(self, "DESC")
        return desc.get(desc['VALUE_MAP'].get(self.data),{NAME:INVALID})[NAME]
