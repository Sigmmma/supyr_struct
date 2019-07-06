'''
Definition for the thumbs.db system file that is generated for
quick image preview in various Windows operating systems.
'''
from supyr_struct.defs.filesystem.objs import thumbs
from supyr_struct.defs.filesystem.olecf import olecf_def
from supyr_struct.defs.tag_def import TagDef

__all__ = ("thumbs_def", "get", )


def get(): return thumbs_def

thumbs_def = TagDef("thumbs",
    descriptor=olecf_def.descriptor, sanitize=False,
    ext=".db", endian="<", tag_cls=thumbs.ThumbsTag
    )
