'''
This module is mostly to hold a set of utility functions.
It is not critical to understand this module to be able to use the library.
'''
import os
import re

from pathlib import Path, PureWindowsPath


def fourcc_to_int(value, byteorder='little', signed=False):
    '''
    Converts a string of 4 characters into a 32-bit integer using
    the supplied byteorder, signage, and latin1 encoding.

    Returns the encoded int.
    '''
    assert len(value) == 4, (
        'The supplied four character code string must be 4 characters long.')
    # The fcc wont let me be, or let me be me, so let me see.....
    return int.from_bytes(bytes(value, encoding='latin1'),
                          byteorder, signed=signed)


def int_to_fourcc(value, byteorder='big', signed=False):
    '''
    Converts a 32-bit integer to a 4 character code.
    '''
    return value.to_bytes(4, byteorder, signed=signed).decode(
        encoding='latin-1')


def backup_and_rename_temp(filepath, temppath, backuppath=None,
                           remove_old_backup=False):
    '''
    Moves file from temppath to filepath.
    Backs up existing filepath to backuppath if given.
    Doesn't overwrite old backups unless remove_old_backup=True.
    '''
    filepath = Path(filepath)
    temppath = Path(temppath)

    assert not filepath.is_dir(), "filepath cannot already exist as a directory."
    assert temppath.exists() and temppath.is_file(), "temppath must exist and be a file."

    if backuppath is None: # Make no backup.
        if filepath.exists():
            filepath.unlink()
        temppath.rename(filepath)
        return

    backuppath = Path(backuppath)

    assert not backuppath.is_dir(), "backuppath cannot already exist as a directory."

    if remove_old_backup and backuppath.exists():
        backuppath.unlink()

    if filepath.exists() and not backuppath.exists():
        backuppath.parent.mkdir(exist_ok=True, parents=True)
        filepath.rename(backuppath)
    elif filepath.exists():
        filepath.unlink()

    # Try to rename the temp files to the new file names.
    # Restore the backup if we can't rename the temp to the original
    try:
        temppath.rename(filepath)
        return
    except Exception:
        try:
            backuppath.rename(filepath)
        except Exception:
            pass

    raise IOError(("ERROR: Could not rename temp file:\n"
                   ' '*4 + "%s\nto\n" + ' '*4 + "%s") %
                  (temppath, filepath))


non_alphanum_set = r'[^a-zA-Z0-9]+'
digits_at_start = r'^[0-9]+'

def str_to_identifier(string):
    '''
    Converts given string to a usable identifier. Replaces every sequence
    of invalid non-alphanumeric characters with an underscore.
    Trailing underscores are removed.
    '''
    assert isinstance(string, str), "Expected str, but got %s" % type(string)

    new_string = re.sub(non_alphanum_set, '_', string)
    new_string = re.sub(digits_at_start, '', new_string)
    new_string = new_string.rstrip('_')

    assert new_string, "Identifier %r sanitized to an empty string." % (string)

    return new_string


