'''
Need to document this thing
'''
import os

from pathlib import Path
from traceback import format_exc

from supyr_struct.defs.filesystem.thumbs import thumbs_def
from supyr_struct.defs.filesystem.objs.thumbs import catalog_def,\
     fast_thumb_stream_def, thumb_stream_def, SOI
from supyr_struct.defs.filesystem.objs.thumbs import ThumbsTag
from supyr_struct.examples.olecf_extractor import OlecfExtractor, TAGS_DIR

class ThumbsExtractor(OlecfExtractor):

    tag_def_cls = thumbs_def
    tag_cls = ThumbsTag

    def __init__(self, **kwargs):
        OlecfExtractor.__init__(self, **kwargs)
        self.title("Thumbnail database extractor v1.1")

    def extract_all(self):
        loaded_tag = self.loaded_tag
        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return
        self.extract(range(len(loaded_tag.catalog)))

    def get_item_data(self, index):
        return self.loaded_tag.get_thumbnail_data(index)

    def get_listbox_entries(self):
        tag     = self.loaded_tag
        indices = list(range(len(tag.catalog))) if tag else []
        entries = {i: tag.get_thumbnail_path(i) for i in indices}
        return entries, indices

try:
    if __name__ == '__main__':
        extractor = ThumbsExtractor(
            filepath=TAGS_DIR.joinpath('images/test_thumbs.db')
            )
        extractor.mainloop()
except Exception:
    print(format_exc())
    input()
