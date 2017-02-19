'''
Definition for Microsoft Word doc files.
'''
from ..filesystem.olecf import *


def get(): return doc_def

doc_def = TagDef("doc",
    descriptor=olecf_def.descriptor, sanitize=False,
    ext=".doc", endian="<", tag_cls=olecf_def.tag_cls
    )
