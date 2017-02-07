import gc

from . import mtTkinter as tk
import tkinter.ttk

from os.path import exists
from tkinter import messagebox
from tkinter import constants as t_c
from .edit_manager import EditManager
from .field_widgets import *
from .widgets import BinillaWidget
from .widget_picker import *

from traceback import format_exc


__all__ = ("TagWindow", "ConfigWindow",
           "make_hotkey_string", "read_hotkey_string",)


def make_hotkey_string(hotkey):
    keys = hotkey.combo
    prefix = keys.modifier.enum_name.replace('_', '-')
    key = keys.key.enum_name

    if key == 'NONE':
        return None
    elif prefix == 'NONE':
        prefix = ''
    else:
        prefix += '-'

    combo = '<%s%s>'
    if key[0] == '_': key = key[1:]
    if key in "1234567890":
        combo = '%s%s'
    elif key in 'abcdefghijklmnopqrstuvwxyz' and 'Shift' in prefix:
        key = key.upper()

    return combo % (prefix, key)


def read_hotkey_string(combo):
    combo = combo.strip('<>')
    pieces = combo.split('-')

    keys = ['', 'NONE']
    if len(pieces):
        keys[1] = pieces.pop(-1)

        # sort them alphabetically so the enum_name will match
        if len(pieces):
            pieces = sorted(pieces)
            for i in range(len(pieces)):
                keys[0] += pieces[i] + '_'
            keys[0] = keys[0][:-1]
        else:
            keys[0] = 'NONE'

    return keys


