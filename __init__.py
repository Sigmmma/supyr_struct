'''import the modules that need to be linked to one another'''
from supyr_struct import handler, field_methods, blocks, tag

#give the tag_obj, and re_wr_de_en a reference to blocks
tag.blocks = field_methods.blocks = blocks

#give handler and blocks a reference to tag_obj
handler.tag = blocks.block.tag = tag

#create and give a tag_obj.tag_obj to handler.Handler for when one isnt provided
handler.Handler.default_tag_cls = tag.Tag

'''fields needs to directly access the attributes of
Re_We_De_En and blocks, so we dont worry about setting
up its dependencies since it imports its dependencies by itself.
Other modules need a reference to it though, so import it.'''
from supyr_struct import fields

'''Tag_Def needs a reference to fields and blocks,
and Builder and Handler need a reference to Tag_Def'''
from supyr_struct.defs import tag_def, block_def

#give block_def references to blocks and fields
block_def.blocks = blocks
block_def.fields = fields
block_def.tag    = tag

#give handler a reference to tag_def
handler.tag_def = tag_def

#give fields a reference to block_def
fields.block_def = block_def
