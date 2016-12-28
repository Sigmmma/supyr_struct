from supyr_struct.defs.constants import *

# padding to use when packing a widget being oriented vertically
VERTICAL_PADX = (20, 0)
VERTICAL_PADY = (0, 5)

# padding to use when packing a widget being oriented horizontally
HORIZONTAL_PADX = (0, 10)
HORIZONTAL_PADY = (0, 5)

# The default text width of the title label for widgets
TITLE_WIDTH = 35
# The default number of text units wide a ScrollMenu is
SCROLL_MENU_WIDTH = 35
ENUM_MENU_WIDTH = 10

TEXTBOX_HEIGHT = 10
TEXTBOX_WIDTH = 50

# The number of pixels wide and tall a BoolFrame is at a minimum
BOOL_FRAME_MIN_WIDTH = 160
BOOL_FRAME_MIN_HEIGHT = 17
# The number of pixels wide and tall a BoolFrame is at a maximum
BOOL_FRAME_MAX_WIDTH = 300
BOOL_FRAME_MAX_HEIGHT = 255

# Widths of different types of data that an EntryFrame can be used for
MIN_ENTRY_WIDTH = 4

DEF_INT_ENTRY_WIDTH = 8
DEF_FLOAT_ENTRY_WIDTH = 10
DEF_STRING_ENTRY_WIDTH = 35

MAX_INT_ENTRY_WIDTH = 20
MAX_FLOAT_ENTRY_WIDTH = 20
MAX_STRING_ENTRY_WIDTH = 35

SCROLL_MENU_MAX_WIDTH = 35
SCROLL_MENU_MAX_HEIGHT = 15

# default colors for the widgets
IO_FG_COLOR = '#%02x%02x%02x' % (200, 200, 200)  # very light grey
IO_BG_COLOR = '#%02x%02x%02x' % (50, 50, 50)  # dark grey
INVALID_PATH_COLOR = '#%02x%02x%02x' % (255, 0, 0)  # red
TOOLTIP_BG_COLOR = '#%02x%02x%02x' % (255, 255, 224)
WHITE = '#%02x%02x%02x' % (255, 255, 255)
BLACK = '#%02x%02x%02x' % (0, 0, 0)

# ORIGINAL GUERILLA SETTINGS
'''
# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 2
FRAME_DEPTH = 3

DEFAULT_BG_COLOR = '#%02x%02x%02x' % (236, 233, 216)  # light tan
COMMENT_BG_COLOR = '#%02x%02x%02x' % (241, 239, 226)  # lighter tan
FRAME_BG_COLOR = '#%02x%02x%02x' % (172, 168, 153)  # muddy tan
'''

# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 1
FRAME_DEPTH = 1

DEFAULT_BG_COLOR = '#%02x%02x%02x' % (240, 240, 240)
COMMENT_BG_COLOR = '#%02x%02x%02x' % (200, 200, 200)
FRAME_BG_COLOR = '#%02x%02x%02x' % (160, 160, 160)
BUTTON_COLOR = DEFAULT_BG_COLOR

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
WIDGET_KWARGS = [
    'parent', 'desc', 'node', 'attr_index', 'app_root', 'f_widget_parent',
    'vert_oriented', 'show_frame', 'show_title', 'disabled',
    'pack_padx', 'pack_pady', 'tag_window'
    ]

RAW_BYTES = '<RAW BYTES>'
UNNAMED_FIELD = '<UNNAMED>'
INVALID_OPTION = '<INVALID>'
UNKNOWN_BOOLEAN = 'unknown %s'
