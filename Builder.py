from supyr_struct.Defs import Tag_Def

class Builder():
    '''docstring'''
    _Sanitizer = Tag_Def.Tag_Def()

    def __init__(self, Descriptor, Fields=None, **kwargs):
        '''docstring'''
        if kwargs.get("Sanitizer"):
            self._Sanitizer = kwargs["Sanitizer"]
            
        #The descriptor used to build this Tag_Block
        self.Descriptor = self._Sanitizer.Sanitize(Descriptor)
        #The Builders for each of the fields within this Tag_Block.
        #If a field doesnt build into a Tag_Block, it wont have a builder.
        #Examples of this are 'Data' struct members, like ints and strings
        self.Fields = Fields
            

    def Build(self, **kwargs):
        '''builds a tag block'''
        Desc = self.Descriptor
    
        if Desc is None:
            raise TypeError("Unable to build Tag_Block without a descriptor.")

        kwargs['Tag']    = kwargs.get("Tag",    None)
        kwargs['Test']   = kwargs.get("Test",   False)
        kwargs['Parent'] = kwargs.get("Parent", None)
        kwargs['Offset']   = kwargs.get("Offset",   0)      
        kwargs['Filepath'] = kwargs.get("Filepath", None)
        kwargs['Raw_Data'] = kwargs.get("Raw_Data", None) 
        kwargs['Attr_Index']    = kwargs.get("Attr_Index",    None) 
        kwargs['Root_Offset']   = kwargs.get("Root_Offset",   0)
        kwargs['Allow_Corrupt'] = kwargs.get("Allow_Corrupt", False)

        try:
            if TYPE in Desc:
                if hasattr(Desc['TYPE'], 'Py_Type'):
                    New_Attr_Type = Desc['TYPE'].Py_Type
                else:
                    raise KeyError('')
            else:
                raise AttributeError('Could not locate Field_Type in' +
                                     'descriptor to build Tag_Block from.')

            #create and return the new Tag_Block
            return New_Attr_Type(Desc, **kwargs)
        except Exception:
            raise Exception("Error occurred during Tag_Block construction.")
