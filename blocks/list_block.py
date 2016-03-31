from .block import *

class ListBlock(list, Block):
    """
    List_Blocks are the primary method of storing hierarchial
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
    
    __slots__ = ("DESC", "PARENT")

    def __init__(self, desc=None, parent=None, **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME')
        assert 'NAME_MAP' in desc and 'ENTRIES' in desc
        
        object.__setattr__(self, "DESC",   desc)
        object.__setattr__(self, 'PARENT', parent)
        
        if kwargs:
            self.read(**kwargs)

    
    def __str__(self, **kwargs):
        '''docstring'''
        #set the default things to show
        show = set(def_show)
        
        seen = kwargs['seen'] = set(kwargs.get('seen',()))
        seen.add(id(self))
        
        if "show" in kwargs:
            show = kwargs['show']
            if isinstance(kwargs["show"], str):
                show = set([show])
            else:
                show = set(show)
                
        level  = kwargs.get('level', 0)
        indent = kwargs.get('indent', BLOCK_PRINT_INDENT)
        block_index = kwargs.get('block_index', None)
        precision = kwargs.get('precision', None)
        printout  = kwargs.get('printout', False)

        #if the list includes 'all' it means to show everything
        if 'all' in show:
            show.remove('all')
            show.update(all_show)

        print_ramsize = "ramsize" in show
        print_binsize = "binsize" in show
        print_children = "children" in show
        print_py_type = "py_type" in show
        print_py_id = "py_id" in show
        print_offset = "offset" in show
        print_unique = "unique" in show
        print_flags = "flags" in show
        print_value = "value" in show
        print_index = "index" in show
        print_type = "field" in show
        print_name = "name" in show
        print_size = "size" in show
        print_raw = "raw" in show
        
        if print_ramsize: show.remove('ramsize')
        if print_binsize: show.remove('binsize')

        kwargs['show'] = show

        #used to display different levels of indention
        indent_str0 = ' '*indent*level
        indent_str1 = ' '*indent*(level+1)
        indent_str2 = ' '*indent*(level+2)
        
        tag_str =  indent_str0 + '['
        kwargs['level'] = level+1
        
        tempstr = ''

        desc = object.__getattribute__(self,'DESC')
        
        if print_index and block_index is not None:
            tempstr = ', #:%s' % block_index
        if print_type and hasattr(self, 'TYPE'):
            tempstr += ', %s' % desc['TYPE'].name
        if print_offset:
            if hasattr(self, POINTER):
                tempstr += ', pointer:%s' % self.get_meta('POINTER')
            else:
                try:
                    tempstr += (', offset:%s' % self.PARENT['ATTR_OFFS']\
                                   [block_index])
                except Exception:
                    pass
        if print_unique:
            tempstr += ', unique:%s' % ('ORIG_DESC' in desc)
        if print_py_id:
            tempstr += ', py_id:%s' % id(self)
        if print_py_type:
            tempstr += ', py_type:%s' % desc['TYPE'].py_type
        if print_size:
            if hasattr(self, 'SIZE') and not desc['TYPE'].is_container:
                tempstr += ', size:%s' % self.get_size()
            tempstr += ', entries:%s' % len(self)
        if print_name and 'NAME' in desc:
            if 'block_name' in kwargs:
                tempstr += ', %s'%kwargs['block_name']
                del kwargs['block_name']
            else:
                tempstr += ', %s'%desc.get('NAME')

        tag_str += tempstr.replace(',','',1)
        
        if printout:
            if tag_str:
                print(tag_str)
            tag_str = ''
        else:
            tag_str += '\n'

        #create an attr_offsets list for printing attribute offsets
        try:
            attr_offsets = desc['ATTR_OFFS']
        except Exception:
            attr_offsets = []

        is_array = desc['TYPE'].is_array
            
        #Print all this ListBlock's indexes
        for i in range(len(self)):
            data = self[i]
            kwargs['block_index'] = i
            
            tempstr = ''
            
            if isinstance(data, Block):
                if id(data) in seen:
                    if print_index:
                        tempstr = ' #:%s,' % i
                    tag_str += (indent_str1 + tempstr + " " +
                                   RECURSIVE % (data.NAME))
                else:
                    try:
                        tag_str += data.__str__(**kwargs)
                    except Exception:
                        tag_str += '\n' + format_exc()
            else:
                tag_str += indent_str1 + '['
                try:
                    if is_array:
                        attr_desc = desc['SUB_STRUCT']
                    else:
                        attr_desc = desc[i]
                except Exception: 
                    tag_str = tag_str[:-1] + MISSING_DESC% type(data)+"\n"
                    continue

                field = attr_desc['TYPE']
                if print_index:
                    tempstr += ', #:%s' % i
                if print_type:
                    tempstr += ', %s' % attr_desc['TYPE'].name
                if print_offset:
                    try:
                        tempstr += ', offset:%s'%attr_offsets[i]
                    except Exception:
                        pass
                if print_unique:
                    tempstr += ', unique:%s' % ('ORIG_DESC' in attr_desc)
                if print_py_id:
                    tempstr += ', py_id:%s' % id(data)
                if print_py_type:
                    tempstr += ', py_type:%s' % field.py_type
                if print_size:
                    try:
                        tempstr += ', size:%s' % self.get_size(i)
                    except Exception:
                        pass
                if print_name:
                    tempstr += ', %s' % attr_desc.get('NAME')
                    
                if print_value:
                    if isinstance(data, float) and isinstance(precision, int):
                        tempstr += ', %s'%("{:."+str(precision)+"f}")\
                                      .format(round(data, precision))
                    elif field.is_raw and not print_raw:
                        tempstr += ', ' + RAWDATA
                    else:
                        tempstr += ', %s' % data
                        
                tag_str += tempstr.replace(',','',1) + ' ]'
                    
            if printout:
                if tag_str:
                    print(tag_str)
                tag_str = ''
            else:
                tag_str += '\n'

        if printout:
            print(indent_str1 + ']')
        else:
            tag_str += indent_str1 + ']'
            
        #Print this ListBlock's child if it has one
        if hasattr(self, 'CHILD') and self.CHILD is not None and print_children:
            child = self.CHILD
            kwargs['block_index'] = None
            
            if printout:
                print(indent_str0 + '[ child:')
            else:
                tag_str += '\n' + indent_str0 + '[ child:\n'
            
            tempstr = ''
            tempstr2 = ''
            
            if isinstance(child, Block):
                if id(child) in seen:
                    tag_str += (indent_str1 + RECURSIVE_BLOCK % (child.NAME))
                else:
                    try:
                        tag_str += child.__str__(**kwargs)
                    except Exception:
                        tag_str += '\n' + format_exc()
                    
                if printout:
                    if tag_str:
                        print(tag_str)
                    tag_str = ''
                else:
                    tag_str += '\n'
                    
            else:  
                tag_str += indent_str1 + '['
                c_desc = desc['CHILD']
                c_field = c_desc['TYPE']
                    
                if print_type:
                    tempstr += ', %s' % c_field.name
                if print_unique:
                    tempstr += (', unique:%s' % ('ORIG_DESC' in c_desc))
                if print_py_id:
                    tempstr += ', py_id:%s' % id(child)
                if print_py_type:
                    tempstr += ', py_type:%s' % c_field.py_type
                if print_size and 'SIZE' in c_desc:
                    tempstr += ', size:%s' % self.get_size('CHILD')
                if print_name and 'NAME' in c_desc:
                    tempstr += ', %s' % c_desc['NAME']
                
                if print_value:
                    if isinstance(child, float) and isinstance(precision, int):
                        tempstr2 += ', %s' %("{:."+str(precision)+"f}")\
                                       .format(round(child,precision))
                    elif c_field.is_raw and not print_raw:
                        tempstr2 += ', ' + RAWDATA
                    else:
                        tempstr2 += ', %s' % child

                if printout:
                    try:
                        print(tag_str+(tempstr+tempstr2)\
                              .replace(',','',1) + ' ]')
                    except Exception:
                        print(tag_str + tempstr.replace(',','',1)+
                              ', %s ]' % UNPRINTABLE)
                    tag_str = ''
                else:
                    tag_str += ((tempstr+tempstr2).replace(',','',1) + ' ]\n')
                    
            tag_str += indent_str1 + ']'
                    
        if printout:
            if tag_str:
                print(tag_str)
            tag_str = ''

        if print_ramsize:
            if not printout:
                tag_str += '\n'
            blocksize = self.__sizeof__()
            tag_str += indent_str0 + '"In-memory Block" is %s bytes' % blocksize
        
        if printout:
            if tag_str:
                print(tag_str)
            tag_str = ''
            
        if print_binsize:
            if not printout:
                tag_str += '\n'
            block_binsize = self.binsize
            tag_str += (indent_str0 + '"Packed structure" is %s bytes'
                           % block_binsize)

            if print_ramsize:
                x_larger = "∞"
                if block_binsize:
                    size_str = "{:." + str(precision) + "f}"
                    x_larger = blocksize/block_binsize
                    
                    if precision:
                        x_larger = size_str.format(round(x_larger, precision))
                    
                tag_str += ('\n'+indent_str0 + '"In-memory Block" is ' +
                               str(x_larger) + " times as large.")
        
        if printout:
            if tag_str:
                print(tag_str)
            return ''
        else:
            return tag_str


    
    def __copy__(self):
        '''Creates a shallow copy, but keeps the same descriptor.'''
        #if there is a parent, use it
        try:
            parent = object.__getattribute__(self,'PARENT')
        except AttributeError:
            parent = None
            
        dup_block = type(self)(object.__getattribute__(self,'DESC'),
                               init_data=self, parent=parent)

        if hasattr(self, 'CHILD'):
            object.__setattr__(dup_block, 'CHILD',
                               object.__getattribute__(self, 'CHILD'))
        
        return dup_block

    
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
        #make sure the attributes arent initialized. it'll just waste time.
        memo[id(self)] = dup_block = type(self)(object.__getattribute__\
                                                (self,'DESC'),
                                                parent=parent, init_attrs=False)

        #clear the block so it can be populated
        list.__delitem__(dup_block, slice(None, None, None))
        list.extend(dup_block, [None]*len(self))
        
        #populate the duplicate
        for i in range(len(self)):
            list.__setitem__(dup_block, i, deepcopy(list.__getitem__(self,i),
                                                    memo))

        #CHILD has to be done last as its structure
        #likely relies on attributes of this, its parent
        if hasattr(self, 'CHILD'):
            object.__setattr__(dup_block, 'CHILD',
                               deepcopy(object.__getattribute__(self,'CHILD'),
                                        memo))
            
        return dup_block

    
    def __sizeof__(self, seenset=None):
        '''docstring'''
        if seenset is None:
            seenset = set()
        elif id(self) in seenset:
            return 0

        seenset.add(id(self))
        bytes_total = list.__sizeof__(self)
                
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
                if isinstance(item, Block):
                    bytes_total += item.__sizeof__(seenset)
                else:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)
            
        return bytes_total


    def __getitem__(self, index):
        '''enables getting attributes by providing
        the attribute name string as an index'''
        if isinstance(index, str):
            return self.__getattr__(index)
        
        return list.__getitem__(self, index)


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
                
            desc = object.__getattribute__(self,'DESC')
            if not desc['TYPE'].is_array:
                field = desc[index]['TYPE']
                if field.is_var_size and field.is_data:
                    #try to set the size of the attribute
                    try:   self.set_size(None, index)
                    except NotImplementedError: pass
                    except AttributeError: pass
                
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
            try: self.set_size(slice_size-len(new_value), None, '-')
            except NotImplementedError: pass
            except AttributeError: pass
        else:
            self.__setattr__(index, new_value)


    def __delitem__(self, index):
        '''enables deleting attributes by providing
        the attribute name string as an index'''
        
        if isinstance(index, int):
            #handle accessing negative indexes
            if index < 0:
                index += len(self)
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if object.__getattribute__(self,'DESC')['TYPE'].is_array:
                self.set_size(1, None, '-')
            else:
                #set the size of the block to 0 since it's being deleted
                try:   self.set_size(0, index)
                except NotImplementedError: pass
                except AttributeError: pass
                
                self.del_desc(index)
                
            list.__delitem__(self, index)
                
        elif isinstance(index, slice):            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            start, stop, step = index.indices(len(self))
            if start < stop:
                start, stop = stop, start
            if step > 0:
                step = -step
            
            if object.__getattribute__(self,'DESC')['TYPE'].is_array:
                self.set_size((stop-start)//step, None, '-')
                list.__delitem__(self, index)
            else: 
                for i in range(start-1, stop-1, step):
                    #set the size of the block to 0 since it's being deleted
                    try:   self.set_size(0, i)
                    except NotImplementedError: pass
                    except AttributeError: pass
                    
                    self.del_desc(i)
                    list.__delitem__(self, i)
        else:
            self.__delattr__(index)


    def _bin_size(self, block, substruct=False):
        '''Does NOT protect against recursion'''
        size = 0
        if isinstance(block, Block):
            field = object.__getattribute__(block, 'DESC')['TYPE']
            if field.name == 'Void':
                return 0
            
            if field.is_struct:
                if field.is_bit_based:
                    #return the size of this bit_struct
                    #since the block contains no substructs
                    if substruct:
                        return 0
                    return block.get_size()
                elif not substruct:
                    #get the size of this structure if it's not a substruct
                    size = block.get_size()
                    substruct = True
                    
            #loop for each of the attributes
            for i in range(len(block)):
                sub_block = block[i]
                if isinstance(sub_block, Block):
                    size += sub_block._bin_size(sub_block, substruct)
                elif not substruct:
                    size += block.get_size(i)

            #add the size of the child
            if hasattr(block, 'CHILD'):
                child = object.__getattribute__(block,'CHILD')
                if isinstance(child, Block):
                    size += child._bin_size(child)
                else:
                    size += block.get_size('CHILD')
        return size


    def append(self, new_attr=None, new_desc=None):
        '''Allows appending objects to this Block while taking
        care of all descriptor related details.
        Function may be called with no arguments if this block type is
        an Array. Doing so will append a fresh structure to the array
        (as defined by the Array's SUB_STRUCT descriptor value).'''

        #get the index we'll be appending into
        index = len(self)
        #create a new, empty index
        list.append(self, None)

        desc = object.__getattribute__(self,'DESC')

        try:
            '''if this block is an array and "new_attr" is None
            then it means to append a new block to the array'''
            if new_attr is None and desc['TYPE'].is_array:
                attr_desc = desc['SUB_STRUCT']
                attr_field = attr_desc['TYPE']

                '''if the type of the default object is a type of Block
                then we can create one and just append it to the array'''
                if issubclass(attr_field.py_type, Block):
                    attr_field.reader(attr_desc, self, None, index)

                    self.set_size(1, None, '+')
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
            
        if new_desc is None and not desc['TYPE'].is_array:
            list.__delitem__(self, index)
            raise AttributeError("Descriptor was not provided and could " +
                                 "not locate descriptor in object of type " +
                                 str(type(new_attr)) + "\nCannot append " +
                                 "without a descriptor for the new item.")
        
        '''try and insert the new descriptor
        and set the new attribute value,
        raise the last error if it fails
        and remove the new empty index'''
        try:
            list.__setitem__(self, index, new_attr)
            if not desc['TYPE'].is_array:
                self.ins_desc(index, new_desc)
        except Exception:
            list.__delitem__(self, index)
            raise

        if desc['TYPE'].is_array:
            #increment the size of the array by 1
            self.set_size(1, None, '+')
        elif desc['TYPE'].is_struct:
            #increment the size of the struct
            #by the size of the new attribute
            self.set_size(self.get_size(index), None, '+')

        #if the object being placed in the ListBlock
        #has a 'PARENT' attribute, set this block to it
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
            for i in range(desc['ENTRIES']):
                self.append(new_attrs[i], desc[i])
        elif (object.__getattribute__(self,'DESC')['TYPE'].is_array
              and isinstance(new_attrs, int)):
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
        desc = object.__getattribute__(self,'DESC')

        '''if this block is an array and "new_attr" is None
        then it means to append a new block to the array'''
        if desc['TYPE'].is_array:
            new_desc = desc['SUB_STRUCT']
            new_field = new_desc['TYPE']

            '''if the type of the default object is a type of Block
            then we can create one and just append it to the array'''
            if new_attr is None and issubclass(new_field.py_type, Block):
                new_field.reader(new_desc, self, None, index)

                self.set_size(1, None, '+')
                #finished, so return
                return

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

        '''try and insert the new descriptor
        and set the new attribute value,
        raise the last error if it fails'''
        try:
            list.__setitem__(self, index, new_attr)
            if not desc['TYPE'].is_array:
                self.ins_desc(index, new_desc)
        except Exception:
            list.__delitem__(self, index)
            raise

        #increment the size of the array by 1
        if desc['TYPE'].is_array:
            self.set_size(1, None, '+')

        #if the object being placed in the ListBlock
        #has a 'PARENT' attribute, set this block to it
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
                index += len(self)
            attr = list.pop(self, index)
            
            '''if this is an array, dont worry about
            the descriptor since its list indexes
            aren't attributes, but instanced objects'''
            if desc['TYPE'].is_array:
                desc = desc['SUB_STRUCT']
                self.set_size(1, None, '-')
            else:
                desc = self.get_desc(index)
                self.del_desc(index)
        elif index in desc['NAME_MAP']:
            attr = list.pop(self, desc['NAME_MAP'][index])
            desc = self.get_desc(index)
            self.del_desc(index)
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
        desc = object.__getattribute__(self,'DESC')

        if isinstance(attr_index, int):
            block = self[attr_index]
            if desc['TYPE'].is_array:
                desc = desc['SUB_STRUCT']
            else:
                desc = desc[attr_index]
        elif isinstance(attr_index, str):
            block = self.__getattr__(attr_index)
            try:
                desc = desc[desc['NAME_MAP'][attr_index]]
            except Exception:
                desc = desc[attr_index]
        else:
            block = self
            

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
            if desc['TYPE'].is_array:
                size = desc['SUB_STRUCT'].get('SIZE')
            else:
                size = desc[attr_index].get('SIZE')
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
            block = self
            size = desc.get('SIZE')
            field = desc['TYPE']

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
            #if kwargs.get('Warn', True):
            #    raise UserWarning('Cannot change a fixed size.')
            
            if op is None:
                self.set_desc('SIZE', newsize, attr_index)
            elif op == '+':
                self.set_desc('SIZE', size+newsize, attr_index)
            elif op == '-':
                self.set_desc('SIZE', size-newsize, attr_index)
            elif op == '*':
                self.set_desc('SIZE', size*newsize, attr_index)
            elif op == '/':
                self.set_desc('SIZE', size//newsize, attr_index)
            else:
                raise TypeError(("Unknown operator type '%s' " +
                                 "for setting 'size'.") % op)
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


    def collect_pointers(self, offset=0, seen=None, pointed_blocks=None,
                         substruct=False, root=False, attr_index=None):
        '''docstring'''
        if seen is None:
            seen = set()
            
        if attr_index is None:
            desc = object.__getattribute__(self,'DESC')
            block = self
        else:
            desc = self.get_desc(attr_index)
            block = self.__getitem__(attr_index)
            
        if id(block) in seen:
            return offset

        if 'POINTER' in desc:
            pointer = desc['POINTER']
            if isinstance(pointer, int) and desc.get('CARRY_OFF', True):
                #if the next blocks are to be located directly after
                #this one then set the current offset to its location
                offset = pointer

            #if this is a block within the root block
            if not root:
                pointed_blocks.append((self, attr_index, substruct))
                return offset

        is_block = isinstance(block, Block)

        if is_block:
            seen.add(id(block))

        field = desc['TYPE']
        if field.is_array:
            b_desc = desc['SUB_STRUCT']
            
            #align the start of the array of structs
            align = desc.get('ALIGN', 1)
            offset += (align-(offset%align))%align
            
            #dont align within the array of structs
            align = None
        elif desc.get('ALIGN'):
            align = desc['ALIGN']
            offset += (align-(offset%align))%align
            
        #increment the offset by this blocks size if it isn't a substruct
        if not substruct and (field.is_struct or field.is_data):
            offset += self.get_size(attr_index)
            substruct = True

        '''If the block isn't a Block it means that this is being run
        on a non-Block that happens to have its location specified by
        pointer. The offset must still be incremented by the size of this
        block, but the block can't contain other blocks, so return early.'''
        if not is_block:
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
                #if "i" is an integer it means this object still
                #exists within the structure, or is "substruct".
                #If it isn't it means its a linked block, which
                #(as of writing this) means its a child block.
                offset = block.collect_pointers(offset, seen, pointed_blocks,
                                    (isinstance(i, int) and substruct), False)
            elif not substruct and isinstance(i, int):
                '''It's pointless to check if this block is in seen
                or not because the block may be an integer, float,
                or string that is shared across multiple blocks.
                The check would succeed or fail at random.'''
                if not field.is_array:
                    b_desc = desc[i]
                    align = b_desc.get('ALIGN')
                    
                pointer = b_desc.get('POINTER')
                if pointer is not None:
                    if not isinstance(pointer, int):
                        #if the block has a variable pointer, add it to the
                        #list and break early so its id doesnt get added
                        pointed_blocks.append((self, i, substruct))
                        continue
                    elif b_desc.get('CARRY_OFF'):
                        offset = pointer
                elif align:
                    #align the block
                    offset += (align-(offset%align))%align
                    
                #add the size of the block to the current offset
                offset += self.get_size(i)
                seen.add(id(block))
            
        return offset



    def read(self, **kwargs):
        '''This function will initialize all of a List_Blocks attributes to
        their default value and adding ones that dont exist. An init_data
        can be provided with which to initialize the values of the block.'''

        attr_index = kwargs.get('attr_index',None)
        init_attrs = kwargs.get('init_attrs',True)
        init_data  = kwargs.get('init_data', None)

        #if an init_data was provided, make sure it can be used
        if (init_data is not None and
            not (hasattr(init_data, '__iter__') and
                 hasattr(init_data, '__len__'))):
            raise TypeError("init_data must be an iterable with a length")

        raw_data = self.get_raw_data(**kwargs)
            
        desc = object.__getattribute__(self, "DESC")
        if attr_index is not None and raw_data is not None:
            #if we are reading or initializing just one attribute
            if attr_index in desc['NAME_MAP']:
                attr_index = self[desc['NAME_MAP'][name]]
            elif isinstance(attr_index, int) and name in desc:
                attr_index = desc[name]
            
            desc = self.get_desc(attr_index)
        else:
            #if we are reading or initializing EVERY attribute
            #clear the block and set it to the right number of empty indices
            if desc['TYPE'].is_array:
                list.__init__(self, [None]*self.get_size())
            else:
                list.__init__(self, [None]*desc['ENTRIES'])

            '''If the init_data is not None then try
            to use it to populate the ListBlock'''
            if isinstance(init_data, dict):
                '''Since dict keys can be strings we assume that the
                reason a dict was provided is to set the attributes
                by name rather than index.
                So call self.__setattr__ instead of self.__setitem__'''
                for name in init_data:
                    self.__setitem__(name, init_data[name])
            elif init_data is not None:
                '''loop over the ListBlock and copy the entries
                from init_data into the ListBlock. Make sure to
                loop as many times as the shortest length of the
                two so as to prevent IndexErrors.'''
                for i in range(min(len(self), len(init_data))):
                    self.__setitem__(i, init_data[i])
        

        if raw_data is not None:
            #build the structure from raw data
            try:
                #Figure out if the parent is this ListBlock or its parent.
                if attr_index is None:
                    parent = self
                else:
                    try:
                        parent = self.PARENT
                    except AttributeError:
                        parent = None
                
                desc['TYPE'].reader(desc, parent, raw_data, attr_index,
                                    kwargs.get('root_offset',0),
                                    kwargs.get('offset',0),
                                    int_test = kwargs.get('int_test',False))
            except Exception:
                raise IOError('Error occurred while trying to '+
                              'read ListBlock from file')
                
        elif init_attrs:
            #initialize the attributes
            
            if desc['TYPE'].is_array:
                '''This ListBlock is an array, so the type of each
                element should be the same then initialize it'''
                try:
                    attr_desc = desc['SUB_STRUCT']
                    attr_field = attr_desc['TYPE']
                    py_type = attr_field.py_type
                except Exception: 
                    raise TypeError("Could not locate the array element " +
                                    "descriptor.\nCould not initialize array")

                #loop through each element in the array and initialize it
                for i in range(len(self)):
                    if list.__getitem__(self, i) is None:
                        attr_field.reader(attr_desc, self, None, i)
            else:
                for i in range(len(self)):
                    '''Only initialize the attribute
                    if a value doesnt already exist'''
                    if list.__getitem__(self, i) is None:
                        b_desc = desc[i]
                        b_desc['TYPE'].reader(b_desc, self, None, i)

            '''Only initialize the child if the block has a
            child and a value for it doesnt already exist.'''
            c_desc = desc.get('CHILD')
            if c_desc and object.__getattribute__(self, 'CHILD') is None:
                c_desc['TYPE'].reader(c_desc, self, None, 'CHILD')
        

class PListBlock(ListBlock):
    '''This ListBlock allows a reference to the child
    block it describes to be stored as well as a
    reference to whatever block it is parented to'''
    __slots__ = ("DESC", 'PARENT', 'CHILD')
    
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
                if isinstance(item, Block):
                    bytes_total += item.__sizeof__(seenset)
                else:
                    seenset.add(id(item))
                    bytes_total += getsizeof(item)
            
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
            
            if attr_name in desc['NAME_MAP']:
                self.__setitem__(desc['NAME_MAP'][attr_name], new_value)
            elif attr_name in desc:
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
            
            if attr_name in desc['NAME_MAP']:
                #set the size of the block to 0 since it's being deleted
                try:   self.set_size(0, attr_name=attr_name)
                except NotImplementedError: pass
                except AttributeError: pass
                self.del_desc(attr_name)
                list.__delitem__(self, desc['NAME_MAP'][attr_name])
            elif attr_name in desc:
                self.del_desc(attr_name)
            else:
                raise AttributeError("'%s' of type %s has no attribute '%s'" %
                                     (desc.get('NAME',UNNAMED),
                                     type(self),attr_name))

