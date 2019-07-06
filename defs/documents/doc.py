'''
Definition for Microsoft Word doc files.
'''
from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.filesystem.olecf import olecf_def

__all__ = ("doc_def", "get", )


def get(): return doc_def

doc_def = TagDef("doc",
    descriptor=olecf_def.descriptor, sanitize=False,
    ext=".doc", endian="<", tag_cls=olecf_def.tag_cls
    )
