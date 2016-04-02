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
    def __init__(self, *desc_entries, **kwargs):
        '''docstring'''
        if 'ext' in kwargs:
            self.ext = str(kwargs['ext'])
            del kwargs['ext']
        if 'tag_cls' in kwargs:
            self.tag_cls = kwargs['tag_cls']
            del kwargs['tag_cls']
        if 'incomplete' in kwargs:
            self.incomplete = bool(kwargs['incomplete'])
            del kwargs['incomplete']
            
        if not hasattr(self, "ext"):        self.ext = ".tag"
        if not hasattr(self, "tag_cls"):    self.tag_cls = None
        if not hasattr(self, "incomplete"): self.incomplete = False

        BlockDef.__init__(self, *desc_entries, **kwargs)


    def build(self, **kwargs):
        '''builds and returns a tag object'''
        kwargs.setdefault("filepath", '')
        
        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("raw_data", None)
        kwargs.setdefault("int_test", False)
        
        return self.tag_cls(definition=self, **kwargs)


    def make_subdefs(self, replace_subdefs=True):
        BlockDef.make_subdefs(self, replace_subdefs)
