import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_const

from .widgets import *
from .widget_picker import *

__all__ = ("TagWindow", )


class TagWindow(tk.Toplevel):
    _tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
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
        self.root_canvas = root = tk.Canvas(self)

        # create and set the x and y scrollbars for the canvas root
        root.hsb = tk.Scrollbar(self, orient='horizontal', command=root.xview)
        root.vsb = tk.Scrollbar(self, orient='vertical',   command=root.yview)
        root.config(xscrollcommand=root.hsb.set, yscrollcommand=root.vsb.set)
        
        root.hsb.pack(side=t_const.BOTTOM, fill='x')
        root.vsb.pack(side=t_const.RIGHT,  fill='y')
        root.pack(side='left', fill='both', expand=True)

        # make it so if this window is selected it changes the
        # selected_tag attribute of self.app_root to self.tag
        self.bind('<Button>', self.select_window)
        self.bind('<FocusIn>', self.select_window)

        # make the window not show up on the start bar
        self.transient(self.app_root)

    def destroy(self):
        '''
        Handles destroying this Toplevel and removing the tag from app_root.
        '''
        try:
            tag = self._tag
            del self._tag  # de-reference so that delete_tag doesnt cause a loop
            self.app_root.delete_tag(tag)
            del tag
        except Exception:
            pass
        tk.Toplevel.destroy(self)

    def select_window(self, event):
        '''Makes this windows tag the selected tag in self.app_root'''
        self.app_root.selected_tag = self.tag

    def update_title(self, title=None):
        if title is None:
            self.title(self._tag.filepath)
        else:
            self.title(title)

    @property
    def tag(self):
        return self._tag
