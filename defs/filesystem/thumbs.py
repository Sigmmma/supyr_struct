'''
Definition for the thumbs.db system file that is generated for
quick image preview in various Windows operating systems.
'''
from .olecf import *
from .objs.thumbs import ThumbsTag


def get(): return thumbs_def

thumbs_def = TagDef("thumbs",
    descriptor=olecf_def.descriptor, sanitize=False,
    ext=".db", endian="<", tag_cls=ThumbsTag
    )
