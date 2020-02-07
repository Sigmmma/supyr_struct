'''
Sanitizers for all standard FieldTypes.

Sanitizers are responsible for ensuring a descriptor is properly formed.
This means raising errors for missing required keys and invalid values,
adding boilerplate keys/values, and immutifying the result.

Like parsers/decoders/etc, sanitizers are attached to a FieldType.
Unlike them though, sanitizers aren't used as methods of the FieldType,
but rather as methods of the BlockDef doing the processing. Their first
argument is expected to be the BlockDef instance they are operating on.
'''
__all__ = [
    'bool_sanitizer', 'enum_sanitizer', 'switch_sanitizer',
    'sequence_sanitizer', 'standard_sanitizer',
    'struct_sanitizer', 'quickstruct_sanitizer',
    'union_sanitizer', 'stream_adapter_sanitizer',
    ]

from math import ceil, log

import supyr_struct

from supyr_struct.defs.constants import (
    NAME, UNNAMED, DEFAULT, NODE_CLS, STEPTREE, TYPE, VALUE_MAP,
    VALUE, ENTRIES, SIZE, ATTR_OFFS, OFFSET, NAME_MAP, ALIGN_MAX, ALIGN,
    POINTER, SUB_STRUCT, CASES, CASE, ADDED, CASE_MAP, ENCODER, DECODER,
    reserved_bool_enum_names, desc_keywords
    )

QSTRUCT_ALLOWED_ENC = set('bB')
for c in 'HhIiQqfd':
    QSTRUCT_ALLOWED_ENC.add('<' + c)
    QSTRUCT_ALLOWED_ENC.add('>' + c)


def adapter_no_encode(parent, buffer, **kwargs):
    '''
    Returns the supplied 'buffer' argument.
    This function is used as the ENCODER entry in the descriptor
    for StreamAdapter FieldTypes when an ENCODER is not present.
    '''
    return buffer


def bool_sanitizer(blockdef, src_dict, **kwargs):
    kwargs['is_bool'] = True
    return bool_enum_sanitize_main(blockdef, src_dict, **kwargs)


def enum_sanitizer(blockdef, src_dict, **kwargs):
    kwargs['is_bool'] = False
    return bool_enum_sanitize_main(blockdef, src_dict, **kwargs)


def bool_enum_sanitize_main(blockdef, src_dict, **kwargs):
    
    p_f_type = src_dict[TYPE]
    is_bool = kwargs.pop('is_bool', False)

    nameset = set()
    src_dict[NAME_MAP] = dict(src_dict.get(NAME_MAP, ()))
    src_dict[VALUE_MAP] = {}

    # Need to make sure there is a value for each element
    blockdef.set_entry_count(src_dict)
    blockdef.find_entry_gaps(src_dict)
    sanitize_option_values(blockdef, src_dict, p_f_type,
                           is_bool=is_bool, **kwargs)

    if not isinstance(src_dict.get(SIZE, 0), int):
        blockdef._e_str += (
            ("ERROR: INVALID TYPE FOR SIZE IN '%s'.\n    EXPECTED %s, GOT %s" +
             ".\n") % (src_dict.get(NAME, UNNAMED), int, type(src_dict[SIZE])))
        blockdef._bad = True

    for i in range(src_dict[ENTRIES]):
        name = blockdef.sanitize_name(
            src_dict, i, allow_reserved=not is_bool,
            p_f_type=p_f_type, p_name=src_dict.get(NAME),
            reserved_names=reserved_bool_enum_names, key_name=i)

        if name in nameset:
            blockdef._e_str += (
                ("ERROR: DUPLICATE NAME FOUND IN '%s'.\nNAME OF OFFENDING " +
                 "ELEMENT IS '%s'\n") % (src_dict.get(NAME, UNNAMED), name))
            blockdef._bad = True
            continue
        src_dict[NAME_MAP][name] = i
        src_dict[VALUE_MAP][src_dict[i][VALUE]] = i
        nameset.add(name)
    return src_dict


