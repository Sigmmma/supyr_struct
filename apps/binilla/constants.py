'''
This module does an import * of the supyr_struct.defs.constants
module and adds a few extra Binilla specific constants of its own.
This module can be used in place of supyr_struct.defs.constants

To inject the new constants into the constants module, call inject()
'''
from supyr_struct.defs.constants import *

# These keywords are used in the gui struct editor
EDITABLE = "EDITABLE"  # If False, attribute is greyed out and uneditable
VISIBLE = "VISIBLE"  # False = Attribute is not rendered when loaded
GUI_NAME = "GUI_NAME"  # The displayed name of the attribute
ORIENT = "ORIENT"  # Which way to display the container entries.
#                    valid values are "v" for vertical and "h" for horizontal.
WIDGET_WIDTH = "WIDGET_WIDTH"  # the width of the widget


TOOLTIP = "TOOLTIP"  # The message a tooltip box will display when the
#                      widget is hovered over. Formatting will be done
#                      manually, meaning insert /n returns where needed
COMMENT = "COMMENT"  # A comment box will be displayed above the widget
#                      with this as the content. Formatting will be done
#                      manually, meaning insert /n returns where needed
SIDETIP = "SIDETIP"  # A label to the right of the widget to display
#                        a small tip and is usually a couple characters.
#                        Mainly used for displaying units(grams for example).

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
#                        Portability is assumed True if not specified.
WIDGET = "WIDGET"  # The FieldWidget class used to represent this field

def inject():
    # add the new descriptor keywords to the sets
    add_desc_keywords(EDITABLE, VISIBLE, GUI_NAME, ORIENT, WIDGET_WIDTH,
                      MAX, MIN, ALLOW_MAX, ALLOW_MIN, UNIT_SCALE,
                      EXT, PORTABLE, WIDGET,
                      TOOLTIP, COMMENT, SIDETIP)
