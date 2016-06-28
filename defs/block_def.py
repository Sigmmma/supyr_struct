'''
'''
from math import log, ceil

from supyr_struct.defs.frozen_dict import FrozenDict
from supyr_struct.defs.constants import *
from supyr_struct.defs.common_descriptors import *

# linked to through supyr_struct.__init__
blocks = None
fields = None


class BlockDef():
    '''
    BlockDefs are objects which contain a dict tree of structure
    descriptions(called a descriptor). The BlockDef uses this
    descriptor when its build method is invoked to build Blocks
    from either a buffer of raw data, a file(given as a filepath),
    or from nothing(builds a Block with all attributes defaulted).

    Take a look at supyr_struct.defs.constants for a list of all supported
    descriptor keywords and detailed descriptions of their purposes.

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
         'TYPE': <Field:'UInt32', endian:'>', enc:'>I'>},
     1: {'NAME': 'some_bytes',
         'SIZE': 256,
         'TYPE': <Field:'BytesRaw', endian:'=', enc:'B'>},
     'ENDIAN': '>',
     'ENTRIES': 2,
     'NAME': 'some_blockdef',
     'NAME_MAP': FrozenDict({'some_int': 0, 'some_bytes': 1}),
     'TYPE': <Field:'Container', endian:'=', enc:'None'>}

    Instance properties:
        bool:
            sani_warn
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
    _e_str = ''  #  A string description of any errors encountered
    #               while sanitizing. An exception is raised using
    #               this string after sanitization is completed.
    _initialized = False  # Whether or not the definition has been built.
    sani_warn = True
    align_mode = ALIGN_NONE
    endian = ''
    def_id = None

    # initialize the class
    def __init__(self, def_id, *desc_entries, **kwargs):
        '''
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
                         If a Field is not supplied under the TYPE keyword,
                         the BlockDef will default to using Container.
                         If supplying a descriptor in this way, do not provide
                         one through the "descriptor" keyword as well. Doing
                         so will raise a TypeError

        Keyword arguments:
        # bool:
        sani_warn ------ Whether or not to print warnings(not errors) about
                         possible issues to the console when the sanitization
                         routine is run.
        # dict:
        descriptor ----- A dictionary which stores a detailed and well formed
                         tree of other detailed and well formed dictionaries
                         which each describe some type of data or structure.
                         Most descriptors are only required to have NAME and
                         TYPE entries, but depending on the Field instance in
                         the TYPE, other entries may be required. If supplying
                         a descriptor in this way, do not provide one through
                         positional arguments and desc_keyword named arguments.
                         Doing so will raise a TypeError
        subdefs -------- Used for storing individual or extra pieces of
                         the structure. When a BlockDef is created and its
                         descriptor sanitized, each of the fields within the
                         immediate nesting layer will have a BlockDef created
                         and have its descriptor set to the descriptor entry
                         in the parent BlockDef. This is done so a BlockDef is
                         readily accessible for any descriptor in a BlockDef.
                         A BlockDef will not be made for a field if its
                         'is_block' attribute is False.
        # str:
        align_mode ----- The alignment method to use for aligning containers
                         and their attributes to whole byte boundaries based
                         on each ones byte size. Valid values for this are
                         ALIGN_AUTO and ALIGN_NONE.
        endian --------- The default endianness to use for every field in the
                         descriptor. This can be overridden by specifying the
                         endianness per field. Endian carries over from outer
                         field to inner fields
        '''

        if self._initialized:
            return

        if not hasattr(self, "descriptor"):
            self.descriptor = {}
        if not hasattr(self, "subdefs"):
            self.subdefs = {}

        self.align_mode = kwargs.get("align_mode", self.align_mode)
        self.descriptor = kwargs.get("descriptor", self.descriptor)
        self.endian = str(kwargs.get("endian", self.endian))
        self.sani_warn = bool(kwargs.get("sani_warn", self.sani_warn))
        self.subdefs = dict(kwargs.get("subdefs", self.subdefs))
        self.def_id = def_id
        self._initialized = True

        # make sure the endian value is valid
        assert self.endian in '<>', ("Invalid endianness character provided." +
                                     "Valid characters are '<' for little, " +
                                     "'>' for big, and '' for none.")

        # whether or not a descriptor should be built from the
        # keyword arguments and optional positional arguments.
        build_desc = (desc_entries or
                      not desc_keywords.isdisjoint(kwargs.keys()))

        if self.descriptor and build_desc:
            raise TypeError(("A descriptor already exists or was " +
                             "provided for the '%s' BlockDef, but " +
                             "individual BlockDef arguments were also " +
                             "supplied.\nCannot accept positional arguments " +
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
        '''builds and returns a block'''

        desc = self.descriptor
        field = desc[TYPE]

        rawdata = blocks.Block.get_rawdata(None, **kwargs)
        new_block = desc.get(DEFAULT, field.py_type)(desc, init_attrs=True)

        kwargs.setdefault("offset", 0)
        kwargs.setdefault("root_offset", 0)
        kwargs.setdefault("int_test", False)

        kwargs["rawdata"] = rawdata

        if kwargs.get("allow_corrupt"):
            try:
                field.reader(desc, new_block, **kwargs)
            except Exception:
                pass
        else:
            field.reader(desc, new_block, **kwargs)
        return new_block

    def decode_value(self, value, key, p_name, p_field, **kwargs):
        ''''''
        if self.endian == '':
            endian = p_field.endian
        else:
            endian = kwargs.get('end', self.endian)

        endian = {'>': 'big', '<': 'little'}.get(p_field.endian, 'little')

        if isinstance(value, bytes):
            try:
                if p_field is not None:
                    d_value = p_field.decoder_func(p_field, value)
                elif endian == '<':
                    d_value = int.from_bytes(value, 'little')
                else:
                    d_value = int.from_bytes(value, 'big')
            except Exception:
                self._e_str += (("ERROR: UNABLE TO DECODE THE BYTES " +
                                 "%s IN '%s' OF '%s' AS '%s'.\n\n") %
                                (value, key, p_name, p_field))
                self._bad = True
                return
        elif (isinstance(value, str) and (issubclass(p_field.data_type, int) or
              (issubclass(p_field.py_type, int) and
               issubclass(p_field.data_type, type(None))))):
            # if the value is a string and the field's data_type is an
            # int, or its py_type is an int and its data_type is type(None),
            # then convert the string into bytes and then into an integer.
            if endian == 'little':
                value = ''.join(reversed(value))

            d_value = int.from_bytes(bytes(value, encoding='latin1'),
                                     byteorder=endian)
        else:
            d_value = value

        return d_value

    def find_errors(self, src_dict, **kwargs):
        '''Returns a string textually describing any errors that were found.'''
        # Get the name of this block so it can be used in the below routines
        p_name = src_dict.get(NAME, UNNAMED)
        p_field = src_dict.get(TYPE, Void)
        substruct = kwargs.get('substruct')
        cont_field = kwargs.get('p_field')

        e = "ERROR: %s.\n"
        error_str = ''
        if src_dict.get(ENDIAN, '') not in '<>':
            error_str += e % (("ENDIANNESS CHARACTERS MUST BE EITHER '<' " +
                               "FOR LITTLE ENDIAN, '>' FOR BIG ENDIAN, OR ''" +
                               " FOR NONE. NOT  %s" % kwargs.get('end')))

        # make sure bit and byte level fields arent mixed improperly
        if isinstance(cont_field, fields.Field):
            if cont_field.is_bit_based and cont_field.is_struct:
                # parent is a bitstruct
                if not p_field.is_bit_based:
                    # but this is NOT bitbased
                    error_str += e % ("bit_structs MAY ONLY CONTAIN " +
                                      "bit_based data Fields.")
                elif p_field.is_struct:
                    error_str += "ERROR: bit_structs CANNOT CONTAIN structs.\n"
            elif p_field.is_bit_based and not p_field.is_struct:
                error_str += e % ("bit_based Fields MUST RESIDE " +
                                  "IN A bit_based struct.")

        # if the field is inside a struct, make sure its allowed to be
        if substruct:
            # make sure open ended sized data isnt in a struct
            if p_field.is_oe_size:
                error_str += e % "oe_size Fields CANNOT BE USED IN A struct."
            # make sure containers aren't inside structs
            if p_field.is_container:
                error_str += e % ("containers CANNOT BE USED IN A struct. " +
                                  "structs ARE REQUIRED TO BE A FIXED SIZE " +
                                  "WHEREAS containers ARE NOT.")

        if p_field.is_var_size and p_field.is_data:
            if substruct and not isinstance(src_dict.get(SIZE), int):
                error_str += e % ("var_size data WITHIN A STRUCT MUST HAVE " +
                                  "ITS SIZE STATICALLY DEFINED BY AN INTEGER")
            elif SIZE not in src_dict and not p_field.is_oe_size:
                error_str += e % ("var_size data MUST HAVE ITS SIZE " +
                                  "GIVEN BY EITHER A FUNCTION, PATH " +
                                  "STRING, OR INTEGER.")

        if p_field.is_array:
            # make sure arrays have a size if they arent open ended
            if not(p_field.is_oe_size or SIZE in src_dict):
                error_str += e % ("NON-OPEN ENDED arrays MUST HAVE " +
                                  "A SIZE DEFINED IN THEIR DESCRIPTOR.")
            # make sure arrays have a SUB_STRUCT entry
            if SUB_STRUCT not in src_dict:
                error_str += e % (
                    "arrays MUST HAVE A SUB_STRUCT ENTRY IN THEIR DESCRIPTOR.")
        if error_str:
            error_str += ("    NAME OF THE OFFENDING ELEMENT IS " +
                          "'%s' OF TYPE '%s'\n" % (p_name, p_field.name))

        return error_str

    def get_align(self, src_dict, key):
        ''''''
        this_d = src_dict[key]
        if not isinstance(this_d, dict):
            self._e_str += ("ERROR: EXPECTED %s IN %s OF %s, GOT %s\n" %
                            (dict, key, src_dict.get(NAME), type(this_d)))
            self._bad = True
            return 0
        field = this_d.get(TYPE, Void)
        align = size = 1

        if field.is_raw:
            size = 1
        elif field.is_data or (field.is_bit_based and field.is_struct):
            # if the entry is data(or a bitstruct) then align
            # it by its size, or by char size if its a string
            if field.is_str:
                size = field.size
            else:
                size = self.get_size(src_dict, key)
        elif field.is_array:
            if SUB_STRUCT in src_dict[key]:
                # get and use the alignment of the substruct descriptor
                align = self.get_align(src_dict[key], SUB_STRUCT)
        elif field.is_struct:
            # search through all entries in the struct
            # to find the largest alignment and use it
            align = 1
            for i in range(this_d.get(ENTRIES, 1)):
                algn = self.get_align(this_d, i)
                if algn > align:
                    align = algn
                # early return for speedup
                if align >= ALIGN_MAX:
                    return ALIGN_MAX

        if ALIGN in this_d:
            # alignment is specified manually
            align = this_d[ALIGN]
        elif self.align_mode == ALIGN_AUTO and size > 0:
            # automatic alignment is to be used
            align = 2**int(ceil(log(size, 2)))
            if align > ALIGN_MAX:
                align = ALIGN_MAX

        return align

    def get_endian(self, src_dict, **kwargs):
        '''Returns the proper endianness of the field type'''
        p_field = src_dict.get(TYPE, Void)

        if ENDIAN in src_dict:
            end = src_dict[ENDIAN]
        elif kwargs.get('end') in ('<', '>'):
            end = kwargs['end']
        elif self.endian != '':
            end = self.endian
        else:
            end = None

        return end

    def get_size(self, src_dict, key=None):
        ''''''
        if key is None:
            this_d = src_dict
        else:
            this_d = src_dict[key]
        field = this_d.get(TYPE, Void)

        # make sure we have names for error reporting
        p_name = src_dict.get(NAME, UNNAMED)
        name = this_d.get(NAME, UNNAMED)

        if (field.is_var_size and field.is_data) or\
           (SIZE in this_d and isinstance(this_d[SIZE], int)):
            if SIZE not in this_d:
                self._e_str += ("ERROR: var_size data MUST HAVE ITS SIZE " +
                                "GIVEN BY EITHER A FUNCTION, PATH STRING, " +
                                "OR INTEGER.\n    OFFENDING ELEMENT IS " +
                                "'%s' IN '%s'\n" % (name, p_name))
                self._bad = True
                return 0

            size = this_d[SIZE]
        elif field.is_struct:
            # find the size of the struct as a sum of the sizes of its entries
            size = 0
            for i in range(this_d.get(ENTRIES, 0)):
                size += self.get_size(this_d, i)
        else:
            size = field.size

        if field.is_bit_based and not field.is_struct and not\
           src_dict.get(TYPE, Void).is_bit_based:
            size = int(ceil(size/8))

        return size

    def include_attributes(self, src_dict):
        ''''''
        include = src_dict.get(INCLUDE)
        if isinstance(include, dict):
            del src_dict[INCLUDE]

            for i in include:
                # dont replace it if an attribute already exists there
                if i not in src_dict:
                    src_dict[i] = include[i]

                if i == INCLUDE:
                    # if the include has another include in it, rerun this
                    src_dict = self.include_attributes(src_dict)
        return src_dict

    def make_desc(self, *desc_entries, **desc):
        '''
        Converts the supplied positional arguments and keyword arguments
        into a dictionary properly formatted to be used as a descriptor.
        Returns the formatted dictionary.
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

        sub_kwargs = {'align_mode': self.align_mode, 'endian': self.endian,
                      'sani_warn': self.sani_warn}

        # make sure all the subdefs are BlockDefs
        for i in self.subdefs:
            d = self.subdefs[i]
            if not isinstance(d, BlockDef):
                self.subdefs[i] = BlockDef(str(i), descriptor=d, **sub_kwargs)

        # try and make all the entries in this block into their own BlockDefs
        for i in desc:
            # if the key already exists then dont worry about making one
            if i in self.subdefs and not replace_subdefs:
                continue
            d = desc[i]
            if isinstance(d, dict) and TYPE in d and d[TYPE].is_block:
                name = d[NAME]
                try:
                    self.subdefs[name] = BlockDef(name, descriptor=d,
                                                  sanitize=False, **sub_kwargs)
                except Exception:
                    pass

    def sanitize(self, desc=None):
        '''
        Use this to sanitize a descriptor.
        Adds key things to the Tag_Def that may be forgotten,
        mistyped, or simply left out and informs the user of
        potential and definite issues through print().
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
        ''''''
        # if the src_dict is a FrozenDict, make it
        # mutable and assume it's already sanitized
        if isinstance(src_dict, FrozenDict):
            return dict(src_dict)

        # combine the entries from INCLUDE into the dictionary
        src_dict = self.include_attributes(src_dict)

        # if the type doesnt exist nothing needs to be done, so quit early
        if TYPE not in src_dict:
            return src_dict

        p_field = src_dict[TYPE]
        if p_field not in fields.all_fields:
            self._bad = True
            raise TypeError("'TYPE' in a descriptor must be a valid Field.\n" +
                            "Got %s of type %s" % (p_field, type(p_field)))

        # Change the Field to the endianness specified.
        endian = self.get_endian(src_dict, **kwargs)
        if endian is not None:
            p_field = {'>': p_field.big, '<': p_field.little}[endian]
        src_dict[TYPE] = p_field
        p_name = src_dict.get(NAME, UNNAMED)
        kwargs['end'] = endian

        # check for any errors with the layout of the descriptor
        error_str = self.find_errors(src_dict, **kwargs)

        kwargs['p_field'] = p_field
        kwargs['p_name'] = p_name

        # if any errors occurred, print them
        if error_str:
            self._e_str += error_str + '\n'
            self._bad = True

        # let all the sub-descriptors know they are inside a struct
        if p_field.is_struct:
            kwargs["substruct"] = True

        # if a default was in the dict then we try to decode it
        # and replace the default value with the decoded version
        if DEFAULT in src_dict and src_dict[TYPE].is_data:
            src_dict[DEFAULT] = self.decode_value(src_dict[DEFAULT], DEFAULT,
                                                  p_name, p_field,
                                                  end=kwargs.get('end'))

        # run the sanitization routine specific to this field
        return p_field.sanitizer(self, src_dict, **kwargs)

    def sanitize_element_ordering(self, src_dict, **kwargs):
        '''Sets the number of entries in a descriptor block'''

        if ENTRIES in src_dict:
            # because the element count will have already
            # been added, we can use that as our loop count
            last_entry = src_dict[ENTRIES]
            i = gap_size = 0
            offenders = []

            while i < last_entry:
                if i not in src_dict:
                    # if we cant find 'i' in the dict it means we need to
                    # shift the elements down by at least 1. as such, we
                    # need to look at least 1 higher for the next element
                    gap_size += 1
                    last_entry += 1
                else:
                    # if we DID find the element in the dictionary we need
                    # to check if there are any gaps and, if so, shift down
                    if gap_size > 0:
                        src_dict[i-gap_size] = src_dict[i]
                        offenders.append(src_dict.pop(i))
                i += 1

            if gap_size > 0 and self.sani_warn:
                self._e_str += ("WARNING: Descriptor element ordering " +
                                "needed to be sanitized.\n   Check " +
                                "ordering of '%s'\n" % self.def_id)

                if NAME in src_dict:
                    self._e_str += ("\n   NAME of offending block is " +
                                    "'%s'\n\n" % str(src_dict[NAME]))
                else:
                    self._e_str += ("\n   Offending block is not named.\n\n")
                self._e_str += '\n   Offending attributes in the block are:\n'
                for e in offenders:
                    self._e_str += ('      ' + e.get(NAME, UNNAMED) + '\n')
                self._e_str += '\n'

    def sanitize_name(self, src_dict, key=None, sanitize=True, **kwargs):
        '''
        Sanitizes the NAME value in src_dict into a usable identifier
        and replaces the old entry with the sanitized value.
        '''
        if key is not None:
            src_dict = src_dict[key]

        name = None

        if NAME in src_dict:
            name = src_dict[NAME]

        # sanitize the attribute name string to make it a valid identifier
        if sanitize:
            name = self.str_to_name(name)

        if name is None:
            name = "unnamed"
            p_name = kwargs.get('p_name')
            p_field = kwargs.get('p_field')
            index = kwargs.get('key_name')
            field = src_dict.get(TYPE)

            if field is not None:
                self._e_str += (("ERROR: NAME MISSING IN FIELD OF TYPE " +
                                 "'%s'\n    IN INDEX '%s' OF '%s' OF TYPE " +
                                 "'%s'\n") % (field, index, p_name, p_field))
            else:
                self._e_str += (("ERROR: NAME MISSING IN FIELD LOCATED " +
                                 "IN INDEX '%s' OF '%s' OF TYPE '%s'\n") %
                                (index, p_name, p_field))
            self._bad = True

        src_dict[NAME] = name
        return name

    def sanitize_entry_count(self, src_dict, key=None):
        '''Sets the number of entries in a descriptor'''
        if isinstance(src_dict, dict) and key not in (NAME_MAP, INCLUDE):
            entry_count = 0
            largest = 0
            for i in src_dict:
                if isinstance(i, int):
                    entry_count += 1
                    if i > largest:
                        largest = i

            # we dont want to add an entry count to the NAME_MAP
            # dict or the INCLUDE dict since they aren't parsed
            src_dict[ENTRIES] = entry_count

    def sanitize_option_values(self, src_dict, field, **kwargs):
        ''''''
        is_bool = field.is_bool
        p_name = kwargs.get('p_name', UNNAMED)
        p_field = kwargs.get('p_field', None)
        pad_size = removed = 0

        for i in range(src_dict.get(ENTRIES, 0)):
            opt = src_dict[i]

            if isinstance(opt, dict):
                if opt.get(TYPE) is Pad:
                    # subtract 1 from the pad size because the pad itself is 1
                    pad_size += opt.get(SIZE, 1)-1
                    removed += 1
                    del src_dict[i]
                    continue

                # make a copy to make sure the original is intact
                opt = dict(opt)
            elif isinstance(opt, (list, tuple, str)):
                if isinstance(opt, str):
                    opt = {NAME: opt}
                elif len(opt) == 1:
                    opt = {NAME: opt[0]}
                elif len(opt) == 2:
                    opt = {NAME: opt[0], VALUE: opt[1]}
                else:
                    self._e_str += (("ERROR: EXCEPTED 1 or 2 ARGUMENTS FOR " +
                                     "OPTION NUMBER %s\nIN FIELD %s OF NAME " +
                                     "'%s', GOT %s ARGUMENTS.\n") %
                                    (i, p_field, p_name, len(opt)))
                    self._bad = True
                    continue
            else:
                continue

            if removed:
                del src_dict[i]

            if VALUE not in opt:
                if is_bool:
                    opt[VALUE] = 2**(i + pad_size)
                else:
                    opt[VALUE] = i + pad_size
            if p_field:
                opt[VALUE] = self.decode_value(opt[VALUE], i, p_name,
                                               p_field, end=kwargs.get('end'))
            src_dict[i-removed] = opt

        src_dict[ENTRIES] -= removed

    def str_to_name(self, string, **kwargs):
        '''
        Converts any string given to it into a usable identifier.
        Converts all spaces and dashes into underscores, and removes all
        invalid characters. If the last character is invalid, it will be
        dropped instead of being replaced with an underscore
        '''

        """Docstring snippit about commented out code"""
        # and makes sure the string begins with A-Z, a-z, or an underscore.
        # If the string begins with a number, an underscore will be prepended.
        try:
            sanitized_str = ''
            i = 0
            skipped = False

            if not isinstance(string, str):
                self._e_str += (("ERROR: INVALID TYPE FOR NAME. EXPECTED " +
                                 "%s, GOT %s.\n") % (str, type(string)))
                self._bad = True
                return None

            # make sure the sanitized_strs first character is a valid character
            while len(sanitized_str) == 0 and i < len(string):
                # ignore characters until an alphabetic one is found
                if string[i] in alpha_ids:
                    sanitized_str = string[i]

                i += 1

            # replace all invalid characters with underscores
            for i in range(i, len(string)):
                if string[i] in alpha_numeric_ids:
                    sanitized_str += string[i]
                    skipped = False
                elif not skipped:
                    # no matter how many invalid characters occur in
                    # a row, replace them all with a single underscore
                    sanitized_str += '_'
                    skipped = True

            # make sure the string doesnt end with an underscore
            sanitized_str.rstrip('_')

            if sanitized_str == '':
                self._e_str += (("ERROR: CANNOT USE '%s' AS AN ATTRIBUTE " +
                                 "NAME.\nWHEN SANITIZED IT BECAME ''\n\n") %
                                string)
                self._bad = True
                return None
            elif sanitized_str in desc_keywords:
                self._e_str += ("ERROR: CANNOT USE THE DESCRIPTOR KEYWORD " +
                                "'%s' AS AN ATTRIBUTE NAME.\n\n" % string)
                self._bad = True
                return None
            return sanitized_str
        except Exception:
            return None
