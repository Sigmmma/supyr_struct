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

class BinillaWidget():
    # PADDING
    vertical_pad_x = e_c.VERTICAL_PADX
    vertical_pad_y = e_c.VERTICAL_PADY
    horizontal_pad_x = e_c.HORIZONTAL_PADX
    horizontal_pad_y = e_c.HORIZONTAL_PADY

    # DEPTHS
    comment_depth = e_c.COMMENT_DEPTH
    listbox_depth = e_c.LISTBOX_DEPTH
    entry_depth = e_c.ENTRY_DEPTH
    button_depth = e_c.BUTTON_DEPTH
    frame_depth = e_c.FRAME_DEPTH

    # COLORS
    default_bg_color = e_c.DEFAULT_BG_COLOR
    comment_bg_color = e_c.COMMENT_BG_COLOR
    frame_bg_color = e_c.FRAME_BG_COLOR

    text_normal_color = e_c.TEXT_NORMAL_COLOR
    text_disabled_color = e_c.TEXT_DISABLED_COLOR
    text_selected_color = e_c.TEXT_SELECTED_COLOR
    text_highlighted_color = e_c.TEXT_HIGHLIGHTED_COLOR

    enum_normal_color = e_c.ENUM_NORMAL_COLOR 
    enum_disabled_color = e_c.ENUM_DISABLED_COLOR 
    enum_selected_color = e_c.ENUM_SELECTED_COLOR

    io_fg_color = e_c.IO_FG_COLOR
    io_bg_color = e_c.IO_BG_COLOR

    # MISC
    title_width = e_c.TITLE_WIDTH
    scroll_menu_size = e_c.SCROLL_MENU_SIZE


class ScrollMenu(tk.Frame, BinillaWidget):
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

    options_sane = False

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

    def __init__(self, *args, **kwargs):
        sel_index = kwargs.pop('sel_index', -1)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent')

        kwargs.update(relief='sunken', bd=2, bg=self.default_bg_color)
        tk.Frame.__init__(self, *args, **kwargs)

        self.sel_label = tk.Label(self, bd=2, bg=self.enum_normal_color,
                                  relief='groove', width=self.scroll_menu_size)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', height=18, width=18,
                                     bd=0, bg=self.default_bg_color)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(self.button_frame,
                                      bd=self.button_depth, text="▼",
                                      width=1, bg=self.default_bg_color)
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
        self.sel_index = sel_index
        self.option_box.select_set(sel_index)
        self.option_box.see(sel_index)
        self.f_widget_parent.select_option(sel_index)

    def decrement_sel(self, e=None):
        new_index = self.sel_index - 1
        if new_index < 0:
            return
        self.sel_index = new_index
        self.f_widget_parent.select_option(new_index)

    def destroy(self):
        if self.click_outside_funcid is not None:
            self.winfo_toplevel().unbind('<Button>', self.click_outside_funcid)
        tk.Frame.destroy(self)

    def deselect_option_box(self, e=None):
        if self.disabled:
            self.config(bg=self.enum_disabled_color)
            self.sel_label.config(bg=self.enum_disabled_color)
        else:
            self.config(bg=self.enum_normal_color)
            self.sel_label.config(bg=self.enum_normal_color)

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
        self.config(bg=self.enum_disabled_color)
        self.sel_label.config(bg=self.enum_disabled_color)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=self.enum_normal_color)
        self.arrow_button.config(state='normal')

    def increment_listbox_sel(self, e=None):
        sel_index = self.option_box.curselection()[0] + 1
        if sel_index > self.max_index:
            return
        self.option_box.select_clear(0, tk.END)
        self.sel_index = sel_index
        self.option_box.select_set(sel_index)
        self.option_box.see(sel_index)
        self.f_widget_parent.select_option(sel_index)

    def increment_sel(self, e=None):
        new_index = self.sel_index + 1
        if new_index > self.max_index:
            return
        self.sel_index = new_index
        self.f_widget_parent.select_option(new_index)

    def select_menu(self, e=None):
        sel_index = self.option_box.curselection()
        if not sel_index:
            return
        self.sel_index = sel_index[0]
        self.f_widget_parent.select_option(self.sel_index)
        self.deselect_option_box()
        self.arrow_button.focus_set()
        self.arrow_button.bind('<FocusOut>', self.deselect_option_box)

    def click_label(self, e=None):
        if self.option_box_visible:
            self.select_menu()
        else:
            self.select_option_box()

    def select_option_box(self, e=None):
        if not self.disabled:
            self.show_menu()
            self.sel_label.config(bg=self.enum_selected_color)

    def show_menu(self):
        options = self.f_widget_parent.options
        if not len(options):
            return

        self.arrow_button.unbind('<FocusOut>')

        if not self.options_sane:
            END = tk.END
            self.option_box.delete(0, END)
            insert = self.option_box.insert
            for opt in options:
                insert(END, opt)

            self.options_sane = True

        self_height = self.winfo_reqheight()
        root = self.winfo_toplevel()

        pos_x = self.sel_label.winfo_rootx() - root.winfo_x()
        pos_y = self.winfo_rooty() + self_height - root.winfo_y()
        height = min(len(options), self.max_height)*14 + 4
        width = (self.sel_label.winfo_reqwidth() +
                 self.arrow_button.winfo_reqwidth())

        # figure out how much space is above and below where the list will be
        space_above = pos_y - self_height - 32
        space_below = (root.winfo_height() + 32 - pos_y - 4)

        # if there is more space above than below, swap the position
        if space_above <= space_below or space_below < height:
            height = min(height, space_below)
        elif space_above > space_below:
            height = min(height, space_above)
            pos_y = pos_y - self_height - height + 4

        if len(options) > self.max_height:
            self.option_bar.pack(side='left', fill='y')
        else:
            # place it off the frame so it can still be used for key bindings
            self.option_bar.place(x=pos_x + width, y=pos_y, anchor=tk.NW)
        self.option_bar.focus_set()

        self.option_frame.place(x=pos_x - 4, y=pos_y - 32, anchor=tk.NW,
                                height=height, width=width)
        # make a binding to the parent Toplevel to remove the
        # options box if the mouse is clicked outside of it.
        self.click_outside_funcid = self.winfo_toplevel().bind(
            '<Button>', lambda e, s=self: s.click_outside_option_box(e))
        self.option_box_visible = True

        self.option_box.select_set(self.f_widget_parent.sel_index)
        self.option_box.see(self.f_widget_parent.sel_index)

    def update_label(self):
        parent = self.f_widget_parent
        option = parent.get_option()
        if option is None:
            option = ""
        self.sel_label.config(text=option, anchor="w")
