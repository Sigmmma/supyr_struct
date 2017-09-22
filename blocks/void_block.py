'''
A module that implements VoidBlock, a subclass of Block.
VoidBlocks are used as placeholders where a Block is
required, but doesnt need to store any unique objects.
'''
from .block import *


class VoidBlock(Block):
    '''
    A Block class meant to be used with placeholder
    FieldTypes, like Pad and Void.

    Intended to be used where a Block is needed because it can hold a
    descriptor and has the Block superclass's methods, but where no
    attributes or other unique objects actually need to be stored.

    For example, VoidBlocks are used as the default node
    created when no default is set in a Switch descriptor.
    '''
    __slots__ = ('desc', '_parent', '__weakref__')

    def __init__(self, desc=None, parent=None, **kwargs):
        '''
        Initializes a VoidBlock. Sets its desc and parent to those supplied.

        Raises AssertionError is desc is missing 'TYPE' or 'NAME' keys.
        '''
        assert isinstance(desc, dict) and ('TYPE' in desc and 'NAME' in desc)

        object.__setattr__(self, "desc",   desc)
        self.parent = parent

    def __copy__(self):
        '''
        Creates a copy of this Block which references
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
        Creates a copy of this Block which references
        the same descriptor and parent.

        Returns the copy.
        '''
        # if a duplicate already exists then use it
        if id(self) in memo:
            return memo[id(self)]

        # if there is a parent, use it
        try:
            parent = object.__getattribute__(self, 'parent')
            parent = memo.get(id(parent), parent)
        except AttributeError:
            parent = None

        # make a new Block sharing the same descriptor.
        dup_block = type(self)(object.__getattribute__(self, 'desc'),
                               parent=parent)
        memo[id(self)] = dup_block

        return dup_block

    def __str__(self, **kwargs):
        '''
        Returns a formatted string representation of this VoidBlock.

        Optional keywords arguments:
        # int:
        indent ----- The number of spaces of indent added per indent level

        # set:
        show ------- An iterable containing strings specifying what to
                     include in the string. Valid strings are as follows:
            index ----- The index the field is located in in its parent
            name ------ The name of the field
            value ----- The field value(the node)
            type ------ The FieldType of the field
            size ------ The size of the field
            endian ---- The endianness of the field
            unique ---- Whether or not the descriptor of a field is unique
            parent_id - The id() of self.parent
            node_id --- The id() of the node
            node_cls -- The type() of the node
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

    def __binsize__(self, node, substruct=False):
        '''
        VoidBlocks are expected to have a byte size of zero. The only
        exception to this is when a VoidBlock is used for a Pad FieldType.
        Returns self.desc.get('SIZE', 0)
        '''
        if substruct:
            return 0
        return self.get_size()

    def get_size(self, attr_index=None, **context):
        '''
        VoidBlocks are expected to have a byte size of zero. The only
        exception to this is when a VoidBlock is used for a Pad FieldType.
        Returns self.desc.get('SIZE', 0)
        '''
        desc = object.__getattribute__(self, 'desc')
        return desc.get('SIZE', 0)

    def parse(self, **kwargs):
        '''VoidBlocks have nothing to parse. Does nothing.'''
        pass
