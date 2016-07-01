'''
A module that implements VoidBlock, a subclass of Block.
VoidBlocks are used as placeholders where a Block is
required, but doesnt need to store any unique objects.
'''
from .block import *


class VoidBlock(Block):
    '''
    A Block class meant to be used with placeholder Fields, like Pad and Void.

    Intended to be used where a Block is needed because it can hold a
    descriptor and has the Block superclass's methods, but where no
    attributes or other unique objects actually need to be stored.

    For example, VoidBlocks are used as the default Block
    created when no default is set in a Switch descriptor.
    '''
    __slots__ = ('desc', 'parent')

    def __init__(self, desc=None, parent=None, **kwargs):
        '''Initializes a VoidBlock, setting its descriptor and parent.'''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        object.__setattr__(self, "parent", parent)

    def __copy__(self):
        '''
        Creates a copy of this block which references
        the same descriptor and parent.

        Returns the copy.
        '''
        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
        except AttributeError:
            parent = None
        return type(self)(object.__getattribute__(self, 'desc'), parent=parent)

    def __deepcopy__(self, memo):
        '''
        Creates a copy of this block which references
        the same descriptor and parent.

        Returns the copy.
        '''
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
                               parent=parent)
        memo[id(self)] = dup_block

        return dup_block

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this VoidBlock.

        Optional keywords arguments:
        # int:
        indent ------ The number of spaces of indent added per indent level

        # set:
        show -------- An iterable containing strings specifying what to
                      include in the string. Valid strings are as follows:
            index ---- The index the attribute is located in in its parent
            field ---- The Field of the attribute
            endian --- The endianness of the Field
            unique --- Whether or not the descriptor of an attribute is unique
            py_id ---- The id() of the attribute
            py_type -- The type() of the attribute
            size ----- The size of the attribute
            name ----- The name of the attribute
            value ---- The attribute value
        '''
        if 'name' in kwargs.get('show', ()) and 'attr_name' not in kwargs:
            try:
                kwargs.setdefault('attr_name',
                                  self.parent.desc[
                                      self.parent.index_by_id(self)][NAME])
            except Exception:
                pass
        tag_str = Block.__str__(self, **kwargs).replace(',', '', 1)

        return tag_str

    def _binsize(self, block, substruct=False):
        '''VoidBlocks have a binary size of 0. Returns 0'''
        return 0

    def get_size(self, attr_index=None, **kwargs):
        '''VoidBlocks have a size of 0. Returns 0'''
        return 0

    def build(self, **kwargs):
        '''VoidBlocks have nothing to build. Does nothing.'''
        pass
