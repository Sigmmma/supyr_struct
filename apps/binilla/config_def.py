from supyr_struct.defs.tag_def import TagDef
from supyr_struct.apps.binilla.field_widgets import *
from supyr_struct.apps.binilla.constants import *
from supyr_struct.field_types import *

pad_str = "Padding applied to the %s of widgets oriented %sally"

flag_tooltips = (
    "Whether to syncronize movement of tag windows with the main window.",
    "Whether to reload the tags that were open when the program was closed.",
    "Whether to write console output to a log.",
    "Whether to write tag printouts to the log file",
    "Whether to be in debug mode or not.\nDoesnt do much right now."
    )

handler_flag_tooltips = (
    ("Whether to rename original files with a .backup extension before\n" +
     "the first time you save, so as to keep an original backup."),
    "Whether to write tags to temp files instead of the original filepath",
    ("Whether to allow loading corrupt tags, which can then be displayed.\n" +
     "(This is a debugging feature and should be used with care)"),
    ("Whether to do an 'integrity test' after saving a tag to ensure it isnt corrupt.\n" +
     "If the tag can be re-opened, it passes the test.\n" +
     "If it cant, it is considered corrupt and the saving is cancelled."),
    )

tag_window_flag_tooltips = (
    "Enables editing all fields.\nBE CAREFUL!",
    "Shows every field(even internal values like array counts).\nBE CAREFUL!",
    ("Whether to clip entered data to the 'max' value for all fields.\n" +
     "For integers and floats, this is the highest number you can enter.\n" +
     "For arrays, it is the maximum number of entries in the array.\n" +
     "For everything else, it is the maximum number of bytes the data is."),
    ("Whether to clip entered data to the 'min' value for all fields.\n" +
     "For integers and floats, this is the lowest number you can enter.\n" +
     "For arrays, it is the minimum number of entries in the array.\n" +
     "For everything else, it is the minimum number of bytes the data is."),
    "Whether to scale values by their 'unit scale' before displaying them.",
    ("Whether to use a specially given 'gui name' for the title of each\n" +
     "field instead of replacing all underscores in its name with spaces."),
    "Whether to start all collapsable blocks in a tag as expanded or collapsed.",
    "Whether to show comments.",
    "Whether to show tooltips.",
    "Whether to show sidetips.",
    ("Whether to cap the size of tag windows when auto-sizing them\n" +
     "so that they dont expand past the edge of the screen."),
    "Whether to allow shrinking tag windows when auto-sizing them",
    ("Whether to resize tag windows to fit their contents when something\n" +
     "happens to the contents(mouse scrolling, a widget is changed, etc)."),
    "Whether to set tag window dimensions to the default ones when opening a tag.",
    ("Whether to display a checkbox for each available bit in a boolean, even\n" +
     "if that bit doesnt represent anything. Used for debugging and testing.")
    )

app_window_tooltips = (
    "Width of the main window",
    "Height of the main window",
    "X position of the main window",
    "Y position of the main window",
    ("Max number of entries to display in the 'windows' menu." +
     "\nAfter this, a 'window manager' button will be added."),
    ("Number of locations a tag window can be placed\n" +
     "horizontally before moving down one step."),
    ("Number of locations a tag window can be placed\n" +
     "vertically before resetting to placing at the top left."),
    "Amount of horizontal spacing between 'steps' when cascading tag windows.",
    ("Amount of horizontal spacing between 'steps' when tiling tag windows.\n" +
     "This is also used when placing new tag windows."),
    ("Amount of vertical spacing between 'steps' when tiling tag windows.\n" +
     "This is also used when placing new tag windows."),
    "Default width of tag windows if not auto-sizing them.",
    "Default height of tag windows if not auto-sizing them.",
    "Number of pixels to jump when scrolling horizontally.",
    "Number of pixels to jump when scrolling vertically.",
    )

