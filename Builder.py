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
        
        self.Allow_Corrupt = kwargs.get("Allow_Corrupt", False)
            

    def Build(self, **kwargs):
        '''builds a tag block'''
        Parent = None
        Desc = self.Descriptor
    
        if Desc is None:
            raise TypeError("Unable to build Tag_Block without a descriptor.")

        if isinstance(kwargs.get('Parent'), Tag_Block):
            Parent = kwargs["Parent"]
        
        Tag      = kwargs.get("Tag", None)
        Test     = kwargs.get("Test", False)
        Offset   = kwargs.get("Offset", 0)      
        Filepath = kwargs.get("Filepath", False)
        Raw_Data = kwargs.get("Raw_Data", None) 
        Attr_Index    = kwargs.get("Attr_Index", 0) 
        Root_Offset   = kwargs.get("Root_Offset", 0)
        Allow_Corrupt = kwargs.get("Allow_Corrupt", self.Allow_Corrupt)

        try:
            if Parent is not None and Attr_Index is not None:
                '''The Parent and Attr_Index are valid, so
                we can just call the Reader for that block.'''
                Parent.Get_Desc('TYPE', Attr_Index).Reader(Parent, Raw_Data,
                                                           Attr_Index,
                                                           Root_Offset, Offset,
                                                           Tag=Tag, Test=Test)
                return Parent[Attr_Index]
            else:
                '''if the Parent or Attr_Index are None, then 
                this block is being built without a parent,
                meaning we need to figure out how to build it'''
                #See what type of Tag_Block we need to make
                try:
                    New_Attr_Type = Desc['TYPE'].Py_Type
                except AttributeError:
                    raise AttributeError('Could not locate Field_Type in' +
                                         'descriptor to build Tag_Block from.')

                '''If the attribute has a child block, but the
                Tag_Block type that we will make it from doesnt
                support holding one, create a P_List_Block instead.'''
                if 'CHILD' in Desc and not hasattr(New_Attr_Type, 'CHILD'):
                      New_Attr_Type = P_List_Block

                New_Attr = New_Attr_Type(Desc, Raw_Data=Raw_Data,
                                         Filepath=Filepath, Test=Test,
                                         Offset=Offset, Root_Offset=Root_Offset,
                                         Allow_Corrupt=Allow_Corrupt)
                return New_Attr
        except Exception:
            raise Exception("Exception occurred while trying "+
                            " to construct Tag_Block.")