def desc_variant(desc, *replacements, verify=False, **kwargs):
    '''
    Fringe: Used to generate a new descriptor using a set of replacements.
    Replacements can either be a field descriptor, or a tuple containing
    the name of the field to replace, and the replacement field descriptor.
    If verify is True, replacement fields will have their size checked to
    ensure it matches the size of the replaced. If they don't match or it
    can't be determiend if they do, a ValueError is thrown.

    desc_variant(some_descriptor,
        (str:name_of_old_field, FieldType:new_field_def),
        (str:name_of_another_old_field, FieldType:some_other_field_def),
        FieldType:new_field_def_with_same_name_as_old,
    )
    Ex:
    ```py
    thing = Struct("name_of_struct",
        UInt32("one"),
        UInt32("two"),
        UInt32("three"),
        )
    thing_variant = desc_variant(thing,
        ("two", Struct("new_two", UInt16("something"), Uint16("some_other"))),
        Struct("three", UInt16("aaaa"), Uint16("bbbb")),
        )
    ```
    This would make thing_variant a variant of thing where UInt32 "two" is
    replaced by a Struct called "new_two", and "three" is similarly replaced.
    '''
    desc, name_map = dict(desc), dict()
    desc.update(kwargs)
    
    # NOTE: this function has been improved to make it much harder to 
    #       accidentally replace the wrong field, or use a field with
    #       a mismatched size. If a name isn't provided, we're assumed
    #       to need to find something to replace with the same name as
    #       what we've been provided. Additionally, we can check that
    #       the size of the replacement is the same as what is replaced

    for i in range(desc['ENTRIES']):
        sub_desc = desc[i]
        name = sub_desc.get('NAME', None)
        ftyp = sub_desc.get('TYPE')

        # padding uses _ as its name, so if it's 
        if name != "_":
            name_map[str_to_identifier(name)] = i
        elif not ftyp or ftyp.name != "Pad":
            # dont let this silently cause bugs
            raise ValueError("Expected padding, but got %s" % ftyp)
        else:
            # generate the name we expect the user to pass for the padding
            name_map['pad_%d' % i] = i

    for replacement in replacements:
        name, new_sub_desc = None, None

        if isinstance(replacement, dict):
            # we were provided just a desc
            new_sub_desc = replacement
        elif not(replacement and isinstance(replacement, (list, tuple))):
            raise ValueError("Invalid replacement supplied: %s of type %s" % 
                (replacement, type(replacement))
                )
        else:
            # we were given a list or tuple. figure out what was passed
            for val in replacement:
                if not name and isinstance(val, str):
                    name = val
                elif not isinstance(val, dict):
                    raise ValueError("Unknown replacement value passed: %s" % val)
                elif not new_sub_desc and val.get('TYPE'):
                    new_sub_desc = val
                else:
                    raise ValueError("Unexpected replacement value passed: %s" % val)

        if not new_sub_desc:
            raise ValueError("No replacement desc provided.")

        if name is None:
            # we were provided a replacement desc without a target name.
            # assume the name of the field we're replacing matches its name
            name = new_sub_desc["NAME"]

        # figure out what index to put the replacement into, and
        # (if requested) do some validation on the replacement.
        index = name_map[str_to_identifier(name)]
        verify_args = (desc, new_sub_desc, desc[index])
        if verify and get_replacement_field_conflict(*verify_args):
            raise ValueError(
                "Incompatible replacement detected for field '%s':\n\t%s" % 
                (name, get_replacement_field_conflict(*verify_args))
                )

        desc[index] = new_sub_desc

    return desc


def desc_variant_with_verify(desc, *replacements, **kwargs):
    '''Version of desc_variant with size verification defaulted to True.'''
    kwargs.setdefault("verify", True)
    return desc_variant(desc, *replacements, **kwargs)


def get_replacement_field_conflict(parent_desc, new_desc, old_desc):
    '''
    Returns a string to indicate why a field is not a valid
    replacement for another field. An empty string will be
    returned if there are no conflicts.
    '''
    parent_type = parent_desc["TYPE"]
    old_type = old_desc["TYPE"]
    new_type = new_desc["TYPE"]
    old_size = old_desc.get("SIZE") if old_type.is_var_size else old_type.size
    new_size = new_desc.get("SIZE") if new_type.is_var_size else new_type.size

    error_str  = ""
    error_args = ()
    if old_size is None and new_size is None:
        # sizes are both undefined, so the parent must be a container.
        # if not, then the size of both will be calculated later, and
        # that means we can't verify they match here.
        if not parent_type.is_container:
            error_str = "Neither field size defined in non open-ended parent"
    elif None in (old_size, new_size):
        # only one field is missing its size. this is a problem, as
        # we can't verify they match.
        error_str = "One field size could not be determined - %s vs %s"
        error_args = (old_size, new_size)
    elif old_size != new_size:
        error_str = "Field sizes dont match - %s vs %s"
        error_args = (old_size, new_size)

    return error_str % error_args


def is_in_dir(path, directory):
    '''Checks if path is in directory. Respects symlinks.'''
    try:
        Path(path).relative_to(directory)
        return True
    except ValueError:
        return False


def is_path_empty(path):
    '''
    `if not path` will not always return if a path is empty
    because of Path objects. Instead do `if is_path_empty(path)`
    '''
    return not path or str(path) == "."