widget_tooltips = (
    "Number of characters wide the title of each vertically oriented field is.",
    ("Default number of characters wide an enumerator widget will be when\n" +
     "not being used to represent an enumerator(such as in an array or union)"),
    "Default number of characters wide an enumerator widget will be.",
    "Minimum number of characters wide an entry field must be.",

    "Width of multi-line text boxes",
    "Height of multi-line text boxes",

    "Minimum number of pixels wide a boolean frame must be.",
    "Minimum number of pixels tall a boolean frame must be.",
    "Maximum number of pixels wide a boolean frame can be.",
    "Maximum number of pixels tall a boolean frame can be.",

    "Default number of characters wide an integer entry field will be.",
    "Default number of characters wide a float entry field will be.",
    "Default number of characters wide a string entry field will be.",

    "Maximum number of characters wide an integer entry field can be.",
    "Maximum number of characters wide a float entry field can be.",
    "Maximum number of characters wide a string entry field can be.",

    ("Maximum number of characters wide an enumerator widget can be.\n" +
     "(This is regardless of what the enumerator widget is being used for)"),
    ("Maximum number of characters tall an enumerator widget can be.\n" +
     "(This is regardless of what the enumerator widget is being used for)"),
    )

depth_tooltip = "\
Number of pixels to surround the widget with to give an appearance of depth."

widget_depth_names = ("frame", "button", "entry", "listbox", "comment")

color_names = (
    "io_fg", "io_bg",
    "default_bg", "comment_bg", "frame_bg", "button",
    "text_normal", "text_disabled", "text_highlighted",
    "enum_normal", "enum_disabled", "enum_highlighted",
    "entry_normal", "entry_disabled", "entry_highlighted",
    "invalid_path", "tooltip_bg",
    )

modifier_enums = (
    {GUI_NAME: "", NAME: "NONE"},
    "Alt",
    "Shift",
    "Control",

    {NAME: "Alt_Shift", GUI_NAME: "Alt+Shift"},
    {NAME: "Alt_Control", GUI_NAME: "Alt+Control"},
    {NAME: "Control_Shift", GUI_NAME: "Control+Shift"},

    {NAME: "Alt_Control_Shift", GUI_NAME: "Alt+Control+Shift"},
    )

