'''
This module contains generic structures that fit various needs.

These structures are not meant to be used as is(except void_desc)
and need to be included in a descriptor before it is sanitized.

Critical keys will be missing if they aren't sanitized.
'''

from supyr_struct.defs.constants import *
from supyr_struct.defs.frozen_dict import FrozenDict
from supyr_struct.fields import *

void_desc = FrozenDict(NAME='voided', TYPE=Void, NAME_MAP={})


def remaining_data_length(block=None, parent=None, attr_index=None,
                          rawdata=None, new_value=None, *args, **kwargs):
    '''
    Size getter for the amount of data left in the rawdata
    starting at kwargs['offset'] + kwargs['root_offset']

    If not provided, offset and root_offset default to 0.
    '''
    if new_value is not None:
        # there is no size to set for an open ended data stream
        return

    if rawdata is not None:
        # the data is being initially read
        return (len(rawdata) - kwargs.get('offset', 0) +
                kwargs.get('root_offset', 0))
    elif parent is not None:
        # the data already exists, so just return its length
        remainder = parent[attr_index]
        try:
            return len(remainder)
        except Exception:
            pass
    return 0


# used when you just want to read the rest of the rawdata into a bytes object
remaining_data = BytearrayRaw("remaining_data", SIZE=remaining_data_length)
