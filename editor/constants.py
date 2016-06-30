'''
This module injects a few extra Orangutag specific constants into the
constants module and then does a star import of the constants module.
'''
from supyr_struct.defs import constants as _c
from supyr_struct.defs.constants import *

# These keywords are used in the gui struct editor
_c.EDITABLE = "EDITABLE"  # If False, attribute is greyed out and uneditable
_c.GUI_NAME = "GUI_NAME"  # The displayed name of the attribute
_c.MAX = "MAX"  # Max integer/float value, array length, string length, etc
_c.MIN = "MIN"  # Min integer/float value, array length, string length, etc
_c.ORIENT = "ORIENT"  # Which way to display the data; vertical or horizontal
_c.PORTABLE = "PORTABLE"  # Whether or not the block is exportable by itself
#                           Some blocks might not be able to be exported
#                           separately for various reasons, such as reading
#                           them could require information from their parent.
_c.VISIBLE = "VISIBLE"  # False = Attribute is not rendered when loaded
                 
_c.desc_keywords.update((_c.EDITABLE, _c.GUI_NAME, _c.MAX, _c.MIN,
                         _c.ORIENT, _c.PORTABLE, _c.VISIBLE))
