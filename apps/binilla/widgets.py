'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import tkinter as tk

from time import time
from traceback import format_exc

from . import editor_constants as e_c

win_10_pad = 2


class BinillaWidget():
    '''
    This class exists solely as an easy way to change
    the config properties of the widgets in Binilla.
    '''
    # PADDING
    vertical_padx = e_c.VERTICAL_PADX
    vertical_pady = e_c.VERTICAL_PADY
    horizontal_padx = e_c.HORIZONTAL_PADX
    horizontal_pady = e_c.HORIZONTAL_PADY

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
    button_color = e_c.BUTTON_COLOR 

    text_normal_color = e_c.TEXT_NORMAL_COLOR
    text_disabled_color = e_c.TEXT_DISABLED_COLOR
    text_highlighted_color = e_c.TEXT_HIGHLIGHTED_COLOR

    enum_normal_color = e_c.ENUM_NORMAL_COLOR 
    enum_disabled_color = e_c.ENUM_DISABLED_COLOR 
    enum_highlighted_color = e_c.ENUM_HIGHLIGHTED_COLOR

    entry_normal_color = e_c.ENTRY_NORMAL_COLOR 
    entry_disabled_color = e_c.ENTRY_DISABLED_COLOR 
    entry_highlighted_color = e_c.ENTRY_HIGHLIGHTED_COLOR

    io_fg_color = e_c.IO_FG_COLOR
    io_bg_color = e_c.IO_BG_COLOR
    invalid_path_color = e_c.INVALID_PATH_COLOR
    tooltip_bg_color = e_c.TOOLTIP_BG_COLOR

    # MISC
    title_width = e_c.TITLE_WIDTH
    enum_menu_width = e_c.ENUM_MENU_WIDTH
    scroll_menu_width = e_c.SCROLL_MENU_WIDTH
    min_entry_width = e_c.MIN_ENTRY_WIDTH
    textbox_height = e_c.TEXTBOX_HEIGHT
    textbox_width = e_c.TEXTBOX_WIDTH

    bool_frame_min_width = e_c.BOOL_FRAME_MIN_WIDTH
    bool_frame_min_height = e_c.BOOL_FRAME_MIN_HEIGHT
    bool_frame_max_width = e_c.BOOL_FRAME_MAX_WIDTH
    bool_frame_max_height = e_c.BOOL_FRAME_MAX_HEIGHT

    def_int_entry_width = e_c.DEF_INT_ENTRY_WIDTH
    def_float_entry_width = e_c.DEF_FLOAT_ENTRY_WIDTH
    def_string_entry_width = e_c.DEF_STRING_ENTRY_WIDTH

    max_int_entry_width = e_c.MAX_INT_ENTRY_WIDTH
    max_float_entry_width = e_c.MAX_FLOAT_ENTRY_WIDTH
    max_string_entry_width = e_c.MAX_STRING_ENTRY_WIDTH

    scroll_menu_max_width = e_c.SCROLL_MENU_MAX_WIDTH
    scroll_menu_max_height = e_c.SCROLL_MENU_MAX_HEIGHT

    tooltip_string = None


