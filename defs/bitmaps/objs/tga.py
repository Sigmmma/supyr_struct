from supyr_struct.tag import *


class TgaTag(Tag):
    def __init__(self, **kwargs):
        kwargs.setdefault('zero_fill', False)
        Tag.__init__(self, **kwargs)

    def flip_image_origin(self):
        '''Flips the image data upside down and inverts the image origin bit'''
        if self.data is None:
            return
        header = self.data.header
        height = header.height
        width = header.width
        bpp = (header.bpp + 7)//8  # +7 to round up to nearest byte
        screen_origin = header.image_descriptor.screen_origin

        # get the pixels to modify
        pixels = self.data.pixels_wrapper.pixels

        # make a new buffer for the mirrored image
        flipped_pixels = b''

        assert width*height*bpp <= len(pixels), ('Expected more pixel data ' +
                                                 'than was found. Can not ' +
                                                 'mirror image vertically.')

        stride = width*bpp
        # reassemble the image upside down
        for x in range((height-1)*stride, -1, -1*stride):
            flipped_pixels += pixels[x:x+stride]

        # swap the pixels with the mirrored image
        self.data.pixels_wrapper.pixels = type(pixels)(flipped_pixels)

        # invert the origin bit
        if screen_origin.data_name == 'lower_left':
            screen_origin.set_data('upper_left')
        else:
            screen_origin.set_data('lower_left')
