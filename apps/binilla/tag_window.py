import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_c
from .field_widgets import *
from .widget_picker import *

__all__ = ("TagWindow", )


class TagWindow(tk.Toplevel):
    _tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
    field_widget = None  # the single FieldWidget held in this window
    widget_picker = def_widget_picker  # the WidgetPicker to use for selecting
    #                                    the widget to build when populating
    _resizing = False

    '''
    TODO:
        Write widget creation routine
    '''

    def __init__(self, master, tag, *args, **kwargs):
        self._tag = tag
        self.app_root = kwargs.pop('app_root', master)
        if 'widget_picker' in kwargs:
            self.widget_picker = kwargs.pop('widget_picker')
        elif hasattr(self.app_root, 'widget_picker'):
            self.widget_picker = self.app_root.widget_picker

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
        self.bind('<MouseWheel>', self._mousewheel_scroll)

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

    def _mousewheel_scroll(self, e):
        try:
            if self.focus_get().can_scroll:
                return
        except Exception:
            pass
        if self.winfo_containing(e.x_root, e.y_root):
            self.root_canvas.yview_scroll(e.delta//-120, "units")

    def resize_window(self, new_width=None, new_height=None, cap_size=True):
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
            # the -8 and -64 account for the width of the windows border
            max_width = self.winfo_screenwidth() - self.winfo_x() - 8
            max_height = self.winfo_screenheight() - self.winfo_y() - 64

            # if the new width/height is larger than the max, cap them
            if max_width < new_width:   new_width = max_width
            if max_height < new_height: new_height = max_height

        # aint nothin to do if they're the same!
        if new_width == old_width and new_height == old_height:
            return

        self.geometry('%sx%s' % (new_width, new_height))

    def _resize_canvas(self, e):
        '''
        Updates the size of the canvas when the window is resized.
        '''
        rf = self.root_frame; rc = self.root_canvas
        # need to make sure the frame is allowed to update so the requested
        # size is accurate. Without doing this the size can get really wonky
        # DISABLED BECAUSE IT LAGS PRETTY BAD
        #rf.update_idletasks()
        rf_w, rf_h = (rf.winfo_reqwidth(), rf.winfo_reqheight())
        rc.config(scrollregion="0 0 %s %s" % (rf_w, rf_h))
        if rf_w != rc.winfo_reqwidth():  rc.config(width=rf_w)
        if rf_h != rc.winfo_reqheight(): rc.config(height=rf_h)

        # account for the size of the scrollbars when resizing the window
        self.resize_window(rf_w + self.root_vsb.winfo_reqwidth() + 2,
                           rf_h + self.root_hsb.winfo_reqheight() + 2)

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
            tag = self._tag
            del self._tag
            self.app_root.delete_tag(tag)
            del tag
        except Exception:
            pass
        tk.Toplevel.destroy(self)

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
        root_block = self._tag.data

        # Get the widget to build
        widget_cls = self.widget_picker.get_widget(root_block.desc)

        # Rebuild everything
        self.field_widget = widget_cls(self.root_frame, node=root_block,
                                       show_frame=True, app_root=self.app_root)
        self.field_widget.pack(expand=True, fill='both')

    def update_title(self, new_title=None):
        if new_title is None:
            new_title = self._tag.filepath
        self.title(new_title)

    @property
    def tag(self):
        return self._tag
