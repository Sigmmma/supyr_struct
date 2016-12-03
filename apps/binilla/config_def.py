from supyr_struct.defs.tag_def import TagDef
from supyr_struct.apps.binilla.constants import *
from supyr_struct.field_types import *

__all__ = (
    "hotkey", "open_tag", "filepath",
    "config_header", "style_header",
    "app_window", "widgets", "array_counts",
    "open_tags", "recent_tags", "directory_paths",
    "widget_depths", "colors", "hotkeys",
    "config_def", "style_def",
    )


hotkey = Container("hotkey",
    UInt8("combo_str_len", VISIBLE=False),
    StrAscii("combo", SIZE=".combo_str_len"),

    UInt8("method_str_len", VISIBLE=False),
    StrAscii("method", SIZE=".method_str_len"),
    )

open_tag = Container("open_tag",
    # NEED TO UPDATE THIS TO INCLUDE MORE INFORMATION, LIKE
    # WINDOW POSITION, DIMENSIONS, WHICH FIELDS ARE VISIBLE, ETC
    UInt32("def_id_len", VISIBLE=False),
    StrUtf8("def_id", SIZE=".def_id_len"),

    UInt32("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len"),
    )

filepath = Container("filepath",
    UInt32("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len")
    )



config_header = Struct("header",
    UInt32("id", DEFAULT='alnB'),
    UInt32("version", DEFAULT=1),
    Bool32("flags",
        "sync_window_movement",
        "load_last_workspace",
        "log_output",
        "show_debug",
        ),

    Bool32("handler_flags",
        "backup_tags",
        "write_as_temp",
        "allow_corrupt",
        "integrity_test",
        ),

    Bool32("tag_window_flags",
        "show_invisible",
        "edit_uneditable",
        #"row_row_fight_powuh",
        "enforce_max",
        "enforce_min",
        "use_unit_scales",
        "use_gui_names",

        "cap_window_size",
        "dont_shrink_window",
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
        "show_all",
        ),

    Timestamp("data_created"),
    Timestamp("data_modified"),

    UInt16("recent_tag_max"),
    UInt16("undo_level_max"),

    UInt16("print_precision"),
    UInt16("print_indent"),
    SIZE=128
    )


style_header = Struct("header",
    UInt32("id", DEFAULT='lytS'),
    UInt32("version", DEFAULT=1),
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
    SIZE=128
    )

app_window = Struct("app_window",
    UInt16("app_width"),
    UInt16("app_height"),
    SInt16("app_offset_x"),
    SInt16("app_offset_y"),

    UInt16("window_menu_max_len"),

    UInt8("max_step_x"),
    UInt8("max_step_y"),

    UInt16("cascade_stride_x"),
    UInt16("tile_stride_x"),
    UInt16("tile_stride_y"),

    UInt16("default_tag_window_width"),
    UInt16("default_tag_window_height"),

    SIZE=128
    )

widgets = Struct("widgets",
    UInt16("scroll_menu_size"),
    UInt16("title_width"),

    QStruct("vertical_pad_x",   UInt16("l"), UInt16("r"), ORIENT='h'),
    QStruct("vertical_pad_y",   UInt16("t"), UInt16("b"), ORIENT='h'),
    QStruct("horizontal_pad_x", UInt16("l"), UInt16("r"), ORIENT='h'),
    QStruct("horizontal_pad_y", UInt16("t"), UInt16("b"), ORIENT='h'),
    SIZE=128
    )

open_tags = Array("open_tags",
    SUB_STRUCT=open_tag, SIZE=".array_counts.open_tag_count"
    )

recent_tags = Array("recent_tags",
    SUB_STRUCT=filepath, SIZE=".array_counts.recent_tag_count"
    )

directory_paths = Array("directory_paths",
    SUB_STRUCT=filepath, SIZE=".array_counts.directory_path_count", MAX=4,
    NAME_MAP=("last_load_dir", "last_defs_dir", "last_imp_dir", "curr_dir",
              "debug_log_path", )
    )

widget_depths = Array("widget_depths",
    SUB_STRUCT=UInt16("depth"),
    SIZE=".array_counts.widget_depth_count", MAX=5,
    NAME_MAP=("frame", "button", "entry", "listbox", "comment")
    )

colors = Array("colors",
    SUB_STRUCT=StrHex('color', SIZE=3),
    SIZE=".array_counts.color_count", MAX=12,
    NAME_MAP=(
        "io_fg", "io_bg", "default_bg", "comment_bg", "frame_bg",
        "text_normal", "text_disabled", "text_selected", "text_highlighted",
        "enum_normal", "enum_disabled", "enum_selected",
        ),
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
    widget_depths,
    colors,
    hotkeys,
    tag_window_hotkeys,
    ENDIAN='<', ext=".cfg",
    )

style_def = TagDef("binilla_style",
    style_header,
    array_counts,
    app_window,
    widgets,
    widget_depths,
    colors,
    hotkeys,
    tag_window_hotkeys,
    ENDIAN='<', ext=".sty",
    )
