For a detailed overview of the more abstract concepts and
features of supyr, read the text files in the 'docs' folder.

This readme needs more general highlights of the library, but for now I guess this is fine.
-------------------------------------------------------------------------------

SupyrStruct is an extensible and powerful binary data parsing, editing,
and serializing library for Python 3. Supyrs parsing and serializing is
declarative, meaning that rather than write code to handle reading and
writing data, one instead pieces together a description of the structure
using various "FieldTypes". This description is passed to a BlockDef,
which uses it to build "Block" objects to represent/hold the parsed data.


Example:

```python
>>> from supyr_struct import *
>>> asdf = BlockDef('some_blockdef',
...     UInt32('some_int'),
...     BytesRaw('some_bytes', SIZE=16),
...     ENDIAN='>'
...     )
>>> test_block = asdf.build()
>>> test_block.some_int = 1337
>>> test_block.some_bytes = b'heres a cstring\x00'
>>> str_rep = test_block.pprint(printout=True)
[ Container, entries:2, some_blockdef
    [ UInt32, size:4, some_int, 1337 ]
    [ BytesRaw, size:16, some_bytes, <RAWDATA> ]
    ]
>>> test_block.serialize()
bytearray(b'\x00\x00\x059heres a cstring\x00')
```


Supyr also supports forcing the endianness of the library to be either big,
little, or back to normal on a global scale and/or on individual FieldTypes.

```python
>>> field_types.FieldType.force_little()
>>> test_block.serialize()
bytearray(b'9\x05\x00\x00heres a cstring\x00')
>>> field_types.FieldType.force_normal()
>>> test_block.serialize()
bytearray(b'\x00\x00\x059heres a cstring\x00')
>>> field_types.BUInt32.force_little()
>>> test_block.serialize()
bytearray(b'9\x05\x00\x00heres a cstring\x00')
>>> field_types.BUInt32.force_normal()
>>> test_block.serialize()
bytearray(b'\x00\x00\x059heres a cstring\x00')
```


Supyr also implements a BlockDef subclass called a TagDef,
which creates Tag instances rather than Block instances.
Tags are a kind of header object that hold a reference to
the root of the structure, the TagDef used to build the Tag, 
a filepath to parse from/serialize to, and other properties.
Tags and TagDefs are not required to parse/serialize files,
but are a simple way to treat a parsed structure as a file.


Below is an example program that uses supyr to create valid bmp, gif,
tga, and dds bitmap Tags using procedurally generated pixels as the
image, and then serializing them to files in the current directory.

