'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import tkinter as tk
from . import editor_constants as e_c
from traceback import format_exc


class BoolCheckbutton(tk.Checkbutton):
    '''
    Used inside a BoolCanvas for each of
    the individual boolean options available.
    '''

    def __init__(self, *args, **kwargs):
        self.func = kwargs.pop('func', lambda: None)

        kwargs["command"] = lambda: self.check(i)
        tk.CheckButton.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def check(self, i):
        self._func(self, i)


'''
TODO:
NOTES:
    Use Menu.post() and Menu.unpost to allow displaying cascade menus anywhere

    MAKE SURE TO MAKE THE MENU ROOTED TO self.app_root TO ENSURE IT DOESNT
    RESIZE THE CANVAS AND CAN FALL OFF THE EDGE OF THE WINDOW IF IT NEEDS TO

    Use ttk.Treeview for tag explorer window
'''

class ScrollMenu(tk.Frame):
    '''
    Used as a menu for certain FieldWidgets, such as when
    selecting an array element or an enumerator option.
    '''
    disabled = False
    sel_index = None
    f_widget_parent = None
    max_height = 20
    max_index = 0

    can_scroll = True

    def __init__(self, *args, **kwargs):
        sel_index = kwargs.pop('sel_index', -1)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent')

        kwargs.update(relief='sunken', bd=2)
        tk.Frame.__init__(self, *args, **kwargs)

        self.sel_index = tk.IntVar(self)
        self.sel_index.set(sel_index)

        self.sel_label = tk.Label(self, bd=2, bg=e_c.WHITE, relief='groove',
                                  width=e_c.SCROLL_MENU_SIZE)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', bd=0,
                                     height=18, width=18)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(self.button_frame, bd=e_c.BUTTON_DEPTH,
                                      text="▼", width=1)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill=None, expand=False)
        self.arrow_button.pack()

        # make sure the TagWindow knows the arrow_button is scrollable
        self.arrow_button.can_scroll = self.can_scroll

        # make bindings so arrow keys can be used to navigate the menu
        self.button_frame.bind('<Up>', self.decrement_sel)
        self.button_frame.bind('<Down>', self.increment_sel)
        self.arrow_button.bind('<Up>', self.decrement_sel)
        self.arrow_button.bind('<Down>', self.increment_sel)

        self.sel_label.bind('<Button-1>', self.select_arrow)
        self.arrow_button.bind('<ButtonRelease-1>', self.select_arrow)
        self.arrow_button.bind('<FocusOut>', self.deselect_arrow)
        self.arrow_button.bind_all('<MouseWheel>', self._mousewheel_scroll)

        self.update_label()

    def update_label(self):
        parent = self.f_widget_parent
        option = parent.get_option()
        if not option:
            option = ""
        self.sel_label.config(text=option, anchor="w")

    def make_menu(self):
        pass

    def disable(self):
        if self.disabled:
            return
        self.disabled = True
        self.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
        self.sel_label.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=e_c.WHITE)
        self.arrow_button.config(state='normal')

    def select_arrow(self, e=None):
        if not self.disabled:
            self.arrow_button.focus_set()
            self.sel_label.config(bg=e_c.ENUM_BG_SELECTED_COLOR)

    def deselect_arrow(self, e=None):
        if self.disabled:
            self.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
            self.sel_label.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
        else:
            self.config(bg=e_c.ENUM_BG_NORMAL_COLOR)
            self.sel_label.config(bg=e_c.ENUM_BG_NORMAL_COLOR)

    def _mousewheel_scroll(self, e):
        f = self.focus_get()
        try:
            # This seems kinda hacky, but its the best I can come up with.
            # Make sure the widget in focus is a ScrollMenu. If it is, call
            # its decrement or increment methods based on the scroll change
            sm = f.master.master
            if isinstance(sm, ScrollMenu) and not sm.disabled:
                if e.delta > 0:
                    sm.decrement_sel()
                elif e.delta < 0:
                    sm.increment_sel()
        except Exception:
            pass

    def increment_sel(self, e=None):
        new_index = self.sel_index.get() + 1
        if new_index > self.max_index:
            return
        self.sel_index.set(new_index)
        self.f_widget_parent.select_option(new_index)

    def decrement_sel(self, e=None):
        new_index = self.sel_index.get() - 1
        if new_index < 0:
            return
        self.sel_index.set(new_index)
        self.f_widget_parent.select_option(new_index)