hotkey_enums = (
    {GUI_NAME: "", NAME: "NONE"},
    {GUI_NAME: "  1", NAME: "_1"}, {GUI_NAME: "  2", NAME: "_2"},
    {GUI_NAME: "  3", NAME: "_3"}, {GUI_NAME: "  4", NAME: "_4"},
    {GUI_NAME: "  5", NAME: "_5"}, {GUI_NAME: "  6", NAME: "_6"},
    {GUI_NAME: "  7", NAME: "_7"}, {GUI_NAME: "  8", NAME: "_8"},
    {GUI_NAME: "  9", NAME: "_9"}, {GUI_NAME: "  0", NAME: "_0"},

    {GUI_NAME: "  a", NAME: "a"}, {GUI_NAME: "  b", NAME: "b"},
    {GUI_NAME: "  c", NAME: "c"}, {GUI_NAME: "  d", NAME: "d"},
    {GUI_NAME: "  e", NAME: "e"}, {GUI_NAME: "  f", NAME: "f"},
    {GUI_NAME: "  g", NAME: "g"}, {GUI_NAME: "  h", NAME: "h"},
    {GUI_NAME: "  i", NAME: "i"}, {GUI_NAME: "  j", NAME: "j"},
    {GUI_NAME: "  k", NAME: "k"}, {GUI_NAME: "  l", NAME: "l"},
    {GUI_NAME: "  m", NAME: "m"}, {GUI_NAME: "  n", NAME: "n"},
    {GUI_NAME: "  o", NAME: "o"}, {GUI_NAME: "  p", NAME: "p"},
    {GUI_NAME: "  q", NAME: "q"}, {GUI_NAME: "  r", NAME: "r"},
    {GUI_NAME: "  s", NAME: "s"}, {GUI_NAME: "  t", NAME: "t"},
    {GUI_NAME: "  u", NAME: "u"}, {GUI_NAME: "  v", NAME: "v"},
    {GUI_NAME: "  w", NAME: "w"}, {GUI_NAME: "  x", NAME: "x"},
    {GUI_NAME: "  y", NAME: "y"}, {GUI_NAME: "  z", NAME: "z"},

    {GUI_NAME: "  A", NAME: "A"}, {GUI_NAME: "  B", NAME: "B"},
    {GUI_NAME: "  C", NAME: "C"}, {GUI_NAME: "  D", NAME: "D"},
    {GUI_NAME: "  E", NAME: "E"}, {GUI_NAME: "  F", NAME: "F"},
    {GUI_NAME: "  G", NAME: "G"}, {GUI_NAME: "  H", NAME: "H"},
    {GUI_NAME: "  I", NAME: "I"}, {GUI_NAME: "  J", NAME: "J"},
    {GUI_NAME: "  K", NAME: "K"}, {GUI_NAME: "  L", NAME: "L"},
    {GUI_NAME: "  M", NAME: "M"}, {GUI_NAME: "  N", NAME: "N"},
    {GUI_NAME: "  O", NAME: "O"}, {GUI_NAME: "  P", NAME: "P"},
    {GUI_NAME: "  Q", NAME: "Q"}, {GUI_NAME: "  R", NAME: "R"},
    {GUI_NAME: "  S", NAME: "S"}, {GUI_NAME: "  T", NAME: "T"},
    {GUI_NAME: "  U", NAME: "U"}, {GUI_NAME: "  V", NAME: "V"},
    {GUI_NAME: "  W", NAME: "W"}, {GUI_NAME: "  X", NAME: "X"},
    {GUI_NAME: "  Y", NAME: "Y"}, {GUI_NAME: "  Z", NAME: "Z"},

    {GUI_NAME: "  Space", NAME: "space"},
    {GUI_NAME: "  <", NAME: "less"},
    {GUI_NAME: "  >", NAME: "greater"},
    {GUI_NAME: "  ,", NAME: "comma"},
    {GUI_NAME: "  .", NAME: "period"},
    {GUI_NAME: "  /", NAME: "slash"},
    {GUI_NAME: "  ?", NAME: "question"},
    {GUI_NAME: "  ;", NAME: "semicolon"},
    {GUI_NAME: "  :", NAME: "colon"},
    {GUI_NAME: "  '", NAME: "quoteright"},
    {GUI_NAME: '  "', NAME: "quotedbl"},
    {GUI_NAME: "  [", NAME: "bracketright"},
    {GUI_NAME: "  ]", NAME: "bracketleft"},
    {GUI_NAME: "  {", NAME: "braceright"},
    {GUI_NAME: "  }", NAME: "braceleft"},
    {GUI_NAME: "  \\", NAME: "backslash"},
    {GUI_NAME: "  |", NAME: "bar"},
    {GUI_NAME: "  -", NAME: "minus"},
    {GUI_NAME: "  +", NAME: "plus"},
    {GUI_NAME: "  _", NAME: "underscore"},
    {GUI_NAME: "  =", NAME: "equal"},
    {GUI_NAME: "  `", NAME: "quoteleft"},
    {GUI_NAME: "  ~", NAME: "asciitilde"},
    {GUI_NAME: "  !", NAME: "exclam"},
    {GUI_NAME: "  @", NAME: "at"},
    {GUI_NAME: "  #", NAME: "numbersign"},
    {GUI_NAME: "  $", NAME: "dollar"},
    {GUI_NAME: "  %", NAME: "percent"},
    {GUI_NAME: "  ^", NAME: "caret"},
    {GUI_NAME: "  &", NAME: "ampersand"},
    {GUI_NAME: "  *", NAME: "asterisk"},
    {GUI_NAME: "  (", NAME: "parenleft"},
    {GUI_NAME: "  )", NAME: "parenright"},

    {GUI_NAME: "  Keypad 1", NAME: "KP_1"},
    {GUI_NAME: "  Keypad 2", NAME: "KP_2"},
    {GUI_NAME: "  Keypad 3", NAME: "KP_3"},
    {GUI_NAME: "  Keypad 4", NAME: "KP_4"},
    {GUI_NAME: "  Keypad 5", NAME: "KP_5"},
    {GUI_NAME: "  Keypad 6", NAME: "KP_6"},
    {GUI_NAME: "  Keypad 7", NAME: "KP_7"},
    {GUI_NAME: "  Keypad 8", NAME: "KP_8"},
    {GUI_NAME: "  Keypad 9", NAME: "KP_9"},
    {GUI_NAME: "  Keypad 0", NAME: "KP_0"},

    {GUI_NAME: "  Keypad .", NAME: "KP_Decimal"},
    {GUI_NAME: "  Keypad +", NAME: "KP_Add"},
    {GUI_NAME: "  Keypad =", NAME: "KP_Subtract"},
    {GUI_NAME: "  Keypad /", NAME: "KP_Divide"},
    {GUI_NAME: "  Keypad *", NAME: "KP_Multiply"},
    {GUI_NAME: "  Keypad Delete", NAME: "KP_Delete"},
    {GUI_NAME: "  Keypad Enter", NAME: "KP_Enter"},

    {GUI_NAME: "  Break", NAME: "Cancel"},
    {GUI_NAME: "  Backspace", NAME: "BackSpace"},
    {GUI_NAME: "  Enter", NAME: "Return"},
    {GUI_NAME: "  Caps Lock", NAME: "Caps_Lock"},
    {GUI_NAME: "  Num Lock", NAME: "Num_Lock"},
    {GUI_NAME: "  Scroll Lock", NAME: "Scroll_Lock"},
    {GUI_NAME: "  Pageup", NAME: "Prior"},
    {GUI_NAME: "  Pagedown", NAME: "Next"},
    {GUI_NAME: "  Printscreen", NAME: "Print"},
    {GUI_NAME: "  Tab", NAME: "Tab"},
    {GUI_NAME: "  Pause", NAME: "Pause"},
    {GUI_NAME: "  Escape", NAME: "Escape"},
    {GUI_NAME: "  End", NAME: "End"},
    {GUI_NAME: "  Home", NAME: "Home"},
    {GUI_NAME: "  Alt L", NAME: "Alt_L"},
    {GUI_NAME: "  Alt R", NAME: "Alt_R"},
    {GUI_NAME: "  Control L", NAME: "Control_L"},
    {GUI_NAME: "  Control R", NAME: "Control_R"},
    {GUI_NAME: "  Shift L", NAME: "Shift_L"},
    {GUI_NAME: "  Shift R", NAME: "Shift_R"},
    {GUI_NAME: "  Left", NAME: "Left"},
    {GUI_NAME: "  Up", NAME: "Up"},
    {GUI_NAME: "  Right", NAME: "Down"},
    {GUI_NAME: "  Insert", NAME: "Insert"},
    {GUI_NAME: "  Delete", NAME: "Delete"},
    {GUI_NAME: "  F1", NAME: "F1"}, {GUI_NAME: "  F2", NAME: "F2"},
    {GUI_NAME: "  F3", NAME: "F3"}, {GUI_NAME: "  F4", NAME: "F4"},
    {GUI_NAME: "  F5", NAME: "F5"}, {GUI_NAME: "  F6", NAME: "F6"},
    {GUI_NAME: "  F7", NAME: "F7"}, {GUI_NAME: "  F8", NAME: "F8"},
    {GUI_NAME: "  F9", NAME: "F9"}, {GUI_NAME: "  F10", NAME: "F10"},
    {GUI_NAME: "  F11", NAME: "F11"}, {GUI_NAME: "  F12", NAME: "F12"},
    {GUI_NAME: "  Mousewheel", NAME: "MouseWheel"},
    )