class TagWindow(tk.Toplevel, BinillaWidget):
    tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
    field_widget = None  # The single FieldWidget held in this window
    widget_picker = def_widget_picker  # Rhe WidgetPicker to use for selecting
    #                                    the widget to build when populating
    # The tag handler that built the tag this window is displaying
    handler = None

    can_scroll = True

    edit_manager = None

    # whether the user declined to resize the edit history
    resize_declined = False

    # The config flags governing the way the window works
    flags = None

    # Determines whether this TagWindow is currently trying to undo or redo
    # This exists to prevent trying to apply multiple undos or redos at once
    _applying_edit_state = False

    def __init__(self, master, tag=None, *args, **kwargs):
        self.tag = tag
        if 'tag_def' in kwargs:
            self.tag_def = kwargs.pop('tag_def')
        elif self.tag is not None:
            self.tag_def = self.tag.definition

        if 'widget_picker' in kwargs:
            self.widget_picker = kwargs.pop('widget_picker')
        elif hasattr(self.app_root, 'widget_picker'):
            self.widget_picker = self.app_root.widget_picker
        self.app_root = kwargs.pop('app_root', master)
        self.handler = kwargs.pop('handler', None)

        try:
            max_undos = self.app_root.max_undos
        except AttributeError:
            max_undos = 100
        try:
            self.flags = self.app_root.config_file.data.header.tag_window_flags
        except AttributeError:
            pass

        kwargs.update(bg=self.default_bg_color)

        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.update_title()

        self.edit_manager = EditManager(max_undos)

        # create the root_canvas and the root_frame within the canvas
        self.root_canvas = rc = tk.Canvas(
            self, highlightthickness=0, bg=self.default_bg_color)
        self.root_frame = rf = tk.Frame(
            rc, highlightthickness=0, bg=self.default_bg_color)

        # create and set the x and y scrollbars for the root_canvas
        self.root_hsb = tk.Scrollbar(
            self, orient='horizontal', command=rc.xview)
        self.root_vsb = tk.Scrollbar(
            self, orient='vertical', command=rc.yview)
        rc.config(xscrollcommand=self.root_hsb.set,
                  yscrollcommand=self.root_vsb.set,
                  xscrollincrement=self.app_root.scroll_increment_x,
                  yscrollincrement=self.app_root.scroll_increment_y)
        self.root_frame_id = rc.create_window((0, 0), window=rf, anchor='nw')

        # make it so if this window is selected it changes the
        # selected_tag attribute of self.app_root to self.tag
        self.bind('<Button>', self.select_window)
        self.bind('<FocusIn>', self.select_window)

        rf.bind('<Configure>', self._resize_canvas)
        rc.bind('<Configure>', self._resize_frame)

        # make the window not show up on the start bar
        self.transient(self.app_root)

        # populate the window
        self.populate()

        # pack da stuff
        self.root_hsb.pack(side=t_c.BOTTOM, fill='x')
        self.root_vsb.pack(side=t_c.RIGHT,  fill='y')
        rc.pack(side='left', fill='both', expand=True)

        # set the hotkey bindings
        self.bind_hotkeys()

        # if this tag doesnt exist at the given filepath, it's new.
        try: new = not exists(self.tag.filepath)
        except Exception: new = True

        if new:
            try: self.field_widget.set_edited()
            except Exception: pass
        self.root_frame.update_idletasks()
        self.resize_window(self.root_frame.winfo_width(),
                           self.root_frame.winfo_height(), dont_shrink=False)

    @property
    def max_height(self):
        # The -64 accounts for the width of the windows border
        return self.winfo_screenheight() - self.winfo_y() - 64

    @property
    def max_width(self):
        # The -8 accounts for the width of the windows border
        return self.winfo_screenwidth() - self.winfo_x() - 8

    def _resize_canvas(self, e):
        '''
        Updates the size of the canvas when the window is resized.
        '''
        rf = self.root_frame; rc = self.root_canvas
        rf_w, rf_h = (rf.winfo_reqwidth(), rf.winfo_reqheight())
        rc.config(scrollregion="0 0 %s %s" % (rf_w, rf_h))
        if rf_w != rc.winfo_reqwidth():  rc.config(width=rf_w)
        if rf_h != rc.winfo_reqheight(): rc.config(height=rf_h)

        # account for the size of the scrollbars when resizing the window
        new_window_height = rf_h + self.root_hsb.winfo_reqheight() + 2
        new_window_width = rf_w + self.root_vsb.winfo_reqwidth() + 2

        if self.flags is not None:
            cap_size = self.flags.cap_window_size
            dont_shrink = self.flags.dont_shrink_window
            auto_resize = self.flags.auto_resize_window
        else:
            cap_size = dont_shrink = auto_resize = True

        if auto_resize:
            self.resize_window(new_window_width, new_window_height,
                               cap_size, dont_shrink)

            self.can_scroll = False
            if new_window_height > self.max_height:
                self.can_scroll = True

    def _resize_frame(self, e):
        '''
        Update the size of the frame and scrollbars when the canvas is resized.
        '''
        rf = self.root_frame; rc = self.root_canvas
        rf_id = self.root_frame_id
        rc_w, rc_h = (rc.winfo_reqwidth(), rc.winfo_reqheight())
        if rc_w != rf.winfo_reqwidth():  rc.itemconfigure(rf_id, width=rc_w)
        if rc_h != rf.winfo_reqheight(): rc.itemconfigure(rf_id, height=rc_h)

    def mousewheel_scroll_x(self, e):
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        #focus = self.focus_get()
        #if hasattr(focus, 'can_scroll') and focus.can_scroll:
        #    return
        if hasattr(under_mouse, 'can_scroll') and under_mouse.can_scroll:
            return

        if self.can_scroll and self.winfo_containing(e.x_root, e.y_root):
            self.root_canvas.xview_scroll(e.delta//60, "units")

    def mousewheel_scroll_y(self, e):
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        #focus = self.focus_get()
        #if hasattr(focus, 'can_scroll') and focus.can_scroll:
        #    return
        if hasattr(under_mouse, 'can_scroll') and under_mouse.can_scroll:
            return

        if self.can_scroll and self.winfo_containing(e.x_root, e.y_root):
            self.root_canvas.yview_scroll(e.delta//-120, "units")

    def bind_hotkeys(self, new_hotkeys=None):
        '''
        Binds the given hotkeys to the given methods of this class.
        Class methods must be the name of each method as a string.
        '''
        if new_hotkeys is None:
            new_hotkeys = {}
            for hotkey in self.app_root.config_file.data.tag_window_hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None or not hotkey.method.enum_name:
                    continue
                new_hotkeys[combo] = hotkey.method.enum_name

        assert isinstance(new_hotkeys, dict)

        # unbind any old hotkeys
        self.unbind_hotkeys()
        curr_hotkeys = self.app_root.curr_tag_window_hotkeys

        self.new_hotkeys = {}

        for key, func_name in new_hotkeys.items():
            try:
                if hasattr(self, func_name):
                    self.bind(key, self.__getattribute__(func_name))

                    curr_hotkeys[key] = func_name
            except Exception:
                print(format_exc())

    def destroy(self):
        '''
        Handles destroying this Toplevel and removing the tag from app_root.
        '''
        try:
            tag = self.tag
            try:
                w = self.field_widget
                if w.needs_flushing:
                    w.flush()
                if w.edited:
                    try:
                        path = tag.filepath
                    except Exception:
                        path = "This tag"
                    ans = messagebox.askyesnocancel(
                        "Unsaved changes", ("%s contains unsaved changes!\n" +
                        "Do you want to save changes before closing?") % path,
                        icon='warning', parent=self)

                    try: self.app_root.select_tag_window(self)
                    except Exception: pass
                    if ans is None:
                        return True
                    elif ans is True:
                        self.app_root.save_tag(tag)
            except Exception:
                print(format_exc())

            self.tag = None

            # remove the tag from the handler's tag library
            if hasattr(self.handler, 'delete_tag'):
                self.handler.delete_tag(tag=tag)

            # remove the tag and tag_window from the app_root
            if hasattr(self.app_root, 'delete_tag'):
                self.app_root.delete_tag(tag, False)

        except Exception:
            print(format_exc())

        tk.Toplevel.destroy(self)
        gc.collect()

    def save(self, **kwargs):
        '''Flushes any lingering changes in the widgets to the tag.'''
        if self.field_widget.needs_flushing:
            self.field_widget.flush()

        handler_flags = self.app_root.config_file.data.header.handler_flags
        kwargs.setdefault('temp', handler_flags.write_as_temp)
        kwargs.setdefault('backup', handler_flags.backup_tags)
        kwargs.setdefault('int_test', handler_flags.integrity_test)
        self.tag.serialize(**kwargs)
        self.field_widget.set_edited(False)

    def resize_window(self, new_width=None, new_height=None,
                      cap_size=True, dont_shrink=True):
        '''
        Resizes this TagWindow to the width and height specified.
        If cap_size is True the width and height will be capped so they
        do not expand beyond the right and bottom edges of the screen.
        '''
        old_width = self.winfo_reqwidth()
        old_height = self.winfo_reqheight()
        if new_width is None:  new_width = old_width
        if new_height is None: new_height = old_height

        if cap_size:
            # get the max size the width and height that the window
            # can be set to before it would be partially offscreen
            max_width = self.max_width
            max_height = self.max_height

            # if the new width/height is larger than the max, cap them
            if max_width < new_width:
                new_width = max_width
                old_width = 0
            if max_height < new_height:
                new_height = max_height
                old_height = 0

        if dont_shrink:
            if new_width < old_width: new_width = old_width
            if new_height < old_height: new_height = old_height

        # aint nothin to do if they're the same!
        if new_width == old_width and new_height == old_height:
            return
        self.geometry('%sx%s' % (new_width, new_height))

    def populate(self):
        '''
        Destroys the FieldWidget attached to this TagWindow and remakes it.
        '''
        # Destroy everything
        if hasattr(self.field_widget, 'destroy'):
            self.field_widget.destroy()
            self.field_widget = None

        # Get the desc of the top block in the tag
        root_block = self.tag.data

        # Get the widget to build
        widget_cls = self.widget_picker.get_widget(root_block.desc)

        # Rebuild everything
        self.field_widget = widget_cls(self.root_frame, node=root_block,
                                       show_frame=True, tag_window=self)
        self.field_widget.pack(expand=True, fill='both')

    def select_window(self, e):
        '''Makes this windows tag the selected tag in self.app_root'''
        self.app_root.selected_tag = self.tag

    def unbind_hotkeys(self, hotkeys=None):
        if hotkeys is None:
            hotkeys = {}
            for hotkey in self.app_root.config_file.data.tag_window_hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None or not hotkey.method.enum_name:
                    continue
                hotkeys[combo] = hotkey.method.enum_name
        if isinstance(hotkeys, dict):
            hotkeys = hotkeys.keys()
        for key in hotkeys:
            try:
                self.unbind(key)
            except Exception:
                pass

    def edit_undo(self, e=None):
        if self.edit_manager is None: return
        focus = self.focus_get()

        # Text widgets handle their own undo/redo states, and it
        # would be a real pain to try and override all of that
        if isinstance(focus, tk.Text):
            if hasattr(focus, 'text_undo'):
                focus.text_undo()
            return

        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            state = self.edit_manager.undo()
            if state is not None:
                state.apply_func(edit_state=state, undo=True)
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_redo(self, e=None):
        if self.edit_manager is None: return
        focus = self.focus_get()

        # Text widgets handle their own undo/redo states, and it
        # would be a real pain to try and override all of that
        if isinstance(focus, tk.Text):
            if hasattr(focus, 'text_redo'):
                focus.text_redo()
            return

        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            state = self.edit_manager.redo()
            if state is not None:
                state.apply_func(edit_state=state, undo=False)
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_add_state(self, edit_state):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            em = self.edit_manager
            if em.edit_index < em.maxlen:
                self.resize_declined = False
            elif em.edit_index == em.maxlen and not self.resize_declined:
                try:
                    added = max(self.app_root.max_undos, 100)
                except AttributeError:
                    added = 100
                ans = messagebox.askyesno(
                    "Edit history maxed.",
                    "This edit will begin overwriting the edit history!\n" +
                    "Do you wish to extend the history by %s states first?" %
                    added, icon='warning', parent=self)

                if ans:
                    em.resize(em.maxlen + added)
                else:
                    self.resize_declined = True

            em.add_state(edit_state)
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_clear(self):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            self.edit_manager.clear()
            self.resize_declined = False
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_resize(self, maxlen):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            self.edit_manager.resize(maxlen)
            self.resize_declined = False
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def update_title(self, new_title=None):
        if new_title is None:
            new_title = self.tag.filepath
        self.title(new_title)


class ConfigWindow(TagWindow):

    def destroy(self):
        tag = self.tag
        self.tag = None
        try:
            self.save()
        except Exception:
            pass
        try:
            self.app_root.delete_tag(tag, False)
        except Exception:
            pass
        tk.Toplevel.destroy(self)
        self.app_root.config_window = None
