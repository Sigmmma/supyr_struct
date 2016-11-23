from supyr_struct.defs.constants import *

# The default amount of padding that widgets within
# node frames have from each of the sides of the
# frame that they are contained within
NODE_FRAME_PADX = 10
NODE_FRAME_PADY = 0

# The default amount of padding that data canvas
# widgets have from their neighboring sibling widgets.
NODE_CANVAS_PADX = 10
NODE_CANVAS_PADY = 0

# The default amount of padding that data widgets
# have from their neighboring sibling widgets.
DATA_PADX = 5
DATA_PADY = 2

# The default text width of the title label for frame based widgets
FRAME_TITLE_WIDTH = 40

# default depths for each of the different widget types
TOOLTIP_DEPTH = ARRAY_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = FRAME_DEPTH = 2

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
FIELD_LABEL_SIZE = 75
# The number of text units wide the ScrollMenu is at a minimum
SCROLL_MENU_SIZE = 30

WIDGET_KWARGS = ('parent', 'node', 'attr_index', 'app_root', 'f_widget_parent',
                 'vert_oriented', 'show_frame', 'show_title')