def sanitize_option_values(blockdef, src_dict, f_type, **kwargs):
    
    is_bool = kwargs.get('is_bool')
    p_name = kwargs.get('p_name', UNNAMED)
    p_f_type = kwargs.get('p_f_type', None)
    pad_size = removed = 0
    def_val = 0

    for i in range(src_dict.get(ENTRIES, 0)):
        opt = src_dict[i]

        if isinstance(opt, dict):
            if opt.get(TYPE) is supyr_struct.field_types.Pad:
                # subtract 1 from the pad size because the pad itself is 1
                pad_size += opt.get(SIZE, 1) - 1
                removed += 1
                del src_dict[i]
                def_val += 1
                continue

            # make a copy to make sure the original is intact
            opt = dict(opt)
        elif isinstance(opt, str):
            opt = {NAME: opt}
        elif isinstance(opt, (list, tuple)):
            if len(opt) == 1:
                opt = {NAME: opt[0]}
            elif len(opt) == 2:
                opt = {NAME: opt[0], VALUE: opt[1]}
            else:
                blockdef._e_str += (
                    "ERROR: EXPECTED TUPLE OR LIST OF LENGTH 1 or 2 " +
                    "FOR\nOPTION NUMBER %s IN FIELD %s OF NAME '%s', " +
                    "GOT LENGTH OF %s.\n") % (i, p_f_type, p_name, len(opt))
                blockdef._bad = True
                continue
        else:
            continue

        # remove any keys that aren't descriptor keywords
        for key in tuple(opt.keys()):
            if not(isinstance(key, int) or key in desc_keywords):
                opt.pop(key)

        if removed:
            del src_dict[i]

        if VALUE in opt:
            if isinstance(opt[VALUE], int):
                if is_bool:
                    if opt[VALUE] <= 0:
                        blockdef._e_str += (
                            "ERROR: VALUE OF BOOLEAN WAS <= 0 FOR OPTION NUMBER" +
                            "%s IN FIELD %s OF NAME '%s'") % (i, p_f_type, p_name)
                        blockdef._bad = True
                        continue
                    def_val = int(log(opt[VALUE], 2))
                else:
                    def_val = opt[VALUE]
                pad_size = 0
        elif is_bool:
            opt[VALUE] = 2**(def_val + pad_size)
        else:
            opt[VALUE] = def_val + pad_size

        if p_f_type:
            opt[VALUE] = blockdef.decode_value(
                opt[VALUE], key=i, p_name=p_name, p_f_type=p_f_type,
                end=kwargs.get('end'))
        src_dict[i-removed] = opt
        def_val += 1

    src_dict[ENTRIES] -= removed


