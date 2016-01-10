'''import the modules that need to be linked to one another'''
from supyr_struct import Builder, Library, Re_Wr_De_En, Tag_Blocks, Tag_Obj

#give the Tag_Obj and Re_Wr_De_En a reference to Tag_Blocks
Tag_Obj.Tag_Blocks     = Tag_Blocks
Re_Wr_De_En.Tag_Blocks = Tag_Blocks

#give the Library and Tag_Blocks a reference to Tag_Obj
Library.Tag_Obj    = Tag_Obj
Tag_Blocks.Tag_Obj = Tag_Obj

#create and give a Tag_Obj.Tag_Obj to Library.Library for when one isnt provided
Library.Library.Default_Tag_Obj = Tag_Obj.Tag_Obj


'''Field_Types needs to directly access the attributes of
Re_We_De_En and Tag_Blocks, so we dont worry about setting
up its dependencies since it imports its dependencies by itself.
Other modules need a reference to it though, so import it.'''
from supyr_struct import Field_Types
'''Tag_Def needs a reference to Field_Types and Tag_Blocks,
and Builder and Library need a reference to Tag_Def'''
from supyr_struct.Defs import Tag_Def

#give Tag_Def references to Tag_Blocks and Field_Types
Tag_Def.Tag_Blocks  = Tag_Blocks
Tag_Def.Field_Types = Field_Types

#give Builder and Library a reference to Tag_Def
Builder.Tag_Def = Tag_Def
Library.Tag_Def = Tag_Def

#create a sanitizer for Builder.Builder and set it to _Sanitizer
Builder.Builder._Sanitizer = Tag_Def.Tag_Def()
