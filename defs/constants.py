'''
This module contains descriptor keyword constants, structure
alignment constants, Block printing constants, supyr_struct
exception classes, and a four-character-code function(fcc)
for converting a string of 4 characters into an int.
'''

from string import ascii_letters as _ascii_letters
from os.path import join as _join


# ##################################################
# ----      Descriptor keyword constants      ---- #
# ##################################################

# These are the most important and most used keywords
NAME = "NAME"  # The given name of an element. This is copied into
#                the NAME of the parent descriptor.
#                Must be a string.
TYPE = "TYPE"  # The Field that describes the data
#                Must be a Field.
SIZE = "SIZE"  # Specifies an arrays entry count, a structs byte size,
#                the length of a string, the length of a bytes object, etc.
#                Must be an int, function, or a pathstring.
SUB_STRUCT = "SUB_STRUCT"  # The structure to repeat in an array or the
#                            structure that is wrapped in a StreamAdapter.
#                            Must be a descriptor.
CASE = "CASE"  # Specifies which descriptor to use for a Switch Field.
#                Must be an int, function, or a pathstring.
#                If used in a WhileArray, this must be a function
#                and must return a bool specifying whether or not
#                another Block should be built.
CASES = "CASES"  # Contains all the different possible descriptors that can
#                  be chosen by the Union/Switch block it is enclosed in.
#                  CASE determines which key to look for the descriptor
#                  under. If the descriptor doesnt exist under that key,
#                  a VoidBlock with a void_desc is built instead.
#                  Must be a dict.
VALUE = "VALUE"  # The value of a specific enumerator/boolean option.
#                  If not specified, one will be deduced. The position 'i'
#                  is the integer key of the option in the descriptor plus
#                  the amount of padding before it. For bools, VALUE will
#                  default to '2**i'. Otherwise it will default to 'i'.
#                  Must be an int, str, or bytes.
DECODER = "DECODER"  # A function used to decode and return a Buffer for
#                      the StreamAdapter Field before it is handed off
#                      to be parsed by the StreamAdapter's SUB_STRUCT.
#                      Also returns how much of the input stream was decoded.
#                      Must be a function.


# These are supplementary keywords that give more control
# over creating a structure, how and where to read/write, etc
ALIGN = "ALIGN"  # The byte size to align the offset to before reading or
#                  writing. Alignment is done using this method:
#                      offset += (align - (offset % align)) % align
#                  Must be an int.
INCLUDE = "INCLUDE"  # This one's a convience really. When a dict is in
#                      a descriptor under this key and the descriptor is
#                      sanitized, all entries in that dict are copied
#                      into the descriptor. Must be a dict.
CARRY_OFF = "CARRY_OFF"  # Whether or not to return the incremented offset
#                          after a Block is finished being parsed. If False,
#                          the initially supplied offset is returned.
#                          Defaults to True if not given. This is mainly
#                          intended to be used with pointers.
#                          Must be a bool.
DEFAULT = "DEFAULT"  # Used to specify what the value of some attribute
#                      should be in a field when a blank structure is created.
#                      If the Field.py_type is not a subclass of Block, then
#                      this should be an object which will be copied and the
#                      copy placed into the parent structure.
#                      For Fields whose py_type is a subclass of Block,
#                      this should be the class constructor of that Block.
ENDIAN = "ENDIAN"  # Specifies which endianness instance of a Field to use.
#                    This is only used by BlockDefs during their sanitization
#                    process. If not given, the Field that already exists in
#                    the descriptor will be used. ENDIAN is carried over into
#                    inner descriptors during the sanitization process.
#                    Valid values are '<' for little and '>' for big endian.
#                    Must be a string.
OFFSET = "OFFSET"  # The offset within the structure the data is located at.
#                    Meant specifically for struct elements. When a descriptor
#                    is sanitized, this is removed from the descriptor it is
#                    in and moved into the parent descriptors ATTR_OFFS list.
#                    Must be an int.
POINTER = "POINTER"  # Defines where in the buffer to read or write.
#                      The differences between POINTER and OFFSET are that
#                      POINTER is not removed from the descriptor it's in and
#                      POINTER is used relative to root_offset whereas OFFSET
#                      is used relative to the offset of the parent structure.
#                      Must be an int, function or a pathstring.
ENCODER = "ENCODER"  # A function used to encode and return the buffer that was
#                      written to by the StreamAdapter's SUB_STRUCT attribute.
#                      This encoded buffer should be able to be decoded by this
#                      same descriptors DECODE function.
#                      Must be a function.
CHILD = "CHILD"  # A descriptor used for a Block that is usually described
#                  by its parent. CHILD blocks are not members of a structure,
#                  but are linked  to it. They are read/written in a different
#                  order than the elements of a structure.
#                  Must be a descriptor.


