import os

import re

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


non_alphanum_set = r'[^a-zA-Z0-9]+'
digits_at_start = r'^[0-9]+'

def str_to_identifier(string):
    '''Converts given string to a usable identifier. Replaces every sequence
    of invalid non-alphanumeric characters with an underscore.
    Trailing underscores are removed.'''
    assert isinstance(string, str)

    new_string = re.sub(non_alphanum_set, '_', string)
    new_string = re.sub(digits_at_start, '', new_string)
    new_string = new_string.rstrip('_')

    assert new_string, "Identifier %s sanitized to an empty string." % (string)

    return new_string


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
