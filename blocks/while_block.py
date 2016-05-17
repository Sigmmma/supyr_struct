from .list_block import *

class WhileBlock(ListBlock):
    '''docstring'''
    __slots__ = ('DESC', 'PARENT')

    def __setitem__(self, index, new_value):
        '''enables setting attributes by providing
        the attribute name string as an index'''
        if isinstance(index, int):
            #handle accessing negative indexes
            if index < 0:
                index += len(self)
            list.__setitem__(self, index, new_value)

            '''if the object being placed in the Block
            has a 'PARENT' attribute, set this block to it'''
            if hasattr(new_value, 'PARENT'):
                object.__setattr__(new_value, 'PARENT', self)
                
        elif isinstance(index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step
            
            assert hasattr(new_value, '__iter__'), ("must assign iterable "+
                                                    "to extended slice")
                
            slice_size = (stop-start)//step
            
            if step != -1 and slice_size > len(new_value):
                raise ValueError("attempt to assign sequence of size "+
                                 "%s to extended slice of size %s" %
                                 (len(new_value), slice_size))
            
            list.__setitem__(self, index, new_value)
        else:
            self.__setattr__(index, new_value)


    def __delitem__(self, index):
        '''enables deleting attributes by providing
        the attribute name string as an index'''
        if isinstance(index, str):
            self.__delattr__(index)
        else:
            if index < 0:
                index += len(self)
            list.__delitem__(self, index)
            

    def append(self, new_attr=None, new_desc=None):
        '''Allows appending objects to this Block while taking
        care of all descriptor related details.
        Function may be called with no arguments if this block type is
        an Array. Doing so will append a fresh structure to the array
        (as defined by the Array's SUB_STRUCT descriptor value).'''

        #create a new, empty index
        list.append(self, None)

        try:
            desc = object.__getattribute__(self,'DESC')

            '''if this block is an array and "new_attr" is None
            then it means to append a new block to the array'''
            if new_attr is None:
                attr_desc = desc['SUB_STRUCT']
                attr_field = attr_desc['TYPE']

                '''if the type of the default object is a type of Block
                then we can create one and just append it to the array'''
                if issubclass(attr_field.py_type, Block):
                    attr_field.reader(attr_desc, self, None, len(self)-1)
                    return
        
            list.__setitem__(self, -1, new_attr)
        except Exception:
            list.__delitem__(self, -1)
            raise
        try:
            object.__setattr__(new_attr, 'PARENT', self)
        except Exception:
            pass
            

    def extend(self, new_attrs):
        '''Allows extending this ListBlock with new attributes.
        Provided argument must be a ListBlock so that a descriptor
        can be found for all attributes, whether they carry it or
        the provided block does.
        Provided argument may also be an integer if this block type is an Array.
        Doing so will extend the array with that amount of fresh structures
        (as defined by the Array's SUB_STRUCT descriptor value)'''
        if isinstance(new_attrs, ListBlock):
            desc = new_attrs.DESC
            for i in range(len(ListBlock)):
                self.append(new_attrs[i], desc[i])
        elif isinstance(new_attrs, int):
            #if this block is an array and "new_attr" is an int it means
            #that we are supposed to append this many of the SUB_STRUCT
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

        #create a new, empty index
        list.insert(self, index, None)

        new_desc = object.__getattribute__(self,'DESC')['SUB_STRUCT']
        new_field = new_desc['TYPE']

        try:
            '''if the type of the default object is a type of Block
            then we can create one and just append it to the array'''
            if new_attr is None and issubclass(new_field.py_type, Block):
                new_field.reader(new_desc, self, None, index)
                #finished, so return
                return
        except Exception:
            list.__delitem__(self, index)
            raise

        #if the new_attr has its own descriptor,
        #use that instead of any provided one
        try:
            new_desc = new_attr.DESC
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
            object.__setattr__(new_attr, 'PARENT', self)
        except Exception:
            pass


    def pop(self, index=-1):
        '''Pops the attribute at 'index' out of the ListBlock
        and returns a tuple containing it and its descriptor.'''
        
        desc = object.__getattribute__(self, "DESC")
        
        if isinstance(index, int):
            if index < 0:
                return (list.pop(self, index + len(self)), desc['SUB_STRUCT'])
            return (list.pop(self, index), desc['SUB_STRUCT'])
        elif 'NAME' in desc:
            raise AttributeError("'%s' of type %s has no attribute '%s'"
                                 % (desc['NAME'], type(self), index))
        else:
            raise AttributeError("'%s' has no attribute '%s'"
                                 %(type(self), index))
            
        return(attr, desc)


    def get_size(self, attr_index=None, **kwargs):
        '''Returns the size of self[attr_index] or self if attr_index == None.
        size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''

        if isinstance(attr_index, int):
            desc = object.__getattribute__(self,'DESC')
            block = self[attr_index]
            desc = desc['SUB_STRUCT']
        elif isinstance(attr_index, str):
            desc = object.__getattribute__(self,'DESC')
            block = self.__getattr__(attr_index)
            try:
                desc = desc[desc['NAME_MAP'][attr_index]]
            except Exception:
                desc = desc[attr_index]
        else:
            return len(self)
            

        #determine how to get the size
        if 'SIZE' in desc:
            size = desc['SIZE']
            
            if isinstance(size, int):
                return size
            elif isinstance(size, str):
                '''get the pointed to size data by traversing the tag
                structure along the path specified by the string'''
                return self.get_neighbor(size, block)
            elif hasattr(size, "__call__"):
                '''find the pointed to size data by
                calling the provided function'''
                try:
                    parent = block.PARENT
                except AttributeError:
                    parent = self
                    
                return size(attr_index=attr_index, parent=parent,
                            block=block, **kwargs)
            else:
                block_name = object.__getattribute__(self,'DESC')['NAME']
                if isinstance(attr_index, (int,str)):
                    block_name = attr_index
                raise TypeError(("size specified in '%s' is not a valid type."+
                                 "\nExpected int, str, or function. Got %s.") %
                                (block_name, type(size)) )
        #use the size calculation routine of the Field
        return desc['TYPE'].sizecalc(block)



    def set_size(self, new_value=None, attr_index=None, op=None, **kwargs):
        '''Sets the size of self[attr_index] or self if attr_index == None.
        size units are dependent on the data type being measured. Structs and
        variables will be measured in bytes and containers/arrays will be
        measured in entries. Checks the data type and descriptor for the size.
        The descriptor may specify size in terms of already parsed fields.'''
        
        desc = object.__getattribute__(self,'DESC')
        
        if isinstance(attr_index, int):
            block = self[attr_index]
            size = desc['SUB_STRUCT'].get('SIZE')
            field = self.get_desc(TYPE, attr_index)
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)

            error_num = 0
            #try to get the size directly from the block
            try:
                #do it in this order so desc doesnt get
                #overwritten if SIZE can't be found in desc
                size = block.DESC['SIZE']
                desc = block.DESC
            except Exception:
                #if that fails, try to get it from the descriptor of the parent
                try:
                    desc = desc[desc['NAME_MAP'][attr_index]]
                except Exception:
                    desc = desc[attr_index]

                try:
                    size = desc['SIZE']
                except Exception:
                    #its parent cant tell us the size, raise this error
                    error_num = 1
                    if 'TYPE' in desc and not desc['TYPE'].is_var_size:
                        #the size is not variable so it cant be set
                        #without changing the type. raise this error
                        error_num = 2
            
            block_name = desc.get('NAME')
            if isinstance(attr_index, (int,str)):
                block_name = attr_index
            if error_num == 1:
                raise AttributeError(("Could not determine size for "+
                                      "attribute '%s' in block '%s'.") %
                                     (block_name, object.__getattribute__\
                                      (self,'DESC')['NAME']))
            elif error_num == 2:
                raise AttributeError(("Can not set size for attribute '%s' "+
                                      "in block '%s'.\n'%s' has a fixed size "+
                                      "of '%s'.\nTo change the size of '%s' "+
                                      "you must change its data type.") %
                                     (block_name, object.__getattribute__\
                                      (self,'DESC')['NAME'],
                                   desc['TYPE'], desc['TYPE'].size, block_name))
            field = desc['TYPE']
        else:
            #cant set size of While_Arrays
            return

        #raise exception if the size is None
        if size is None:
            block_name = desc['NAME']
            if isinstance(attr_index, (int,str)):
                block_name = attr_index
            raise AttributeError("'SIZE' does not exist in '%s'." % block_name)

        #if a new size wasnt provided then it needs to be calculated
        if new_value is None:
            op = None
            if hasattr(block, 'PARENT'):
                parent = block.PARENT
            else:
                parent = self
        
            newsize = field.sizecalc(parent=parent, block=block,
                                      attr_index=attr_index)
        else:
            newsize = new_value


        if isinstance(size, int):
            '''Because literal descriptor sizes are supposed to be static
            (unless you're changing the structure), we don't change the size
            if the new size is less than the current one. This has the added
            benefit of not having to create a new unique descriptor, thus saving
            RAM. This can be bypassed by explicitely providing the new size.'''
            if new_value is None and newsize <= size:
                return

            #if the size if being automatically set and it SHOULD
            #be a fixed size, then try to raise a UserWarning
            '''Enable this code when necessary'''
            #if kwargs.get('warn', True):
            #    raise UserWarning('Cannot change a fixed size.')
            
            if op is None:
                self.set_desc('SIZE', newsize, attr_index)
            elif op == '+':
                self.set_desc('SIZE', size+newsize, attr_index)
            elif op == '-':
                self.set_desc('SIZE', size-newsize, attr_index)
            elif op == '*':
                self.set_desc('SIZE', size*newsize, attr_index)
            else:
                raise TypeError("Unknown operator '%s' for setting size" % op)
            
        elif isinstance(size, str):
            '''set size by traversing the tag structure
            along the path specified by the string'''
            self.set_neighbor(size, newsize, block, op)
        elif hasattr(size, "__call__"):
            '''set size by calling the provided function'''
            if hasattr(block, 'PARENT'):
                parent = block.PARENT
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
            block_name = object.__getattribute__(self,'DESC')['NAME']
            if isinstance(attr_index, (int,str)):
                block_name = attr_index
            
            raise TypeError(("size specified in '%s' is not a valid type." +
                             "Expected int, str, or function. Got %s.\n") %
                            (block_name, type(size)) +
                            "Cannot determine how to set the size." )


    def read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An init_data
        can be provided with which to initialize the values of the block.'''

        attr_index = kwargs.get('attr_index',None)
        init_attrs = kwargs.get('init_attrs',True)
        init_data  = kwargs.get('init_data', None)

        #if an init_data was provided, make sure it can be used
        assert (init_data is None or
                (hasattr(init_data, '__iter__') and
                 hasattr(init_data, '__len__'))), (
                     "init_data must be an iterable with a length")
        
        rawdata = self.get_rawdata(**kwargs)
            
        desc = object.__getattribute__(self, "DESC")
        
        if attr_index is not None:
            #if we are reading or initializing just one attribute
            if isinstance(attr_index, str):
                attr_index = desc['NAME_MAP'][attr_index]

            #read the attr_index and return
            attr_desc = desc[attr_index]
            return attr_desc[TYPE].reader(attr_desc, self, rawdata, attr_index,
                                          kwargs.get('root_offset',0),
                                          kwargs.get('offset',0),
                                          int_test=kwargs.get('int_test',0))
        else:
            #if we are reading or initializing EVERY attribute
            list.__delitem__(self, slice(None, None, None))

            '''If the init_data is not None then try
            to use it to populate the ListBlock'''
            if init_data is not None:
                list.extend(self, [None]*len(init_data[i]))
                for i in range(len(init_data)):
                    self.__setitem__(i, init_data[i])
        

        #initialize the attributes
        if rawdata is not None:
            #build the structure from raw data
            try:
                desc['TYPE'].reader(desc, self, rawdata, attr_index,
                                    kwargs.get('root_offset',0),
                                    kwargs.get('offset',0),
                                    int_test = kwargs.get('int_test',False))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read %s from file' % type(self))
                
        elif init_attrs:
            '''This ListBlock is an array, so the type of each
            element should be the same then initialize it'''
            try:
                attr_desc = desc['SUB_STRUCT']
                attr_field = attr_desc['TYPE']
            except Exception: 
                raise TypeError("Could not locate the array element " +
                                "descriptor.\nCould not initialize array")

            #loop through each element in the array and initialize it
            for i in range(len(self)):
                attr_field.reader(attr_desc, self, None, i)

            '''Only initialize the child if the block has a
            child and a value for it doesnt already exist.'''
            c_desc = desc.get('CHILD')
            if c_desc:
                c_desc['TYPE'].reader(c_desc, self, None, 'CHILD')


class PWhileBlock(WhileBlock):
    '''docstring'''
    __slots__ = ('DESC', 'PARENT', 'CHILD')
    
    def __init__(self, desc, child=None, parent=None,**kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME')
        assert 'CHILD' in desc and 'NAME_MAP' in desc and 'ENTRIES' in desc
        
        object.__setattr__(self, 'CHILD',  child)
        object.__setattr__(self, 'DESC',   desc)
        object.__setattr__(self, 'PARENT', parent)
        
        self.read(**kwargs)
    
    def __sizeof__(self, seenset=None):
        '''docstring'''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = list.__sizeof__(self)

        if hasattr(self, 'CHILD'):
            child = object.__getattribute__(self,'CHILD')
            if isinstance(child, Block):
                bytes_total += child.__sizeof__(seenset)
            else:
                seenset.add(id(child))
                bytes_total += getsizeof(child)
                
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
        
        for i in range(len(self)):
            item = list.__getitem__(self, i)
            if not id(item) in seenset:
                bytes_total += item.__sizeof__(seenset)
            
        return bytes_total


    def __setattr__(self, attr_name, new_value):
        '''docstring'''
        try:
            object.__setattr__(self, attr_name, new_value)
            if attr_name == 'CHILD':
                field = object.__getattribute__(self,'DESC')['CHILD']['TYPE']
                if field.is_var_size and field.is_data:
                    #try to set the size of the attribute
                    try:
                        self.set_size(None, 'CHILD')
                    except NotImplementedError: pass
                    except AttributeError: pass
                    
                #if this object is being given a child then try to
                #automatically give the child this object as a parent
                try:
                    if object.__getattribute__(new_value, 'PARENT') != self:
                        object.__setattr__(new_value, 'PARENT', self)
                except Exception:
                    pass
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if attr_name in desc:
                self.set_desc(attr_name, new_value)
            else:
                raise AttributeError(("'%s' of type %s has no attribute '%s'")%
                                     (desc.get('NAME',UNNAMED),
                                      type(self), attr_name))

    def __delattr__(self, attr_name):
        '''docstring'''
        try:
            object.__delattr__(self, attr_name)
            if attr_name == 'CHILD':
                #set the size of the block to 0 since it's being deleted
                try:   self.set_size(0, 'CHILD')
                except NotImplementedError: pass
                except AttributeError: pass
        except AttributeError:
            desc = object.__getattribute__(self, "DESC")
            
            if attr_name in desc:
                self.del_desc(attr_name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME',UNNAMED),
                                     type(self),attr_name))
