import gc
import os
import sys
import tkinter as tk

from copy import deepcopy
from datetime import datetime
from io import StringIO
from time import time, sleep
from os.path import basename, dirname, exists
from tkinter.font import Font
from tkinter.constants import *
from tkinter.filedialog import askopenfilenames, askopenfilename,\
     askdirectory, asksaveasfilename
from traceback import format_exc

# load the binilla constants so they are injected before any defs are loaded
from . import constants as s_c
s_c.inject()

from . import editor_constants as e_c
from .tag_window import *
from .config_def import *
from .widget_picker import *
from .widgets import BinillaWidget
from ..handler import Handler

this_curr_dir = os.path.abspath(os.curdir)

default_config_path = dirname(__file__) + '%sbinilla.cfg' % s_c.PATHDIV

default_hotkeys = {
    '<Control-w>': 'close_selected_window',
    '<Control-o>': 'load_tags',
    '<Control-n>': 'new_tag',
    '<Control-s>': 'save_tag',
    '<Control-f>': 'show_defs',
    '<Control-p>': 'print_tag',

    '<Control-BackSpace>': 'clear_console',
    '<Control-backslash>': 'cascade',
    '<Control-Shift-bar>': 'tile_vertical',
    '<Control-Shift-underscore>': 'tile_horizontal',

    '<Alt-m>': 'minimize_all',
    '<Alt-r>': 'restore_all',
    '<Alt-w>': 'show_window_manager',
    '<Alt-c>': 'show_config_file',
    '<Alt-o>': 'load_tag_as',
    '<Alt-s>': 'save_tag_as',
    '<Alt-F4>': 'exit',

    '<Alt-Control-c>': 'apply_config',

    '<Control-Shift-s>': 'save_all',
    }


default_tag_window_hotkeys = {
    '<Control-z>': 'undo_edit',
    '<Control-y>': 'redo_edit',
    '<MouseWheel>': 'mousewheel_scroll_y',
    '<Shift-MouseWheel>': 'mousewheel_scroll_x',
    }



class IORedirecter(StringIO):
    # Text widget to output text to
    text_out = None
    log_file = None
    edit_log = None

    def __init__(self, text_out, *args, **kwargs):
        self.log_file = kwargs.pop('log_file', None)
        self.edit_log = kwargs.pop('edit_log', None)
        StringIO.__init__(self, *args, **kwargs)
        self.text_out = text_out

    def write(self, string):
        if self.edit_log and self.log_file is not None:
            try:
                self.log_file.write(string)
            except Exception:
                pass
        self.text_out.config(state=NORMAL)
        self.text_out.insert(END, string)
        self.text_out.see(END)
        self.text_out.config(state=DISABLED)


