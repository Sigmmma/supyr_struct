'''
A module that implements the TagDef class, a subclass
of BlockDef which builds Tags instead of Blocks.
'''
from supyr_struct.defs.block_def import *


class TagDef(BlockDef):
    '''
    TagDefs are objects which serve the same purposes as
    BlockDefs, but instead of building Blocks, they build Tags.

    Look at BlockDef for information on this class.
    '''
    ext = ".tag"
    incomplete = False
    tag_cls = None

    # initialize the class
    def __init__(self, def_id, *desc_entries, **kwargs):
        '''
        Initializes a TagDef.

        Positional arguments:
        # str:
        def_id --------- An identifier string used for naming and keeping
                         track of BlockDefs. Used as the NAME entry in the
                         top level of the descriptor if one doesnt exist.

        Optional positional arguments:
        # dict:
        *desc_entries -- Dictionaries formatted as descriptors. A descriptor
                         will be built from all supplied positional arguments
                         and all keyword arguments(if the keyword is in the
                         desc_keywords set). Positional arguments are keyed
                         under the index they are located at in desc_entries,
                         and keyword arguments are keyed under their keyword.
                         If a FieldType is not supplied under the TYPE keyword,
                         the BlockDef will default to using Container.
                         If supplying a descriptor in this way, do not provide
                         one through the "descriptor" keyword as well. Doing
                         so will raise a TypeError

        Optional keyword arguments:
        # bool:
        incomplete ----- Specifies that the definition is only partially
                         written and that any editing must be done to a
                         copy of the original data in order to keep all
                         of the the undefined data intact.
                         Blocks SHOULD NEVER be added or deleted from data
                         mapped out with an incomplete definition, though
                         this library will not prevent you from doing so.

        # str:
        ext ------------ Used as the extension when writing a Tag to a file.

        # type:
        tag_cls -------- The Tag class constructor to build instances of.

        Passes 'def_id', all positional arguments, and
        all other keyword arguments to BlockDef.__init__
        '''
        self.ext = str(kwargs.pop('ext', self.ext))
        self.incomplete = bool(kwargs.pop('incomplete', self.incomplete))
        self.tag_cls = kwargs.pop('tag_cls', self.tag_cls)

        BlockDef.__init__(self, def_id, *desc_entries, **kwargs)

    def build(self, **kwargs):
        '''
        Builds an instance of this TagDefs 'tag_cls' attribute.

        Passes all supplied keyword arguments on to the tag_cls constructor.

        Returns the self.tag_cls instance
        '''
        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("int_test", False)
        kwargs['definition'] = self

        return self.tag_cls(**kwargs)

    def make_subdefs(self, replace_subdefs=True):
        BlockDef.make_subdefs(self, replace_subdefs)

# The docstrings of both methods should be the same since
# the only difference between the two is that the TagDef
# method has the default value of replace_subdefs as True
TagDef.make_subdefs.__doc__ = BlockDef.make_subdefs.__doc__
