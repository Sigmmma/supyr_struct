'''
This module injects a few extra Orangutag specific constants
into the constants module and does a star import of the constants.
'''
from supyr_struct.defs.constants import *

# These keywords are used in the gui struct editor
EDITABLE = "EDITABLE"  # If False, attribute is greyed out and uneditable
GUI_NAME = "GUI_NAME"  # The displayed name of the attribute
MAX = "MAX"  # Max integer/float value, array length, string length, etc
MIN = "MIN"  # Min integer/float value, array length, string length, etc
ORIENT = "ORIENT"  # Which way to display the data; vertical or horizontal
PORTABLE = "PORTABLE"  # Whether or not the block is exportable by itself
#                        Some Blocks might not be able to be exported
#                        separately for various reasons, such as reading
#                        them could require information from their parent.
VISIBLE = "VISIBLE"  # False = Attribute is not rendered when loaded
USE_ENTRY = "USE_ENTRY"  # If True, use an Entry widget instead of a Text
#                          widget for this field. Useful when new line
#                          terminators shouldnt exist in these nodes.


# add the new descriptor keywords to the sets
add_desc_keywords(EDITABLE, GUI_NAME, MAX, MIN, ORIENT, PORTABLE, VISIBLE,
                  USE_ENTRY)

