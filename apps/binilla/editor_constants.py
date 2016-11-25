from supyr_struct.defs.constants import *

# padding to use when packing a widget being oriented vertically
VERTICAL_FRAME_PADX = (20, 0)
VERTICAL_FRAME_PADY = (0, 5)

# padding to use when packing a widget being oriented horizontally
HORIZONTAL_PADX = (0, 10)
HORIZONTAL_PADY = (0, 5)

# The default text width of the title label for widgets
FRAME_TITLE_WIDTH = 40

# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 2
FRAME_DEPTH = 3

# default colors for the widgets
WHITE = '#%02x%02x%02x' % (255, 255, 255)
BLACK = '#%02x%02x%02x' % (0, 0, 0)

DEFAULT_BG_COLOR = '#%02x%02x%02x' % (236, 233, 216)  # light tan
TOOLTIP_BG_COLOR = '#%02x%02x%02x' % (241, 239, 226)  # lighter tan
FRAME_BG_COLOR = '#%02x%02x%02x' % (172, 168, 153)  # muddy tan
IO_BG_COLOR = '#%02x%02x%02x' % (47, 47, 50)  # dark grey
IO_FG_COLOR = '#%02x%02x%02x' % (195, 195, 200)  # very light grey
FIELD_BG_NORMAL_COLOR = WHITE
FIELD_BG_DISABLED_COLOR = DEFAULT_BG_COLOR

ENUM_BG_NORMAL_COLOR = WHITE
ENUM_BG_DISABLED_COLOR = DEFAULT_BG_COLOR
ENUM_BG_SELECTED_COLOR = '#%02x%02x%02x' % (49, 106, 197)

TEXT_NORMAL_COLOR = BLACK
TEXT_DISABLED_COLOR = FRAME_BG_COLOR
TEXT_SELECTED_COLOR = FIELD_BG_NORMAL_COLOR


# The number of text units wide the ScrollMenu is at a minimum
SCROLL_MENU_SIZE = 30

# A list of the kwargs used by FrameWidget classes. This list
# exists to prune these items from kwargs as they are passed
# to the actual tkinter class that they are subclassing.
WIDGET_KWARGS = ['parent', 'node', 'attr_index', 'app_root', 'f_widget_parent',
                 'vert_oriented', 'show_frame', 'show_title',
                 'pack_padx', 'pack_pady']
