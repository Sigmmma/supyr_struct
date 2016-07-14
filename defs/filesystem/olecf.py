'''
Object linking and embedding (ole) compound file (cf) definition

This definition was written using information located here:
    https://msdn.microsoft.com/en-us/library/dd942335.aspx
    https://msdn.microsoft.com/en-us/library/dd941946.aspx
    https://msdn.microsoft.com/en-us/library/dd942048.aspx
    https://msdn.microsoft.com/en-us/library/dd942434.aspx
    https://msdn.microsoft.com/en-us/library/dd941958.aspx
    https://msdn.microsoft.com/en-us/library/dd942368.aspx
    https://msdn.microsoft.com/en-us/library/dd942380.aspx
    https://msdn.microsoft.com/en-us/library/dd942304.aspx
    https://msdn.microsoft.com/en-us/library/dd942475.aspx
    https://msdn.microsoft.com/en-us/library/dd942153.aspx

An OLECF file structure loosely resembles a FAT filesystem.
The file is partitioned into sectors which are chained together
with a file allocation table which contains chains of sectors related
to each file. A directory holds information for contained files
with a sector id(SID) for the starting sector of a chain and so on.
'''
from supyr_struct.defs.tag_def import *
from supyr_struct.field_methods import *
from supyr_struct.fields import *
from array import array

from .objs.olecf import OlecfTag


# ##################################
#      Sector number constants     #
# ##################################
MAXREGSECT = 0xFFFFFFFA    # Maximum regular sector number.
RESERVEDSECT = 0xFFFFFFFB  # Reserved for future use.
DIFSECT = 0xFFFFFFFC       # DIFAT sector.
FATSECT = 0xFFFFFFFD       # FAT sector.
ENDOFCHAIN = 0xFFFFFFFE    # End of a linked chain of sectors.
FREESECT = 0xFFFFFFFF      # Unallocated sector.


# ##################################
#        Stream ID constants       #
# ##################################
MAXREGSID = 0xFFFFFFFA  # maximum regular stream id
NOSTREAM = 0xFFFFFFFF  # the stream id used when no sibling/child stream exists

# ##################################
#         Other constants          #
# ##################################
OLECF_RELEASESIG = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
OLECF_BETASIG = b'\x0E\x11\xFC\x0D\xD0\xCF\x11\xE0'
#D0CF11E0 = DOCFILE0 (anyone want some DEADBEEF?)

CLSID_NULL = b'\x00'*16

OLE_LE_SIG = b'\xFE\xFF'
OLE_BE_SIG = b'\xFF\xFE'

HEADER_DIFAT_LEN = 109
HEADER_DIFAT_EMPTY = array('I', (FREESECT for i in range(HEADER_DIFAT_LEN)))

# ##################################
#          Directory names         #
# ##################################
ROOT_ENTRY_STR = 'Root Entry'
STORAGE_STR = 'Storage %s'
STREAM_STR = 'Stream %s'


# ##################################
#     Time conversion constants    #
# ##################################
CATALOG_ENTRY_MIN_LEN = 16  # number of bytes of the non string fields
SECS_PER_100NS = 10**9 // 100
SECS_FROM_WIN32_TO_PY_TIME = 11644473600


def win32time_to_pytime(win32time):
    '''
    Converts a Windows 8byte unsigned long long(integer)
    timestamp to a python double(floating point) timestamp.
    '''
    return win32time/SECS_PER_100NS - SECS_FROM_WIN32_TO_PY_TIME


def pytime_to_win32time(pytime):
    '''
    Converts a python double(floating point) timestamp to
    a Windows 8byte unsigned long long(integer) timestamp.
    '''
    return int(pytime + SECS_FROM_WIN32_TO_PY_TIME) * SECS_PER_100NS


def olecf_header_pad_size(block=None, parent=None, attr_index=None,
                          rawdata=None, new_value=None, *args, **kwargs):
    '''Sizecalc routine for getting the byte size of the header padding'''
    if new_value is None:
        # if the sector_shift is provided, it will speed things up
        if 'sector_shift' in kwargs:
            return max(0, (1 << kwargs['sector_shift']) - 512)
        try:
            return max(0, (1 << parent.header.sector_shift) - 512)
        except AttributeError:
            return 0


def sector_size(block=None, parent=None, attr_index=None,
                rawdata=None, new_value=None, *args, **kwargs):
    '''Sizecalc routine for getting the byte size of a sector in the FAT'''
    if new_value is None:
        # if the sector_shift is provided, it will speed things up
        if 'sector_shift' in kwargs:
            return 1 << kwargs['sector_shift']
        try:
            return 1 << parent.get_root().data.header.sector_shift
        except AttributeError:
            return 0