```python
from math import sqrt
from os.path import join, dirname
from supyr_struct.defs.bitmaps import bmp, dds, tga, gif

# dimensions of the bitmap
width = height = 256
bpp = 24

'''Generate the 24 bit b8g8r8 pixels for the bitmap'''
# figure out how many bytes the pixels will be based on the dimensions
bytes_per_pixel = bpp//8
bytes_per_line = width*bytes_per_pixel
pixels_size = width*height*bytes_per_pixel

pixels = bytearray(pixels_size)
len_sq = int((127.5)**2)

for y in range(256):
    i = y*bytes_per_line
    y = 255-y  # invert the value because bmp and tga images are upside-down
    y = y+1 if y < 128 else y  # make the image centered properly
    for x in range(256):
        j = x*bytes_per_pixel
        x = x+1 if x < 128 else x  # make the image centered properly
        z_sq = len_sq - (x-128)**2 - (y-128)**2
        if z_sq < 0:
            pixels[i+j: i+j+bytes_per_pixel] = (128, 255-y, 255-x)
        else:
            pixels[i+j: i+j+bytes_per_pixel] = (int(sqrt(z_sq)+128), y, x)

# To make a truecolor image in gif, we'll split the image
# into a bunch of 256 pixel strips with local palettes.
# This kind of gif isnt supported by all applications, but
# windows Paint and the windows shell display it just fine.
# Because the indexing MUST be compressed with lzw, im just
# going to include an already compressed indexing stream
gif_indexing = bytearray(b'\x08\xff\x00\xfd\xf9\xeb\xc7o\x9f\xbe|\xf8\xee\
\xd9\xabGo\x9e\xbcx\xf0\xde\xb9k\xc7n\x9d\xbat\xe8\xce\x99+Gn\x9c\xb8\
p\xe0\xbey\xeb\xc6m\x9b\xb6l\xd8\xaeY\xabFm\x9a\xb4h\xd0\x9e9k\xc6l\x99\
\xb2d\xc8\x8e\x19+Fl\x98\xb0`\xc0~\xf9\xea\xc5k\x97\xae\\\xb8n\xd9\xaa\
Ek\x96\xacX\xb0^\xb9j\xc5j\x95\xaaT\xa8N\x99*Ej\x94\xa8P\xa0>y\xea\xc4\
i\x93\xa6L\x98.Y\xaaDi\x92\xa4H\x90\x1e9j\xc4h\x91\xa2D\x88\x0e\x19*Dh\
\x90\xa0@\x80\xfe\xf8\xe9\xc3g\x8f\x9e<x\xee\xd8\xa9Cg\x8e\x9c8p\xde\
\xb8i\xc3f\x8d\x9a4h\xce\x98)Cf\x8c\x980`\xbex\xe9\xc2e\x8b\x96,X\xaeX\
\xa9Be\x8a\x94(P\x9e8i\xc2d\x89\x92$H\x8e\x18)Bd\x88\x90 @~\xf8\xe8\xc1\
c\x87\x8e\x1c8n\xd8\xa8Ac\x86\x8c\x180^\xb8h\xc1b\x85\x8a\x14(N\x98(Ab\
\x84\x88\x10 >x$\xe8\xc0a\x83\x86\x0c\x18.X\xa8@a\x82\x84\x08\x10\x1e\
8h\xc0`\x81\x82\x04\x08\x0e\x18(@`\x80\x80\x00\x00\x04\x04\x00')


'''Create the bmp, dds, and tga Tag instances and give them filepaths'''
folder = dirname(__file__)
bmp_tag = bmp.bmp_def.build()
dds_tag = dds.dds_def.build()
tga_tag = tga.tga_def.build()
gif_tag = gif.gif_def.build()
bmp_tag.filepath = join(folder, "normal_disc.bmp")
dds_tag.filepath = join(folder, "normal_disc.dds")
tga_tag.filepath = join(folder, "normal_disc.tga")
gif_tag.filepath = join(folder, "normal_disc.gif")


#####################  BMP  #####################
head     = bmp_tag.data.header
dib_head = bmp_tag.data.dib_header
dib_head.image_width  = width
dib_head.image_height = height
dib_head.bpp = bpp

head.pixels_pointer = bmp_tag.data.binsize
head.filelength = head.pixels_pointer + len(pixels)
bmp_tag.data.pixels = pixels


#####################  DDS  #####################
head = dds_tag.data.header
pixel_format = head.dds_pixelformat
head.width  = width
head.height = height

pixel_format.size = len(pixels)
pixel_format.flags.RGB = True
pixel_format.rgb_bitcount = bpp
pixel_format.r_bitmask = 0xff0000
pixel_format.g_bitmask = 0xff00
pixel_format.b_bitmask = 0xff

# dds doesnt allow textures to be stored upside down, so flip the image
dds_pixels = bytearray()
for i in range(256-1, -1, -1):
    dds_pixels += pixels[i*bytes_per_line:(i+1)*bytes_per_line]

dds_tag.data.pixel_data = dds_pixels


#####################  TGA  #####################
head = tga_tag.data.header
head.image_type.format.set_to("unmapped_rgb")
head.image_type.rle_compressed = True  # compress with rle just cause
head.width  = width
head.height = height
head.bpp = bpp

tga_tag.data.pixels_wrapper.pixels = pixels


#####################  GIF  #####################
head = gif_tag.data.gif_logical_screen
blocks = gif_tag.data.data_blocks

head.canvas_width  = width
head.canvas_height = height

for i in range(256):
    # create a fresh image_block to put this line of pixels into
    blocks.append(case=44)  # 44 is the switch case for the image_block
    image = blocks[-1]
    image.top = 255-i  # invert the top edge since the image is upside down
    image.width  = 256
    image.height = 1
    image.flags.color_table_size = 7
    image.flags.color_table = True
    # need to reverse the bytes since the color table
    # counts down from 255 rather than up from 0 and
    # the r and b channels are swapped for gif images
    image.local_color_table = bytes(reversed(pixels[
        i*bytes_per_line:(i+1)*bytes_per_line]))
    image.image_data_wrapper.image_data = gif_indexing


'''Serialize all the tags to their files'''
bmp_tag.serialize(temp=False, backup=False, int_test=False)
dds_tag.serialize(temp=False, backup=False, int_test=False)
tga_tag.serialize(temp=False, backup=False, int_test=False)
gif_tag.serialize(temp=False, backup=False, int_test=False)
```

This gif image is the result of running the above code
![normal_disc.gif](https://bitbucket.org/repo/KKAggn/images/2507909416-normal_disc.gif)