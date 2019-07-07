'''
Targa image file definitions

Structures were pieced together from various online sources
'''
from supyr_struct.defs.tag_def import TagDef
from supyr_struct.defs.common_descs import remaining_data_length
from supyr_struct.field_types import *
from supyr_struct.buffer import BytearrayBuffer
from supyr_struct.defs.bitmaps.objs import tga

__all__ = ("tga_def", "get", )


def get(): return tga_def

# it isnt possible to set the size in the below functions
# because the size is derived from multiple source inputs
# and must be set manually. This is expected to happen for
# some types of structures, so rather than raise an error,
# do nothing since this is normal and the user handles it


def tga_color_table_size(parent=None, attr_index=None,
                         new_value=None, **kwargs):
    '''Size getter for the byte size of a tga color table'''
    if new_value is not None:
        return
    if parent is None:
        raise KeyError("Cannot calculate the size of tga " +
                       "color table without a supplied parent.")
    if attr_index is not None and hasattr(parent[attr_index], '__len__'):
        return len(parent[attr_index])
    header = parent.header

    if not header.has_color_map:
        return 0
    elif header.color_map_depth in (15, 16):
        return 2 * header.color_map_length
    return header.color_map_depth * header.color_map_length // 8


def tga_pixel_bytes_size(parent=None, attr_index=None,
                         new_value=None, **kwargs):
    '''Size getter for the byte size of tga pixel data'''
    if new_value is not None:
        return
    if parent is None:
        raise KeyError("Cannot calculate the size of tga " +
                       "pixels without without a supplied parent.")
    if attr_index is not None and hasattr(parent[attr_index], '__len__'):
        return len(parent[attr_index])

    header = parent.parent.header
    pixels = header.width * header.height
    image_type = header.image_type

    if image_type.format == 0:
        return pixels // 8
    elif header.bpp in (15, 16):
        return 2 * pixels
    return header.bpp * pixels // 8


def parse_rle_stream(parent, rawdata, root_offset=0, offset=0, **kwargs):
    '''
    Returns a buffer of pixel data from the supplied rawdata as
    well as the number of bytes long the compressed data was.
    If the tag says the pixel data is rle compressed, this
    function will decompress the buffer before returning it.
    '''
    assert parent is not None, "Cannot parse tga pixels without without parent"

    header = parent.parent.header
    pixels_count = header.width * header.height
    image_type = header.image_type

    bpp = (header.bpp+7)//8  # +7 to round up to nearest byte

    start = root_offset+offset
    bytes_count = pixels_count * bpp

    if image_type.rle_compressed:
        pixels = BytearrayBuffer([0]*bytes_count)

        comp_bytes_count = curr_pixel = 0
        rawdata.seek(start)

        while curr_pixel < pixels_count:
            packet_header = rawdata.read(1)[0]
            if packet_header & 128:
                # this packet is compressed with RLE
                pixels.write(rawdata.read(bpp)*(packet_header-127))
                comp_bytes_count += 1 + bpp
                curr_pixel += packet_header-127
            else:
                # it's a raw packet
                pixels.write(rawdata.read((packet_header+1)*bpp))
                comp_bytes_count += 1 + (packet_header+1)*bpp
                curr_pixel += packet_header+1

        return pixels, comp_bytes_count
    else:
        return BytearrayBuffer(rawdata[start:start+bytes_count]), bytes_count


def serialize_rle_stream(parent, buffer, **kwargs):
    '''
    Returns a buffer of pixel data from the supplied buffer.
    If the tag says the pixel data is rle compressed, this
    function will compress the buffer before returning it.
    '''
    assert parent is not None, "Cannot write tga pixels without without parent"

    header = parent.parent.header

    if header.image_type.rle_compressed:
        bpp = (header.bpp+7)//8  # +7 to round up to nearest byte

        buffer.seek(0)

        # start the compressed pixels buffer out as the same size as the
        # uncompressed pixels to minimize the number of times python has to
        # reallocate space every time the comp_pixels buffer is written to
        comp_pixels = BytearrayBuffer([0]*len(buffer))

        # get the first pixel to compress
        curr_pixel = buffer.read(bpp)
        next_pixel = buffer.peek(bpp)

        # keep running as long as there are pixels
        while curr_pixel:
            if curr_pixel == next_pixel:
                # this packet can be compressed with RLE
                rle_len = 1
                packet = curr_pixel

                # DO NOT REVERSE THESE CONDITIONS. If you do, read
                # wont be called and the read position will be wrong
                while curr_pixel == buffer.read(bpp) and rle_len < 128:
                    # see how many repeated pixels we can find(128 at most)
                    rle_len += 1

                # seek backward and read the last pixel
                buffer.seek(-bpp, 1)
                curr_pixel = buffer.read(bpp)
                next_pixel = buffer.peek(bpp)

                # write the header and the packet to comp_pixels
                comp_pixels.write(bytes([127 + rle_len]) + packet)

                # if the next read returns nothing, there are not more pixels
                if len(next_pixel) != bpp:
                    break
            else:
                # this should be a raw packet
                packet = b''

                while curr_pixel != next_pixel and len(packet)//bpp < 128:
                    # see how many non-repeated pixels we can find(128 at most)
                    packet += curr_pixel
                    curr_pixel = next_pixel
                    next_pixel = buffer.read(bpp)

                    # if next_pixel is the start of a repeated
                    # sequence of pixels then just break here
                    if curr_pixel == next_pixel or len(next_pixel) != bpp:
                        break

                # write the header and the packet to comp_pixels
                comp_pixels.write(bytes([len(packet)//bpp - 1]) + packet)

                # if the next read returns nothing, there are not more pixels
                if len(curr_pixel) != bpp:
                    break

        # slice the compressed pixels off at when the last write was
        comp_pixels = comp_pixels[:comp_pixels.tell()]
    else:
        comp_pixels = buffer

    return comp_pixels


tga_header = Struct("header",
    UInt8("image_id_length"),
    UEnum8("has_color_map",
        "no",
        "yes"
        ),
    LBitStruct("image_type",
        UBitEnum("format",
            "bw_1_bit",
            "color_mapped_rgb",
            "unmapped_rgb",
            "bw_8_bit",
            SIZE=2
            ),
        Pad(1),
        Bit("rle_compressed"),
        Pad(4),
        SIZE=1
        ),
    LUInt16("color_map_origin"),
    LUInt16("color_map_length"),
    UInt8("color_map_depth"),
    LUInt16("image_origin_x"),
    LUInt16("image_origin_y"),
    LUInt16("width"),
    LUInt16("height"),
    UInt8("bpp"),
    LBitStruct("image_descriptor",
        UBitInt("alpha_bit_count", SIZE=4),
        Pad(1),
        UBitEnum("screen_origin",
            "lower_left",
            "upper_left",
            SIZE=1
            ),
        UBitEnum("interleaving",
            "none",
            "two_way",
            "four_way",
            SIZE=2
            ),
        SIZE=1
        ),
    SIZE=18
    )

# create the definition that builds tga files
tga_def = TagDef('tga',
    tga_header,
    BytesRaw('image_id',    SIZE='.header.image_id_length'),
    BytesRaw('color_table', SIZE=tga_color_table_size),
    StreamAdapter('pixels_wrapper',
        SUB_STRUCT=BytesRaw('pixels', SIZE=tga_pixel_bytes_size),
        DECODER=parse_rle_stream, ENCODER=serialize_rle_stream),
    BytesRaw('remaining_data', SIZE=remaining_data_length),

    tag_cls=tga.TgaTag, ext=".tga", endian="<"
    )
