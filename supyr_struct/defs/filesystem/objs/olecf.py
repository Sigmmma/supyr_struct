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

    _sectors   = ()
    _fat_chain = ()   # an iterable which contains the sector numbers
    #                   of the FAT sectors of the olecf Tag being parsed.
    #                   If the stream being parsed is in the ministream,
    #                   this will instead contain the miniFAT sector numbers.
    #                   This basically functions as a contiguous DIFAT array.

    _start_sector     = 0
    _sector_idx       = 0
    _pos              = 0
    _mini_sector_size = 64  # number of bytes in a miniFAT sector
    _sector_size      = 512 # number of bytes in a sector
    _sects_per_fat    = 128 # number of array entries in each FAT/miniFAT sector

    def __init__(self, storage_block):
        self._storage_block = storage_block
        self._tag = tag = storage_block.get_root()
        header = tag.data.header

        self._pos = 0

        self._sectors          = self._tag.data.sectors
        self._start_sector     = self._storage_block.stream_sect_start
        self._sector_idx       = self._start_sector
        self._mini_sector_size = 1 << header.mini_sector_shift
        self._sector_size      = 1 << header.sector_shift
        self._sects_per_fat    = self._sector_size // 4

        is_minifat = (
            storage_block.stream_len < header.mini_stream_cutoff and
            storage_block.storage_type.enum_name != 'root'
            )
        self._fat_chain = tag.minifat_sectors if is_minifat else tag.fat_sectors

        if is_minifat:
            # this stream exists in the ministream, so make an instance
            # of OlecfDataStream to handle parsing the ministream so this
            # can simply focus on parsing the stream within the ministream.
            self._ministream = (getattr(tag, "ministream", None)
                                or tag.get_stream_by_index(0))
            self._contig_ministream = (getattr(tag, "contig_ministream", None)
                                       or self._ministream.peek())

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

    @property
    def contig_ministream(self):
        return self._contig_ministream or (
            self._ministream.peek() if self._ministream else None
            )

    @property
    def fat_sector_idx(self):  return self._fat_chain[self.chain_idx]
    @property
    def sub_sector_idx(self):  return self.sector_idx  % self._sects_per_fat
    @property
    def chain_idx(self):       return self.sector_idx // self._sects_per_fat
    @property
    def sector_idx(self):      return self._sector_idx
    @property
    def next_sector_idx(self): return self.fat_sector.sect_nums[self.sub_sector_idx]
    @property
    def sector(self):      return self._sectors[self.sector_idx]
    @property
    def fat_sector(self):  return self._sectors[self.fat_sector_idx]
    @property
    def sector_data(self): return self.contig_ministream or self.sector.data

    def __len__(self):  return self._storage_block.stream_len
    def size(self):     return len(self)
    def tell(self):     return self._pos

    def read(self, count=None):
        '''Reads and returns 'count' number of bytes as a bytes object.'''
        streamsize = self.size()
        remainder  = streamsize - self.tell()

        # make sure to clip 'count' to how many can actually be read
        count = remainder if count is None else min(remainder, count)

        # read and return 'count' number of bytes
        assert isinstance(count, int), "'count' must be None or an int."

        # determine if we need to read from the sectors array or the ministream.
        # if it's the ministream, we have it assemble it from all the sectors
        data = b''

        is_mini = bool(self.contig_ministream)
        mini_stride = self._mini_sector_size if is_mini else 0
        stride      = mini_stride or self._sector_size
        while count > 0:
            offset  = (self._pos % stride) + self.sector_idx * mini_stride
            size    = count if count < stride else stride
            chunk   = self.sector_data[offset: offset + size]
            if not chunk:
                break

            # if we've moved to the next FAT or miniFAT sector,
            # update the pos, sector, and cell to reflect it
            data += chunk
            size  = len(chunk)
            if (self._pos % stride) + size >= stride:
                self._sector_idx = self.next_sector_idx

            self._pos += len(chunk)
            count     -= len(chunk)

        return data

    def peek(self, count=None, offset=None):
        '''
        Reads and returns 'count' number of bytes from the Buffer
        without changing the current read/write pointer position.
        '''
        orig = (self._sector_idx, self._pos)
        try:
            offset is None or self.seek(min(offset, self.size()))
            return self.read(count)
        finally:
            (self._sector_idx, self._pos) = orig

    def seek(self, pos, whence=SEEK_SET):
        '''
        Changes the position of the read pointer based on 'pos' and 'whence'.

        If whence is os.SEEK_SET, the read pointer is set to pos
        If whence is os.SEEK_CUR, the read pointer has pos added to it
        If whence is os.SEEK_END, the read pointer is set to len(self) + pos

        Raises AssertionError if the read pointer would be outside the buffer.
        Raises ValueError if whence is not SEEK_SET, SEEK_CUR, or SEEK_END.
        '''
        if whence not in (SEEK_SET, SEEK_CUR, SEEK_END):
            raise ValueError("Invalid value for whence. Expected " +
                             "0, 1, or 2, got %s." % whence)

        if whence == SEEK_SET:
            # reset so we can seek forward
            self._sector_idx = self._start_sector
            self._pos    = 0
        elif whence == SEEK_END:
            pos = (pos + len(self)) - self.tell()

        assert pos >= 0, "Read position cannot be negative."
        assert pos < self.size(), "Read position cannot be outside the buffer."

        # to seek, need to actually jump from sector to sector
        is_mini = bool(self.contig_ministream)
        stride  = self._mini_sector_size if is_mini else self._sector_size
        while pos > 0:
            size = pos if pos < stride else stride
            if (self._pos % stride) + size >= stride:
                self._sector_idx = self.next_sector_idx

            pos       -= size
            self._pos += size

    def write(self, s):
        raise NotImplementedError('Writing to Olecf not currently supported.')


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

        try:
            self.ministream = self.get_stream_by_index(0)
        except Exception:
            self.ministream = None
        try:
            self.contig_ministream = self.ministream.peek()
        except Exception:
            self.contig_ministream = b''

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
