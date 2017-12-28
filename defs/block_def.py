'''
NEED TO DOCUMENT
'''
from math import log as _log, ceil as _ceil
from traceback import format_exc

from supyr_struct.defs.frozen_dict import FrozenDict
from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.defs.common_descs import *
from supyr_struct.buffer import get_rawdata

# linked to through supyr_struct.__init__
blocks = None
field_types = None


class BlockDef():
    '''
    BlockDefs are objects which contain a dict tree of structure
    descriptions(called a descriptor). The BlockDef uses this
    descriptor when its build method is invoked to build Blocks
    from either a buffer of rawdata, a file(given as a filepath),
    or from nothing(builds a Block with all attributes defaulted).

    The sanitizer function of the TYPE entry in each descriptor
    is responsible for taking a descriptor and 'sanitizing' it.
    Sanitizing involves reporting any errors detected and generating
    required entries from supplied ones(such as NAME_MAP, ATTR_OFFS,
    CASE_MAP, ENTRIES, etc). Sanitizers are called during the course
    of a BlockDefs sanitize method being run.

    Take a look at supyr_struct\\docs\\descriptors.txt for much more
    information on what a descriptor is, how it functions, etc

    Example:

    >>> asdf = BlockDef('some_blockdef',
    ...     UInt32('some_int'),
    ...     BytesRaw('some_bytes', SIZE=256),
    ...     ENDIAN='>'
    ...     )

    The def_id 'some_blockdef' is also reused as the descriptors NAME entry.
    The resulting descriptor(after being run through the BlockDef sanitizing
    routines) would look like this:

    >>> pprint(asdf.descriptor)
    {0: {'NAME': 'some_int',
         'TYPE': <FieldType:'UInt32', endian:'>', enc:'>I'>},
     1: {'NAME': 'some_bytes',
         'SIZE': 256,
         'TYPE': <FieldType:'BytesRaw', endian:'=', enc:'B'>},
     'ENDIAN': '>',
     'ENTRIES': 2,
     'NAME': 'some_blockdef',
     'NAME_MAP': FrozenDict({'some_int': 0, 'some_bytes': 1}),
     'TYPE': <FieldType:'Container', endian:'=', enc:'None'>}

    Instance properties:
        dict:
            subdefs
        FrozenDict:
            descriptor
        str:
            align_mode
            def_id
            endian

    Read this classes __init__.__doc__ for descriptions of these properties.
    '''

    _bad = False  # Signals to the sanitize function that errors
    #               were encountered during sanitization.
    _e_str = ''  # A string description of any errors encountered
    #              while sanitizing. An exception is raised using
    #              this string after sanitization is completed.
    _initialized = False  # Whether or not the definition has been built.
    sani_warn = True
    align_mode = ALIGN_NONE
    endian = ''
    def_id = None

    # initialize the class
    def __init__(self, def_id_or_desc, *desc_entries, **kwargs):
        '''
        Initializes a BlockDef.

        Instead of passing a complete descriptor as a keyword argument,
        the int keyed entries in a descriptor may be passed as positional
        arguments and the str keyed entries as keyword arguments.

        Positional arguments:
        # str:
        def_id --------- An identifier string used for naming and keeping
                         track of BlockDefs. Used as the NAME entry in the
                         top level of the descriptor if one doesnt exist.

        Optional positional arguments:
        # dict:
        *desc_entries -- Dictionaries formatted as descriptors. A descriptor
                         will be built from all supplied positional arguments
                         and all keyword arguments(if the keyword is in the
                         desc_keywords set). Positional arguments are keyed
                         under the index they are located at in desc_entries,
                         and keyword arguments are keyed under their keyword.
                         If a FieldType is not supplied under the TYPE keyword,
                         the BlockDef will default to using Container.
                         If supplying a descriptor in this way, do not provide
                         one through the "descriptor" keyword as well. Doing
                         so will raise a TypeError

        Optional keyword arguments:
        # dict:
        descriptor ----- A dictionary which stores a detailed and well formed
                         tree of other detailed and well formed dictionaries
                         which each describe some type of data or structure.
                         Most descriptors are only required to have NAME and
                         TYPE entries, but depending on the FieldType instance
                         in the TYPE, other entries may be required.
                         If supplying a descriptor in this way, do not provide
                         one through positional arguments and desc_keyword
                         named arguments. Doing so will raise a TypeError
        subdefs -------- Used for storing individual or related pieces of
                         the structure.

        # str:
        align_mode ----- The alignment method to use for aligning containers
                         and their attributes to whole byte boundaries based
                         on each ones byte size. Valid values for this are
                         ALIGN_NONE and ALIGN_AUTO.
        endian --------- The default endianness to use for every field in the
                         descriptor. This can be overridden by specifying the
                         endianness per field. Endian carries over from outer
                         field to inner fields
        '''
        if self._initialized:
            return

        if isinstance(def_id_or_desc, dict):
            self.descriptor = def_id_or_desc
            def_id = def_id_or_desc["NAME"]
        else:
            def_id = def_id_or_desc

        if not hasattr(self, "descriptor"):
            self.descriptor = {}
        if not hasattr(self, "subdefs"):
            self.subdefs = {}

        self.align_mode = kwargs.pop("align_mode", self.align_mode)
        self.descriptor = kwargs.pop("descriptor", self.descriptor)
        self.endian = kwargs.pop("endian", self.endian)
        self.sani_warn = bool(kwargs.pop("sani_warn", self.sani_warn))
        self.subdefs = dict(kwargs.pop("subdefs", self.subdefs))
        self.def_id = def_id
        self._initialized = True

        # make sure def_id is valid
        if not isinstance(self.def_id, str):
            raise TypeError("Invalid type for 'def_id'. Expected %s, got %s." %
                            (str, type(self.def_id)))

        # make sure the endian value is valid
        if not isinstance(self.endian, str):
            raise TypeError("Invalid type for 'endian'. Expected %s, got %s." %
                            (str, type(self.endian)))
        if self.endian not in ('<', '', '>'):
            raise ValueError(
                "Invalid endianness character provided.Valid characters are " +
                "'<' for little, '>' for big, and '' for none.")

        # whether or not a descriptor should be built from the
        # keyword arguments and optional positional arguments.
        build_desc = (desc_entries or
                      not desc_keywords.isdisjoint(kwargs.keys()))

        if self.descriptor and build_desc:
            raise TypeError(
                ("A descriptor already exists or was provided for the " +
                 "'%s' BlockDef, but individual BlockDef arguments were " +
                 "also supplied.\nCannot accept positional arguments " +
                 "when a descriptor exists.") % self.def_id)

        # determine how to get/make this BlockDefs descriptor
        if build_desc:
            self.descriptor = self.make_desc(*desc_entries, **kwargs)
            self.descriptor = FrozenDict(self.sanitize(self.descriptor))
        elif isinstance(self.descriptor, BlockDef):
            self.subdefs.update(self.descriptor.subdefs)
            self.descriptor = FrozenDict(self.descriptor.descriptor)
        elif self.descriptor and kwargs.get('sanitize', True):
            self.descriptor = FrozenDict(self.sanitize(self.descriptor))

        self.make_subdefs()

    def build(self, **kwargs):
        '''Builds and returns a block'''
        desc = self.descriptor
        f_type = desc[TYPE]

        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("int_test", False)
        kwargs.setdefault("rawdata", get_rawdata(**kwargs))
        kwargs.pop("filepath", None)  # rawdata and filepath cant both exist

        # create the Block instance to parse the rawdata into
        new_block = desc.get(BLOCK_CLS, f_type.node_cls)(desc, init_attrs=False)

        if kwargs.pop("allow_corrupt", False):
            try:
                new_block.parse(**kwargs)
            except Exception:
                print(format_exc())
        else:
            new_block.parse(**kwargs)
        return new_block

    def decode_value(self, value, **kwargs):
        '''
        '''
        p_f_type = kwargs.get('p_f_type')
        endian = 'big' if p_f_type.endian == '>' else 'little'

        if (isinstance(value, str) and (issubclass(p_f_type.data_cls, int) or
                                        (issubclass(p_f_type.node_cls, int)))):
            # if the value is a string and either the FieldTypes
            # data_cls or its node_cls is an int, then convert
            # the string into bytes and then into an integer.
            if endian == 'little':
                value = ''.join(reversed(value))

            return int.from_bytes(
                bytes(value, encoding='latin1'),  byteorder=endian)
        else:
            return value

    def find_entry_gaps(self, src_dict):
        '''Finds and reports gaps in descriptors that should be gap-less.'''

        if ENTRIES not in src_dict:
            return

        last_entry = src_dict[ENTRIES]
        i = gap = 0
        offender_names = []

        while i < last_entry:
            if i not in src_dict:
                gap += 1
                last_entry += 1
            elif gap:
                offender_names.append(src_dict[i].get(NAME, UNNAMED))
            i += 1

        if gap:
            self._bad = True
            self._e_str += (
                ("ERROR: DESCRIPTOR CONTAINS %s GAPS IN ITS INTEGER " +
                 "KEYED ITEMS.\n   CHECK THE ORDERING OF '%s'\n") %
                (gap, self.def_id))
            self._e_str += ("\n   NAME OF OFFENDING DESCRIPTOR IS " +
                            "'%s'\n\n" % src_dict.get(NAME, UNNAMED))
            self._e_str += '\n   OFFENDING DESCRIPTOR ENTRIES ARE:\n'
            for name in offender_names:
                self._e_str += '      %s\n' % name
            self._e_str += '\n'

    def find_errors(self, src_dict, **kwargs):
        '''Returns a string textually describing any errors that were found.'''
        # Get the name of this block so it can be used in the below routines
        name = src_dict.get(NAME, UNNAMED)
        f_type = src_dict.get(TYPE, Void)

        substruct = kwargs.get('substruct')
        p_f_type = kwargs.get('p_f_type')
        p_name = kwargs.get('p_name')

        e = "ERROR: %s.\n"
        error_str = ''
        if src_dict.get(ENDIAN, '') not in '<>':
            error_str += e % ("ENDIANNESS CHARACTERS MUST BE EITHER '<' FOR " +
                              "LITTLE ENDIAN, '>' FOR BIG ENDIAN, OR '' " +
                              "FOR NONE. NOT %s" % kwargs.get('end'))

        # make sure bit and byte level fields arent mixed improperly
        if isinstance(p_f_type, field_types.FieldType):
            if p_f_type.is_bit_based and p_f_type.is_struct:
                # parent is a bitstruct
                if not f_type.is_bit_based:
                    # but this is NOT bitbased
                    error_str += e % (
                        "bit_structs MAY ONLY CONTAIN bit_based data FIELDS")
                elif f_type.is_struct:
                    error_str += "ERROR: bit_structs CANNOT CONTAIN structs"
            elif f_type.is_bit_based and not f_type.is_struct:
                error_str += e % (
                    "bit_based FIELDS MUST RESIDE IN A bit_based struct")

        # if the field is inside a struct, make sure its allowed to be
        if substruct:
            # make sure open ended sized data isnt in a struct
            if f_type.is_oe_size:
                error_str += e % "oe_size FIELDS CANNOT EXIST IN A struct"
            # make sure containers aren't inside structs
            if f_type.is_container and not(
                f_type.is_array and isinstance(src_dict.get("SIZE"), int)):
                error_str += e % (
                    "containers CANNOT EXIST IN A struct. structs ARE " +
                    "REQUIRED TO BE A FIXED SIZE WHEREAS containers ARE NOT")

        if f_type.is_var_size and f_type.is_data:
            if substruct and not isinstance(src_dict.get(SIZE), int):
                error_str += e % ("var_size data WITHIN A STRUCT MUST HAVE " +
                                  "ITS SIZE STATICALLY DEFINED BY AN INTEGER")
            elif SIZE not in src_dict and not f_type.is_oe_size:
                error_str += e % ("var_size data MUST HAVE ITS SIZE GIVEN BY" +
                                  "EITHER A FUNCTION, PATH STRING, OR INTEGER")

        if f_type.is_array:
            # make sure arrays have a size if they arent open ended
            if not(f_type.is_oe_size or SIZE in src_dict):
                error_str += e % ("NON-OPEN ENDED arrays MUST HAVE " +
                                  "A SIZE DEFINED IN THEIR DESCRIPTOR")
            # make sure arrays have a SUB_STRUCT entry
            if SUB_STRUCT not in src_dict:
                error_str += e % (
                    "arrays MUST HAVE A SUB_STRUCT ENTRY IN THEIR DESCRIPTOR")
        if error_str:
            error_str = (
                ("\n%s    NAME OF OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" +
                 "    OFFENDING ELEMENT IS LOCATED IN '%s' OF TYPE %s.\n") %
                (error_str, name, f_type.name, p_name, p_f_type.name))

        return error_str

    def get_align(self, src_dict, key):
        '''
        '''
        this_d = src_dict[key]
        if not isinstance(this_d, dict):
            self._e_str += ("ERROR: EXPECTED %s IN %s OF %s, GOT %s\n" %
                            (dict, key, src_dict.get(NAME), type(this_d)))
            self._bad = True
            return 0
        f_type = this_d.get(TYPE, Void)
        align = size = 1

        if f_type.is_raw:
            size = 1
        elif f_type.is_data or (f_type.is_bit_based and f_type.is_struct):
            # if the entry is data(or a bitstruct) then align
            # it by its size, or by char size if its a string
            if f_type.is_str:
                size = f_type.size
            else:
                size = self.get_size(src_dict, key)
        elif f_type.is_array:
            if SUB_STRUCT in src_dict[key]:
                # get and use the alignment of the substruct descriptor
                align = self.get_align(src_dict[key], SUB_STRUCT)
        elif f_type.is_struct:
            # search through all entries in the struct
            # to find the largest alignment and use it
            align = 1
            for i in range(this_d.get(ENTRIES, 1)):
                desc_align = self.get_align(this_d, i)
                if desc_align > align:
                    align = desc_align
                if align >= ALIGN_MAX:
                    return ALIGN_MAX

        if ALIGN in this_d:
            # alignment is specified manually
            return this_d[ALIGN]
        elif self.align_mode == ALIGN_AUTO and size > 0:
            # automatic alignment is to be used
            align = 2**int(_ceil(_log(size, 2)))
            if align > ALIGN_MAX:
                return ALIGN_MAX
        return align

    def get_endian(self, src_dict, end=None):
        '''Returns the wanted endianness of the FieldType'''
        if ENDIAN in src_dict:
            return src_dict[ENDIAN]
        elif end in ('<', '>'):
            return end
        elif self.endian != '':
            return self.endian
        return None  # just to make it obvious that it should return None

    def get_size(self, src_dict, key=None):
        '''
        '''
        this_d = src_dict.get(key, src_dict)
        f_type = this_d.get(TYPE, Void)

        # make sure we have names for error reporting
        p_name = src_dict.get(NAME, UNNAMED)
        name = this_d.get(NAME, UNNAMED)

        if (f_type.is_var_size and f_type.is_data) or\
           (SIZE in this_d and isinstance(this_d[SIZE], int)):
            if SIZE not in this_d:
                self._e_str += (
                    "ERROR: var_size data MUST HAVE ITS SIZE GIVEN BY " +
                    "EITHER A FUNCTION, PATH STRING, OR INTEGER.\n    " +
                    "OFFENDING ELEMENT IS '%s' IN '%s'\n" % (name, p_name))
                self._bad = True
                return 0

            size = this_d[SIZE]

            # this is an array, so multiply its size by the element's size
            if f_type.is_array:
                subsize = self.get_size(this_d[SUB_STRUCT])
                if not isinstance(subsize, int):
                    self._e_str += (
                        "ERROR: array MUST HAVE ITS SUB_STRUCT SIZE " +
                        "GIVEN BY AN INTEGER.\n    OFFENDING ELEMENT " +
                        "IS '%s' IN '%s'\n" % (name, p_name))
                    self._bad = True
                    return 0
                size *= subsize
        elif f_type.is_struct:
            # find the size of the struct as a sum of the sizes of its entries
            size = 0
            for i in range(this_d.get(ENTRIES, 0)):
                size += self.get_size(this_d, i)
        else:
            size = f_type.size

        if f_type.is_bit_based and not(f_type.is_struct or
                                       src_dict.get(TYPE, Void).is_bit_based):
            size = int(_ceil(size/8))
        return size

    def include_attrs(self, src_dict):
        '''
        '''
        if INCLUDE not in src_dict:
            return src_dict

        all_includes = (src_dict.pop(INCLUDE), )

        while all_includes:
            include_more = []
            for include in all_includes:
                for key in set(include.keys()):
                    # if there is another include, add it to include_more.
                    if key == INCLUDE:
                        include_more.append(include.pop(key))
                        continue
                    # if an item doesnt exist under this key, include it
                    src_dict.setdefault(key, include[key])
            all_includes = tuple(include_more)
        return src_dict

    def make_desc(self, *desc_entries, **desc):
        '''
        Converts the supplied positional arguments and keyword arguments
        into a dictionary properly formatted to be used as a descriptor.
        Returns the descriptor.
        '''
        # make sure the descriptor has a type and a name.
        subdefs = self.subdefs
        desc.setdefault(TYPE, Container)
        desc.setdefault(NAME, self.def_id)

        # remove all keyword arguments that aren't descriptor keywords
        for key in tuple(desc.keys()):
            if key not in desc_keywords:
                del desc[key]
                continue
            elif isinstance(desc[key], BlockDef):
                # if the entry in desc is a BlockDef, it
                # needs to be replaced with its descriptor.
                subdefs[key] = desc[key]
                desc[key] = desc[key].descriptor

        # add all the positional arguments to the descriptor
        for i in range(len(desc_entries)):
            desc[i] = desc_entries[i]
            if isinstance(desc[i], BlockDef):
                # if the entry in desc is a BlockDef, it
                # needs to be replaced with its descriptor.
                subdefs[i] = desc[i]
                desc[i] = desc[i].descriptor

        return desc

    def make_subdefs(self, replace_subdefs=False):
        '''
        Converts all the entries in self.subdefs into BlockDefs and
        tries to make BlockDefs for all the entries in the descriptor.
        '''
        desc = self.descriptor

        sub_kwargs = {'align_mode': self.align_mode, 'endian': self.endian}

        # make sure all the subdefs are BlockDefs
        for i in self.subdefs:
            d = self.subdefs[i]
            if not isinstance(d, BlockDef):
                self.subdefs[i] = BlockDef(str(i), descriptor=d, **sub_kwargs)

        # DO NOT REMOVE THE RETURN!!!!!
        # The below code was causing a 300% memory bloat and making library
        # startup take much longer. Only enable if a solution is found.
        return

        # try to make all descriptors in this Blockdef into their own BlockDefs
        for i in desc:
            # if the key already exists then dont worry about making one
            if i in self.subdefs and not replace_subdefs:
                continue
            d = desc[i]
            if isinstance(d, dict) and TYPE in d and d[TYPE].is_block:
                name = d[NAME]
                try:
                    self.subdefs[name] = BlockDef(name, descriptor=d,
                                                  **sub_kwargs)
                except Exception:
                    pass

    def sanitize(self, desc=None):
        '''
        Use this to sanitize a descriptor.
        Adds key things to the Tag_Def that may be forgotten, mistyped,
        or simply left out and informs the user of issues through print().
        '''

        # reset the error status to normal
        self._bad = False

        if desc is None:
            desc = self.descriptor

        # make sure desc is mutable
        desc = dict(desc)

        try:
            self.sanitize_name(desc)
            struct_cont = self.sanitize_loop(desc, key_name=None,
                                             end=self.endian)
        except Exception:
            self._e_str = '\n' + self._e_str
            self._bad = self._initialized = True
            raise SanitizationError((self._e_str + "\n'%s' encountered " +
                                     "the above errors during its " +
                                     "initialization.") % self.def_id)

        # if an error occurred while sanitizing, raise an exception
        if self._bad:
            self._e_str = '\n' + self._e_str
            self._initialized = True
            raise SanitizationError((self._e_str + "\n'%s' encountered " +
                                     "the above errors during its " +
                                     "initialization.") % self.def_id)
        return struct_cont

    def sanitize_loop(self, src_dict, **kwargs):
        '''
        '''
        # if the src_dict is a FrozenDict, make it mutable
        if isinstance(src_dict, FrozenDict):
            src_dict = dict(src_dict)

        # combine the entries from INCLUDE into the dictionary
        src_dict = self.include_attrs(src_dict)

        # if the type doesnt exist nothing needs to be done, so quit early
        if TYPE not in src_dict:
            return src_dict

        p_f_type = src_dict[TYPE]
        if p_f_type not in field_types.all_field_types:
            self._bad = True
            raise TypeError(
                "'TYPE' in a descriptor must be a valid FieldType.\n" +
                "Got %s of type %s" % (p_f_type, type(p_f_type)))

        # Change the FieldType to the endianness specified.
        endian = kwargs['end'] = self.get_endian(src_dict, kwargs.get('end'))
        if endian is not None:
            p_f_type = {'>': p_f_type.big, '<': p_f_type.little}[endian]
        src_dict[TYPE] = p_f_type
        p_name = src_dict.get(NAME, UNNAMED)

        sub_kwargs = dict(kwargs, p_f_type=p_f_type, p_name=p_name)

        # let all the sub-descriptors know they are inside a struct
        sub_kwargs["substruct"] = p_f_type.is_struct

        # if a default was in the dict then we try to decode it
        # and replace the default value with the decoded version
        if DEFAULT in src_dict:
            src_dict[DEFAULT] = self.decode_value(
                src_dict[DEFAULT], key=DEFAULT, p_name=p_name,
                p_f_type=p_f_type, end=sub_kwargs.get('end'))

        # run the sanitization routine specific to this FieldType
        src_dict = p_f_type.sanitizer(self, src_dict, **sub_kwargs)

        # check for any errors with the layout of the descriptor
        error_str = self.find_errors(src_dict, **kwargs)
        if error_str:
            self._e_str += error_str + '\n'
            self._bad = True

        return src_dict

    def sanitize_name(self, src_dict, key=None, **kwargs):
        '''
        Sanitizes the NAME value in src_dict into a usable identifier
        and replaces the old entry with the sanitized value.
        '''
        src_dict = src_dict.get(key, src_dict)

        # sanitize the attribute name string to make it a valid identifier
        src_dict[NAME] = name = self.str_to_name(src_dict.get(NAME), **kwargs)

        if name:
            return name

        name = src_dict[NAME] = "unnamed"
        p_name = kwargs.get('p_name')
        p_f_type = kwargs.get('p_f_type')
        index = kwargs.get('key_name')
        f_type = src_dict.get(TYPE)

        if f_type is not None:
            self._e_str += (("ERROR: NAME MISSING IN FIELD OF TYPE " +
                             "'%s'\n    IN INDEX '%s' OF '%s' OF TYPE " +
                             "'%s'\n") % (f_type, index, p_name, p_f_type))
        else:
            self._e_str += (("ERROR: NAME MISSING IN FIELD LOCATED " +
                             "IN INDEX '%s' OF '%s' OF TYPE '%s'\n") %
                            (index, p_name, p_f_type))
        self._bad = True

    def set_entry_count(self, src_dict, key=None):
        '''Creates an ENTRIES item in src_dict which specifies
        the number of integer keyed items found in src_dict.
        This is usually used for counting the fields in a descriptor, but
        can be used to count other things, like bool and enum options.'''
        if key not in uncountable_desc_keys and isinstance(src_dict, dict):
            int_count = 0
            for i in src_dict:
                if isinstance(i, int):
                    int_count += 1
            src_dict[ENTRIES] = int_count

    def str_to_name(self, string, **kwargs):
        try:

            if not isinstance(string, str):
                self._e_str += (("ERROR: INVALID TYPE FOR NAME. EXPECTED " +
                                 "%s, GOT %s.\n") % (str, type(string)))
                self._bad = True
                return None

            sanitized_str = str_to_identifier(string)

            if not sanitized_str:
                self._e_str += (("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE " +
                                 "NAME.\nWHEN SANITIZED IT BECAME ''\n\n") %
                                string)
                self._bad = True
                return None
            elif sanitized_str in reserved_desc_names and\
                 not kwargs.get('allow_reserved', False):
                self._e_str += ("ERROR: CANNOT USE THE RESERVED KEYWORD " +
                                "'%s' AS AN ATTRIBUTE NAME.\n\n" % string)
                self._bad = True
                return None
            return sanitized_str
        except Exception:
            return None
