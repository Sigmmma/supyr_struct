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
    ''''''
    if not backuppath:
        # Not backing anything up.
        # Delete any file currently at the output path
        if os.path.isfile(filepath) and os.path.isfile(temppath):
            os.remove(filepath)

        # Rename the temp file to the output path
        os.rename(temppath, filepath)
        return

    # if there's already a backup of this file then we
    # delete the old file(not the backup). If there isnt then
    # we backup the old file by renaming it to the backup name.
    if not os.path.isfile(filepath):
        # not overwriting anything. do nothing special
        pass
    elif not os.path.isfile(backuppath):
        # backup doesn't exist. rename the file to its backup path
        try:
            os.makedirs(os.path.dirname(backuppath), exist_ok=True)
            os.rename(filepath, backuppath)
        except Exception:
            pass
    elif remove_old_backup:
        # backup exists and we're being told to remove it
        os.remove(backuppath)
        os.rename(filepath, backuppath)
    else:
        # backup exists and we DON'T want to remove it. remove the other
        os.remove(filepath)

    # Try to rename the temp files to the new file names.
    # Restore the backup if we can't rename the temp to the original
    try:
        os.rename(temppath, filepath)
        return
    except Exception:
        try:
            os.rename(backuppath, filepath)
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
    dir = os.path.join(os.path.realpath(os.path.expanduser(dir)), '')
    path = os.path.realpath(os.path.expanduser(path))
    if not case_sensitive:
        path = path.lower()
        dir = dir.lower()
    return os.path.commonprefix((path, dir)) == dir



if PATHDIV == "/":
    def sanitize_path(path):
        return path.replace('\\', '/')
else:
    def sanitize_path(path):
        return path.replace('/', '\\')
