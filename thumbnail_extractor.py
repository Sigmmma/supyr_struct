from os import makedirs
from traceback import format_exc

from supyr_struct.defs.filesystem.thumbs import thumbs_db_def
from supyr_struct.defs.filesystem.objs.thumbs import catalog_def,\
     fast_thumb_stream_def, thumb_stream_def, SOI
from supyr_struct.defs.constants import *

try:

    base_path = 'C:\\Python34\\Lib\\site-packages\\supyr_struct\\tags\\test'

    output_folder = base_path + '\\'
    output_path_template = output_folder + '%s.jpg'

    makedirs(output_folder, exist_ok=True)

    thumbs_tag = thumbs_db_def.build(filepath=base_path + '.db')
    get_stream = thumbs_tag.get_stream_by_name

    # Make a catalog Block from the stream data
    catalog = catalog_def.build(rawdata=get_stream('Catalog').read(),
                                allow_corrupt=True)

    print('%s thumbnails' % len(catalog.catalog_array))

    # loop over every entry in the catalog
    for i in range(len(catalog.catalog_array)):
        catalog_entry = catalog.catalog_array[i]
        try:
            print('    %s' % catalog_entry.name)

            # make the output path for the thumbnail
            output_path = output_path_template % catalog_entry.name
            # Get a stream buffer to read the thumbnail from.
            # The thumbnails name is the reversed thumbnail index as a string
            thumb_stream = get_stream(str(i+1)[::-1])

            # get the raw thumbnail stream data
            thumb_stream_data = thumb_stream.read()


            # if this is a non-headered thumbnail then just write it as is
            if thumb_stream.peek(2) == SOI:
                with open(output_path) as f:
                    f.write(thumbnail.thumb_stream_data)
                continue

            # othewise we build the jpeg thumbnail object and get its stream data
            thumbnail = fast_thumb_stream_def.build(rawdata=thumb_stream_data)

            # write the jpeg stream to the output file
            with open(output_path, 'w+b') as f:
                f.write(thumbnail.stream_data)
        except Exception:
            print('        FAILED TO EXTRACT %s' % catalog_entry.name)
            continue

    print()
    print('-' * 79)
    print('Finished extracting')
    print('-' * 79)
except:
    print(format_exc())

input()
