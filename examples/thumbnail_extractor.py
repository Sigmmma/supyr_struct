'''
Need to document this thing
'''
import os

from traceback import format_exc

from supyr_struct.defs.filesystem.thumbs import thumbs_def
from supyr_struct.defs.filesystem.objs.thumbs import catalog_def,\
     fast_thumb_stream_def, thumb_stream_def, SOI
from supyr_struct.defs.filesystem.objs.thumbs import ThumbsTag
from supyr_struct.examples.olecf_extractor import OlecfExtractor

test_path = (__file__.split('\\thumbnail_extractor.py')[0] +
    '\\test_tags\\images\\test_thumbs.db')

class ThumbsExtractor(OlecfExtractor):

    tag_def_cls = thumbs_def
    tag_cls = ThumbsTag
    catalog = None

    def __init__(self, **kwargs):
        OlecfExtractor.__init__(self, **kwargs)
        self.title("Thumbnail database extractor v1.0")

    def load_tag(self, filepath=None):
        OlecfExtractor.load_tag(self, filepath)
        self.catalog = None

        if self.loaded_tag:
            self.catalog = catalog_def.build(
                rawdata=self.loaded_tag.get_stream_by_name('Catalog').read())
            self.populate_listbox()

    def extract_all(self):
        loaded_tag = self.loaded_tag
        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return
        self.extract(range(len(self.catalog.catalog_array)))

    def extract(self, file_indices=(), extract_selected=False):
        '''
        Extracts the specified thumbnails from the given loaded_tag to a
        folder with the same name as the thumbs file in the same parent folder.
        '''
        loaded_tag = self.loaded_tag
        catalog = self.catalog

        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return

        # faster local reference and shortens line lengths
        get_stream = loaded_tag.get_stream_by_name
        dirname = os.path.dirname
        exists = os.path.exists
        makedirs = os.makedirs

        # get the filepath of the tag without the extension
        thumbs_path = os.path.splitext(loaded_tag.filepath)[0]
        output_path_template = thumbs_path + '\\%s.jpg'

        # make sure a thumbnail output folder exists
        makedirs(thumbs_path + '\\', exist_ok=True)

        if extract_selected:
            file_indices = [self.listbox_map[i] for i in
                            self.file_listbox.curselection()]

        print('extracting %s thumbnails' % len(file_indices))

        # loop over every entry in the catalog
        for i in file_indices:
            try:
                catalog_entry = catalog.catalog_array[i]
                print('    %s' % catalog_entry.name)

                # get the filename
                name = catalog_entry.name.replace('/', '\\').split('\\', 1)[-1]

                # make the output path for the thumbnail
                output_path = output_path_template % name
                output_folder = dirname(output_path)

                # make sure an output folder exists
                if not exists(output_folder):
                    makedirs(output_folder, exist_ok=True)

                # Get a stream buffer to read the thumbnail from.
                # The name is the reversed thumbnail index as a string
                thumb_stream = get_stream(str(i+1)[::-1])

                # get the raw thumbnail stream data
                thumb_data = thumb_stream.read()

                with open(output_path, 'w+b') as f:
                    # if this is a non-headered thumbnail then just write it
                    if thumb_stream.peek(2) == SOI:
                        f.write(thumb_stream)
                        continue

                    # othewise build the jpeg thumbnail object
                    thumbnail = fast_thumb_stream_def.build(rawdata=thumb_data)

                    # write the thumbnails jpeg stream to the output file
                    f.write(thumbnail.data_stream)
            except Exception:
                print('        FAILED TO EXTRACT THUMBNAIL AT INDEX %s' % i)
                print(format_exc())
                continue

        print('\n%s\n%s\n%s' % ('-'*79, 'Finished extracting', '-'*79))

    def get_listbox_entries(self):
        catalog = self.catalog
        loaded_tag = self.loaded_tag
        if not(loaded_tag and catalog):
            return {}, ()

        listbox_entries = {}

        # loop over every directory entry
        for i in range(len(catalog.catalog_array)):
            listbox_entries[i] = catalog.catalog_array[i].name
        return listbox_entries, list(range(len(catalog.catalog_array)))

try:
    if __name__ == '__main__':
        extractor = ThumbsExtractor(filepath=test_path)
        extractor.mainloop()
except:
    print(format_exc())
    input()
