'''import the modules that need to be linked to one another'''
from supyr_struct import builder, handler, field_methods, blocks, tag

#give the Tag_Obj, Builder, and re_wr_de_en a reference to blocks
tag.blocks = builder.blocks = field_methods.blocks = blocks

#give the Handler and blocks a reference to Tag_Obj
handler.tag = blocks.block.tag = tag

#create and give a Tag_Obj.Tag_Obj to Handler.Handler for when one isnt provided
handler.Handler.default_tag_cls = tag.Tag

'''fields needs to directly access the attributes of
Re_We_De_En and blocks, so we dont worry about setting
up its dependencies since it imports its dependencies by itself.
Other modules need a reference to it though, so import it.'''
from supyr_struct import fields

'''Tag_Def needs a reference to fields and blocks,
and Builder and Handler need a reference to Tag_Def'''
from supyr_struct.defs import tag_def

#give Tag_Def references to blocks and fields
tag_def.blocks = blocks
tag_def.fields = fields
tag_def.tag    = tag

#give Builder and Handler a reference to Tag_Def
builder.tag_def = handler.tag_def = tag_def

#create a sanitizer for Builder.Builder and set it to _Sanitizer
builder.Builder._sanitizer = tag_def.TagDef()
