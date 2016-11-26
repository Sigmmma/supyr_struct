import gc
import os
import sys
import tkinter as tk

from copy import deepcopy
from io import StringIO
from time import time, sleep
from os.path import dirname
from tkinter.font import Font
from tkinter.constants import *
from tkinter.filedialog import askopenfilenames, askopenfilename,\
     askdirectory, asksaveasfilename
from traceback import format_exc

from . import constants as s_c
from . import editor_constants as e_c
from .tag_window import *
from .widget_picker import *
from ..handler import Handler


def_hotkey_bindings = {
    '<Control-w>': 'close_selected_window',
    '<Control-o>': 'load_tags',
    '<Control-n>': 'new_tag',
    '<Control-s>': 'save_tag',
    '<Control-f>': 'show_defs',

    '<Alt-w>': 'show_window_manager',
    '<Alt-o>': 'load_tag_as',
    '<Alt-s>': 'save_tag_as',

    '<Control-Shift-s>': 'save_all',
    '<Control-p>': 'print_tag',
    }

class IORedirecter(StringIO):
    # Text widget to output text to
    text_out = None

    def __init__(self, text_out, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self.text_out = text_out

    def write(self, string):
        self.text_out.config(state=NORMAL)
        self.text_out.insert(END, string)
        self.text_out.see(END)
        self.text_out.config(state=DISABLED)


class Binilla(tk.Tk):
    # the tag of the currently in-focus TagWindow
    selected_tag = None
    # the Handler for managing loaded tags
    handler = None

    # a window that displays and allows selecting loaded definitions
    def_selector_window = None

    # the default WidgetPicker instance to use for selecting widgets
    widget_picker = WidgetPicker()

    default_tag_window_class = TagWindow

    # dict of open TagWindow instances. keys are the ids of each of the windows
    tag_windows = None
    # map of the id of each tag to the id of the window displaying it
    tag_id_to_window_id = None

    curr_dir = os.path.abspath(os.curdir)
    last_load_dir = curr_dir
    last_defs_dir = curr_dir
    last_imp_dir  = curr_dir

    '''Miscellaneous properties'''
    app_name = "Binilla"  # the name of the app(used in window title)
    version = '0.2'
    untitled_num = 0  # when creating a new, untitled tag, this is its name
    backup_tags = True
    write_as_temp = False

    '''Window properties'''
    # When tags are opened they are tiled, first vertically, then horizontally.
    # step_y_curr is incremented for each tag opened till it reaches step_y_max
    # At that point it resets to 0 and increments step_x_curr by 1.
    # If step_x_curr reaches step_x_max it will reset to 0. The position of an
    # opened TagWindow is set relative to the application's top left corner.
    # The x offset is shifted right by step_x_curr*step_x_tile_stride and
    # the y offset is shifted down  by step_y_curr*step_y_stride.
    step_x_max = 4
    step_y_max = 8

    step_x_curr = 0
    step_y_curr = 0

    step_x_cascade_stride = 60
    step_x_tile_stride = 120
    step_y_stride = 30

    default_tag_window_width = 500
    default_tag_window_height = 640

    window_menu_max_len = 15

    app_width = 640
    app_height = 480
    app_offset_x = None
    app_offset_y = None

    io_str = None
    io_fg_color = e_c.IO_FG_COLOR
    io_bg_color = e_c.IO_BG_COLOR

    sync_window_movement = True  # Whether or not to sync the movement of
    #                              the TagWindow instances with the app.

    # a mapping of hotkey bindings to method names
    hotkeys = None

    '''
    TODO:
        Finish incomplete methods(marked by #### INCOMPLETE ####)
    '''
    
    def __init__(self, *args, **kwargs):
        #### INCOMPLETE ####
        self.curr_dir = kwargs.pop('curr_dir', self.curr_dir)
        self.app_name = kwargs.pop('app_name', self.app_name)
        self.version = str(kwargs.pop('version', self.version))
        self.window_menu_max_len = kwargs.pop('window_menu_max_len',
                                               self.window_menu_max_len)

        self.app_width = kwargs.pop('app_width', self.app_width)
        self.app_height = kwargs.pop('app_height', self.app_height)
        self.app_offset_x = kwargs.pop('app_offset_x', self.app_offset_x)
        self.app_offset_y = kwargs.pop('app_offset_y', self.app_offset_y)

        hotkeys = kwargs.pop('hotkeys', def_hotkey_bindings)

        self.widget_picker = kwargs.pop('widget_picker', self.widget_picker)
        if 'handler' in kwargs:
            self.handler = kwargs.pop('handler')
        else:
            self.handler = Handler(debug=3)
        tk.Tk.__init__(self, *args, **kwargs)
        self.tag_windows = {}
        self.tag_id_to_window_id = {}

        #fonts
        self.fixed_font = Font(family="Courier", size=8)
        self.container_title_font = Font(family="Courier", size=10,
                                         weight='bold')

        # center the app if offsets arent provided
        if self.app_offset_x is None:
            self.app_offset_x = (self.winfo_screenwidth()-self.app_width)//2
        if self.app_offset_y is None:
            self.app_offset_y = (self.winfo_screenheight()-self.app_height)//2
        
        self.title('%s v%s' % (self.app_name, self.version))
        self.geometry("%sx%s+%s+%s" % (self.app_width, self.app_height,
                                       self.app_offset_x, self.app_offset_y))
        self.minsize(width=200, height=50)
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.bind('<Configure>', self.sync_tag_window_pos)
        self.bind_hotkeys(hotkeys)

        ######################################################################
        ######################################################################
        # MAKE METHODS FOR CREATING/DESTROYING MENUS SO THEY CAN BE CUSTOMIZED
        # This includes creating a system to manage the menus and keep track
        # of which ones exist, their order on the menu bar, their names, etc.
        # Once that is done, replace the below code with code that uses them.
        ######################################################################
        ######################################################################

        #create the main menu and add its commands
        self.main_menu    = tk.Menu(self)
        self.file_menu    = tk.Menu(self.main_menu, tearoff=0)
        self.options_menu = tk.Menu(self.main_menu, tearoff=0)
        self.debug_menu   = tk.Menu(self.main_menu, tearoff=0)
        self.windows_menu = tk.Menu(self.main_menu, tearoff=0,
                                    postcommand=self.generate_windows_menu)

        self.config(menu=self.main_menu)

        #add cascades and commands to the main_menu
        self.main_menu.add_cascade(label="File",    menu=self.file_menu)
        self.main_menu.add_cascade(label="Options", menu=self.options_menu)
        self.main_menu.add_cascade(label="Debug",   menu=self.debug_menu)
        self.main_menu.add_cascade(label="Windows", menu=self.windows_menu)
        #self.main_menu.add_command(label="Help")
        #self.main_menu.add_command(label="About")

        #add the commands to the file_menu
        fm_ac = self.file_menu.add_command
        fm_ac(label="New",        command=self.new_tag)
        fm_ac(label="Load",       command=self.load_tags)
        fm_ac(label="Load as...", command=self.load_tag_as)
        self.file_menu.add_separator()
        fm_ac(label="Save",       command=self.save_tag)
        fm_ac(label="Save as...", command=self.save_tag_as)
        fm_ac(label="Save all",   command=self.save_all)
        self.file_menu.add_separator()
        fm_ac(label="Exit",       command=self.exit)
        
        #add the commands to the options_menu
        self.options_menu.add_command(
            label="Set definitions folder", command=self.select_defs)
        self.options_menu.add_separator()
        self.options_menu.add_command(
            label="Show defs", command=self.show_defs)

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
        self.io_str = sys.stdout = IORedirecter(self.io_text)

    def bind_hotkeys(self, new_hotkeys):
        '''
        Binds the given hotkeys to the given methods of this class.
        Class methods must be the name of each method as a string.
        '''
        assert isinstance(new_hotkeys, dict)

        # unbind any hotkeys colliding with the new_hotkeys
        self.unbind_hotkeys(new_hotkeys)

        self.hotkeys = hotkeys = {}

        for key, func_name in new_hotkeys.items():
            try:
                self.bind_all(key, self.__getattribute__(func_name))
                hotkeys[key] = func_name
            except Exception:
                print(format_exc())

    def cascade(self):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.step_y_curr = 0
        self.step_x_curr = 0
        x_stride = self.step_x_cascade_stride
        y_stride = self.step_y_stride
        self.selected_tag = None
        
        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont cascade hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.step_y_curr > self.step_y_max:
                self.step_y_curr = 0
                self.step_x_curr += 1
            if self.step_x_curr > self.step_x_max:
                self.step_x_curr = 0

            self.place_window_relative(
                window, (self.step_x_curr*x_stride +
                         self.step_y_curr*(x_stride//2) + 5),
                self.step_y_curr*y_stride + 50)
            self.step_y_curr += 1
            window.update_idletasks()
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

    def delete_tag(self, tag):
        try:
            tid = id(tag)
            def_id = tag.def_id
            path = tag.filepath
            tags = self.handler.tags
            tid_to_wid = self.tag_id_to_window_id

            if tid in tid_to_wid:
                wid = tid_to_wid[tid]
                t_window = self.tag_windows[wid]
                del tid_to_wid[tid]
                del self.tag_windows[wid]

                # ONLY delete the TagWindow if it still has a tag(this means
                # the TagWindow isnt calling delete_tag by destroying itself)
                if hasattr(t_window, 'tag'):
                    t_window.destroy()

            # remove the tag from the handler's tag library
            self.handler.delete_tag(tag=tag)

            if self.selected_tag is tag:
                self.selected_tag = None
            del tag
            gc.collect()
        except Exception:
            print(format_exc())

    def exit(self):
        '''Exits the program.'''
        self.destroy()  # wont close if a listener prompt is open without this
        raise SystemExit()

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
        menu.add_separator()

        i = 0
        max_len = self.window_menu_max_len

        for wid in self.tag_windows:
            if i >= max_len:
                break
            w = self.tag_windows[wid]
            try:
                menu.add_command(
                    label="[%s] %s" % (w.tag.def_id, w.tag.filepath),
                    command=lambda w=w: self.select_tag_window(w))
                i += 1
            except Exception:
                print(format_exc())
        # if at least 1 window exists
        if i:
            menu.add_separator()
        menu.add_command(label="Window manager",
                         command=self.show_window_manager)

    def toggle_sync(self):
        self.sync_window_movement = not self.sync_window_movement

    def get_tag(self, def_id, filepath):
        '''
        Returns the tag from the handler under the given def_id and filepath.
        '''
        return self.handler.tags.get(def_id, {}).get(filepath)

    def get_tag_window_by_tag(self, tag):
        return self.tag_windows[self.tag_id_to_window_id[id(tag)]]

    def get_is_tag_loaded(self, filepath, def_id=None):
        if def_id is None:
            def_id = self.handler.get_def_id(filepath)
        return bool(self.get_tag(def_id, filepath))

    def load_tags(self, filepaths=None, def_id=None):
        '''Prompts the user for a tag(s) to load and loads it.'''
        if isinstance(filepaths, tk.Event): filepaths = None
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

        for path in filepaths:
            if self.get_is_tag_loaded(path):
                continue

            #try to load the new tags
            try:
                new_tag = self.handler.load_tag(path, def_id)
            except Exception:
                print("Could not load tag '%s'" % path)
                continue

            # if the path is blank(new tag), give it a unique name
            if not path:
                # remove the tag from the handlers tag collection
                tags_coll = self.handler.tags[new_tag.def_id]
                tags_coll.pop(new_tag.filepath, None)

                ext = str(new_tag.ext)
                new_tag.filepath = ('untitled%s' + ext) % self.untitled_num
                # re-index the tag under its new filepath
                tags_coll[new_tag.filepath] = new_tag
                self.untitled_num += 1

            try:
                #build the window
                w = self.make_tag_window(new_tag, False)
            except Exception:
                raise IOError("Could not display tag '%s'." % path)

        self.select_tag_window(w)

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
        if fp != "":
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

    def make_tag_window(self, tag, focus=True):
        '''
        Creates and returns a TagWindow instance for the supplied
        tag and sets the current focus to the new TagWindow.
        '''
        window = self.default_tag_window_class(self, tag, app_root=self)

        # reposition the window
        if self.step_y_curr > self.step_y_max:
            self.step_y_curr = 0
            self.step_x_curr += 1
        if self.step_x_curr > self.step_x_max:
            self.step_x_curr = 0

        self.place_window_relative(
            window, self.step_x_curr*self.step_x_tile_stride + 5,
            self.step_y_curr*self.step_y_stride + 50)
        self.step_y_curr += 1
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

    def minimize_all(self):
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
        try:
            if self.selected_tag is None:
                return
            self.selected_tag.pprint(printout=True, show=s_c.MOST_SHOW)
        except Exception:
            print(format_exc())

    def restore_all(self):
        '''Restores all open TagWindows to being visible.'''
        windows = self.tag_windows
        for wid in sorted(windows):
            w = windows[wid]
            try:
                if w.state() == 'withdrawn':
                    w.deiconify()
            except Exception:
                print(format_exc())

    def save_tag(self, tag=None):
        if isinstance(tag, tk.Event): tag = None
        if tag is None:
            if self.selected_tag is not None:
                tag = self.selected_tag
            else:
                return

        if hasattr(tag, "serialize"):
            # make sure the tag has a valid filepath whose directories
            # can be made if they dont already exist(dirname must not be '')
            if not(hasattr(tag, "filepath") and tag.filepath and
                   dirname(tag.filepath)):
                self.save_tag_as(tag)
                return
            
            try:
                tag.serialize(temp=self.write_as_temp, backup=self.backup_tags)
            except Exception:
                raise IOError("Could not save tag.")

    def save_tag_as(self, tag=None):
        if isinstance(tag, tk.Event): tag = None
        if tag is None:
            if self.selected_tag is not None:
                tag = self.selected_tag
            else:
                return

        if hasattr(tag, "serialize"):
            ext = tag.ext
            orig_filepath = tag.filepath
            filepath = asksaveasfilename(
                initialdir=dirname(orig_filepath), defaultextension=ext,
                title="Save tag as...", filetypes=[
                    (ext[1:], "*" + ext), ('All', '*')] )
            if filepath != "":
                try:
                    tags_coll = self.handler.tags[tag.def_id]
                    assert filepath not in tags_coll,\
                           "A tag with that name is already open."
                    # and re-index the tag under its new filepath
                    tags_coll[filepath] = tag
                    tag.serialize(filepath=filepath, temp=False, backup=False)
                    tag.filepath = filepath
                except Exception:
                    raise IOError("Could not save tag.")

                try:
                    # remove the tag from the handlers tag collection
                    tags_coll.pop(filepath, None)
                    self.get_tag_window_by_tag(tag).update_title()
                except Exception:
                    # this isnt really a big deal
                    pass
                    #print(format_exc())

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
                defs_root = defs_root.replace('\\', s_c.PATHDIV)\
                            .replace('/', s_c.PATHDIV)
                defs_path = defs_root.split(self.curr_dir+s_c.PATHDIV)[-1]
                defs_path = defs_path.replace(s_c.PATHDIV, '.')
                self.handler.reload_defs(defs_path=defs_path)
                self.last_defs_dir = defs_root
                print('Selected definitions loaded')
            except Exception:
                raise IOError("Could not load tag definitions.")

    def show_defs(self, e=None):
        if self.def_selector_window:
            return
        
        self.def_selector_window = DefSelectorWindow(self, action=lambda x: x)
        self.place_window_relative(self.def_selector_window, 30, 50)

    def show_window_manager(self, e=None):
        ### INCOMPLETE ###
        pass

    def sync_tag_window_pos(self, e):
        '''Syncs TagWindows to move with the app.'''
        dx = int(self.winfo_x()) - self.app_offset_x
        dy = int(self.winfo_y()) - self.app_offset_y
        self.app_offset_x += dx
        self.app_offset_y += dy

        if not self.sync_window_movement:
            return

        for w in self.tag_windows.values():
            w.geometry('%sx%s+%s+%s' %
                       (w.winfo_width(), w.winfo_height(),
                        dx + int(w.winfo_x()), dy + int(w.winfo_y())))

    def tile_vertical(self):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.step_y_curr = 0
        self.step_x_curr = 0
        x_stride = self.step_x_tile_stride
        y_stride = self.step_y_stride

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.step_y_curr > self.step_y_max:
                self.step_y_curr = 0
                self.step_x_curr += 1
            if self.step_x_curr > self.step_x_max:
                self.step_x_curr = 0

            self.place_window_relative(window,
                                       self.step_x_curr*x_stride + 5,
                                       self.step_y_curr*y_stride + 50)
            self.step_y_curr += 1
            window.update_idletasks()
            self.select_tag_window(window)

    def tile_horizontal(self):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.step_y_curr = 0
        self.step_x_curr = 0
        x_stride = self.step_x_tile_stride
        y_stride = self.step_y_stride

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.step_x_curr > self.step_x_max:
                self.step_x_curr = 0
                self.step_y_curr += 1
            if self.step_y_curr > self.step_y_max:
                self.step_y_curr = 0

            self.place_window_relative(window,
                                       self.step_x_curr*x_stride + 5,
                                       self.step_y_curr*y_stride + 50)
            self.step_x_curr += 1
            window.update_idletasks()
            self.select_tag_window(window)

    def unbind_hotkeys(self, hotkeys=None):
        if hotkeys is None:
            hotkeys = self.hotkeys
        if isinstance(hotkeys, dict):
            hotkeys = hotkeys.keys()
        for key in hotkeys:
            try:
                self.unbind(key)
            except Exception:
                print(format_exc())


class DefSelectorWindow(tk.Toplevel):

    def __init__(self, master, action, *args, **kwargs):
        try:
            title = master.handler.defs_filepath
        except AttributeError:
            title = "Tag definitions"

        title = kwargs.pop('title', title)
            
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        
        self.title(title)
        
        self.action = action
        self.def_id = None
        self.sorted_def_ids = []
        self.minsize(width=400, height=300)
        self.protocol("WM_DELETE_WINDOW", self.destruct)

        self.list_canvas = tk.Canvas(self, highlightthickness=0)
        self.button_canvas = tk.Canvas(self, height=50, highlightthickness=0)
        
        #create and set the y scrollbar for the canvas root
        self.def_listbox = tk.Listbox(
            self.list_canvas, selectmode=SINGLE, highlightthickness=0,
            font=master.fixed_font)
        self.ok_btn = tk.Button(self.button_canvas, text='OK', width=16,
                                command=self.complete_action)
        self.cancel_btn = tk.Button(self.button_canvas, text='Cancel',
                                    width=16, command=self.destruct)
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
        self.def_listbox.bind('<Return>', lambda x: self.complete_action())
        self.def_listbox.bind('<Double-Button-1>', lambda x: self.complete_action())
        self.ok_btn.bind('<Return>', lambda x: self.complete_action())
        self.cancel_btn.bind('<Return>', lambda x: self.destruct())
        self.bind('<Escape>', lambda x: self.destruct())
        

        self.transient(self.master)
        self.grab_set()

        self.cancel_btn.focus_set()
        self.populate_listbox()


    def destruct(self):
        try:
            self.master.def_selector_window = None
        except AttributeError:
            pass
        self.destroy()

    def complete_action(self):
        if self.def_id is not None:
            self.action(self.def_id)
        self.destruct()

    def populate_listbox(self):
        defs_root = self.master.handler.defs_path
        defs = self.master.handler.defs
        
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
        index = self.def_listbox.curselection()
        
        if len(index) == 1:
            self.def_id = self.sorted_def_ids[int(index[0])]