class Binilla(tk.Tk, BinillaWidget):
    # the tag of the currently in-focus TagWindow
    selected_tag = None
    # the Handler for managing loaded tags
    handler = None

    # a window that displays and allows selecting loaded definitions
    def_selector_window = None
    # a window that allows you to select a TagWindow from all open ones
    tag_window_manager = None

    # the default WidgetPicker instance to use for selecting widgets
    widget_picker = WidgetPicker()
    def_tag_window_cls = TagWindow

    # dict of open TagWindow instances. keys are the ids of each of the windows
    tag_windows = None
    # map of the id of each tag to the id of the window displaying it
    tag_id_to_window_id = None

    '''Directories'''
    curr_dir = this_curr_dir
    last_load_dir = curr_dir
    last_defs_dir = curr_dir
    last_imp_dir  = curr_dir

    recent_tag_max = 20
    recent_tagpaths = ()

    '''Miscellaneous properties'''
    _initialized = False
    app_name = "Binilla"  # the name of the app(used in window title)
    version = '0.3'
    log_filename = 'binilla.log'
    debug = 0
    untitled_num = 0  # when creating a new, untitled tag, this is its name
    undo_level_max = 1000

    '''Config properties'''
    style_def = style_def
    config_def = config_def
    config_version = 1
    config_path = default_config_path
    config_window = None
    # the tag that holds all the config settings for this application
    config_file = None

    '''Window properties'''
    # When tags are opened they are tiled, first vertically, then horizontally.
    # curr_step_y is incremented for each tag opened till it reaches max_step_y
    # At that point it resets to 0 and increments curr_step_x by 1.
    # If curr_step_x reaches max_step_x it will reset to 0. The position of an
    # opened TagWindow is set relative to the application's top left corner.
    # The x offset is shifted right by curr_step_x*tile_stride_x and
    # the y offset is shifted down  by curr_step_y*tile_stride_y.
    max_step_x = 4
    max_step_y = 8

    curr_step_x = 0
    curr_step_y = 0

    cascade_stride_x = 60
    tile_stride_x = 120
    tile_stride_y = 30

    default_tag_window_width = 480
    default_tag_window_height = 640

    window_menu_max_len = 15

    app_width = 640
    app_height = 480
    app_offset_x = 0
    app_offset_y = 0

    terminal_out = ''

    sync_window_movement = True  # Whether or not to sync the movement of
    #                              the TagWindow instances with the app.

    # a mapping of hotkey bindings to method names
    curr_hotkeys = None
    curr_tag_window_hotkeys = None

    def __init__(self, *args, **kwargs):
        for s in ('curr_dir', 'config_version', 'window_menu_max_len',
                  'app_width', 'app_height', 'app_offset_x', 'app_offset_y'):
            if s in kwargs:
                object.__setattr__(self, s, kwargs.pop(s))

        self.widget_picker = kwargs.pop('widget_picker', self.widget_picker)
        self.debug = kwargs.pop('debug', self.debug)
        if 'handler' in kwargs:
            self.handler = kwargs.pop('handler')
        else:
            self.handler = Handler(debug=self.debug)

        self.recent_tagpaths = []
        if self.curr_hotkeys is None:
            self.curr_hotkeys = {}
        if self.curr_tag_window_hotkeys is None:
            self.curr_tag_window_hotkeys = {}

        if self.config_file is not None:
            pass
        elif exists(self.config_path):
            # load the config file
            try:
                self.load_config()
            except Exception:
                print(format_exc())
                self.make_config()
        else:
            # make a config file
            self.make_config()

        if not exists(self.curr_dir):
            self.curr_dir = this_curr_dir
            try:
                self.config_file.data.directory_paths.curr_dir.path = curr_dir
            except Exception:
                pass

        self.app_name = kwargs.pop('app_name', self.app_name)
        self.app_name = str(kwargs.pop('version', self.app_name))

        if self.handler is not None:
            self.handler.log_filename = self.log_filename

        tk.Tk.__init__(self, *args, **kwargs)
        self.tag_windows = {}
        self.tag_id_to_window_id = {}

        #fonts
        self.fixed_font = Font(family="Courier", size=8)
        self.container_title_font = Font(
            family="Courier", size=10, weight='bold')
        self.comment_font = Font(family="Courier", size=9)
        
        self.title('%s v%s' % (self.app_name, self.version))
        self.geometry("%sx%s+%s+%s" % (self.app_width, self.app_height,
                                       self.app_offset_x, self.app_offset_y))
        self.minsize(width=200, height=50)
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.bind('<Configure>', self.sync_tag_window_pos)

        self.bind_hotkeys()

        ######################################################################
        ######################################################################
        # MAKE METHODS FOR CREATING/DESTROYING MENUS SO THEY CAN BE CUSTOMIZED
        # This includes creating a system to manage the menus and keep track
        # of which ones exist, their order on the menu bar, their names, etc.
        # Once that is done, replace the below code with code that uses them.
        ######################################################################
        ######################################################################

        #create the main menu and add its commands
        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0)
        self.edit_menu = tk.Menu(self.main_menu, tearoff=0)
        self.settings_menu = tk.Menu(self.main_menu, tearoff=0)
        self.debug_menu   = tk.Menu(self.main_menu, tearoff=0)
        self.windows_menu = tk.Menu(
            self.main_menu, tearoff=0, postcommand=self.generate_windows_menu)
        self.recent_tags_menu = tk.Menu(
            self.main_menu, tearoff=0,
            postcommand=self.generate_recent_tag_menu)

        self.config(menu=self.main_menu)

        #add cascades and commands to the main_menu
        self.main_menu.add_cascade(label="File",    menu=self.file_menu)
        #self.main_menu.add_cascade(label="Edit",   menu=self.edit_menu)
        self.main_menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.main_menu.add_cascade(label="Windows", menu=self.windows_menu)
        #self.main_menu.add_command(label="Help")
        #self.main_menu.add_command(label="About")
        try:
            show_debug = self.config_file.data.header.flags.show_debug
        except Exception:
            show_debug = True
        finally:
            if show_debug:
                self.main_menu.add_cascade(label="Debug", menu=self.debug_menu)

        #add the commands to the file_menu
        fm_ac = self.file_menu.add_command
        fm_ac(label="New",        command=self.new_tag)
        fm_ac(label="Open",       command=self.load_tags)
        self.file_menu.add_cascade(label="Recent tags     ",
                                   menu=self.recent_tags_menu)
        fm_ac(label="Open as...", command=self.load_tag_as)
        fm_ac(label="Close", command=self.close_selected_window)
        self.file_menu.add_separator()
        fm_ac(label="Save",       command=self.save_tag)
        fm_ac(label="Save as...", command=self.save_tag_as)
        fm_ac(label="Save all",   command=self.save_all)
        self.file_menu.add_separator()
        fm_ac(label="Exit",       command=self.exit)

        #add the commands to the settings_menu
        self.settings_menu.add_command(
            label="Load definitions", command=self.select_defs)
        self.settings_menu.add_command(
            label="Show definitions", command=self.show_defs)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Apply config", command=self.apply_config)
        self.settings_menu.add_command(
            label="Edit config", command=self.show_config_file)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Load style", command=self.apply_style)
        self.settings_menu.add_command(
            label="Save current style", command=self.make_style)

        self.debug_menu.add_command(label="Print tag", command=self.print_tag)
        self.debug_menu.add_command(label="Clear console",
                                    command=self.clear_console)
        
        # make the canvas for anything in the main window
        self.root_frame = tk.Frame(self, bd=3, highlightthickness=0,
                                   relief=SUNKEN)
        self.root_frame.pack(fill=BOTH, side=LEFT, expand=True)

        # make the canvas for the console output
        self.io_frame = tk.Frame(self.root_frame, highlightthickness=0)
        self.io_text = tk.Text(self.io_frame,
                               font=self.fixed_font, state=DISABLED,
                               fg=self.io_fg_color, bg=self.io_bg_color)
        self.io_scroll_y = tk.Scrollbar(self.io_frame, orient=VERTICAL)

        self.io_scroll_y.config(command=self.io_text.yview)
        self.io_text.config(yscrollcommand=self.io_scroll_y.set)

        self.io_scroll_y.pack(fill=Y, side=RIGHT)
        self.io_text.pack(fill=BOTH, expand=True)
        self.io_frame.pack(fill=BOTH, expand=True)

        # make the io redirector and redirect sys.stdout to it
        self.orig_stdout = sys.stdout

        flags = self.config_file.data.header.flags
        log_file = None
        if flags.log_output:
            curr_dir = self.curr_dir
            if not curr_dir.endswith(s_c.PATHDIV):
                curr_dir += s_c.PATHDIV

            self.log_file = open(curr_dir + self.log_filename, 'a+')

            try:
                # write a timestamp to the file
                time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                self.log_file.write("\n%s%s%s\n" %
                                    ("-"*30, time, "-"*(50-len(time))))
            except Exception:
                pass

        self.terminal_out = sys.stdout = IORedirecter(
            self.io_text, edit_log=flags.log_output, log_file=self.log_file)
        self._initialized = True

        self.update_window_settings()

    def bind_hotkeys(self, new_hotkeys=None):
        '''
        Binds the given hotkeys to the given methods of this class.
        Class methods must be the name of each method as a string.
        '''
        if new_hotkeys is None:
            new_hotkeys = {}
            for hotkey in self.config_file.data.hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None:
                    continue
                new_hotkeys[combo] = hotkey.method.enum_name
        assert isinstance(new_hotkeys, dict)

        # unbind any old hotkeys
        self.unbind_hotkeys()
        self.curr_hotkeys = new_hotkeys

        for hotkey, func_name in new_hotkeys.items():
            try:
                self.bind_all(hotkey, self.__getattribute__(func_name))
            except Exception:
                print(format_exc())

    def cascade(self, e=None):
        windows = self.tag_windows
        sel_tag = self.selected_tag

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.cascade_stride_x
        y_stride = self.tile_stride_y
        self.selected_tag = None
        
        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont cascade hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0
                self.curr_step_x += 1
            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0

            self.place_window_relative(
                window, (self.curr_step_x*x_stride +
                         self.curr_step_y*(x_stride//2) + 5),
                self.curr_step_y*y_stride + 50)
            self.curr_step_y += 1
            window.update_idletasks()

            if sel_tag is None or window.tag is not sel_tag:
                self.select_tag_window(window)

    def close_selected_window(self, e=None):
        if self.selected_tag is None:
            return

        # close the window and make sure the tag is deleted
        self.delete_tag(self.selected_tag)

        # select the next TagWindow
        try:
            for w in self.tag_windows.values():
                if hasattr(w, 'tag') and w.state() != 'withdrawn':
                    self.select_tag_window(w)
                    self.update()
                    return
        except Exception:
            pass

    def clear_console(self, e=None):
        try:
            self.io_text.config(state=NORMAL)
            self.io_text.delete('1.0', END)
            self.io_text.config(state=DISABLED)
        except Exception:
            print(format_exc())

    def delete_tag(self, tag, destroy_window=True):
        try:
            tid = id(tag)
            def_id = tag.def_id
            path = tag.filepath
            tid_to_wid = self.tag_id_to_window_id

            if tid in tid_to_wid:
                wid = tid_to_wid[tid]
                t_window = self.tag_windows[wid]
                del tid_to_wid[tid]
                del self.tag_windows[wid]

                if destroy_window:
                    t_window.destroy()

            if self.selected_tag is tag:
                self.selected_tag = None

            gc.collect()
        except Exception:
            print(format_exc())

    def exit(self, e=None):
        '''Exits the program.'''
        sys.stdout = self.orig_stdout
        try:
            self.update_config()
            self.save_config()
        except Exception:
            print(format_exc())
        try:
            self.log_file.close()
        except Exception:
            pass
        self.destroy()  # wont close if a listener prompt is open without this
        raise SystemExit(0)

    def generate_windows_menu(self):
        menu = self.windows_menu
        menu.delete(0, "end")  # clear the menu

        #add the commands to the windows_menu
        menu.add_command(label="Minimize all", command=self.minimize_all)
        menu.add_command(label="Restore all", command=self.restore_all)
        menu.add_command(label="Toggle movement sync", command=self.toggle_sync)
        menu.add_separator()
        menu.add_command(label="Cascade", command=self.cascade)
        menu.add_command(label="Tile vertical", command=self.tile_vertical)
        menu.add_command(label="Tile horizontal", command=self.tile_horizontal)

        i = 0
        max_len = self.window_menu_max_len

        if not self.tag_windows:
            return

        menu.add_separator()

        # store the windows by label
        windows_by_label = {}
        for w in self.tag_windows.values():
            windows_by_label["[%s] %s" % (w.tag.def_id, w.title())] = w

        for label in sorted(windows_by_label):
            w = windows_by_label[label]
            if i >= max_len:
                menu.add_separator()
                menu.add_command(label="Window manager",
                                 command=self.show_window_manager)
                break
            try:
                menu.add_command(
                    label=label, command=lambda w=w: self.select_tag_window(w))
                i += 1
            except Exception:
                print(format_exc())

    def generate_recent_tag_menu(self):
        menu = self.recent_tags_menu
        menu.delete(0, "end")  # clear the menu

        i = 1
        menu.add_command(label="Clear recently opened tags",
                         command=lambda self=self:
                         self.recent_tagpaths.__delitem__(
                             slice(None, None, None))
                         )
        menu.add_separator()
        for tagpath in reversed(self.recent_tagpaths):
            try:
                menu.add_command(
                    label="%s  %s" % (i, tagpath),
                    command=lambda s=tagpath: self.load_tags(s))
                i += 1
            except Exception:
                print(format_exc())

    def apply_config(self, e=None):
        config_data = self.config_file.data
        header = config_data.header

        open_tags = config_data.open_tags
        recent_tags = config_data.recent_tags
        dir_paths = config_data.directory_paths

        self.sync_window_movement = header.flags.sync_window_movement

        __osa__ = object.__setattr__
        __tsa__ = type.__setattr__

        self.recent_tagpaths = paths = []

        for tagpath in recent_tags:
            paths.append(tagpath.path)

        for s in ('recent_tag_max', 'undo_level_max'):
            __osa__(self, s, header[s])

        for s in ('last_load_dir', 'last_defs_dir', 'last_imp_dir',
                  'curr_dir')[:len(dir_paths)]:
            __osa__(self, s, dir_paths[s].path)

        self.handler.tagsdir = dir_paths.tags_dir.path

        self.log_filename = basename(dir_paths.debug_log_path.path)

        self.apply_style(style_file=self.config_file)

    def load_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path
        assert exists(filepath)

        # load the config file
        self.config_file = self.config_def.build(filepath=filepath)
        self.apply_config()

        hotkeys = self.config_file.data.hotkeys
        tag_window_hotkeys = self.config_file.data.tag_window_hotkeys

        for hotkey in hotkeys:
            combo = make_hotkey_string(hotkey)
            if combo is None:
                continue
            self.curr_hotkeys[combo] = hotkey.method.enum_name

        for hotkey in tag_window_hotkeys:
            combo = make_hotkey_string(hotkey)
            if combo is None:
                continue
            self.curr_tag_window_hotkeys[combo] = hotkey.method.enum_name

    def apply_style(self, filepath=None, style_file=None):
        if isinstance(filepath, tk.Event):
            filepath = None
        if style_file is None:
            if filepath is None:
                filepath = askopenfilename(
                    initialdir=self.last_load_dir,
                    title="Select style to load",
                    filetypes=(("binilla_style", "*.sty"), ('All', '*')))

            if not filepath:
                return

            assert exists(filepath)
            self.last_load_dir = dirname(filepath)
            style_file = self.style_def.build(filepath=filepath)

        assert hasattr(style_file, 'data')

        style_data = style_file.data

        header = style_data.header
        app_window = style_data.app_window
        widgets = style_data.widgets

        widget_depths = style_data.widget_depths
        colors = style_data.colors

        __osa__ = object.__setattr__
        __tsa__ = type.__setattr__

        for s in app_window.NAME_MAP.keys():
            __osa__(self, s, app_window[s])

        for s in ('title_width', 'scroll_menu_width', 'enum_menu_width'):
            __tsa__(BinillaWidget, s, widgets[s])

        for s in ('vertical_padx', 'vertical_pady',
                  'horizontal_padx', 'horizontal_pady'):
            __tsa__(BinillaWidget, s, tuple(widgets[s]))

        for s in widget_depth_names[:len(widget_depths)]:
            __tsa__(BinillaWidget, s + '_depth', widget_depths[s])

        for s in color_names[:len(colors)]:
            # it has to be a tuple for some reason
            __tsa__(BinillaWidget, s + '_color',
                    '#%02x%02x%02x' % tuple(colors[s]))

        if self._initialized:
            self.update_config()

    def make_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path

        # create the config file from scratch
        self.config_file = self.config_def.build()
        self.config_file.filepath = filepath

        data = self.config_file.data

        # make sure these have as many entries as they're supposed to
        for block in (data.directory_paths, data.widget_depths, data.colors):
            block.extend(len(block.NAME_MAP))

        self.curr_hotkeys = dict(default_hotkeys)
        self.curr_tag_window_hotkeys = dict(default_tag_window_hotkeys)

        self.update_config()

        c_hotkeys = data.hotkeys
        c_tag_window_hotkeys = data.tag_window_hotkeys

        for k_set, b in ((default_hotkeys, c_hotkeys),
                         (default_tag_window_hotkeys, c_tag_window_hotkeys)):
            default_keys = k_set
            hotkeys = b
            for combo, method in k_set.items():
                hotkeys.append()
                keys = hotkeys[-1].combo

                modifier, key = read_hotkey_string(combo)
                keys.modifier.set_to(modifier)
                keys.key.set_to(key)

                hotkeys[-1].method.set_to(method)

    def make_style(self):
        # create the style file from scratch
        filepath = asksaveasfilename(
            initialdir=self.last_load_dir, defaultextension='.sty',
            title="Save style as...",
            filetypes=(("binilla style", "*.sty"), ('All', '*')))

        if filepath:
            self.last_load_dir = dirname(filepath)
            style_file = self.style_def.build()
            style_file.filepath = filepath

            style_file.data.widget_depths.extend(5)
            style_file.data.colors.extend(12)

            self.update_style(style_file)
            style_file.serialize(temp=False, backup=False)

    def toggle_sync(self):
        self.sync_window_movement = not self.sync_window_movement
        flags = self.config_file.data.header.flags
        flags.sync_window_movement = not flags.sync_window_movement

    def get_tag(self, def_id, filepath):
        '''
        Returns the tag from the handler under the given def_id and filepath.
        '''
        filepath = self.handler.sanitize_path(filepath)
        return self.handler.tags.get(def_id, {}).get(filepath)

    def get_tag_window_by_tag(self, tag):
        return self.tag_windows[self.tag_id_to_window_id[id(tag)]]

    def get_is_tag_loaded(self, filepath, def_id=None):
        if def_id is None:
            def_id = self.handler.get_def_id(filepath)
        return bool(self.get_tag(def_id, filepath))

    def load_tags(self, filepaths=None, def_id=None):
        '''Prompts the user for a tag(s) to load and loads it.'''
        if isinstance(filepaths, tk.Event):
            filepaths = None
        if filepaths is None:
            filetypes = [('All', '*')]
            defs = self.handler.defs
            for id in sorted(defs.keys()):
                filetypes.append((id, defs[id].ext))
            filepaths = askopenfilenames(initialdir=self.last_load_dir,
                                         filetypes=filetypes,
                                         title="Select the tag to load")
            if not filepaths:
                return

        if isinstance(filepaths, str):
            filepaths = (filepaths,)

        self.last_load_dir = dirname(filepaths[-1])
        w = None

        windows = []
        tagsdir = self.handler.tagsdir
        if not tagsdir.endswith(s_c.PATHDIV):
            tagsdir += s_c.PATHDIV

        sani = self.handler.sanitize_path

        for path in filepaths:
            path = sani(path)
            if self.get_is_tag_loaded(path):
                print('%s is already loaded' % path)
                continue
            elif path and not exists(path):
                print('%s does not exist' % path)
                continue

            #try to load the new tags
            try:
                handler_flags = self.config_file.data.header.handler_flags
                new_tag = self.handler.load_tag(
                    path, def_id, allow_corrupt=handler_flags.allow_corrupt)
                self.handler.tags
            except Exception:
                if self.handler.debug:
                    print(format_exc())
                print("Could not load tag '%s'" % path)
                continue

            if path:
                recent = self.recent_tagpaths
                while path in recent:
                    recent.pop(recent.index(path))

                while len(recent) >= self.recent_tag_max:
                    recent.pop(0)
                recent.append(new_tag.filepath)
            else:
                # if the path is blank(new tag), give it a unique name
                tags_coll = self.handler.tags[new_tag.def_id]
                # remove the tag from the handlers tag collection
                tags_coll.pop(new_tag.filepath, None)

                ext = str(new_tag.ext)
                new_tag.filepath = '%suntitled%s%s' % (
                    tagsdir, self.untitled_num, ext)
                # re-index the tag under its new filepath
                tags_coll[new_tag.filepath] = new_tag
                self.untitled_num += 1

            try:
                #build the window
                w = self.make_tag_window(new_tag, focus=False)
                windows.append(w)
            except Exception:
                print(format_exc())
                raise IOError("Could not display tag '%s'." % path)

        self.select_tag_window(w)
        return windows

    def load_tag_as(self, e=None):
        '''Prompts the user for a tag to load and loads it.'''
        if self.def_selector_window:
            return
        
        filetypes = [('All', '*')]
        defs = self.handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))
        fp = askopenfilename(initialdir=self.last_load_dir,
                             filetypes=filetypes,
                             title="Select the tag to load")

        if not fp:
            return

        self.last_load_dir = dirname(fp)
        dsw = DefSelectorWindow(
            self, title="Select a definition to use", action=lambda def_id:
            self.load_tags(filepaths=fp, def_id=def_id))
        self.def_selector_window = dsw
        self.place_window_relative(self.def_selector_window, 30, 50)

    def place_window_relative(self, window, x=0, y=0):
        # calculate x and y coordinates for this window
        x_base, y_base = self.winfo_x(), self.winfo_y()
        w, h = window.geometry().split('+')[0].split('x')[:2]
        if w == h and w == '1':
            w = window.winfo_reqwidth()
            h = window.winfo_reqheight()
        window.geometry('%sx%s+%s+%s' % (w, h, x + x_base, y + y_base))

    def make_tag_window(self, tag, *, focus=True, window_cls=None):
        '''
        Creates and returns a TagWindow instance for the supplied
        tag and sets the current focus to the new TagWindow.
        '''
        if len(self.tag_windows) == 0:
            self.curr_step_y = self.curr_step_x = 0
        if window_cls is None:
            window_cls = self.def_tag_window_cls
        window = window_cls(self, tag, app_root=self, handler=self.handler)

        # reposition the window
        if self.curr_step_y > self.max_step_y:
            self.curr_step_y = 0
            self.curr_step_x += 1
        if self.curr_step_x > self.max_step_x:
            self.curr_step_x = 0

        self.place_window_relative(
            window, self.curr_step_x*self.tile_stride_x + 5,
            self.curr_step_y*self.tile_stride_y + 50)
        self.curr_step_y += 1
        window.geometry("%sx%s" % (
            self.default_tag_window_width, self.default_tag_window_height))

        self.tag_windows[id(window)] = window
        self.tag_id_to_window_id[id(tag)] = id(window)

        # make sure the window is drawn now that it exists
        window.update_idletasks()

        if focus:
            # set the focus to the new TagWindow
            self.select_tag_window(window)

        return window

    def minimize_all(self, e=None):
        '''Minimizes all open TagWindows.'''
        windows = self.tag_windows
        for wid in sorted(windows):
            w = windows[wid]
            try:
                w.withdraw()
            except Exception:
                print(format_exc())

    def new_tag(self, e=None):
        if self.def_selector_window:
            return
        
        dsw = DefSelectorWindow(
            self, title="Select a definition to use", action=lambda def_id:
            self.load_tags(filepaths='', def_id=def_id))
        self.def_selector_window = dsw
        self.place_window_relative(self.def_selector_window, 30, 50)

    def print_tag(self, e=None):
        '''Prints the currently selected tag to the console.'''
        if not self.config_file.data.header.flags.show_debug:
            return

        try:
            if self.selected_tag is None:
                return
            try:
                show = set()
                header = self.config_file.data.header
                precision = header.print_precision
                indent = header.print_indent

                for name in header.block_print.NAME_MAP:
                    if header.block_print.get(name):
                        show.add(name.split('show_')[-1])

                if not header.flags.log_tag_print:
                    self.terminal_out.edit_log = False
            except Exception:
                show = s_c.MOST_SHOW
            self.selected_tag.pprint(printout=True, show=show,
                                     precision=precision, indent=indent)

            try: self.terminal_out.edit_log = bool(header.flags.log_output)
            except Exception: pass
        except Exception:
            print(format_exc())

    def restore_all(self, e=None):
        '''Restores all open TagWindows to being visible.'''
        windows = self.tag_windows
        for wid in sorted(windows):
            w = windows[wid]
            try:
                if w.state() == 'withdrawn':
                    w.deiconify()
            except Exception:
                print(format_exc())

    def save_config(self, e=None):
        self.config_file.serialize(temp=False, backup=False)

    def save_tag(self, tag=None):
        if isinstance(tag, tk.Event):
            tag = None
        if tag is None:
            if self.selected_tag is None:
                return
            tag = self.selected_tag

        if hasattr(tag, "serialize"):
            # make sure the tag has a valid filepath whose directories
            # can be made if they dont already exist(dirname must not be '')
            if not(hasattr(tag, "filepath") and tag.filepath and
                   dirname(tag.filepath)):
                self.save_tag_as(tag)
                return

            # make sure to flush any changes made using widgets to the tag
            w = self.get_tag_window_by_tag(tag)
            w.flush()
            
            try:
                handler_flags = self.config_file.data.header.handler_flags
                tag.serialize(
                    temp=handler_flags.write_as_temp,
                    backup=handler_flags.backup_tags,
                    int_test=handler_flags.integrity_test)
            except Exception:
                print(format_exc())
                raise IOError("Could not save tag.")

            recent = self.recent_tagpaths
            path = tag.filepath
            if path in recent:
                recent.pop(recent.index(path))
            while len(recent) >= self.recent_tag_max:
                recent.pop(0)
            recent.append(path)

        return tag

    def save_tag_as(self, tag=None, filepath=None):
        if isinstance(tag, tk.Event):
            tag = None
        if tag is None:
            if self.selected_tag is None:
                return
            tag = self.selected_tag

        if not hasattr(tag, "serialize"):
            return

        # make sure to flush any changes made using widgets to the tag
        w = self.get_tag_window_by_tag(tag)
        w.flush()

        if filepath is None:
            ext = tag.ext
            orig_filepath = tag.filepath
            filepath = asksaveasfilename(
                initialdir=dirname(orig_filepath), defaultextension=ext,
                title="Save tag as...", filetypes=[
                    (ext[1:], "*" + ext), ('All', '*')] )

        if not filepath:
            return

        try:
            tags_coll = self.handler.tags[tag.def_id]
            if self.get_is_tag_loaded(filepath):
                print('%s is already loaded' % filepath)
                return
            # and re-index the tag under its new filepath
            tags_coll[filepath] = tag

            handler_flags = self.config_file.data.header.handler_flags
            tag.serialize(
                filepath=filepath, temp=False,
                backup=handler_flags.backup_tags,
                int_test=handler_flags.integrity_test)

            tag.filepath = filepath

            recent = self.recent_tagpaths
            if filepath in recent:
                recent.pop(recent.index(filepath))
            while len(recent) >= self.recent_tag_max:
                recent.pop(0)
            recent.append(filepath)
        except Exception:
            print(format_exc())
            raise IOError("Could not save tag.")

        try:
            # remove the tag from the handlers tag collection
            tags_coll.pop(filepath, None)
            self.get_tag_window_by_tag(tag).update_title()
        except Exception:
            # this isnt really a big deal
            #print(format_exc())
            pass

        return tag

    def save_all(self, e=None):
        '''
        Saves all currently loaded tags to their files.
        '''
        tags = self.handler.tags
        for def_id in tags:
            tag_coll = tags[def_id]
            for tag_path in tag_coll:
                try:
                    self.save_tag(tag_coll[tag_path])
                except Exception:
                    print(format_exc())
                    print("Exception occurred while trying to save '%s'" %
                          tag_path)

    def select_tag_window(self, window=None):
        try:
            if window is None:
                self.selected_tag = None
                self.focus_set()
                return

            if window.tag is not None:
                tag = window.tag
                # if the window IS selected, minimize it
                if self.selected_tag == tag:
                    self.selected_tag = None
                    window.withdraw()
                    return

                self.selected_tag = window.tag
                if window.state() == 'withdrawn':
                    window.deiconify()

                # focus_set wasnt working, so i had to play hard ball
                window.focus_force()
        except Exception:
            print(format_exc())

    def select_tag_window_by_tag(self, tag=None):
        if tag is None:
            return
        try:
            self.select_tag_window(self.get_tag_window_by_tag(tag))
        except Exception:
            print(format_exc())

    def select_defs(self):
        '''Prompts the user to specify where to load the tag defs from.
        Reloads the tag definitions from the folder specified.'''
        #### INCOMPLETE ####
        defs_root = askdirectory(initialdir=self.last_defs_dir,
                                 title="Select the tag definitions folder")
        if defs_root != "":
            print('Loading selected definitions...')
            self.update_idletasks()
            try:
                defs_root = self.handler.sanitize_path(defs_root)
                defs_path = defs_root.split(self.curr_dir + s_c.PATHDIV)[-1]
                defs_path = defs_path.replace(s_c.PATHDIV, '.')
                self.handler.reload_defs(defs_path=defs_path)
                self.last_defs_dir = defs_root
                print('Selected definitions loaded')
            except Exception:
                raise IOError("Could not load tag definitions.")

    def show_config_file(self, e=None):
        if self.config_window is not None:
            return
        self.config_window = self.make_tag_window(self.config_file,
                                                  window_cls=ConfigWindow)

    def show_defs(self, e=None):
        if self.def_selector_window:
            return
        
        self.def_selector_window = DefSelectorWindow(self, action=lambda x: x)
        self.place_window_relative(self.def_selector_window, 30, 50)

    def show_window_manager(self, e=None):
        if self.tag_window_manager is not None:
            return

        self.tag_window_manager = TagWindowManager(self)
        self.place_window_relative(self.tag_window_manager, 30, 50)

    def sync_tag_window_pos(self, e):
        '''Syncs TagWindows to move with the app.'''
        dx = int(self.winfo_x()) - self.app_offset_x
        dy = int(self.winfo_y()) - self.app_offset_y
        self.app_offset_x += dx
        self.app_offset_y += dy

        # keep a tabs on these so the config file can be updated
        self.app_width = self.winfo_width()
        self.app_height = self.winfo_height()

        if not self.sync_window_movement:
            return

        for w in self.tag_windows.values():
            w.geometry('%sx%s+%s+%s' %
                       (w.winfo_width(), w.winfo_height(),
                        dx + int(w.winfo_x()), dy + int(w.winfo_y())))

    def tile_vertical(self, e=None):
        windows = self.tag_windows
        sel_tag = self.selected_tag

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.tile_stride_x
        y_stride = self.tile_stride_y

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0
                self.curr_step_x += 1
            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0

            self.place_window_relative(window,
                                       self.curr_step_x*x_stride + 5,
                                       self.curr_step_y*y_stride + 50)
            self.curr_step_y += 1
            window.update_idletasks()

            if sel_tag is None or window.tag is not sel_tag:
                self.select_tag_window(window)

    def tile_horizontal(self, e=None):
        windows = self.tag_windows
        sel_tag = self.selected_tag

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.tile_stride_x
        y_stride = self.tile_stride_y

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0
                self.curr_step_y += 1
            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0

            self.place_window_relative(window,
                                       self.curr_step_x*x_stride + 5,
                                       self.curr_step_y*y_stride + 50)
            self.curr_step_x += 1
            window.update_idletasks()

            if sel_tag is None or window.tag is not sel_tag:
                self.select_tag_window(window)

    def unbind_hotkeys(self, hotkeys=None):
        if hotkeys is None:
            hotkeys = self.curr_hotkeys
        if isinstance(hotkeys, dict):
            hotkeys = hotkeys.keys()
        for key in tuple(hotkeys):
            try:
                self.unbind(key)
            except Exception:
                pass

    def update_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        config_data = config_file.data

        header = config_data.header

        open_tags = config_data.open_tags
        recent_tags = config_data.recent_tags
        dir_paths = config_data.directory_paths

        header.version = self.config_version
        header.flags.sync_window_movement = self.sync_window_movement

        __oga__ = object.__getattribute__

        del recent_tags[:]

        # make sure there are enough tagsdir entries in the directory_paths
        if len(dir_paths.NAME_MAP) > len(dir_paths):
            dir_paths.extend(len(dir_paths.NAME_MAP) - len(dir_paths))

        for path in self.recent_tagpaths:
            recent_tags.append()
            recent_tags[-1].path = path

        for s in ('recent_tag_max', 'undo_level_max'):
            header[s] = __oga__(self, s)

        for s in ('last_load_dir', 'last_defs_dir', 'last_imp_dir',
                  'curr_dir', ):
            dir_paths[s].path = __oga__(self, s)

        dir_paths.tags_dir.path = self.handler.tagsdir
        dir_paths.debug_log_path.path = self.log_filename

        self.update_style(config_file)

    def update_style(self, style_file):
        style_data = style_file.data
        config_data = self.config_file.data

        header = style_data.header
        app_window = style_data.app_window
        widgets = style_data.widgets

        widget_depths = style_data.widget_depths
        colors = style_data.colors

        header.parse(attr_index='data_modified')

        __oga__ = object.__getattribute__
        __tga__ = type.__getattribute__

        for s in app_window.NAME_MAP.keys():
            app_window[s] = __oga__(self, s)

        for s in ('title_width', 'scroll_menu_width', 'enum_menu_width'):
            widgets[s] = __tga__(BinillaWidget, s)

        for s in ('vertical_padx', 'vertical_pady',
                  'horizontal_padx', 'horizontal_pady'):
            widgets[s][:] = tuple(__tga__(BinillaWidget, s))

        for s in widget_depth_names:
            widget_depths[s] = __tga__(BinillaWidget, s + '_depth')

        for s in color_names:
            color = __tga__(BinillaWidget, s + '_color')[1:]
            colors[s][0] = int(color[0:2], 16)
            colors[s][1] = int(color[2:4], 16)
            colors[s][2] = int(color[4:6], 16)

    def update_window_settings(self):
        for m in (self.main_menu, self.file_menu, self.settings_menu,
                  self.debug_menu, self.windows_menu):
            m.config(bg=self.enum_normal_color, fg=self.text_normal_color)

        self.config(bg=self.default_bg_color)
        self.io_text.config(fg=self.io_fg_color, bg=self.io_bg_color)