method_enums = (
    {GUI_NAME: "undo", NAME: "edit_undo"},
    {GUI_NAME: "redo", NAME: "edit_redo"},
    {GUI_NAME: "mousewheel scroll x", NAME: "mousewheel_scroll_x"},
    {GUI_NAME: "mousewheel scroll y", NAME: "mousewheel_scroll_y"},
    {GUI_NAME: "close window", NAME: "close_selected_window"},
    {GUI_NAME: "load tags", NAME: "load_tags"},
    {GUI_NAME: "new tag", NAME: "new_tag"},
    {GUI_NAME: "save tag", NAME: "save_tag"},
    {GUI_NAME: "show defs", NAME: "show_defs"},
    {GUI_NAME: "show window manager", NAME: "show_window_manager"},
    {GUI_NAME: "load tag as", NAME: "load_tag_as"},
    {GUI_NAME: "save tag as", NAME: "save_tag_as"},
    {GUI_NAME: "save all open tags", NAME: "save_all"},
    {GUI_NAME: "print tag", NAME: "print_tag"},

    {GUI_NAME: "cascade windows", NAME: "cascade"},
    {GUI_NAME: "tile windows vertically", NAME: "tile_vertical"},
    {GUI_NAME: "tile windows horizontally", NAME: "tile_horizontal"},
    {GUI_NAME: "minimize all windows", NAME: "minimize_all"},
    {GUI_NAME: "restore all windows", NAME: "restore_all"},
    {GUI_NAME: "display config file", NAME: "show_config_file"},
    {GUI_NAME: "apply config file", NAME: "apply_config"},
    {GUI_NAME: "exit program", NAME: "exit"},
    {GUI_NAME: "clear console", NAME: "clear_console"},
    )

