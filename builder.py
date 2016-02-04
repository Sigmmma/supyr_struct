class Builder():
    '''docstring'''
    _sanitizer = None

    def __init__(self, descriptor, fields=None, **kwargs):
        '''docstring'''
        if kwargs.get("Sanitizer"):
            self._sanitizer = kwargs["Sanitizer"]
            
        #The descriptor used to build this Block
        self.descriptor = self._sanitizer.sanitize(descriptor)
        #The Builders for each of the fields within this Block.
        #If a field doesnt build into a Block, it wont have a builder.
        #Examples of this are 'Data' struct members, like ints and strings
        self.fields = fields
            

    def build(self, **kwargs):
        '''builds a block'''
        desc = self.descriptor
    
        if desc is None:
            raise TypeError("Unable to build Block without a descriptor.")

        kwargs['tag']      = kwargs.get("tag",      None)
        kwargs['int_test'] = kwargs.get("int_test", False)
        kwargs['parent']   = kwargs.get("parent",   None)
        kwargs['offset']   = kwargs.get("offset",   0)
        kwargs['filepath'] = kwargs.get("filepath", None)
        kwargs['raw_data'] = kwargs.get("raw_data", None) 
        kwargs['attr_index']    = kwargs.get("attr_index",    None) 
        kwargs['root_offset']   = kwargs.get("root_offset",   0)
        kwargs['allow_corrupt'] = kwargs.get("allow_corrupt", False)

        try:
            if TYPE in desc:
                if hasattr(desc['TYPE'], 'py_type'):
                    new_attr_type = desc['TYPE'].py_type
                else:
                    raise KeyError('')
            else:
                raise AttributeError('Could not locate Field in' +
                                     'descriptor to build Block from.')

            #create and return the new Block
            return new_attr_type(desc, **kwargs)
        except Exception:
            raise Exception("Error occurred during Block construction.")
        
