'''
'''
from supyr_struct import field_methods, blocks, tag

__version__ = "0.9.0"

# give the tag_obj, and re_wr_de_en a reference to blocks
tag.blocks = blocks

# give blocks a reference to tag_obj
blocks.block.tag = tag

# fields needs to directly access the attributes of
# Re_We_De_En and blocks, so we dont worry about setting
# up its dependencies since it imports its dependencies by itself.
# Other modules need a reference to it though, so import it.
from supyr_struct import fields

# Tag_Def needs a reference to fields and blocks,
# and Builder and Handler need a reference to Tag_Def
from supyr_struct.defs import tag_def, block_def, common_descriptors

# give references to blocks and fields
block_def.blocks = tag_def.blocks = field_methods.blocks = blocks
block_def.fields = tag_def.fields = field_methods.fields = fields

field_methods.common_descriptors = common_descriptors