hotkey = Struct("hotkey",
    BitStruct("combo",
        BitUEnum("modifier", GUI_NAME="", *modifier_enums, SIZE=4,
            TOOLTIP="Additional combination to hold when pressing the key"),
        BitUEnum("key", GUI_NAME="and", *hotkey_enums, SIZE=28),
        SIZE=4, ORIENT='h'
        ),
    UEnum32("method", *method_enums,
        TOOLTIP="Function to run when this hotkey is pressed")
    )

open_tag = Container("open_tag",
    Struct("header",
        UInt16("width"),
        UInt16("height"),
        SInt16("offset_x"),
        SInt16("offset_y"),
        Bool32("flags",
            "minimized",
            ),

        # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
        Pad(48 - 2*4 - 4*1),

        UInt16("def_id_len", VISIBLE=False, EDITABLE=False),
        UInt16("path_len", VISIBLE=False, EDITABLE=False),
        SIZE=64
        ),

    StrUtf8("def_id", SIZE=".header.def_id_len"),
    StrUtf8("path", SIZE=".header.path_len"),
    )

filepath = Container("filepath",
    UInt16("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len")
    )


config_header = Struct("header",
    LUEnum32("id", ('Bnla', 'alnB'), VISIBLE=False, DEFAULT='alnB'),
    UInt32("version", DEFAULT=1, VISIBLE=False, EDITABLE=False),
    Bool32("flags",
        {NAME: "sync_window_movement", TOOLTIP: flag_tooltips[0]},
        {NAME: "load_last_workspace", TOOLTIP: flag_tooltips[1]},
        {NAME: "log_output",    TOOLTIP: flag_tooltips[2]},
        {NAME: "log_tag_print", TOOLTIP: flag_tooltips[3]},
        {NAME: "debug_mode",    TOOLTIP: flag_tooltips[4]},
        DEFAULT=sum([1<<i for i in (0, 2, 3)])
        ),

    Bool32("handler_flags",
        {NAME: "backup_tags",   TOOLTIP: handler_flag_tooltips[0]},
        {NAME: "write_as_temp", TOOLTIP: handler_flag_tooltips[1]},
        {NAME: "allow_corrupt", TOOLTIP: handler_flag_tooltips[2]},
        {NAME: "integrity_test", TOOLTIP: handler_flag_tooltips[3]},
        DEFAULT=sum([1<<i for i in (0, 3)])
        ),

    Bool32("tag_window_flags",
        {NAME: "edit_uneditable", TOOLTIP: tag_window_flag_tooltips[0]},
        {NAME: "show_invisible",  TOOLTIP: tag_window_flag_tooltips[1]},
        #"row_row_fight_powuh",
        {NAME: "enforce_max", TOOLTIP: tag_window_flag_tooltips[2]},
        {NAME: "enforce_min", TOOLTIP: tag_window_flag_tooltips[3]},
        {NAME: "use_unit_scales", TOOLTIP: tag_window_flag_tooltips[4]},
        {NAME: "use_gui_names", TOOLTIP: tag_window_flag_tooltips[5]},

        {NAME: "blocks_start_hidden", TOOLTIP: tag_window_flag_tooltips[6]},
        {NAME: "show_comments", TOOLTIP: tag_window_flag_tooltips[7]},
        {NAME: "show_tooltips", TOOLTIP: tag_window_flag_tooltips[8]},
        {NAME: "show_sidetips", TOOLTIP: tag_window_flag_tooltips[9]},

        {NAME: "cap_window_size", TOOLTIP: tag_window_flag_tooltips[10]},
        {NAME: "dont_shrink_window", TOOLTIP: tag_window_flag_tooltips[11]},
        {NAME: "auto_resize_window", TOOLTIP: tag_window_flag_tooltips[12]},
        {NAME: "use_default_window_dimensions", TOOLTIP: tag_window_flag_tooltips[13]},

        {NAME: "show_all_bools", TOOLTIP: tag_window_flag_tooltips[14]},
        DEFAULT=sum([1<<i for i in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)])
        ),

    Bool32("block_print",
        "show_index",
        "show_name",
        "show_value",
        "show_type",
        "show_size",
        "show_offset",
        "show_node_id",
        "show_node_cls",
        "show_endian",
        "show_flags",
        "show_trueonly",
        "show_steptrees",
        "show_filepath",
        "show_unique",
        "show_binsize",
        "show_ramsize",


        ("show_all", 1<<31),
        DEFAULT=sum([1<<i for i in (
            0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 14, 15)]),
        TOOLTIP="Flags governing what is shown when a tag is printed."
        ),

    Timestamp("data_created", EDITABLE=False),
    Timestamp("data_modified", EDITABLE=False),

    UInt16("recent_tag_max", DEFAULT=20,
        TOOLTIP="Max number of files in the 'recent' menu."),
    UInt16("max_undos", DEFAULT=1000,
        TOOLTIP="Max number of undo/redo operations per tag window."),

    UInt16("print_precision", DEFAULT=8,
        TOOLTIP="Number of decimal places to round to when printing floats."),
    UInt16("print_indent", DEFAULT=NODE_PRINT_INDENT,
        TOOLTIP="Number of spaces to indent each print level."),

    UInt16("backup_count", DEFAULT=1,
        TOOLTIP="Max number of backups to make before overwriting the oldest"),
    SIZE=128
    )