def directory_sector_size(block=None, parent=None, attr_index=None,
                          rawdata=None, new_value=None, *args, **kwargs):
    '''
    Sizecalc routine for getting the number
    of directory entries in a directory sector
    '''
    # the "- 7" is because the directory entries are each 128 bytes(1 << 7)
    # so to get the number of entries that can be in a sector we simply
    # subtract the log2 size of the directory from the shift(logs are great)
    if new_value is None:
        # if the sector_shift is provided, it will speed things up
        if 'sector_shift' in kwargs:
            return 1 << max(0, kwargs['sector_shift'] - 7)
        try:
            return 1 << max(0, parent.get_root().data.header.sector_shift - 7)
        except AttributeError:
            return 0


def mini_sector_size(block=None, parent=None, attr_index=None,
                     rawdata=None, new_value=None, *args, **kwargs):
    '''Sizecalc routine for getting the byte size of a sector in the miniFAT'''
    if new_value is None:
        # if the mini_sector_shift is provided, it will speed things up
        if 'mini_sector_shift' in kwargs:
            return 1 << kwargs['mini_sector_shift']
        try:
            return 1 << parent.get_root().data.header.mini_sector_shift
        except AttributeError:
            return 0    


def sector_reader(self, desc, parent=None, rawdata=None, attr_index=None,
                  root_offset=0, offset=0, **kwargs):
    """
    """
    try:
        if attr_index is None and parent is not None:
            new_block = parent
        else:
            new_block = (desc.get(BLOCK_CLS, self.py_type)
                         (desc, parent=parent, init_attrs=rawdata is None))
            parent[attr_index] = new_block

        if rawdata:
            # give a more descriptive name to this array of sectors
            sector_array = new_block
            sector_desc = sector_array.desc[SUB_STRUCT]
            sector_field_reader = sector_desc[TYPE].reader

            sector_size = 1 << sector_array.get_root().data.header.sector_shift
            sector_count = len(rawdata) // sector_size - 1

            # the number of entries in a FAT sect_nums array
            fat_array_size = sector_size // 4

            # This is the last sector number whose FAT is addressed within
            # the header_difat. Any sector number higher than it will be
            # allocated to a FAT sector which is allocated to a DIFAT sector
            header_difat_max_sect = (HEADER_DIFAT_LEN - 1)*fat_array_size - 1
            sects_per_difat = (fat_array_size - 1)*fat_array_size

            # get the parent Tag object for accessing its 
            parent_tag = parent.get_root()

            if not isinstance(parent_tag, OlecfTag):
                raise TypeError(
                    'Root of an olecf Block tree must be an OlecfTag instance')

            # get the header so we can get information from it to parse with
            header = parent_tag.data.header

            # get the DIFAT array of the header
            header_difat = header.header_difat

            # add header information to kwargs to speed things up
            kwargs['sector_shift'] = header.sector_shift
            kwargs['mini_sector_shift'] = header.mini_sector_shift
            kwargs['mini_stream_cutoff'] = header.mini_stream_cutoff

            # get the starting sector of each sector chain
            difat_start = header.difat_sector_start
            minifat_start = header.minifat_sector_start
            dir_start = header.dir_sector_start

            # get the quick sector mappings
            difat_sectors = parent_tag.difat_sectors
            fat_sectors = parent_tag.fat_sectors
            minifat_sectors = parent_tag.minifat_sectors
            dir_sectors = parent_tag.dir_sectors
            dir_names = parent_tag.dir_names

            parent_tag.sector_size = sector_size

            # clear the quick sector mappings
            del difat_sectors[:]
            del fat_sectors[:]
            del minifat_sectors[:]
            del dir_sectors[:]
            del dir_names[:]

            kwargs['case'] = 'regular'

            # read all the sectors as regular sectors
            sector_array.extend(sector_count)
            for i in range(sector_count):
                offset = sector_field_reader(sector_desc, sector_array,
                                             rawdata, i, root_offset,
                                             offset, **kwargs)

            # first, parse the DIFAT sectors
            kwargs['case'] = 'difat'
            sect_num = difat_start

            # loop over each DIFAT sector, add its sector number to
            # the difat_sectors list, and reparse it as a DIFAT sector
            while sect_num not in (ENDOFCHAIN, FREESECT):
                curr_difat = sector_array[sect_num]
                difat_sectors.append(sect_num)

                # reparse the sector as a DIFAT sector
                sector_field_reader(sector_desc, sector_array,
                                    curr_difat.data,
                                    sect_num, 0, 0, **kwargs)

                sect_num = curr_difat[-1]


            # second, parse the FAT sectors
            kwargs['case'] = 'fat'

            # loop over each DIFAT sector, loop over each FAT sector
            # in that DIFAT sector, add the FATs sector number to
            # the fat_sectors list, and reparse it as a FAT sector
            for i in range(len(difat_sectors) + 1):
                # get the next DIFAT array
                if i:
                    curr_difat = sector_array[difat_sectors[i-1]].sect_nums
                else:
                    curr_difat = header_difat

                # loop over all but the last DIFAT sector number(it contains
                # the sector number of the next DIFAT sector in the chain)
                for sect_num in curr_difat[:-1]:
                    # if the chain of FAT sectors has ended, break out.
                    if sect_num == FREESECT:
                        break

                    fat_sectors.append(sect_num)

                    # reparse the sector as a FAT sector
                    sector_field_reader(sector_desc, sector_array,
                                        sector_array[sect_num].data,
                                        sect_num, 0, 0, **kwargs)


            # third, parse the miniFAT and directory sectors
            for case, sects, sect_num in (
                ('minifat', minifat_sectors, minifat_start),
                ('directory', dir_sectors, dir_start)):

                kwargs['case'] = case
                while sect_num != ENDOFCHAIN:
                    sects.append(sect_num)

                    # reparse the sector
                    sector_field_reader(sector_desc, sector_array,
                                        sector_array[sect_num].data,
                                        sect_num, 0, 0, **kwargs)

                    if case == 'directory':
                        for dir_entry in sector_array[sect_num]:
                            dir_names.append(dir_entry.name)

                    # decide if the FAT sector that holds the next
                    # sect_num in the chain is indexed by the headers
                    # DIFAT or a DIFAT sector somewhere in the file.
                    if sect_num > header_difat_max_sect:
                        fat_sect_index = ((sect_num - header_difat_max_sect) //
                                          fat_array_size)
                    else:
                        # get the index of the FAT sector that holds
                        # the next sector number in the sector chain
                        fat_sect_index = sect_num // fat_array_size
                    # get the next sector number
                    sect_num = sector_array[fat_sectors[fat_sect_index]].\
                               sect_nums[sect_num % fat_array_size]

        return offset
    except Exception as e:
        if 'sect_num' in locals():
            e = format_read_error(e, sector_desc.get(TYPE),
                                  sector_desc, new_block, rawdata,
                                  kwargs.get('case', 'regular'), sect_num)
        e = format_read_error(e, self, desc, parent, rawdata, attr_index,
                              root_offset + offset, **kwargs)
        raise e