class DefSelectorWindow(tk.Toplevel, BinillaWidget):

    def __init__(self, app_root, action, *args, **kwargs):
        try:
            title = app_root.handler.defs_filepath
        except AttributeError:
            title = "Tag definitions"

        title = kwargs.pop('title', title)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)
        self.title(title)

        self.action = action
        self.def_id = None
        self.sorted_def_ids = []
        self.minsize(width=400, height=300)

        self.list_canvas = tk.Canvas(
            self, highlightthickness=0, bg=self.default_bg_color)
        self.button_canvas = tk.Canvas(
            self, height=50, highlightthickness=0, bg=self.default_bg_color)

        #create and set the y scrollbar for the canvas root
        self.def_listbox = tk.Listbox(
            self.list_canvas, selectmode=SINGLE, highlightthickness=0,
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color,
            font=app_root.fixed_font)
        self.ok_btn = tk.Button(
            self.button_canvas, text='OK', command=self.complete_action,
            width=16, bg=self.default_bg_color, fg=self.text_normal_color)
        self.cancel_btn = tk.Button(
            self.button_canvas, text='Cancel', command=self.destroy,
            width=16, bg=self.default_bg_color, fg=self.text_normal_color)
        self.hsb = tk.Scrollbar(self.button_canvas, orient='horizontal')
        self.vsb = tk.Scrollbar(self.list_canvas,   orient='vertical')

        self.def_listbox.config(xscrollcommand=self.hsb.set,
                                yscrollcommand=self.vsb.set)

        self.hsb.config(command=self.def_listbox.xview)
        self.vsb.config(command=self.def_listbox.yview)

        self.list_canvas.pack(fill='both', expand=True)
        self.button_canvas.pack(fill='x')

        self.vsb.pack(side=RIGHT, fill='y')
        self.def_listbox.pack(fill='both', expand=True)

        self.hsb.pack(side=TOP, fill='x')
        self.ok_btn.pack(side=LEFT,      padx=9)
        self.cancel_btn.pack(side=RIGHT, padx=9)

        # make selecting things more natural
        self.def_listbox.bind('<<ListboxSelect>>', self.set_selected_def)
        self.def_listbox.bind('<Return>', self.complete_action)
        self.def_listbox.bind('<Double-Button-1>', self.complete_action)
        self.ok_btn.bind('<Return>', self.complete_action)
        self.cancel_btn.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        self.transient(self.app_root)
        self.grab_set()

        self.cancel_btn.focus_set()
        self.populate_listbox()

    def destroy(self, e=None):
        try:
            self.app_root.def_selector_window = None
        except AttributeError:
            pass
        tk.Toplevel.destroy(self)

    def complete_action(self, e=None):
        if self.def_id is not None:
            self.action(self.def_id)
        self.destroy()

    def populate_listbox(self):
        defs_root = self.app_root.handler.defs_path
        defs = self.app_root.handler.defs

        def_ids_by_path = {}
        id_pad = ext_pad = 0

        #loop over all the defs and find the max amount of
        #padding needed between the ID and the Ext strings
        for def_id in defs:
            d = defs[def_id]
            if len(def_id) > id_pad:
                id_pad = len(def_id)
        sorted_ids = self.sorted_def_ids = tuple(sorted(defs.keys()))

        #loop over all the definitions
        for def_id in sorted_ids:
            d = defs[def_id]

            self.def_listbox.insert(END, 'ID=%s  %sExt=%s'%
                                    (def_id, ' '*(id_pad-len(def_id)), d.ext ))

    def set_selected_def(self, event=None):
        
        if len(index) == 1:
            self.def_id = self.sorted_def_ids[int(index[0])]


