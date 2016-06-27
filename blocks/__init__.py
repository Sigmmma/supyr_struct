'''
A module that provides various different types of Block classes.

Blocks are the objects that are built when a data stream is parsed
into python objects. Blocks store a reference to a descriptor under
the attribute name DESC. A descriptor is a dictionary which serves
as a collection of static attributes that describe the binary data
which the Block represents and/or holds. A minimal descriptor contains
a TYPE entry, which is a reference to the Field instance that describes
the Block, and a NAME entry, which is a string name for the Block.
'''
from .block import Block
from .void_block import VoidBlock
from .data_block import DataBlock, WrapperBlock, EnumBlock, BoolBlock
from .union_block import UnionBlock
from .list_block import ListBlock, PListBlock
from .while_block import WhileBlock, PWhileBlock

__all__ = ['Block', 'VoidBlock', 'DataBlock', 'UnionBlock',
           'WrapperBlock', 'BoolBlock', 'EnumBlock',
           'ListBlock', 'WhileBlock',
           'PListBlock', 'PWhileBlock']