# These are keywords that are mainly used by supyrs implementation
# and are always autogenerated by sanitization routines.
ENTRIES = "ENTRIES"  # The number of integer keyed entries in the descriptor.
#                      Must be an int.
NAME_MAP = "NAME_MAP"  # Maps the given name of each attribute to the list
#                        index or __slot__ name that the attribute is
#                        actually stored under. Must be a dict.
CASE_MAP = "CASE_MAP"  # Maps the given case value of each sub-descriptor
#                        in a Union or Switch descriptor to the index it
#                        is stored under. Must be a dict.
VALUE_MAP = "VALUE_MAP"  # Maps the given value of each possible enumeration
#                          value to the index that specific options descriptor
#                          is located in. This serves to enable a flat lookup
#                          time when trying to determine which enumerator
#                          option is selected. Must be a dict.
ATTR_OFFS = "ATTR_OFFS"  # A list containing the offset of each of structs
#                          attributes. Must be a list.
ORIG_DESC = "ORIG_DESC"  # When the descriptor of an object is modified, that
#                          objects descriptor is shallow copied to be unique.
#                          A reference to the original descriptor is created in
#                          the copy with this as the key. The presence of this
#                          key is what indicates that a descriptor is unique.
#                          Must be a descriptor.
ADDED = "ADDED"  # A freeform entry that is neither expected to exist,
#                  nor have any specific structure. It is ignored by the
#                  sanitizer routine and is primarily meant for allowing
#                  developers to add their own data to a descriptor without
#                  having to make a new descriptor keyword for it.
#                  Can be anything.


# This is a set of all the keywords above, and can be used
# to determine if a string is a valid descriptor keyword.
desc_keywords = set((
                     # required keywords
                     NAME, TYPE, SIZE, SUB_STRUCT,
                     CASE, CASES, VALUE, DECODER,

                     # optional keywords
                     ALIGN, INCLUDE, CARRY_OFF, DEFAULT,
                     ENDIAN, OFFSET, POINTER, ENCODER, CHILD,

                     # keywords used by the supyrs implementation
                     ENTRIES, CASE_MAP, NAME_MAP,
                     VALUE_MAP, ATTR_OFFS, ORIG_DESC, ADDED
                     ))

# Shorthand alias for desc_keywords
desc_kw = desc_keywords

# A set of strings that cant be used as a NAME entry
# in a descriptor. These are either descriptor keywords
# themselves, a __slots__ name, or a Block method.
reserved_desc_names = set(desc_kw)

# update with slot names found in Block __slots__ which would cause conflicts
reserved_desc_names.update(('desc', 'parent', 'u_index'))

# update with python magic method names
reserved_desc_names.update(
    ('__getitem__', '__setitem__', '__delitem__', '__iter__', '__next__',
     '__missing__', '__reversed__', '__len__', '__contains__', '__index__',
     '__get_attr__', '__set_attr__', '__del_attr__', '__bytes__',
     '__get__', '__set__', '__del__', '__copy__', '__deepcopy__', '__hash__',
     '__instancecheck__', '__subclasscheck__', '__subclasshook__',

     '__init__', '__repr__', '__str__', '__new__', '__dir__', '__call__',
     '__format__', '__main__', '__name__', '__sizeof__',

     '__add__',  '__sub__',  '__mul__',  '__truediv__',  'floordiv__',
     '__radd__', '__rsub__', '__rmul__', '__rtruediv__', '__rfloordiv__',

     '__mod__',  '__divmod__',  '__pow__',  '__lshift__',  '__rshift__',
     '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__',

     '__and__',  '__xor__',  '__or__', '__rand__', '__rxor__', '__ror__',

     '__iadd__', '__isub__', '__imul__', '__itruediv__', '__ifloordiv__',
     '__imod__', '__ipow__', '__ilshift__', '__irshift__',
     '__iand__', '__ixor__', '__ior__', '__neg__', '__pos__',
     '__abs__', '__invert__', '__complex__', '__int__', '__float__',

     '__round__', '__ceil__', '__floor__', '__trunc__',

     '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__', '__bool__',
     '__getstate__', '__setstate__', '__reduce__', '__reduce_ex__',
     '__getnewargs__', '__enter__', '__exit__'))

