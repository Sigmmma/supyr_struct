'''

'''
from supyr_struct.defs.block_def import *

# linked to through supyr_struct.__init__
tag = None


class TagDef(BlockDef):
    '''
    '''

    # Primarily used for locating tags when indexing a collection of
    # them, but also used as the extension when writing a tag to a file
    ext = ".tag"

    # Specifies that the definition is only partially written and
    # any file editing must be done to a copy of the original data
    # in order to keep all of the the undefined data intact.
    # Blocks of data SHOULD NEVER be added or deleted from
    # data mapped out with an incomplete definition, though
    # this library will not prevent you from doing so.
    incomplete = False

    # The class to use to build this definitions Tag from
    tag_cls = None

    # initialize the class
    def __init__(self, def_id, *desc_entries, **kwargs):
        ''''''
        self.ext = str(kwargs.get('ext', self.ext))
        self.incomplete = bool(kwargs.get('incomplete', self.incomplete))
        self.tag_cls = kwargs.get('tag_cls', self.tag_cls)

        BlockDef.__init__(self, def_id, *desc_entries, **kwargs)

    def build(self, **kwargs):
        '''Builds and returns a tag object'''
        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("int_test", False)

        return self.tag_cls(definition=self, **kwargs)

    def make_subdefs(self, replace_subdefs=True):
        BlockDef.make_subdefs(self, replace_subdefs)

# The docstrings of both methods should be the same since
# the only difference between the two is that the TagDef
# method has the default value of replace_subdefs as True
TagDef.make_subdefs.__doc__ = BlockDef.make_subdefs.__doc__
