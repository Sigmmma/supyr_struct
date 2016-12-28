from supyr_struct.defs.tag_def import TagDef
from supyr_struct.apps.binilla.field_widgets import *
from supyr_struct.apps.binilla.constants import *
from supyr_struct.field_types import *

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
    {GUI_NAME: "undo", NAME: "undo_edit"},
    {GUI_NAME: "redo", NAME: "redo_edit"},
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
        "sync_window_movement",
        "load_last_workspace",
        "log_output",
        "log_tag_print",
        "debug_mode",
        DEFAULT=sum([1<<i for i in (0, 2, 3)])
        ),

    Bool32("handler_flags",
        "backup_tags",
        "write_as_temp",
        "allow_corrupt",
        "integrity_test",
        DEFAULT=sum([1<<i for i in (0, 3)])
        ),

    Bool32("tag_window_flags",
        "edit_uneditable",
        "show_invisible",
        #"row_row_fight_powuh",
        "enforce_max",
        "enforce_min",
        "use_unit_scales",
        "use_gui_names",

        "blocks_start_hidden",
        "show_comments",
        "show_tooltips",
        "show_sidetips",

        "cap_window_size",
        "dont_shrink_window",
        "auto_resize_window",
        "use_default_window_dimensions",

        "show_all_bools",
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
            0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 14, 15)])
        ),

    Timestamp("data_created", EDITABLE=False),
    Timestamp("data_modified", EDITABLE=False),

    UInt16("recent_tag_max", DEFAULT=20),
    UInt16("max_undos", DEFAULT=1000),

    UInt16("print_precision", DEFAULT=8),
    UInt16("print_indent", DEFAULT=NODE_PRINT_INDENT),

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
    SIZE=128, VISIBLE=False
    )

app_window = Struct("app_window",
    UInt16("app_width", DEFAULT=640),
    UInt16("app_height", DEFAULT=480),
    SInt16("app_offset_x"),
    SInt16("app_offset_y"),

    UInt16("window_menu_max_len", DEFAULT=15),

    UInt8("max_step_x", DEFAULT=4),
    UInt8("max_step_y", DEFAULT=8),

    UInt16("cascade_stride_x", DEFAULT=60),
    UInt16("tile_stride_x", DEFAULT=120),
    UInt16("tile_stride_y", DEFAULT=30),

    UInt16("default_tag_window_width", DEFAULT=480),
    UInt16("default_tag_window_height", DEFAULT=640),

    UInt16("scroll_increment_x", DEFAULT=50),
    UInt16("scroll_increment_y", DEFAULT=50),
    SIZE=128
    )

widgets = Container("widgets",
    UInt16("title_width"),
    UInt16("scroll_menu_width"),
    UInt16("enum_menu_width"),
    UInt16("min_entry_width"),

    UInt16("textbox_width"),
    UInt16("textbox_height"),

    UInt16("bool_frame_min_width"),
    UInt16("bool_frame_min_height"),
    UInt16("bool_frame_max_width"),
    UInt16("bool_frame_max_height"),

    UInt16("def_int_entry_width"),
    UInt16("def_float_entry_width"),
    UInt16("def_string_entry_width"),

    UInt16("max_int_entry_width"),
    UInt16("max_float_entry_width"),
    UInt16("max_string_entry_width"),

    UInt16("scroll_menu_max_width"),
    UInt16("scroll_menu_max_height"),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*18),

    QStruct("vertical_padx",   UInt16("l"), UInt16("r"), ORIENT='h'),
    QStruct("vertical_pady",   UInt16("t"), UInt16("b"), ORIENT='h'),
    QStruct("horizontal_padx", UInt16("l"), UInt16("r"), ORIENT='h'),
    QStruct("horizontal_pady", UInt16("t"), UInt16("b"), ORIENT='h'),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*2*4),

    Array("depths",
        SUB_STRUCT=UInt16("depth"),
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

hotkeys = Array("hotkeys", SUB_STRUCT=hotkey, SIZE=".array_counts.hotkey_count")

tag_window_hotkeys = Array("tag_window_hotkeys", SUB_STRUCT=hotkey,
                           SIZE=".array_counts.tag_window_hotkey_count")

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