# special field that properly parses the sectors in
# the right order using the 'sector_reader' function.
SectorArray = Field(base=WhileArray, name="SectorArray", reader=sector_reader)


# ##################################
#   Directory sector descriptors   #
# ##################################

# Storage directory entry in a directory stream.
# 4 of these structures can fit in a 512 byte directory stream.
storage_dir_entry = Struct('storage_dir_entry',
    LStrUtf16('name', SIZE=64),
    LUInt16('name_len'),

    UEnum8('storage_type',
        'unallocated',
        'storage',
        'stream',
        'lockbytes',  # not intended to be used by developers
        'property',   # not intended to be used by developers
        'root',
        ),
    UEnum8('de_color',
        'red',
        'black',
        ),
    LUInt32('stream_id_left'),
    LUInt32('stream_id_right'),
    LUInt32('stream_id_child'),

    BytesRaw('cls_id', SIZE=16, DEFAULT=CLSID_NULL),
    LUInt32('user_flags'),
    LUInt64('create_time'),
    LUInt64('modify_time'),
    LUInt32('stream_sect_start'),  # valid if storage_type == stream
    LUInt64('stream_len'),         # valid if storage_type == stream
    # For a version 3 file, the value of stream_len MUST be <= 0x80000000.
    # Note that as a consequence of this requirement, the most significant
    # 32 bits of this field MUST be zero in a version 3 compound file.
    # Ignore the most significant 32 bits of this field in version 3 files.

    # If stream_len < header.mini_stream_cutoff then the objects
    # data stream exists in the miniFat, otherwise it's in the FAT
    SIZE=128
    )


# ##################################
#         Sector Structures        #
# ##################################

# All these sectors need to be some sort of Block because they need
# to have their own descriptor since they will be used in a Switch.

# In the FAT and miniFAT arrays, each chain of sectors MUST be
# terminated by setting the last entry in the chain to ENDOFCHAIN.
# If a FAT or miniFAT sector needs to be added, the sector number its being
# placed in must be added to the next available entry in the DIFAT array.
fat_sector = Container('fat_sector',
    LUInt32Array('sect_nums', SIZE=sector_size)
    )

# The locations for miniFAT sectors are stored in a standard chain
# in the FAT, with the beginning of the chain stored in the header.
# A miniFAT sector number can be converted into a byte offset
# into the ministream by using the following formula:
#     sector_number << header.mini_sector_shift.
# This formula is different from the formula used to convert a
# sector number into a byte offset in the file, since no header
# is stored in the Ministream. This also means there is one and
# ONLY one ministream per olecf file. The ministream is chained
# within the FAT in exactly the same fashion as any normal stream.
# It is referenced by the first storage_dir_entry (SID 0).
minifat_sector = Container('minifat_sector',
    LUInt32Array('sect_nums', SIZE=sector_size)
    )

