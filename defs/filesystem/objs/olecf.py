'''
This module provides a base Tag class for a OLECF file.
'''
from supyr_struct.tag import Tag
from supyr_struct.buffer import Buffer, SEEK_SET, SEEK_CUR, SEEK_END

__all__ = ("OlecfDataStream", "OlecfTag", )


class OlecfDataStream(Buffer):
    '''
    A class which allows accessing data within a storage data stream
    as if the stream were one contiguous readable/writable bytes object.

    Does not currently support resizing the data stream.
    '''
    _tag = None  # the tag which the data stream is a part of.
    _storage_block = None  # a Block instance using the storage_dir_entry desc
    #                        which contains the streams name, length, and start

    _ministream = None  # an instance of OlecfDataStream that handles
    #                     parsing the mini stream this stream exists in

    _contig_ministream = None  # the ministream after it's been assembled into
    #                            a contiguous bytes object. much faster to read

    _sector_chain = ()  # an iterable which contains the sector numbers
    #                     of the FAT sectors of the olecf Tag being parsed.
    #                     If the stream being parsed is in the ministream,
    #                     this will instead contain the miniFAT sector numbers.
    #                     This basically functions as a contiguous DIFAT array.

    _pos = 0     # the virtual offset within the data stream that the
    #            read/write pointer would be at if it were contiguous
    _sector = 0  # the offset sector the read/write pointer is at.
    _cell = 0    # the offset within the sector the read/write pointer is at.
    _sector_size = 512    # number of bytes in a sector
    _sects_per_fat = 128  # number of array entries in each FAT/miniFAT sector

    def __init__(self, storage_block):
        self._storage_block = storage_block
        self._tag = tag = storage_block.get_root()
        header = tag.data.header

        self._pos = self._cell = 0

        self._sector = storage_block.stream_sect_start
        self._sects_per_fat = (1 << header.sector_shift) // 4

        if (storage_block.stream_len < header.mini_stream_cutoff and
            storage_block.storage_type.enum_name != 'root'):
            # this stream exists in the ministream, so make an instance
            # of OlecfDataStream to handle parsing the ministream so this
            # can simply focus on parsing the stream within the ministream.
            self._sector_size = 1 << header.mini_sector_shift
            self._sector_chain = tag.minifat_sectors
            if hasattr(tag, 'ministream'):
                self._ministream = tag.ministream
            else:
                self._ministream = tag.get_stream_by_index(0)
            if hasattr(tag, 'contig_ministream'):
                self._contig_ministream = tag.contig_ministream
            else:
                self._contig_ministream = self._ministream.peek()
        else:
            # this is either too large to be in the
            # ministream, or it IS the ministream
            self._sector_size = 1 << header.sector_shift
            self._sector_chain = tag.fat_sectors

    def flush_ministream(self):
        '''
        Flushes changes to the contiguous ministream
        to the ministream if they both exist.
        '''
        if self._ministream and self._contig_ministream:
            self._ministream.seek(0)
            self._ministream.write(self._contig_ministream)
            self._ministream.seek(0)

    def recache_ministream(self):
        '''
        Makes a contiguous cache copy of the ministream
        for more quickly doing reads and writes.
        '''
        if self._ministream:
            self._ministream.seek(0)
            self._contig_ministream = self._ministream.peek()

    def __len__(self):
        return self._storage_block.stream_len

    def size(self):
        return self._storage_block.stream_len

    def read(self, count=None):
        '''Reads and returns 'count' number of bytes as a bytes object.'''

        if count is None:
            # read and return everything after self._pos
            count = len(self) - self._pos
        else:
            # read and return 'count' number of bytes
            assert isinstance(count, int), "'count' must be None or an int."

            # make sure to clip 'count' to how many can actually be read
            count = min(len(self) - self._pos, count)

        if count == 0:
            return b''

        sect = self._sector
        sect_size = self._sector_size
        sect_chain = self._sector_chain
        sect_array = self._tag.data.sectors
        sects_per_fat = self._sects_per_fat
        start_cell = self._cell

        # determine how many bytes need to be read from the first
        # sector in the chain and the last sector in the chain.
        # Every sector between the first and last is fully read.
        sect_0_len = sect_size - (self._pos % sect_size)
        sect_n_len = (self._pos + count) % sect_size

        # determine if more than one sector is being read(if there
        # is a last sector in the chain instead of just a beginning)
        if sect_0_len < count:
            has_last = True

            # if the number of bytes being read is an exact multiple of the
            # sector size, the last sector's size will be set to 0. Fix this.
            if sect_n_len == 0:
                sect_n_len = sect_size
            # determine how many sectors are between the first and last sectors
            if sect_0_len + sect_n_len < count:
                middle_count = (count - sect_0_len - sect_n_len) // sect_size
            else:
                middle_count = 0
        else:
            has_last = False
            middle_count = 0

        # get the FAT or miniFAT sect_nums of the next sector
        fat_sect = sect_array[sect_chain[sect // sects_per_fat]].sect_nums

        # determine if we need to read from the sectors array or the ministream
        mini_stream = self._ministream
        contig_ministream = self._contig_ministream

        if mini_stream or contig_ministream:
            if not contig_ministream:
                # reading from the ministream, so have it assemble it for us
                contig_ministream = mini_stream.peek()

            # the offset within the ministream to read at
            offset = sect * sect_size + start_cell

            # slice out the bytes we want from the first sector
            contig_stream = contig_ministream[offset:offset + sect_0_len]

            # get the next sect and its FAT or miniFAT sect_nums
            sect = fat_sect[sect % sects_per_fat]
            offset = sect * sect_size + start_cell

            # add the middle sectors to the contiguous stream
            while middle_count:
                fat_sect = sect_array[sect_chain[sect //
                                                 sects_per_fat]].sect_nums
                contig_stream += contig_ministream[offset:offset + sect_size]

                # decrement the number of remaining middle sectors
                middle_count -= 1

                # get the next sector and its FAT or miniFAT sect_nums
                sect = fat_sect[sect % sects_per_fat]
                offset = sect * sect_size

            # add the last sector to the contiguous stream
            if has_last:
                fat_sect = sect_array[sect_chain[sect //
                                                 sects_per_fat]].sect_nums
                contig_stream += contig_ministream[offset:offset + sect_n_len]
                sect = fat_sect[sect % sects_per_fat]
        else:
            # slice out the bytes we want from the first sector
            contig_stream = sect_array[sect].data[start_cell:
                                                  start_cell + sect_0_len]

            # get the next sect and its FAT or miniFAT sect_nums
            sect = fat_sect[sect % sects_per_fat]

            # add the middle sectors to the contiguous stream
            while middle_count:
                fat_sect = sect_array[sect_chain[sect //
                                                 sects_per_fat]].sect_nums
                contig_stream += sect_array[sect].data[:]

                # decrement the number of remaining middle sectors
                middle_count -= 1

                # get the next sector and its FAT or miniFAT sect_nums
                sect = fat_sect[sect % sects_per_fat]

            # add the last sector to the contiguous stream
            if has_last:
                fat_sect = sect_array[sect_chain[sect //
                                                 sects_per_fat]].sect_nums
                contig_stream += sect_array[sect].data[:sect_n_len]
                sect = fat_sect[sect % sects_per_fat]

        # change the pos, sector, and cell to reflect the change
        self._pos += count
        self._sector = sect
        self._cell = sect_n_len

        return contig_stream

    def peek(self, count=None):
        '''
        Reads and returns 'count' number of bytes from the Buffer
        without changing the current read/write pointer position.
        '''
        self._pos, self._sector, self._cell, data = (
            self._pos, self._sector, self._cell, self.read(count))
        return data

    def seek(self, pos, whence=SEEK_SET):
        '''
        Changes the position of the read pointer based on 'pos' and 'whence'.

        If whence is os.SEEK_SET, the read pointer is set to pos
        If whence is os.SEEK_CUR, the read pointer has pos added to it
        If whence is os.SEEK_END, the read pointer is set to len(self) + pos

        Raises AssertionError if the read pointer would be outside the buffer.
        Raises ValueError if whence is not SEEK_SET, SEEK_CUR, or SEEK_END.
        Raises TypeError if whence is not an int.
        '''

        if whence == SEEK_SET:
            assert pos < len(self), "Read position cannot be outside buffer."
            assert pos >= 0, "Read position cannot be negative."
            self._pos = pos
        elif whence == SEEK_CUR:
            p = self._pos + pos
            assert p < len(self), "Read position cannot be outside buffer."
            assert p >= 0, "Read position cannot be negative."
            self._pos += pos
        elif whence == SEEK_END:
            assert pos <= 0, "Read position cannot be outside buffer."
            pos += len(self)
            assert pos >= 0, "Read position cannot be negative."
            self._pos = pos
        elif type(whence) is int:
            raise ValueError("Invalid value for whence. Expected " +
                             "0, 1, or 2, got %s." % whence)
        else:
            raise TypeError("Invalid type for whence. Expected " +
                            "%s, got %s" % (int, type(whence)))

        pos = self._pos

        # change the sector and cell to reflect the new pos
        self._cell = pos % self._sector_size
        self._sector = self._sector_chain[pos // self._sects_per_fat]

    def write(self, s):
        raise NotImplementedError('Cant do that yet.')

        # NEED TO MAKE DIS CRAP WURK
        s = memoryview(s).tobytes()
        str_len = len(s)

        if len(s) + self._pos > len(self):
            raise IndexError(
                'Input too long to write to data stream at the current offset')

        self._pos += str_len


class OlecfTag(Tag):
    '''
    '''
    def __init__(self, **kwargs):
        '''Initializes an Olecf Tag'''

        # These next lists are used for quickly jumping around
        # the DIFAT, FAT, miniFAT, and directory sectors without
        # having to follow chains in the FAT or DIFAT.

        # A list of the DIFAT sector numbers IN ORDER.
        # If none exist, this list will be empty.
        # This excludes the array of 109 DIFAT entries in the header.
        self.difat_sectors = []

        # A list of the FAT sector numbers IN ORDER.
        self.fat_sectors = []

        # A list of the miniFAT sector numbers IN ORDER.
        self.minifat_sectors = []

        # A list of the directory sector numbers IN ORDER.
        self.dir_sectors = []

        # A list of the names of each directory entry IN ORDER
        self.dir_names = []

        # A quick reference to the number of bytes in a sector
        self.sector_size = 512

        Tag.__init__(self, **kwargs)

    def get_dir_entry_by_name(self, name):
        '''Returns the directory entry linked to the given name.'''
        return self.get_dir_entry_by_index(self.dir_names.index(name))

    def get_dir_entry_by_index(self, index):
        '''Returns the directory entry in the given index.'''
        dirs_per_sect = self.sector_size // 128
        dir_sect = self.data.sectors[self.dir_sectors[index // dirs_per_sect]]
        return dir_sect[index % dirs_per_sect]

    def get_stream_by_name(self, name):
        '''Returns an OlecfDataStream of the specified directory entry.'''
        return self.get_stream_by_index(self.dir_names.index(name))

    def get_stream_by_index(self, index):
        '''Returns an OlecfDataStream of the specified directory entry.'''
        return OlecfDataStream(self.get_dir_entry_by_index(index))