def struct_sanitizer(blockdef, src_dict, **kwargs):
    """
    """
    # whether or not to calculate a size based on the element sizes
    calc_size = SIZE not in src_dict

    # make sure there is a size(it'll trip error catching routines otherwise)
    if calc_size:
        src_dict[SIZE] = 0

    # do the standard sanitization routine on the non-numbered entries
    src_dict = standard_sanitizer(blockdef, src_dict, **kwargs)

    # if a field doesnt have a specified offset then
    # this will be used as the starting offset and will
    # be incremented by the size of each field after it
    def_offset = 0
    # the largest alignment size requirement of any entry in this block
    l_align = 1

    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # ATTR_OFFS stores the offsets of each attribute by index.
    attr_offs = [0]*src_dict.get(ENTRIES, 0)
    nameset = set()  # contains the name of each entriy in the desc
    rem = 0  # number of dict entries removed
    key = 0
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in (i for i in range(src_dict[ENTRIES])
                if isinstance(src_dict.get(i), dict)):
        # Make sure to shift upper indexes down by how many
        # were removed and make a copy to preserve the original
        this_d = src_dict[key-rem] = dict(src_dict[key])
        key -= rem

        f_type = this_d.get(TYPE)

        if f_type is supyr_struct.field_types.Pad:
            # the dict was found to be padding, so increment
            # the default offset by it, remove the entry from the
            # dict, and adjust the removed and entry counts.
            size = this_d.get(SIZE)

            if size is not None:
                def_offset += size
            else:
                blockdef._bad = True
                blockdef._e_str += (
                    ("ERROR: Pad ENTRY IN '%s' OF TYPE %s AT INDEX %s " +
                     "IS MISSING A SIZE KEY.\n") % (p_name, p_f_type, key))
            if ATTR_OFFS in src_dict:
                blockdef._e_str += (
                    ("ERROR: ATTR_OFFS ALREADY EXISTS IN '%s' OF TYPE " +
                     "%s, BUT A Pad ENTRY WAS FOUND AT INDEX %s.\n" +
                     "    CANNOT INCLUDE Pad FIELDS WHEN ATTR_OFFS " +
                     "ALREADY EXISTS.\n") % (p_name, p_f_type, key + rem))
                blockdef._bad = True
            rem += 1
            src_dict[ENTRIES] -= 1
            continue
        elif f_type is not None:
            # make sure the node has an offset if it needs one
            if OFFSET not in this_d:
                this_d[OFFSET] = def_offset
        elif p_f_type:
            blockdef._bad = True
            blockdef._e_str += (
                "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                "TYPE '%s' AT INDEX %s.\n" % (p_name, p_f_type, key))

        kwargs["key_name"] = key
        this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

        if f_type:
            sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
            if NAME_MAP in src_dict:
                src_dict[NAME_MAP][sani_name] = key

                name = this_d[NAME]
                if name in nameset:
                    blockdef._e_str += (
                        ("ERROR: DUPLICATE NAME FOUND IN '%s' AT INDEX " +
                         "%s.\n    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                        (p_name, key, name))
                    blockdef._bad = True
                nameset.add(name)

            # get the size of the entry(if the parent dict requires)
            if OFFSET in this_d:
                # add the offset to ATTR_OFFS in the parent dict
                offset = this_d[OFFSET]
                size = blockdef.get_size(src_dict, key)

                # make sure not to align within bit structs
                if not p_f_type.is_bit_based:
                    align = blockdef.get_align(src_dict, key)

                    if align > ALIGN_MAX:
                        align = l_align = ALIGN_MAX
                    elif align > l_align:
                        l_align = align

                    if align > 1:
                        offset += (align - (offset % align)) % align

                if isinstance(size, int):
                    def_offset = offset + size
                else:
                    blockdef._e_str += (
                        ("ERROR: INVALID TYPE FOR SIZE FOUND IN '%s' AT " +
                         "INDEX %s.\n    EXPECTED %s, GOT %s. \n    NAME " +
                         "OF OFFENDING ELEMENT IS '%s' OF TYPE %s.\n") %
                        (p_name, key + rem, int, type(size), name, f_type))
                    blockdef._bad = True

                # set the offset and delete the OFFSET entry
                attr_offs[key] = offset
                del this_d[OFFSET]

    # if there were any removed entries (padding) then the
    # ones above where the last key was need to be deleted
    entry_count = src_dict[ENTRIES]
    for i in range(entry_count, entry_count + rem):
        del src_dict[i]

    # prune potentially extra entries from the attr_offs list
    attr_offs = attr_offs[:entry_count]

    # if the f_type is a struct and the ATTR_OFFS isnt already in it
    if ATTR_OFFS not in src_dict:
        src_dict[ATTR_OFFS] = attr_offs

    # Make sure all structs have a defined SIZE
    if p_f_type and calc_size:
        if p_f_type.is_bit_based:
            def_offset = int(ceil(def_offset / 8))

        # calculate the padding based on the largest alignment
        padding = (l_align - (def_offset % l_align)) % l_align
        src_dict[SIZE] = def_offset + padding

    return src_dict


def quickstruct_sanitizer(blockdef, src_dict, **kwargs):
    """
    """
    # do the struct sanitization routine on the src_dict
    src_dict = struct_sanitizer(blockdef, src_dict, **kwargs)
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # make sure nothing exists in the QuickStruct that cant be in it.
    for key, this_d in ((i, src_dict[i]) for i in range(src_dict[ENTRIES])):
        if isinstance(this_d, dict) and this_d.get(TYPE):
            f_type = this_d[TYPE]
            name = this_d.get(NAME, UNNAMED)

            if f_type.is_block:
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CANNOT CONTAIN BLOCKS.\n    " +
                    "OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n    " +
                    "OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (f_type, name, p_name, p_f_type, key)
            elif (f_type.enc not in QSTRUCT_ALLOWED_ENC or
                  f_type.node_cls not in (float, int)):
                blockdef._bad = True
                blockdef._e_str += (
                    "ERROR: QuickStructs CAN ONLY CONTAIN INTEGER AND/OR " +
                    "FLOAT DATA WHOSE ENCODING IS ONE OF THE FOLLOWING:\n" +
                    ("    %s\n" % sorted(QSTRUCT_ALLOWED_ENC)) +
                    "    OFFENDING FIELD OF TYPE %s IS NAMED '%s'.\n" +
                    "    OFFENDING FIELD IS LOCATED IN '%s' OF TYPE %s " +
                    "AT INDEX %s.\n") % (f_type, name, p_name, p_f_type, key)

    return src_dict


def sequence_sanitizer(blockdef, src_dict, **kwargs):
    """
    Loops through each of the numbered entries in the descriptor.
    This is done separate from the non-integer dict entries because
    a check to sanitize offsets needs to be done from 0 up to ENTRIES.
    Looping over a dictionary by its keys will do them in a non-ordered
    way and the offset sanitization requires them to be done in order.
    """

    # do the standard sanitization routine on the non-numbered entries
    src_dict = standard_sanitizer(blockdef, src_dict, **kwargs)

    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    nameset = set()  # contains the name of each entry in the desc
    pad_count = 0

    # loops through the entire descriptor and
    # finalizes each of the integer keyed attributes
    for key in (i for i in range(src_dict[ENTRIES])
                if isinstance(src_dict[i], dict)):
        this_d = src_dict[key] = dict(src_dict[key])
        f_type = this_d.get(TYPE)

        if f_type is supyr_struct.field_types.Pad:
            size = this_d.get(SIZE)

            if size is None:
                blockdef._bad = True
                blockdef._e_str += (
                    ("ERROR: Pad ENTRY IN '%s' OF TYPE %s AT INDEX %s " +
                     "IS MISSING A SIZE KEY.\n") % (p_name, p_f_type, key))
            # make sure the padding follows convention and has a name
            this_d.setdefault(NAME, 'pad_entry_%s' % pad_count)
            if NAME_MAP in src_dict:
                src_dict[NAME_MAP][this_d[NAME]] = key
            pad_count += 1
            continue
        elif f_type is None and p_f_type:
            blockdef._bad = True
            blockdef._e_str += (
                "ERROR: DESCRIPTOR FOUND MISSING ITS TYPE IN '%s' OF " +
                "TYPE '%s' AT INDEX %s.\n" % (p_name, p_f_type, key))

        kwargs["key_name"] = key
        this_d = src_dict[key] = blockdef.sanitize_loop(this_d, **kwargs)

        if f_type:
            sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
            if NAME_MAP in src_dict:
                src_dict[NAME_MAP][sani_name] = key

                name = this_d[NAME]
                if name in nameset:
                    blockdef._e_str += (
                        ("ERROR: DUPLICATE NAME FOUND IN '%s' AT INDEX " +
                         "%s.\n    NAME OF OFFENDING ELEMENT IS '%s'\n") %
                        (p_name, key, name))
                    blockdef._bad = True
                nameset.add(name)

    return src_dict


def standard_sanitizer(blockdef, src_dict, **kwargs):
    
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    # create a NAME_MAP, which maps the name of
    # each attribute to the key it's stored under
    if p_f_type.is_block:
        name_map = src_dict.get(NAME_MAP)

        # if the NAME_MAP is a list of names, turn it into a mapping
        if isinstance(name_map, (list, tuple)):
            name_list = name_map
            name_map = {}
            for i in range(len(name_list)):
                name_map[name_list[i]] = i

        if isinstance(name_map, dict):
            src_dict[NAME_MAP] = dict(name_map)
        else:
            src_dict[NAME_MAP] = {}
        blockdef.set_entry_count(src_dict, kwargs["key_name"])
        blockdef.find_entry_gaps(src_dict)

    # The non integer entries aren't substructs, so set it to False.
    kwargs['substruct'] = False

    # if the node cant hold a STEPTREE, but the descriptor
    # requires that it have a STEPTREE attribute, try to
    # set the NODE_CLS to one that can hold a STEPTREE.
    # Only do this though, if there isnt already a default set.
    if (not hasattr(p_f_type.node_cls, STEPTREE) and
        STEPTREE in src_dict and NODE_CLS not in src_dict):
        try:
            src_dict[NODE_CLS] = p_f_type.node_cls.PARENTABLE
        except AttributeError:
            blockdef._bad = True
            blockdef._e_str += (
                ("ERROR: FOUND DESCRIPTOR WHICH SPECIFIES A STEPTREE, BUT " +
                 "THE CORROSPONDING Block\nHAS NO SLOT FOR A STEPTREE " +
                 "AND DOES NOT SPECIFY A BLOCK THAT HAS A SLOT.\n    " +
                 "OFFENDING ELEMENT IS %s OF TYPE %s\n") % (p_name, p_f_type))

    # loops through the descriptors non-integer keyed sub-sections
    for key in (i for i in tuple(src_dict.keys()) if not isinstance(i, int)):
        if key not in desc_keywords:
            #blockdef._e_str += (
            #    ("ERROR: FOUND ENTRY IN DESCRIPTOR OF '%s' UNDER " +
            #     "UNKNOWN STRING KEY '%s'.\n") % (p_name, key))
            #blockdef._bad = True
            src_dict.pop(key)
            continue
        if isinstance(src_dict[key], dict) and key != ADDED:
            kwargs["key_name"] = key
            f_type = src_dict[key].get(TYPE)
            this_d = dict(src_dict[key])

            # replace with the modified copy so the original is intact
            src_dict[key] = this_d = blockdef.sanitize_loop(this_d,
                                                            **kwargs)

            if f_type:
                # if this is the repeated substruct of an array
                # then we need to calculate and set its alignment
                if ((key == SUB_STRUCT or f_type.is_str) and
                    ALIGN not in this_d):
                    align = blockdef.get_align(src_dict, key)
                    # if the alignment is 1 then adjustments arent needed
                    if align > 1:
                        this_d[ALIGN]

                sani_name = blockdef.sanitize_name(src_dict, key, **kwargs)
                if key != SUB_STRUCT:
                    src_dict[NAME_MAP][sani_name] = key
    return src_dict


def switch_sanitizer(blockdef, src_dict, **kwargs):
    
    # The descriptor is a switch, so individual cases need to
    # be checked and setup as well as the pointer and defaults.
    p_f_type = src_dict[TYPE]
    size = src_dict.get(SIZE)
    p_name = src_dict.get(NAME, UNNAMED)
    pointer = src_dict.get(POINTER)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if src_dict.get(CASE) is None:
        blockdef._e_str += (
            "ERROR: CASE MISSING IN '%s' OF TYPE %s\n" % (p_name, p_f_type))
        blockdef._bad = True
    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += (
            "ERROR: CASES MISSING IN '%s' OF TYPE %s\n" % (p_name, p_f_type))
        blockdef._bad = True

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

    for case in cases:
        case_map[case] = c_index
        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])
        c_f_type = case_desc.get(TYPE, supyr_struct.field_types.Void)
        if not c_f_type.is_block:
            blockdef._e_str += (
                ("ERROR: Switch CASE DESCRIPTORS MUST HAVE THEIR " +
                 "'TYPE' ENTRIES is_block ATTRIBUTE BE True.\n" +
                 "    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "IN '%s'.\n") % (case, c_f_type, p_name))
            blockdef._bad = True

        kwargs['key_name'] = case
        # copy the pointer and size from the switch into each case
        if pointer is not None:
            case_desc.setdefault(POINTER, pointer)
        if size is not None:
            case_desc.setdefault(SIZE, size)

        # need to sanitize the names of the descriptor
        blockdef.sanitize_name(case_desc, **kwargs)
        src_dict[c_index] = blockdef.sanitize_loop(case_desc, **kwargs)

        c_index += 1

    if CASES in src_dict:
        del src_dict[CASES]
    src_dict[CASE_MAP] = case_map

    # make sure there is a default case
    src_dict[DEFAULT] = dict(src_dict.get(
        DEFAULT, supyr_struct.defs.common_descs.void_desc
        ))
    kwargs['key_name'] = DEFAULT

    # copy the pointer and size from the switch into the default
    if pointer is not None:
        src_dict[DEFAULT].setdefault(POINTER, pointer)
    if size is not None:
        src_dict[DEFAULT].setdefault(SIZE, size)
    src_dict[DEFAULT] = blockdef.sanitize_loop(src_dict[DEFAULT], **kwargs)

    return src_dict


def _find_union_errors(blockdef, src_dict):
    
    if isinstance(src_dict, dict) and src_dict.get(TYPE) is not None:
        p_f_type = src_dict[TYPE]
        p_name = src_dict.get(NAME, UNNAMED)
        if STEPTREE in src_dict:
            blockdef._e_str += (
                "ERROR: Union fields CANNOT CONTAIN STEPTREE BLOCKS AT " +
                "ANY POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                "IS '%s' OF TYPE %s." % (p_name, p_f_type))
            blockdef._bad = True

        if POINTER in src_dict:
            blockdef._e_str += (
                "ERROR: Union fields CANNOT BE POINTERED AT ANY " +
                "POINT OF THEIR HIERARCHY.\n    OFFENDING ELEMENT " +
                "IS '%s' OF TYPE %s." % (p_name, p_f_type))
            blockdef._bad = True

        # re-run this check on entries in the dict
        for key in src_dict:
            _find_union_errors(blockdef, src_dict[key])


def union_sanitizer(blockdef, src_dict, **kwargs):
    
    # If the descriptor is a switch, the individual cases need to
    # be checked and setup as well as the pointer and defaults.
    p_f_type = src_dict[TYPE]
    size = src_dict.get(SIZE, 0)
    p_name = src_dict.get(NAME, UNNAMED)
    case_map = src_dict.get(CASE_MAP, {})
    cases = src_dict.get(CASES, ())
    c_index = 0

    if cases is None and CASE_MAP not in src_dict:
        blockdef._e_str += ("ERROR: CASES MISSING IN '%s' OF TYPE %s\n" %
                            (p_name, p_f_type))
        blockdef._bad = True
    if not isinstance(size, int):
        blockdef._e_str += (
            ("ERROR: Union 'SIZE' MUST BE AN INT LITERAL OR UNSPECIFIED, " +
             "NOT %s.\n    OFFENDING BLOCK IS '%s' OF TYPE %s\n") %
            (type(size), p_name, p_f_type))
        blockdef._bad = True
    if p_f_type.is_bit_based:
        blockdef._e_str += (
            "ERROR: Unions CANNOT BE INSIDE A bit_based field.\n    " +
            "OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

    # loop over all union cases and sanitize them
    for case in sorted(cases):
        case_map[case] = c_index

        # copy the case's descriptor so it can be modified
        case_desc = dict(cases[case])

        c_f_type = case_desc.get(TYPE, supyr_struct.field_types.Void)
        c_size = blockdef.get_size(case_desc)

        kwargs['key_name'] = case

        # sanitize the name and gui_name of the descriptor
        blockdef.sanitize_name(case_desc, **kwargs)
        c_name = case_desc.get(NAME, UNNAMED)

        if not c_f_type.is_block:
            blockdef._e_str += (
                ("ERROR: Union CASE DESCRIPTORS MUST HAVE THEIR " +
                 "'TYPE' ENTRIES is_block ATTRIBUTE BE True.\n" +
                 "    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_f_type, case, p_name))
            blockdef._bad = True
        if not c_f_type.is_struct and c_f_type.is_bit_based:
            blockdef._e_str += (
                ("ERROR: Structs ARE THE ONLY bit_based fields ALLOWED IN A " +
                 "Union.\n    OFFENDING ELEMENT IS NAMED '%s' OF TYPE %s " +
                 "UNDER '%s' IN '%s'.\n") % (c_name, c_f_type, case, p_name))
            blockdef._bad = True

        # sanitize the case descriptor
        src_dict[c_index] = blockdef.sanitize_loop(case_desc, **kwargs)

        # check for any nested errors specific to unions
        _find_union_errors(blockdef, case_desc)

        # set size to the largest size out of all the cases
        size = max(size, c_size)
        c_index += 1

    if CASES in src_dict:
        del src_dict[CASES]
    src_dict[CASE_MAP] = case_map
    src_dict[SIZE] = size

    return src_dict


def stream_adapter_sanitizer(blockdef, src_dict, **kwargs):
    
    p_f_type = src_dict[TYPE]
    p_name = src_dict.get(NAME, UNNAMED)

    if SUB_STRUCT not in src_dict:
        blockdef._e_str += (
            "ERROR: MISSING SUB_STRUCT ENTRY.\n" +
            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True
        return src_dict
    if DECODER not in src_dict:
        blockdef._e_str += (
            "ERROR: MISSING STREAM DECODER.\n" +
            "    OFFENDING ELEMENT IS '%s' OF TYPE %s.\n" % (p_name, p_f_type))
        blockdef._bad = True
    if ENCODER not in src_dict:
        # if no encoder was provided, use a dummy one
        src_dict[ENCODER] = adapter_no_encode

    # remove any keys that aren't descriptor keywords
    for key in tuple(src_dict.keys()):
        if not(isinstance(key, int) or key in desc_keywords):
            src_dict.pop(key)

    # copy the substruct desc so it can be modified
    substruct_desc = dict(src_dict[SUB_STRUCT])
    kwargs['key_name'] = SUB_STRUCT

    # sanitize the name and gui_name of the descriptor
    blockdef.sanitize_name(substruct_desc, **kwargs)

    a_name = substruct_desc.get(NAME, UNNAMED)

    # sanitize the case descriptor
    src_dict[SUB_STRUCT] = blockdef.sanitize_loop(substruct_desc, **kwargs)
    src_dict[NAME_MAP] = {SUB_STRUCT: 'data', a_name: 'data'}

    return src_dict
