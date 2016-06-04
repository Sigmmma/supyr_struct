from .block import *

class VoidBlock(Block):
    __slots__ = ('DESC', 'PARENT')

    def __init__(self, desc=None, parent=None, **kwargs):
        '''docstring'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "DESC",   desc)
        object.__setattr__(self, "PARENT", parent)
    
    def __copy__(self):
        '''Creates a shallow copy, keeping the same descriptor.'''
        #if there is a parent, use it
        try:
            parent = object.__getattribute__(self,'PARENT')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self,'DESC'), parent=parent)

    def __deepcopy__(self, memo):
        '''Creates a deep copy, keeping the same descriptor.'''
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
                               parent=parent)
        memo[id(self)] = dup_block
        
        return dup_block
    
    def __str__(self, **kwargs):
        '''docstring'''
        printout = kwargs.get('printout', False)
        kwargs['printout'] = False
        try:
            if 'name' in kwargs['show'] and 'block_name' not in kwargs:
                kwargs['block_name'] = self.PARENT.DESC[self.PARENT.index\
                                                        (self)][NAME]
        except Exception:
            pass
        tag_str = Block.__str__(self, **kwargs).replace(',','',1)
        
        if printout:
            if tag_str:
                print(tag_str)
            return ''
        return tag_str

    def _binsize(self, block, substruct=False):
        '''docstring'''
        return 0
    
    def get_size(self, attr_index=None, **kwargs):
        '''docstring'''
        return 0
    
    def build(self, **kwargs):
        '''void blocks have nothing to build'''
        pass
