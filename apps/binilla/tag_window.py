import gc
import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_c
from .field_widgets import *
from .widget_picker import *

from traceback import format_exc

__all__ = ("TagWindow", )


class TagWindow(tk.Toplevel):
    tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
    field_widget = None  # the single FieldWidget held in this window
    widget_picker = def_widget_picker  # the WidgetPicker to use for selecting
    #                                    the widget to build when populating

    can_scroll = True

    '''
    TODO:
        Write widget creation routine
    '''

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

        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.update_title()

        # create the root_canvas and the root_frame within the canvas
        self.root_canvas = rc = tk.Canvas(self, highlightthickness=0)
        self.root_frame = rf = tk.Frame(rc, highlightthickness=0)

        # create and set the x and y scrollbars for the root_canvas
        self.root_hsb = tk.Scrollbar(
            self, orient='horizontal', command=rc.xview)
        self.root_vsb = tk.Scrollbar(
            self, orient='vertical', command=rc.yview)
        rc.config(xscrollcommand=self.root_hsb.set,
                  yscrollcommand=self.root_vsb.set)
        self.root_frame_id = rc.create_window((0, 0), window=rf, anchor='nw')

        # make it so if this window is selected it changes the
        # selected_tag attribute of self.app_root to self.tag
        self.bind('<Button>', self.select_window)
        self.bind('<FocusIn>', self.select_window)
        self.bind('<MouseWheel>', self._mousewheel_scroll_y)
        self.bind('<Shift-MouseWheel>', self._mousewheel_scroll_x)

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

    def _mousewheel_scroll_x(self, e):
        focus = self.focus_get()
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        if hasattr(focus, 'can_scroll') and focus.can_scroll:
            return
        elif hasattr(under_mouse, 'can_scroll') and under_mouse.can_scroll:
            return
        
        if self.can_scroll and self.winfo_containing(e.x_root, e.y_root):
            self.root_canvas.xview_scroll(e.delta//120, "units")

    def _mousewheel_scroll_y(self, e):
        focus = self.focus_get()
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        if hasattr(focus, 'can_scroll') and focus.can_scroll:
            return
        elif hasattr(under_mouse, 'can_scroll') and under_mouse.can_scroll:
            return
        
        if self.can_scroll and self.winfo_containing(e.x_root, e.y_root):
            self.root_canvas.yview_scroll(e.delta//-120, "units")

    @property
    def max_height(self):
        # The -64 accounts for the width of the windows border
        return self.winfo_screenheight() - self.winfo_y() - 64

    @property
    def max_width(self):
        # The -8 accounts for the width of the windows border
        return self.winfo_screenwidth() - self.winfo_x() - 8

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

    def _resize_canvas(self, e):
        '''
        Updates the size of the canvas when the window is resized.
        '''
        rf = self.root_frame; rc = self.root_canvas
        rf_w, rf_h = (rf.winfo_reqwidth(), rf.winfo_reqheight())
        rc.config(scrollregion="0 0 %s %s" % (rf_w, rf_h))
        if rf_w != rc.winfo_reqwidth():  rc.config(width=rf_w)
        if rf_h != rc.winfo_reqheight(): rc.config(height=rf_h)

        new_window_height = rf_h + self.root_hsb.winfo_reqheight() + 2
        new_window_width = rf_w + self.root_vsb.winfo_reqwidth() + 2

        # account for the size of the scrollbars when resizing the window
        self.resize_window(new_window_width, new_window_height)

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

    def destroy(self):
        '''
        Handles destroying this Toplevel and removing the tag from app_root.
        '''
        try:
            tag = self.tag
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

    def select_window(self, e):
        '''Makes this windows tag the selected tag in self.app_root'''
        self.app_root.selected_tag = self.tag

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
                                       show_frame=True, app_root=self.app_root)
        self.field_widget.pack(expand=True, fill='both')

    def update_title(self, new_title=None):
        if new_title is None:
            new_title = self.tag.filepath
        self.title(new_title)