# If not windows then we're likely on a posix filesystem.
# This function will not break on windows. But it's just slower.
def tagpath_to_fullpath(
        tagdir, tagpath, extension="", force_windows=False, folder=False):
    '''
    Takes a tagpath and case-insenstively goes through the directory
    tree to find the true path if it exists. (True path being the path with
    proper capitalization.) If force_windows is True, it will always treat
    the path as a case insentive path, otherwise it will treat it as whatever
    operating system you are using.

    Tagpaths from saved tagfiles should always be treated as windows.
    Tagpaths from filepickers must be native, and thus not forced_windows.

    If folder is True this program will search for a folder and assume
    that the path does not contain a file at the end.

    Returns properly capitalized path if found. None if not found.
    '''

    if is_path_empty(tagdir) or is_path_empty(tagpath):
        return None

    # Get all elements of the tagpath
    if force_windows:
        tagpath = list(PureWindowsPath(tagpath).parts)
    else:
        tagpath = list(Path(tagpath).parts)

    # Get the final element: The tag!
    tagname = ""
    if not folder:
        tagname = (tagpath.pop(-1) + extension).lower()

    # Store our current progression through the tree.
    cur_path = str(tagdir)
    for directory in tagpath:
        subdirs = os.listdir(cur_path) # Get all files in the current dir
        found = False
        # Check if there is directories with the correct name
        for subdir in subdirs:
            if (subdir.lower() == directory.lower()):
                fullpath = os.path.join(cur_path, subdir)
                if not os.path.isdir(fullpath):
                    continue
                # Add the current directory to the end of our full path.
                cur_path = fullpath
                found = True
                break

        # If no matching directory was found, give up.
        if not found:
            return None

    if folder:
        return fullpath

    # Check if we can find the right file at the end of the chain
    files = os.listdir(cur_path) # Get all files in the current dir
    for file in files:
        fullpath = os.path.join(cur_path, file)
        if file.lower() == tagname and os.path.isfile(fullpath):
            return fullpath

    # If the execution reaches this point, nothing is found.
    return None

def path_split(path, splitword, after=False):
    '''
    Takes a path and case-insentively splits it to the point
    before the given splitword. After if after=True
    '''
    input_class = type(path)
    # Convert path into a list of each seperate piece.
    parts = list(Path(path).parts)
    # Go through the path and find the first occurence of the word before which
    # we want to end the path.
    split_idx = len(parts)
    for i in range(len(parts)-1, -1, -1):
        if parts[i].lower() == splitword.lower():
            split_idx = i
            break

    # Build new path from leftover parts.
    new_path = Path(*parts[:split_idx+1]) if after else Path(*parts[:split_idx])


    # Return path in the same format.
    return input_class(new_path)


def path_replace(path, replace, new, backwards=True, split=False):
    '''
    Case-insentively replaces a part of the given path.
    Checks what pieces exist in the replaced string and will math the new path
    up to the existing point and finishes it with whatever was put in if it
    doesn't completely exist.

    If backbards it set, which it will be by default, it will try to find the
    right most matching part. Otherwise it will try to find the left most.
    '''
    path_type = type(path)
    parts = Path(path).parts
    split_idx = -1

    if backwards:
        enumerator = reversed_enumerate(parts or ())
    else:
        enumerator = enumerate(parts or ())

    for i, part in enumerator:
        if part.lower() == replace.lower():
            split_idx = i
            break

    # Keep the before parts as is.
    before_parts = []
    before_parts.extend(parts[ :split_idx])
    # Start after parts at the replacement point.
    after_parts = [new]
    if not split:
        after_parts.extend(parts[split_idx+1:])

    # Go through each directory level and find the corresponding directory name
    # case insensitively. Give up if we can't find any.
    cur_path = before_parts
    for directory in after_parts:
        # Get all files in the current dir
        subdirs = os.listdir(str(Path(*cur_path)))
        found = False
        # Check if there is directories with the correct name
        for subdir in subdirs:
            if (subdir.lower() == directory.lower()):
                cur_path.append(subdir)
                # Add the current directory to the end of our full path.
                found = True
                break
        # If no matching directory was found, give up.
        if not found:
            break

    # Get the path pieces that don't exist in the new directory and extend it
    # with all lower case versions of the original.
    leftover = parts[len(cur_path):len(parts)]
    for part in leftover:
        cur_path.append(part.lower())

    # Return path in the same type as we got it.
    return path_type(Path(*cur_path))


def path_normalize(path):
    '''
    Normalizes a path: Removes redundant seperators.
    On Windows this lowercases the path.
    '''
    input_class = type(path)
    if is_path_empty(path):
        return input_class(path)
    path = os.path.normpath(os.path.normcase(str(path)))
    return input_class(path)

def reversed_enumerate(iterable):
    '''
    As of Python 3.8 you still can't reverse an enumerate object.
    So, until that is possible, this exists.
    '''
    # This version is avoided because it potentially makes use of a lot of
    # python objects. And thus, memory.

    #return reversed(tuple(enumerate(iterable)))

    # This one is used because it ends up being stored as a simple range
    # iterator and reversed object.
    return zip(
        reversed(range(len(iterable))),
        reversed(iterable)
    )
