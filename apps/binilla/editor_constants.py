from supyr_struct.defs.constants import *

# padding to use when packing a widget being oriented vertically
VERTICAL_PADX = (20, 0)
VERTICAL_PADY = (0, 5)

# padding to use when packing a widget being oriented horizontally
HORIZONTAL_PADX = (0, 10)
HORIZONTAL_PADY = (0, 5)

# The default text width of the title label for widgets
TITLE_WIDTH = 35
# The number of text units wide the ScrollMenu is at a minimum
SCROLL_MENU_WIDTH = 35
# The number of text units wide the ScrollMenu is at a minimum
ENUM_MENU_WIDTH = 10

TEXTBOX_HEIGHT = 10
TEXTBOX_WIDTH = 50

# Widths of different types of data that an EntryFrame can be used for
MIN_ENTRY_WIDTH = 4

DEF_INT_ENTRY_WIDTH = 8
DEF_FLOAT_ENTRY_WIDTH = 10
DEF_STRING_ENTRY_WIDTH = 35

MAX_INT_ENTRY_WIDTH = 20
MAX_FLOAT_ENTRY_WIDTH = 20
MAX_STRING_ENTRY_WIDTH = 50

# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 2
FRAME_DEPTH = 3

# default colors for the widgets
WHITE = '#%02x%02x%02x' % (255, 255, 255)
BLACK = '#%02x%02x%02x' % (0, 0, 0)

IO_BG_COLOR = '#%02x%02x%02x' % (47, 47, 50)  # dark grey
IO_FG_COLOR = '#%02x%02x%02x' % (195, 195, 200)  # very light grey
DEFAULT_BG_COLOR = '#%02x%02x%02x' % (236, 233, 216)  # light tan
COMMENT_BG_COLOR = '#%02x%02x%02x' % (241, 239, 226)  # lighter tan
FRAME_BG_COLOR = '#%02x%02x%02x' % (172, 168, 153)  # muddy tan

BUTTON_NORMAL_COLOR = DEFAULT_BG_COLOR
BUTTON_DISABLED_COLOR = DEFAULT_BG_COLOR
BUTTON_HIGHLIGHTED_COLOR = DEFAULT_BG_COLOR

TEXT_NORMAL_COLOR = BLACK
TEXT_DISABLED_COLOR = FRAME_BG_COLOR
TEXT_HIGHLIGHTED_COLOR = WHITE

ENTRY_NORMAL_COLOR = WHITE
ENTRY_DISABLED_COLOR = DEFAULT_BG_COLOR
ENTRY_HIGHLIGHTED_COLOR = '#%02x%02x%02x' % (55, 110, 210)  # pale lightish blue

ENUM_NORMAL_COLOR = ENTRY_NORMAL_COLOR
ENUM_DISABLED_COLOR = ENTRY_DISABLED_COLOR
ENUM_HIGHLIGHTED_COLOR = ENTRY_HIGHLIGHTED_COLOR


# A list of the kwargs used by FrameWidget classes. This list
# exists to prune these items from kwargs as they are passed
# to the actual tkinter class that they are subclassing.
WIDGET_KWARGS = ['parent', 'node', 'attr_index', 'app_root', 'f_widget_parent',
                 'vert_oriented', 'show_frame', 'show_title', 'disabled',
                 'pack_padx', 'pack_pady']


INVALID_OPTION = '<INVALID>'