style_header = Struct("header",
    UInt32("id", DEFAULT='lytS', VISIBLE=False),
    UInt32("version", DEFAULT=1, VISIBLE=False),
    Timestamp("data_created"),
    Timestamp("data_modified"),
    SIZE=128
    )

array_counts = Struct("array_counts",
    UInt32("open_tag_count", VISIBLE=False),
    UInt32("recent_tag_count", VISIBLE=False),
    UInt32("directory_path_count", VISIBLE=False),
    UInt32("widget_depth_count", VISIBLE=False),
    UInt32("color_count", VISIBLE=False),
    UInt32("hotkey_count", VISIBLE=False),
    UInt32("tag_window_hotkey_count", VISIBLE=False),
    SIZE=128, VISIBLE=False,
    COMMENT="You really shouldnt be messing with these."
    )

app_window = Struct("app_window",
    UInt16("app_width", DEFAULT=640, TOOLTIP=app_window_tooltips[0]),
    UInt16("app_height", DEFAULT=480, TOOLTIP=app_window_tooltips[1]),
    SInt16("app_offset_x", TOOLTIP=app_window_tooltips[2]),
    SInt16("app_offset_y", TOOLTIP=app_window_tooltips[3]),

    UInt16("window_menu_max_len", DEFAULT=15, TOOLTIP=app_window_tooltips[4]),

    UInt8("max_step_x", DEFAULT=4, TOOLTIP=app_window_tooltips[5]),
    UInt8("max_step_y", DEFAULT=8, TOOLTIP=app_window_tooltips[6]),

    UInt16("cascade_stride_x", DEFAULT=60, TOOLTIP=app_window_tooltips[7]),
    UInt16("tile_stride_x", DEFAULT=120, TOOLTIP=app_window_tooltips[8]),
    UInt16("tile_stride_y", DEFAULT=30, TOOLTIP=app_window_tooltips[9]),

    UInt16("default_tag_window_width", DEFAULT=480,
        TOOLTIP=app_window_tooltips[10]),
    UInt16("default_tag_window_height", DEFAULT=640,
        TOOLTIP=app_window_tooltips[11]),

    UInt16("scroll_increment_x", DEFAULT=50, TOOLTIP=app_window_tooltips[12]),
    UInt16("scroll_increment_y", DEFAULT=50, TOOLTIP=app_window_tooltips[13]),
    SIZE=128
    )

