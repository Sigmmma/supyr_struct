import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_const

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
        self.root_canvas = rc = tk.Canvas(self)
        self.root_frame = rf = tk.Frame(rc)

        # create and set the x and y scrollbars for the root_canvas
        self.root_hsb = tk.Scrollbar(
            self, orient='horizontal', command=rc.xview)
        self.root_vsb = tk.Scrollbar(
            self, orient='vertical', command=rc.yview)
        rc.config(xscrollcommand=self.root_hsb.set,
                  yscrollcommand=self.root_vsb.set)
        rf_id = rc.create_window((0, 0), window=rf, anchor='nw')

        # make it so if this window is selected it changes the
        # selected_tag attribute of self.app_root to self.tag
        self.bind('<Button>', self.select_window)
        self.bind('<FocusIn>', self.select_window)

        # make a couple functions, one to update the size of the canvas
        # when the window is resized and another to update the size of
        # the frame and scrollbars when the canvas is resized
        def _resize_canvas(event):
            rf_w, rf_h = (rf.winfo_reqwidth(), rf.winfo_reqheight())
            rc.config(scrollregion="0 0 %s %s" % (rf_w, rf_h))
            if rf_w != rc.winfo_width(): rc.config(width=rf_w)
            if rf_h != rc.winfo_height(): rc.config(height=rf_h)

        def _resize_frame(event):
            rc_w, rc_h = (rc.winfo_reqwidth(), rc.winfo_reqheight())
            item_cfg = rc.itemconfigure
            if rf.winfo_reqwidth() != rc_w:  item_cfg(rf_id, width=rc_w)
            if rf.winfo_reqheight() != rc_h: item_cfg(rf_id, height=rc_h)

        rf.bind('<Configure>', _resize_canvas)
        rc.bind('<Configure>', _resize_frame)

        # make the window not show up on the start bar
        self.transient(self.app_root)

        # populate the window
        self.populate()

        # pack da stuff
        self.root_hsb.pack(side=t_const.BOTTOM, fill='x')
        self.root_vsb.pack(side=t_const.RIGHT,  fill='y')
        rc.pack(side='left', fill='both', expand=True)

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

    def select_window(self, event):
        '''Makes this windows tag the selected tag in self.app_root'''
        self.app_root.selected_tag = self.tag

    def populate(self):
        '''
        Destroys the FieldWidget attached to this TagWindow and rebuilds it.
        '''
        # Destroy everything
        if hasattr(self.field_widget, 'destroy'):
            self.field_widget.destroy()
            self.field_widget = None

        # Get the desc of the top block in the tag
        root_block = self._tag.data

        # Get the widget to build
        widget_cls = self.widget_picker.get_widget(root_block.desc)
        return
        # Rebuild everything
        self.field_widget = widget_cls(self.root_frame, node=root_block)

    def update_title(self, new_title=None):
        if new_title is None:
            new_title = self._tag.filepath
        self.title(new_title)

    @property
    def tag(self):
        return self._tag