# DIFAT(double-indirect file allocation table) is an array of the
# sector numbers of each FAT sector in the order that they chain.
# If another DIFAT sector needs to be added to map out more space
# for additions to the file, the next DIFAT sector in the chain
# needs to be linked to the previous one by putting its sector
# number in the last entry in the previous DIFAT sector array.
difat_sector = Container('difat_sector',
    LUInt32Array('sect_nums', SIZE=sector_size)
    )

# a regular sector(treated as raw data)
regular_sector = Container('regular_sector',
    BytesRaw('data', SIZE=sector_size)
    )

# a sector made up of an array of directory entries
directory_sector = Array('directory_sector',
    SUB_STRUCT=storage_dir_entry, SIZE=directory_sector_size
    )

sector_switch = Switch('sector_switch',
    DEFAULT=regular_sector,
    CASE=no_case,
    CASES={'fat':fat_sector,
           'difat':difat_sector,
           'minifat':minifat_sector,
           'regular':regular_sector,
           'directory':directory_sector,
           }
    )

# the header structure present in EVERY olecf file.
# difat_sector_start, minifat_sector_start, and dir_sector_start are integer
# numbers assigned to each sector to specify what it is and how it should be
# treated. The 'Sector numbers' constants are special sector numbers.
# A sector number below MAXREGSECT is a regular sector.
olecf_header = Struct('header',
    BytesRawEnum("olecf_ver_sig",
        ("release", OLECF_RELEASESIG),
        ("beta",    OLECF_BETASIG),
        DEFAULT=OLECF_RELEASESIG, SIZE=8,
        ),
    BytesRaw('cls_id', SIZE=16,    # Reserved and unused class ID.
             DEFAULT=CLSID_NULL),  # MUST be zeroed out(CLSID_NULL)
    LUInt16('minor_version', DEFAULT=62),  # should be set to 62 if
    #                                        dll_version is 3 or 4
    LUInt16('major_version', DEFAULT=3),  # currently valid values are 3 and 4
    BytesRawEnum('byteorder',
        # I have no idea why they didnt put this earlier in the header
        ('little', OLE_LE_SIG),
        ('big',    OLE_BE_SIG),
        SIZE=2, DEFAULT=OLE_LE_SIG,
        ),
    LUInt16('sector_shift', DEFAULT=9),  # specifies the sector size
    #       of the compound file as power of 2. This must be set to 9 if
    #       major_version is set to 3, or 12 if major_version is set to 4.
    LUInt16('mini_sector_shift', DEFAULT=6),  # specifies the sector size of
    #                                           the mini stream as a power of 2
    #                                           MUST be set to 6 (64 bytes)
    Pad(6),
    LUInt32('dir_sector_count'),  # this is the number of directory sectors.
    #                               if major_version is 3, this MUST be 0
    LUInt32('fat_sector_count'),  # number of FAT sectors in the file
    LUInt32('dir_sector_start',  # starting sector num of the directory stream
            DEFAULT=ENDOFCHAIN),
    LUInt32('trans_sig_num'),  # MAY contain a sequence number that is
    #       incremented every time the compound file is saved by an
    #       implementation that supports file transactions. This field MUST
    #       be set to all zeroes if file transactions are not implemented.
    LUInt32('mini_stream_cutoff', DEFAULT=4096),  # MUST be set to 4096.
    #       Specifies the maximum byte size of a user-defined data stream that
    #       is allocated from mini FAT and mini stream, which is 4096 bytes.
    #       Any user-defined data stream that is larger than or equal to this
    #       cutoff size must be allocated as normal sectors from the FAT.
    LUInt32('minifat_sector_start',  # starting sector num of the miniFAT
            DEFAULT=ENDOFCHAIN),
    LUInt32('minifat_sector_count'),  # number of miniFAT sectors in the file
    LUInt32('difat_sector_start',  # starting sector num of the DIFAT
            DEFAULT=ENDOFCHAIN),
    LUInt32('difat_sector_count'),  # number of DIFAT sectors
    LUInt32Array('header_difat',
                 SIZE=HEADER_DIFAT_LEN * 4,   # contains the first 109 FAT
                 DEFAULT=HEADER_DIFAT_EMPTY), # sector numbers of the file.
    SIZE=512,
    )


olecf_def = TagDef("olecf",
    olecf_header,
    BytesRaw('header_padding', SIZE=olecf_header_pad_size),
    SectorArray('sectors', SUB_STRUCT=sector_switch),
    ext=".olecf", endian="<", tag_cls=OlecfTag
    )
