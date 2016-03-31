'''docstring'''
from supyr_struct.defs.block_def import *


class TagDef(BlockDef):
    '''docstring'''
    
    #Primarily used for locating tags when indexing a collection of
    #them, but also used as the extension when writing a tag to a file
    ext = ".tag"
    
    #Specifies that the definition is only partially written and any
    #editing must be done to a copy of the original data in order to
    #keep all of the the undefined data intact. Blocks of data SHOULD
    #NEVER be added or deleted from data mapped out with an incomplete
    #definition, though you are not prevented from doing so.
    incomplete = False
    
    #The class to use to build this definitions Tag from
    tag_cls = None

    #initialize the class
    def __init__(self, *args, **kwargs):
        '''docstring'''

        if not hasattr(self, "ext") or 'ext' in kwargs:
            self.ext = kwargs.get("ext", ".tag")
        if not hasattr(self, "tag_cls") or 'tag_cls' in kwargs:
            self.tag_cls = kwargs.get("tag_cls", None)
        if not hasattr(self, "incomplete") or 'incomplete' in kwargs:
            self.incomplete = kwargs.get("incomplete", False)

        BlockDef.__init__(self, *args, **kwargs)


    def build(self, **kwargs):
        '''builds and returns a tag object'''
        kwargs.setdefault("filepath", '')
        
        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("raw_data", None)
        kwargs.setdefault("int_test", False)
        
        return self.tag_cls(definition=self, **kwargs)