class ScrollMenu(tk.Frame, BinillaWidget):
    '''
    Used as a menu for certain FieldWidgets, such as when
    selecting an array element or an enumerator option.
    '''
    disabled = False
    sel_index = None
    f_widget_parent = None
    option_box = None
    max_height = None
    max_index = 0

    options_sane = False
    selecting = False  # prevents multiple selections at once

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

    default_entry_text = ''

    menu_width = BinillaWidget.scroll_menu_width

    def __init__(self, *args, **kwargs):
        self.sel_index = kwargs.pop('sel_index', -1)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent', None)
        self.menu_width = kwargs.pop('menu_width', self.menu_width)
        self.options_sane = kwargs.pop('options_sane', False)
        self.default_entry_text = kwargs.pop('default_entry_text', '')
        disabled = kwargs.pop('disabled', False)

        if self.max_height is None:
            self.max_height = self.scroll_menu_max_height

        kwargs.update(relief='sunken', bd=self.listbox_depth,
                      bg=self.default_bg_color)
        tk.Frame.__init__(self, *args, **kwargs)

        self.sel_label = tk.Label(
            self, bg=self.enum_normal_color, fg=self.text_normal_color,
            bd=2, relief='groove', width=self.menu_width)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', height=18, width=18,
                                     bd=0, bg=self.default_bg_color)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(
            self.button_frame, bd=self.button_depth, text="▼", width=1,
            bg=self.button_color, activebackground=self.button_color,
            fg=self.text_normal_color)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill=None, expand=False)
        self.arrow_button.pack(side="left", fill='both', expand=True)

        # make the option box to populate
        self.option_frame = tk.Frame(
            self.winfo_toplevel(), highlightthickness=0, bd=0)
        self.option_frame.pack_propagate(0)
        self.option_bar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.option_box = tk.Listbox(
            self.option_frame, highlightthickness=0,
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.enum_highlighted_color,
            selectforeground=self.text_highlighted_color,
            yscrollcommand=self.option_bar.set, width=self.menu_width)
        self.option_bar.config(command=self.option_box.yview)

        # make sure the TagWindow knows these widgets are scrollable
        for w in (self.sel_label, self.button_frame, self.arrow_button,
                  self.option_frame, self.option_bar, self.option_box):
            w.can_scroll = self.can_scroll

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

        if disabled:
            self.disable()

    def _mousewheel_scroll(self, e):
        if self.option_box_visible or self.disabled:
            return
        elif e.delta > 0:
            self.decrement_sel()
        elif e.delta < 0:
            self.increment_sel()

    def click_outside_option_box(self, e):
        if not self.option_box_visible or self.disabled:
            return
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        if under_mouse not in (self.option_frame, self.option_bar,
                               self.option_box, self.sel_label,
                               self.arrow_button):
            self.select_menu()

    def decrement_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_index = [int(i) - 1 for i in self.option_box.curselection()]
        if sel_index < 0:
            new_index = 0
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.sel_index = sel_index
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.f_widget_parent.select_option(sel_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def decrement_sel(self, e=None):
        if self.selecting:
            return
        new_index = self.sel_index - 1
        if new_index < 0:
            new_index = 0
        try:
            self.selecting = True
            self.sel_index = new_index
            self.f_widget_parent.select_option(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def destroy(self):
        if self.click_outside_funcid is not None:
            self.winfo_toplevel().unbind('<Button>', self.click_outside_funcid)
        tk.Frame.destroy(self)

    def deselect_option_box(self, e=None):
        if self.disabled:
            self.config(bg=self.enum_disabled_color)
            self.sel_label.config(bg=self.enum_disabled_color,
                                  fg=self.text_disabled_color)
        else:
            self.config(bg=self.enum_normal_color)
            self.sel_label.config(bg=self.enum_normal_color,
                                  fg=self.text_normal_color)

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
        self.sel_label.config(bg=self.enum_disabled_color,
                              fg=self.text_disabled_color)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=self.enum_normal_color,
                              fg=self.text_normal_color)
        self.arrow_button.config(state='normal')

    def increment_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_index = [int(i) + 1 for i in self.option_box.curselection()]
        if sel_index > self.max_index:
            new_index = self.max_index
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.sel_index = sel_index
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.f_widget_parent.select_option(sel_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def increment_sel(self, e=None):
        if self.selecting:
            return
        new_index = self.sel_index + 1
        if new_index > self.max_index:
            new_index = self.max_index
        try:
            self.selecting = True
            self.sel_index = new_index
            self.f_widget_parent.select_option(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def select_menu(self, e=None):
        sel_index = [int(i) for i in self.option_box.curselection()]
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
            if self.option_box_visible:
                self.sel_label.config(bg=self.enum_highlighted_color,
                                      fg=self.text_highlighted_color)

    def show_menu(self):
        options = self.f_widget_parent.options
        if not (self.max_index + 1):
            return

        self.arrow_button.unbind('<FocusOut>')
        option_cnt = self.max_index + 1

        if not self.options_sane:
            END = tk.END
            self.option_box.delete(0, END)
            insert = self.option_box.insert
            def_str = '%s' + ('. %s' % self.default_entry_text)
            for i in range(option_cnt):
                if i in options:
                    insert(END, options[i])
                else:
                    insert(END, def_str % i)

            self.options_sane = True

        self.option_box.pack(side='left', expand=True, fill='both')

        self_height = self.winfo_reqheight()
        root = self.winfo_toplevel()

        pos_x = self.sel_label.winfo_rootx() - root.winfo_x()
        pos_y = self.winfo_rooty() + self_height - root.winfo_y()
        height = min(option_cnt, self.max_height)*(14 + win_10_pad) + 4
        width = (self.sel_label.winfo_width() +
                 self.arrow_button.winfo_width())

        # figure out how much space is above and below where the list will be
        space_above = pos_y - self_height - 32
        space_below = (root.winfo_height() + 32 - pos_y - 4)

        # if there is more space above than below, swap the position
        if space_below >= height:
            pass
        elif space_above <= space_below:
            # there is more space below than above, so cap by the space below
            height = min(height, space_below)
        elif space_below < height:
            # there is more space above than below and the space below
            # isnt enough to fit the height, so cap it by the space above
            height = min(height, space_above)
            pos_y = pos_y - self_height - height + 4

        # pack the scrollbar is there isnt enough room to display the list
        if option_cnt > self.max_height or (height - 4)//14 < option_cnt:
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

        if self.sel_index >= option_cnt:
            self.sel_index = self.max_index

        self.option_box.select_clear(0, tk.END)
        try:
            self.option_box.select_set(self.sel_index)
            self.option_box.see(self.sel_index)
        except Exception:
            pass

    def update_label(self):
        if self.sel_index == -1:
            option = ''
        else:
            option = self.f_widget_parent.get_option()
            if option is None:
                option = '%s. %s' % (self.sel_index, self.default_entry_text)
        self.sel_label.config(text=option, anchor="w")


class ToolTipHandler(BinillaWidget):
    app_root = None
    tag_window = None
    tip_window = None
    focus_widget = None

    hover_time = 1.0
    rehover_time = 0.5
    hover_start = 0.0
    rehover_start = 0.0

    curr_tip_text = ''

    # run the check 30 times a second
    schedule_rate = int(1000/30)
    last_mouse_x = 0
    last_mouse_y = 0

    tip_offset_x = 15
    tip_offset_y = 0

    def __init__(self, app_root, *args, **kwargs):
        self.app_root = app_root
        self.hover_start = time()

        # begin the looping
        app_root.after(int(self.schedule_rate), self.check_loop)

    def check_loop(self):
        # get the widget under the mouse
        root = self.app_root
        mouse_x, mouse_y = root.winfo_pointerx(), root.winfo_pointery()

        mouse_dx = mouse_x - self.last_mouse_x
        mouse_dy = mouse_y - self.last_mouse_y

        self.last_mouse_x = mouse_x
        self.last_mouse_y = mouse_y

        # move the tip_window to where it needs to be
        if self.tip_window and mouse_dx or mouse_dy:
            try: self.tip_window.geometry("+%s+%s" % (
                mouse_x + self.tip_offset_x, mouse_y + self.tip_offset_y))
            except Exception: pass

        focus = root.winfo_containing(mouse_x, mouse_y)

        # get the widget in focus if nothing is under the mouse
        #if tip_widget is None:
        #    focus = root.focus_get()

        try: tip_text = focus.tooltip_string
        except Exception: tip_text = None

        curr_time = time()

        if self.curr_tip_text != tip_text and self.tip_window:
            # a tip window is displayed and the focus is different
            self.hide_tip()
            self.rehover_start = curr_time

        if self.tip_window is None:
            # no tip window is displayed, so start trying to display one

            can_display = (curr_time >= self.hover_time + self.hover_start or
                           curr_time <= self.rehover_time + self.rehover_start)
            
            if not tip_text:
                # reset the hover counter cause nothing is under focus
                self.hover_start = curr_time
            elif focus is not self.focus_widget:
                # start counting how long this widget has been in focus
                self.hover_start = curr_time
                self.focus_widget = focus
            elif can_display:
                # reached the hover time! display the tooltip window
                self.show_tip(mouse_x + self.tip_offset_x,
                              mouse_y + self.tip_offset_y, tip_text)
                self.curr_tip_text = tip_text

        self.app_root.after(self.schedule_rate, self.check_loop)

    def show_tip(self, pos_x, pos_y, tip_text):
        if self.tip_window:
            return

        self.tip_window = tk.Toplevel(self.app_root)
        self.tip_window.wm_overrideredirect(1)
        self.tip_window.wm_geometry("+%d+%d" % (pos_x, pos_y))
        label = tk.Label(
            self.tip_window, text=tip_text, justify='left', relief='solid',
            bg=self.tooltip_bg_color, fg=self.text_normal_color, borderwidth=1)
        label.pack()

    def hide_tip(self):
        try: self.tip_window.destroy()
        except Exception: pass
        self.tip_window = None
        self.focus_widget = None
