'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import tkinter as tk
from . import editor_constants as e_c
from traceback import format_exc


'''
TODO:
NOTES:
    Use Menu.post() and Menu.unpost to allow displaying cascade menus anywhere

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
    option_box = None
    max_height = 15
    max_index = 0

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

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
        self.arrow_button.pack(side="left")

        # make the option box to populate
        self.option_frame = tk.Frame(
            self.winfo_toplevel(), highlightthickness=0, bd=0)
        self.option_frame.pack_propagate(0)
        self.option_bar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.option_box = tk.Listbox(
            self.option_frame, highlightthickness=0, bg='white',
            yscrollcommand=self.option_bar.set)
        self.option_bar.config(command=self.option_box.yview)
        self.option_box.pack(side='left', expand=True, fill='both')

        # make sure the TagWindow knows these widgets are scrollable
        self.sel_label.can_scroll = self.can_scroll
        self.button_frame.can_scroll = self.can_scroll
        self.arrow_button.can_scroll = self.can_scroll
        self.option_frame.can_scroll = self.can_scroll
        self.option_bar.can_scroll = self.can_scroll
        self.option_box.can_scroll = self.can_scroll

        # make bindings so arrow keys can be used to navigate the menu
        self.button_frame.bind('<Up>', self.decrement_sel)
        self.button_frame.bind('<Down>', self.increment_sel)
        self.arrow_button.bind('<Up>', self.decrement_sel)
        self.arrow_button.bind('<Down>', self.increment_sel)
        self.option_bar.bind('<Up>', self.decrement_listbox_sel)
        self.option_bar.bind('<Down>', self.increment_listbox_sel)

        self.sel_label.bind('<MouseWheel>', self._mousewheel_scroll)
        self.button_frame.bind('<MouseWheel>', self._mousewheel_scroll)
        self.arrow_button.bind('<MouseWheel>', self._mousewheel_scroll)

        self.sel_label.bind('<Button-1>', self.click_label)
        self.arrow_button.bind('<ButtonRelease-1>', self.select_option_box)
        self.arrow_button.bind('<Return>', self.select_option_box)
        self.arrow_button.bind('<space>', self.select_option_box)
        self.option_bar.bind('<FocusOut>', self.deselect_option_box)
        self.option_bar.bind('<Return>', self.select_menu)
        self.option_bar.bind('<space>', self.select_menu)
        self.option_box.bind('<<ListboxSelect>>', self.select_menu)

        self.update_label()

    def _mousewheel_scroll(self, e):
        if self.option_box_visible:
            return
        elif e.delta > 0:
            self.decrement_sel()
        elif e.delta < 0:
            self.increment_sel()

    def click_outside_option_box(self, e):
        if not self.option_box_visible:
            return
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        if under_mouse not in (self.option_frame, self.option_bar,
                               self.option_box, self.sel_label,
                               self.arrow_button):
            self.select_menu()

    def decrement_listbox_sel(self, e=None):
        sel_index = self.option_box.curselection()[0] - 1
        if sel_index < 0:
            return
        self.option_box.select_clear(0, tk.END)
        self.sel_index.set(sel_index)
        self.option_box.select_set(sel_index)
        self.option_box.see(sel_index)
        self.f_widget_parent.select_option(sel_index)

    def decrement_sel(self, e=None):
        new_index = self.sel_index.get() - 1
        if new_index < 0:
            return
        self.sel_index.set(new_index)
        self.f_widget_parent.select_option(new_index)

    def destroy(self):
        if self.click_outside_funcid is not None:
            self.winfo_toplevel().unbind('<Button>', self.click_outside_funcid)
        tk.Frame.destroy(self)
        self.option_frame.destroy()

    def deselect_option_box(self, e=None):
        if self.disabled:
            self.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
            self.sel_label.config(bg=e_c.ENUM_BG_DISABLED_COLOR)
        else:
            self.config(bg=e_c.ENUM_BG_NORMAL_COLOR)
            self.sel_label.config(bg=e_c.ENUM_BG_NORMAL_COLOR)

        if self.option_box_visible:
            self.option_frame.place_forget()
            self.option_bar.forget()
            self.option_box_visible = False
            self.click_outside_funcid = None

        self.arrow_button.unbind('<FocusOut>')

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

    def increment_listbox_sel(self, e=None):
        sel_index = self.option_box.curselection()[0] + 1
        if sel_index > self.max_index:
            return
        self.option_box.select_clear(0, tk.END)
        self.sel_index.set(sel_index)
        self.option_box.select_set(sel_index)
        self.option_box.see(sel_index)
        self.f_widget_parent.select_option(sel_index)

    def increment_sel(self, e=None):
        new_index = self.sel_index.get() + 1
        if new_index > self.max_index:
            return
        self.sel_index.set(new_index)
        self.f_widget_parent.select_option(new_index)

    def select_menu(self, e=None):
        sel_index = self.option_box.curselection()
        if not sel_index:
            return
        self.sel_index.set(sel_index[0])
        self.f_widget_parent.select_option(sel_index[0])
        self.deselect_option_box()
        self.arrow_button.focus_set()
        self.sel_label.config(bg=e_c.ENUM_BG_SELECTED_COLOR)
        self.arrow_button.bind('<FocusOut>', self.deselect_option_box)

    def click_label(self, e=None):
        if self.option_box_visible:
            self.select_menu()
        else:
            self.select_option_box()

    def select_option_box(self, e=None):
        if not self.disabled:
            self.show_menu()
            self.sel_label.config(bg=e_c.ENUM_BG_SELECTED_COLOR)

    def show_menu(self):
        options = self.f_widget_parent.options
        if not len(options):
            return

        self.arrow_button.unbind('<FocusOut>')

        self.option_box.delete(0, tk.END)

        for opt in options:
            self.option_box.insert(tk.END, opt)

        root = self.winfo_toplevel()
        pos_x = self.sel_label.winfo_rootx() - root.winfo_x()
        pos_y = self.winfo_rooty() - root.winfo_y()
        height = min(len(options), self.max_height)*14 + 4
        # NEED TO DO BOUNDS CHECKING FOR THE HEIGHT TO MAKE
        # SURE IT DOESNT GO OFF THE EDGE OF THE TOPLEVEL

        if len(options) > self.max_height:
            self.option_bar.pack(side='left', fill='y')

        self.option_frame.place(
            x=pos_x - 4, anchor=tk.NW, y=pos_y + self.winfo_reqheight() - 32,
            height=height, width=self.sel_label.winfo_reqwidth() +
            self.arrow_button.winfo_reqwidth())
        # make a binding to the parent Toplevel to remove the
        # options box if the mouse is clicked outside of it.
        self.click_outside_funcid = self.winfo_toplevel().bind(
            '<Button>', lambda e, s=self: s.click_outside_option_box(e))
        self.option_bar.focus_set()
        self.option_box_visible = True

        self.option_box.select_set(self.f_widget_parent.sel_index)
        self.option_box.see(self.f_widget_parent.sel_index)

    def update_label(self):
        parent = self.f_widget_parent
        option = parent.get_option()
        if not option:
            option = ""
        self.sel_label.config(text=option, anchor="w")