widgets = Container("widgets",
    UInt16("title_width", TOOLTIP=widget_tooltips[0]),
    UInt16("scroll_menu_width", TOOLTIP=widget_tooltips[1]),
    UInt16("enum_menu_width", TOOLTIP=widget_tooltips[2]),
    UInt16("min_entry_width", TOOLTIP=widget_tooltips[3]),

    UInt16("textbox_width", TOOLTIP=widget_tooltips[4]),
    UInt16("textbox_height", TOOLTIP=widget_tooltips[5]),

    UInt16("bool_frame_min_width", TOOLTIP=widget_tooltips[6]),
    UInt16("bool_frame_min_height", TOOLTIP=widget_tooltips[7]),
    UInt16("bool_frame_max_width", TOOLTIP=widget_tooltips[8]),
    UInt16("bool_frame_max_height", TOOLTIP=widget_tooltips[9]),

    UInt16("def_int_entry_width", TOOLTIP=widget_tooltips[10]),
    UInt16("def_float_entry_width", TOOLTIP=widget_tooltips[11]),
    UInt16("def_string_entry_width", TOOLTIP=widget_tooltips[12]),

    UInt16("max_int_entry_width", TOOLTIP=widget_tooltips[13]),
    UInt16("max_float_entry_width", TOOLTIP=widget_tooltips[14]),
    UInt16("max_string_entry_width", TOOLTIP=widget_tooltips[15]),

    UInt16("scroll_menu_max_width", TOOLTIP=widget_tooltips[16]),
    UInt16("scroll_menu_max_height", TOOLTIP=widget_tooltips[17]),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*18),

    QStruct("vertical_padx",
        UInt16("l", TOOLTIP=pad_str % ('left', 'vertic')),
        UInt16("r", TOOLTIP=pad_str % ('right', 'vertic')),
        ORIENT='h', TOOLTIP=pad_str % ('left/right', 'vertic')
        ),
    QStruct("vertical_pady",
        UInt16("t", TOOLTIP=pad_str % ('top', 'vertic')),
        UInt16("b", TOOLTIP=pad_str % ('bottom', 'vertic')),
        ORIENT='h', TOOLTIP=pad_str % ('top/bottom', 'vertic')
        ),
    QStruct("horizontal_padx",
        UInt16("l", TOOLTIP=pad_str % ('left', 'horizont')),
        UInt16("r", TOOLTIP=pad_str % ('right', 'horizont')),
        ORIENT='h', TOOLTIP=pad_str % ('left/right', 'horizont')
        ),
    QStruct("horizontal_pady",
        UInt16("t", TOOLTIP=pad_str % ('top', 'horizont')),
        UInt16("b", TOOLTIP=pad_str % ('bottom', 'horizont')),
        ORIENT='h', TOOLTIP=pad_str % ('top/bottom', 'horizont')
        ),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*2*4),

    Array("depths",
        SUB_STRUCT=UInt16("depth", TOOLTIP=depth_tooltip),
        SIZE="..array_counts.widget_depth_count",
        MAX=len(widget_depth_names), MIN=len(widget_depth_names),
        NAME_MAP=widget_depth_names
        )
    )

open_tags = Array("open_tags",
    SUB_STRUCT=open_tag, SIZE=".array_counts.open_tag_count", VISIBLE=False
    )

recent_tags = Array("recent_tags",
    SUB_STRUCT=filepath, SIZE=".array_counts.recent_tag_count", VISIBLE=False
    )

directory_paths = Array("directory_paths",
    SUB_STRUCT=filepath, SIZE=".array_counts.directory_path_count",
    NAME_MAP=("last_load_dir", "last_defs_dir", "last_imp_dir", "curr_dir",
              "tags_dir", "debug_log_path", "styles_dir",),
    VISIBLE=False
    )

colors = Array("colors",
    SUB_STRUCT=QStruct("color",
        UInt8('r'), UInt8('g'), UInt8('b'),
        ORIENT='h', WIDGET=ColorPickerFrame
        ),
    SIZE=".array_counts.color_count",
    MAX=len(color_names), MIN=len(color_names),
    NAME_MAP=color_names,
    )

hotkeys = Array(
    "hotkeys", SUB_STRUCT=hotkey, DYN_NAME_PATH='.method.enum_name',
    SIZE=".array_counts.hotkey_count", WIDGET=DynamicArrayFrame)

tag_window_hotkeys = Array(
    "tag_window_hotkeys", SUB_STRUCT=hotkey, DYN_NAME_PATH='.method.enum_name',
    SIZE=".array_counts.tag_window_hotkey_count", WIDGET=DynamicArrayFrame)

config_def = TagDef("binilla_config",
    config_header,
    array_counts,
    app_window,
    widgets,
    open_tags,
    recent_tags,
    directory_paths,
    colors,
    hotkeys,
    tag_window_hotkeys,
    ENDIAN='<', ext=".cfg",
    )

style_def = TagDef("binilla_style",
    style_header,
    array_counts,
    widgets,
    colors,
    ENDIAN='<', ext=".sty",
    )
