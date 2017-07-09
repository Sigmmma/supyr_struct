from os import remove as _remove,  rename as _rename
from os.path import commonprefix as _commonprefix, join as _join,\
     isfile as _isfile, realpath as _realpath
from .constants import PATHDIV
from .frozen_dict import FrozenDict


def fcc(value, byteorder='little', signed=False):
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


def backup_and_rename_temp(filepath, temppath, backuppath=None):
    ''''''
    if backuppath:
        # if there's already a backup of this tag
        # we try to delete it. if we can't then we try
        # to rename the old tag with the backup name
        if _isfile(backuppath):
            _remove(filepath)
        else:
            try:
                _rename(filepath, backuppath)
            except Exception:
                pass

        # Try to rename the temp files to the new file names.
        # Restore the backup if we can't rename the temp to the original
        try:
            _rename(temppath, filepath)
        except Exception:
            try:
                _rename(backuppath, filepath)
            except Exception:
                pass
            raise IOError(("ERROR: While attempting to save " +
                           "tag, could not rename temp file:\n" +
                           ' ' * BPI + "%s\nto\n" + ' '*BPI + "%s") %
                          (temppath, filepath))
        return
    # Try to delete the file currently at the output path
    try:
        _remove(filepath)
    except Exception:
        pass
    # Try to rename the temp file to the output path
    try:
        _rename(temppath, filepath)
    except Exception:
        pass


def is_in_dir(path, dir, case_sensitive=True):
    if not case_sensitive:
        path = path.lower()
        dir = dir.lower()
    dir = _join(dir, '')
    return _commonprefix((_realpath(path), dir)) == dir



if PATHDIV == "/":
    def sanitize_path(path):
        return path.replace('\\', '/')
else:
    def sanitize_path(path):
        return path.replace('/', '\\')


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


class BinsizeError(SupyrStructError):
    pass


class FieldParseError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.


class FieldSerializeError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.
