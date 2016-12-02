from supyr_struct.defs.tag_def import TagDef
from supyr_struct.apps.binilla.constants import *
from supyr_struct.field_types import *

__all__ = (
    "hotkey", "last_open_filepath", "filepath",
    "header", "app_window", "widgets",
    "last_open_files", "recent_files", "directory_paths",
    "widget_depths", "colors", "hotkeys",
    "config_def",
    )


hotkey = Container("hotkey",
    UInt8("combo_str_len", VISIBLE=False),
    StrAscii("combo", SIZE=".combo_str_len"),

    UInt8("method_str_len", VISIBLE=False),
    StrAscii("method", SIZE=".method_str_len"),
    )

last_open_filepath = Container("last_open_filepath",
    UInt32("def_id_len", VISIBLE=False),
    StrUtf8("def_id", SIZE=".def_id_len"),

    UInt32("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len"),
    )

filepath = Container("filepath",
    UInt32("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len")
    )



header = Struct("header",
    UInt32("id", DEFAULT='alnB'),
    UInt32("config_version", DEFAULT=1),
    BigBool("flags",
        "backup_tags",
        "write_as_temp",
        "sync_window_movement",
        SIZE=8
        ),

    UInt32("last_open_file_count", VISIBLE=False),
    UInt32("recent_file_count", VISIBLE=False),
    UInt32("directory_path_count", VISIBLE=False),
    UInt32("widget_depth_count", VISIBLE=False),
    UInt32("color_count", VISIBLE=False),
    UInt32("hotkey_count", VISIBLE=False),

    UInt16("recent_file_max"),
    UInt16("undo_level_max"),
    SIZE=256
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

last_open_files = Array("last_open_files",
    SUB_STRUCT=last_open_filepath, SIZE=".header.last_open_file_count"
    )

recent_files = Array("recent_files",
    SUB_STRUCT=filepath, SIZE=".header.recent_file_count"
    )

directory_paths = Array("directory_paths",
    SUB_STRUCT=filepath, SIZE=".header.directory_path_count", MAX=4,
    NAME_MAP=("last_load", "last_defs", "last_imp", "curr")
    )

widget_depths = Array("widget_depths",
    SUB_STRUCT=UInt16("depth"),
    SIZE=".header.widget_depth_count", MAX=5,
    NAME_MAP=("frame", "button", "entry", "listbox", "comment")
    )

colors = Array("colors",
    SUB_STRUCT=StrHex('color', SIZE=3),
    SIZE=".header.color_count", MAX=12,
    NAME_MAP=(
        "io_fg", "io_bg", "default_bg", "comment_bg", "frame_bg",
        "text_normal", "text_disabled", "text_selected", "text_highlighted",
        "enum_normal", "enum_disabled", "enum_selected",
        ),
    )

hotkeys = Array("hotkeys", SUB_STRUCT=hotkey, SIZE=".header.hotkey_count")

def get(): return config_def

config_def = TagDef("binilla_config_file",
    header,
    app_window,
    widgets,
    last_open_files,
    recent_files,
    directory_paths,
    widget_depths,
    colors,
    hotkeys,

    ENDIAN='<', ext=".cfg",
    )
