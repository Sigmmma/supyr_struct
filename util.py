import pathlib
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
import os

from supyr_struct.defs.constants import ALPHA_IDS, ALPHA_NUMERIC_IDS,\
     PATHDIV, BPI
from supyr_struct.defs.frozen_dict import FrozenDict


def fourcc_to_int(value, byteorder='little', signed=False):
    '''
    Converts a string of 4 characters into an int using
    the supplied byteorder, signage, and latin1 encoding.

    Returns the encoded int.
    '''
    assert len(value) == 4, (
        'The supplied four character code string must be 4 characters long.')
    # The fcc wont let me be, or let me be me, so let me see.....
    return int.from_bytes(bytes(value, encoding='latin1'),
                          byteorder, signed=signed)


def int_to_fourcc(value, byteorder='big', signed=False):
    return value.to_bytes(4, byteorder, signed=signed).decode(
        encoding='latin-1')


# THESE NAMES ARE DEPRECIATED!
# REMOVE THESE WHENEVER POSSIBLE!
fcc = fourcc_to_int
fourcc = int_to_fourcc


def backup_and_rename_temp(filepath, temppath, backuppath=None,
                           remove_old_backup=False):
    '''Moves file from temppath to filepath.
    Backs up existing filepath to backuppath if given.
    Doesn't overwrite old backups unless remove_old_backup=True.'''
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
                   ' ' * BPI + "%s\nto\n" + ' '*BPI + "%s") %
                  (temppath, filepath))


def str_to_identifier(string):
    '''
    Converts a given string into a usable identifier.
    Replaces each contiguous sequence of invalid characters(characters
    unable to be used in a python object name) with a single underscore.
    If the last character is invalid however, it will be dropped.
    '''
    sanitized_str = ''
    start = 0
    skipped = False

    # make sure the sanitized_strs first character is a valid character
    assert isinstance(string, str)

    while start < len(string):
        start += 1
        # ignore characters until an alphabetic one is found
        if string[start - 1] in ALPHA_IDS:
            sanitized_str = string[start - 1]
            break

    # replace all invalid characters with underscores
    for i in range(start, len(string)):
        if string[i] in ALPHA_NUMERIC_IDS:
            sanitized_str += string[i]
            skipped = False
        elif not skipped:
            # no matter how many invalid characters occur in
            # a row, replace them all with a single underscore
            sanitized_str += '_'
            skipped = True

    # make sure the string doesnt end with an underscore
    if skipped:
        sanitized_str.rstrip('_')

    return sanitized_str


def desc_variant(desc, *replacements):
    desc, name_map = dict(desc), dict()

    pad = 0
    for i in range(desc['ENTRIES']):
        name = desc[i].get('NAME', '_')
        # padding uses _ as its name
        if name == '_':
            name = 'pad_%s' % pad
            pad += 1
        name_map[str_to_identifier(name)] = i

    for name, new_sub_desc in replacements:
        desc[name_map[str_to_identifier(name)]] = new_sub_desc

    return desc


def is_in_dir(path, dir, case_sensitive=True):
    try:
        Path(path).relative_to(dir)
        return True
    except Exception:
        return False


if PATHDIV == "/":
    def sanitize_path(path):
        return path.replace('\\', '/')
else:
    def sanitize_path(path):
        return path.replace('/', '\\')