class TagWindowManager(tk.Toplevel, BinillaWidget):

    app_root = None

    list_index_to_window = None

    def __init__(self, app_root, *args, **kwargs):
        self.app_root = app_root
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        self.list_index_to_window = []

        self.title("Tag window manager")
        self.minsize(width=400, height=250)

        # make the frames
        self.windows_frame = tk.Frame(self)
        self.button_frame = tk.Frame(self)
        self.ok_frame = tk.Frame(self.button_frame)
        self.cancel_frame = tk.Frame(self.button_frame)

        # make the buttons
        self.ok_button = tk.Button(
            self.ok_frame, text='OK', width=15, command=self.select)
        self.cancel_button = tk.Button(
            self.cancel_frame, text='Cancel', width=15, command=self.destroy)

        # make the scrollbars and listbox
        self.scrollbar_y = tk.Scrollbar(self.windows_frame, orient="vertical")
        self.scrollbar_x = tk.Scrollbar(self, orient="horizontal")
        self.windows_listbox = tk.Listbox(
            self.windows_frame, selectmode='single', highlightthickness=0,
            xscrollcommand=self.scrollbar_x.set,
            yscrollcommand=self.scrollbar_y.set)

        # set up the scrollbars
        self.scrollbar_x.config(command=self.windows_listbox.xview)
        self.scrollbar_y.config(command=self.windows_listbox.yview)

        # set up the keybindings
        self.windows_listbox.bind('<Return>', self.select)
        self.scrollbar_x.bind('<Return>', self.select)
        self.scrollbar_y.bind('<Return>', self.select)
        self.windows_listbox.bind('<Double-Button-1>', self.select)
        self.ok_button.bind('<Return>', self.select)
        self.cancel_button.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        # store the windows by title
        windows_by_title = {}
        for w in self.app_root.tag_windows.values():
            windows_by_title[w.title()] = w

        # populate the listbox
        for title in sorted(windows_by_title):
            self.list_index_to_window.append(windows_by_title[title])
            self.windows_listbox.insert('end', title)

        self.windows_listbox.select_set(0)

        # pack everything
        self.ok_button.pack(padx=12, pady=5, side='right')
        self.cancel_button.pack(padx=12, pady=5, side='left')
        self.ok_frame.pack(side='left', fill='x', expand=True)
        self.cancel_frame.pack(side='right', fill='x', expand=True)

        self.windows_listbox.pack(side='left', fill="both", expand=True)
        self.scrollbar_y.pack(side='left', fill="y")

        self.windows_frame.pack(fill="both", expand=True)
        self.scrollbar_x.pack(fill="x")
        self.button_frame.pack(fill="x")

        self.transient(self.app_root)
        self.ok_button.focus_set()
        self.grab_set()

    def destroy(self, e=None):
        try:
            self.app_root.tag_window_manager = None
        except AttributeError:
            pass
        tk.Toplevel.destroy(self)

    def select(self, e=None):
        w = self.list_index_to_window[self.windows_listbox.curselection()[0]]

        self.destroy()
        self.app_root.select_tag_window(w)
