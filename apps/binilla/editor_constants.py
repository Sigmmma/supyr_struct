from supyr_struct.defs.constants import *

# The default amount of padding that widgets within
# node frames have from each of the sides of the
# frame that they are contained within
NODE_FRAME_PAD_L = 15
NODE_FRAME_PAD_R = 5
NODE_FRAME_PAD_T = 15
NODE_FRAME_PAD_B = 5

# The default amount of padding that data canvas
# widgets have from their neighboring sibling widgets.
# This padding is ONLY applied BETWEEN subsequent widgets
NODE_CANVAS_PAD_L = 0
NODE_CANVAS_PAD_R = 0
NODE_CANVAS_PAD_T = 5
NODE_CANVAS_PAD_B = 5

# The default amount of padding that data widgets
# have from their neighboring sibling widgets.
# This padding is ONLY applied BETWEEN subsequent widgets
DATA_PAD_L = 20
DATA_PAD_R = 20
DATA_PAD_T = 5
DATA_PAD_B = 5


# default depths for each of the different widget types
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 2
TOOLTIP_DEPTH = ARRAY_DEPTH = 1
FRAME_DEPTH = 0

# default colors for the widgets
WHITE = '#%02x%02x%02x' % (255, 255, 255)
BLACK = '#%02x%02x%02x' % (0, 0, 0)

DEFAULT_BG_COLOR = '#%02x%02x%02x' % (236, 233, 216)  # light tan
TOOLTIP_BG_COLOR = '#%02x%02x%02x' % (241, 239, 226)  # lighter tan
ARRAY_BG_COLOR = '#%02x%02x%02x' % (172, 168, 153)  # muddy tan
IO_BG_COLOR = '#%02x%02x%02x' % (47, 47, 50)  # dark grey
IO_FG_COLOR = '#%02x%02x%02x' % (195, 195, 200)  # very light grey
FIELD_BG_NORMAL_COLOR = WHITE
FIELD_BG_DISABLED_COLOR = DEFAULT_BG_COLOR

ENUM_BG_NORMAL_COLOR = WHITE
ENUM_BG_DISABLED_COLOR = DEFAULT_BG_COLOR
ENUM_BG_SELECTED_COLOR = '#%02x%02x%02x' % (49, 106, 197)

TEXT_NORMAL_COLOR = BLACK
TEXT_DISABLED_COLOR = ARRAY_BG_COLOR
TEXT_SELECTED_COLOR = FIELD_BG_NORMAL_COLOR


# The number of pixels wide the region is to the left of the
# entry fields which is where the field names are displayed.
FIELD_LABEL_SIZE = 120

WIDGET_KWARGS = ('parent', 'node', 'attr_index', 'func', 'app_root',
                 'pad_l', 'pad_r', 'pad_t', 'pad_b',
                 'f_widget_parent', )
