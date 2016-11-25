'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import tkinter as tk
from .editor_constants import *


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

    def __init__(self, *args, **kwargs):
        sel_index = kwargs.pop('sel_index', -1)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent')

        kwargs.update(relief='sunken', bd=2)
        tk.Frame.__init__(self, *args, **kwargs)

        self.sel_index = tk.IntVar(self)
        self.sel_index.set(sel_index)

        self.sel_label = tk.Label(self, bg=WHITE, width=SCROLL_MENU_SIZE)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', bd=0,
                                     height=18, width=18)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(self.button_frame, bd=BUTTON_DEPTH,
                                      text="▼", width=1)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill=None, expand=False)
        self.arrow_button.pack()

        # make bindings so arrow keys can be used to navigate the menu
        self.button_frame.bind('<Up>', self.decrement_sel)
        self.button_frame.bind('<Down>', self.increment_sel)
        self.arrow_button.bind('<Up>', self.decrement_sel)
        self.arrow_button.bind('<Down>', self.increment_sel)
        self.arrow_button.bind('<ButtonRelease-1>', self.select_arrow)

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
        self.sel_label.config(bg=DEFAULT_BG_COLOR)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=WHITE)
        self.arrow_button.config(state='normal')

    def select_arrow(self, e=None):
        if not self.disabled:
            self.arrow_button.focus_set()

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