# If not windows then we're likely on a posix filesystem.
# This function will not break on windows. But it's just slower.
def tagpath_to_fullpath(tagdir, tagpath, extension="", force_windows=False, folder=False):
    '''Takes a tagpath and case-insenstively goes through the directory
    tree to find the true path if it exists. (True path being the path with
    proper capitalization.) If force_windows is True, it will always treat
    the path as a windows path, otherwise it will treat it as whatever
    operating system you are using.

    Tagpaths from saved tagfiles should always be treated as windows.
    Tagpaths from filepickers must be native, and thus not forced_windows.

    If folder is True this program will search for a folder and assume
    that the path does not contain a file at the end.

    Returns properly capitalized path if found. None if not found.'''

    if tagdir == "" or tagpath == "":
        return None
    # Get all elements of the tagpath
    if force_windows:
        tagpath = list(pathlib.PureWindowsPath(tagpath).parts)
    else:
        tagpath = list(pathlib.PurePath(tagpath).parts)
    # Get the final element: The tag!
    tagname = ""
    if not folder:
        tagname = (tagpath.pop(-1) + extension).lower()
    # Store our current progression through the tree.
    cur_path = tagdir
    for dir in tagpath:
        subdirs = os.listdir(cur_path) # Get all files in the current dir
        found = False
        # Check if there is directories with the correct name
        for subdir in subdirs:
            if (subdir.lower() == dir.lower()):
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
        # Check if we can find the right file at the end of the chain
    if not folder:
        files = os.listdir(cur_path) # Get all files in the current dir
        for file in files:
            fullpath = os.path.join(cur_path, file)
            if file.lower() == tagname and os.path.isfile(fullpath):
                return fullpath
    # If the execution reaches this point, nothing is found.
    return None

def path_split(path, splitword, force_windows=False):
    '''Takes a path and case-insentively splits it to
    the point before the given splitword.'''
    input_class = type(path)
    # Convert path into a list of each seperate piece.
    parts = list(pathlib.PurePath(path).parts)
    # Go through the path and find the first occurence of the word before which
    # we want to end the path.
    split_idx = len(parts)
    for i in range(len(parts)-1, -1, -1):
        if parts[i].lower() == splitword.lower():
            split_idx = i
            break

    # Build new path from leftover parts.
    new_path = Path(parts[:split_idx])

    # Return path in the same format.
    return input_class(new_path)

def path_replace(path, replace, new, backwards=True, split=False):
    '''Case-insentively replaces a part of the given path.
    Checks what pieces exist in the replaced string and will math the new path
    up to the existing point and finishes it with whatever was put in if it
    doesn't completely exist.

    If backbards it set, which it will be by default, it will try to find the
    right most matching part. Otherwise it will try to find the left most.'''
    parts = list(pathlib.PurePath(path).parts)
    split_idx = len(parts)
    if backwards:
        for i in range(len(parts)-1, -1, -1):
            if parts[i].lower() == replace.lower():
                split_idx = i
                break
    else:
        for i in range(len(parts)):
            if parts[i].lower() == replace.lower():
                split_idx = i
                break

    # Keep the before parts as is.
    before_parts = []
    before_parts.extend(parts[:split_idx])
    # Start after parts at the replacement point.
    after_parts = [new]
    if not split:
        after_parts.extend(parts[split_idx+1:])

    # Go through each directory level and find the corresponding directory name
    # case insensitively. Give up if we can't find any.
    cur_path = before_parts
    for dir in after_parts:
        subdirs = os.listdir(Path(*cur_path)) # Get all files in the current dir
        found = False
        # Check if there is directories with the correct name
        for subdir in subdirs:
            if (subdir.lower() == dir.lower()):
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

    # Return path in the same format, or in a string if the format isn't listed.
    if isinstance(path, (PurePath, PurePosixPath)):
        return pathlib.PurePath(*cur_path)
    elif isinstance(path, PureWindowsPath):
        return pathlib.PureWindowsPath(*cur_path)
    elif isinstance(path, Path):
        return Path(*cur_path)

    return str(PurePath(*cur_path))

def path_normalize(path):
    '''Normalizes a path: Removes redundant seperators, and lower cases it on Windows.'''
    # Handling an edge case here. If a path is empty it will turn into "."
    # Which will fuck up some 'not' operators.
    input_class = type(path)
    path = str(path)
    if path == "":
        return path
    path = os.path.normpath(os.path.normcase(path))
    return input_class(path)
