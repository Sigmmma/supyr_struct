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

    def __init__(self, *args, **kwargs):
        self.f_widget_parent = kwargs.pop('f_widget_parent')
        self.sel_index = kwargs.pop('sel_index', None)
        kwargs.update(relief='sunken', bd=2)
        tk.Frame.__init__(self, *args, **kwargs)
        if self.sel_index is None:
            self.sel_index = tk.IntVar()
            self.sel_index.set(-1)

        self.sel_label = tk.Label(self, bg=WHITE, width=SCROLL_MENU_SIZE)
        self.arrow_frame = tk.Frame(self, relief='raised', bd=3,
                                    height=18, width=18)
        self.arrow_frame.pack_propagate(0)
        arrow = tk.Label(self.arrow_frame, text="▼")
        arrow.pack()
        
        self.update_label()

    def update_label(self):
        parent = self.f_widget_parent
        option = parent.get_option()
        if not option:
            option = ""
        self.sel_label.config(text=option, anchor="w")
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.arrow_frame.pack(side="left", fill=None, expand=False)

    def activate(self):
        self.arrow_frame.configure(relief='sunken', bd=2)

    def deactivate(self):
        self.arrow_frame.configure(relief='raised', bd=3)

    def make_menu(self):
        pass

    def place_menu(self, relx=0, rely=0):
        pass

    def disable(self):
        if self.disabled:
            return
        self.disabled = True
        self.sel_label.config(bg=DEFAULT_BG_COLOR)

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=WHITE)