# update with methods found in Block
reserved_desc_names.update(('_binsize',  'binsize', 'make_unique',
                            'attr_to_str', 'validate_name', 'get_rawdata',
                            'set_desc', 'del_desc', 'ins_desc', 'res_desc',
                            'tag', 'get_neighbor', 'set_neighbor', 'get_desc',
                            'get_meta', 'set_meta', 'build', 'serialize',
                            'collect_pointers', 'set_pointers', 'pprint'))

# update with methods found in ListBlock
reserved_desc_names.update(('append', 'extend', 'insert', 'pop',
                            'index_by_id', 'get_size', 'set_size',
                            'set', 'set_to', 'unset', 'data_name',
                            'get_index', 'get_name', 'get_data', 'set_data'))

# update with methods found in UnionBlock
reserved_desc_names.update(('set_active', 'read', 'write'))

# Characters valid to be used in element names.
# ALPHA_NUMERIC_IDS is used for every character after the
# first since python identifiers cant start with an integer
ALPHA_IDS = frozenset(_ascii_letters + '_')
ALPHA_NUMERIC_IDS_STR = _ascii_letters + '_' + '0123456789'
ALPHA_NUMERIC_IDS = frozenset(ALPHA_NUMERIC_IDS_STR)


# Strings used when printing Blocks and errors
UNNAMED = "<UNNAMED>"
INVALID = "<INVALID>"
RAWDATA = "<RAWDATA>"
UNPRINTABLE = "<UNABLE TO PRINT LINE>"
SIZE_CALC_FAIL = "<COULD NOT CALCULATE PACKED SIZE>"
RECURSIVE = "<RECURSIVE BLOCK '%s' ID '%s'>"
MISSING_DESC = "<NO DESCRIPTOR FOR OBJECT OF TYPE %s>"


# ###################################################
# ----      Structure alignment constants      ---- #
# ###################################################

# The largest byte alignment the automatic alignment routine will choose
ALIGN_MAX = 8

# The alignment modes available
ALIGN_NONE = "ALIGN_NONE"
ALIGN_AUTO = "ALIGN_AUTO"

# The algorithm this library uses for automatic alignment is
# align = 2**int(ceil(log(data_size, 2)))
#
# Because of this, "doubles" must be manually defined as having
# 4-byte alignment if imitating Linux or GCC, "long doubles" must be
# manually defined as having 2-byte alignment if imitating DMC.


# ######################################
# ----       Other constants      ---- #
# ######################################

# This is the default amount of spacing a block
# being printed uses when indenting the blocks
BLOCK_PRINT_INDENT = BPI = 4


# The character used to divide folders on this operating system
# This way pathdiv is system dependent so this will work on linux
PATHDIV = _join('a', '')[1:]

# the minimal things to show in a block
MIN_SHOW = frozenset(('field', 'name', 'value', 'children'))

# The default things to show when printing a Block or Tag
DEF_SHOW = frozenset(('field', 'name', 'value', 'offset',
                      'flags', 'size', 'children', 'trueonly'))

# the most important things to show
MOST_SHOW = frozenset((
    "name", "value", "field", "offset", "children",
    "flags", "unique", "size", "index",
    "filepath", "binsize", "ramsize"))

# The things shown when printing a Block or Tag
# and one of the strings in 'show' is 'all'.
ALL_SHOW = frozenset((
    "name", "value", "field", "offset", "children",
    "flags", "unique", "size", "index", "raw",
    "filepath", "py_id", "py_type", "binsize", "ramsize"))


def fcc(value, byteorder='little', signed=False):
    '''
    Converts a string of 4 characters into an int using
    the supplied byteorder, signage, and latin1 encoding.

    Returns the encoded int.
    '''
    # The fcc wont let me be, or let me be me, so let me see.....
    return int.from_bytes(bytes(value, encoding='latin1'),
                          byteorder, signed=signed)


# #######################################
# ----      exception classes      ---- #
# #######################################


class SupyrStructError(Exception):
    pass


class IntegrityError(SupyrStructError):
    pass


class SanitizationError(SupyrStructError):
    pass


class DescEditError(SupyrStructError):
    pass


class DescKeyError(SupyrStructError):
    pass


class FieldReadError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.


class FieldWriteError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.

# cleanup
del _ascii_letters
del _join