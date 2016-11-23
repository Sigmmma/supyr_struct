'''
This module injects a few extra Binilla specific constants
into the constants module and does an import * of the constants.
This module can be used in place of supyr_struct.defs.constants
'''
from supyr_struct.defs.constants import *

# These keywords are used in the gui struct editor
EDITABLE = "EDITABLE"  # If False, attribute is greyed out and uneditable
VISIBLE = "VISIBLE"  # False = Attribute is not rendered when loaded
GUI_NAME = "GUI_NAME"  # The displayed name of the attribute
ORIENT = "ORIENT"  # Which way to display the container entries.
#                    valid values are "v" for vertical and "h" for horizontal.

MAX = "MAX"  # Max integer/float value, array length, string length, etc
MIN = "MIN"  # Min integer/float value, array length, string length, etc
ALLOW_MAX = "ALLOW_MAX"  # Whether the value is allowed to be set to the max
ALLOW_MIN = "ALLOW_MIN"  # Whether the value is allowed to be set to the min
UNIT_SCALE = "UNIT_SCALE"  # Node values are multiplied by this before
#                            they are displayed and are divided by it
#                            before the node value is replaced with it.
#                            This is essentially a unit conversion factor.

EXT = "EXT"  # The extension to use for importing/exporting this node
PORTABLE = "PORTABLE"  # Whether or not the block is exportable by itself
#                        Some Blocks might not be able to be exported
#                        separately for various reasons, such as reading
#                        them could require information from their parent.
#                        Portability is assumed False if not specified.
WIDGET = "WIDGET"  # The FieldWidget class used to represent this field


# add the new descriptor keywords to the sets
add_desc_keywords(EDITABLE, VISIBLE, GUI_NAME, ORIENT,
                  MAX, MIN, ALLOW_MAX, ALLOW_MIN, UNIT_SCALE,
                  EXT, PORTABLE, WIDGET)
