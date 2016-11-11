import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_const

from .widgets import *
from .widget_picker import *

__all__ = ("TagWindow", )


class TagWindow(tk.Toplevel):
    tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
    widget_picker = def_widget_picker  # the WidgetPicker to use for selecting
    #                                    the widget to build when populating

    '''
    TODO:
        Make window transient(doesnt show up on start bar)
        Write widget creation routine
    '''

    def __init__(self, master, tag, *args, **kwargs):
        self.tag = tag
        self.app_root = kwargs.pop('app_root', master)
        if 'widget_picker' in kwargs:
            self.widget_picker = kwargs.pop('widget_picker')
        elif hasattr(self.app_root, 'widget_picker'):
            self.widget_picker = self.app_root.widget_picker

        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.update_title()

        #create the root_canvas and the root_frame within the canvas
        self.root_canvas = root = tk.Canvas(self)

        #create and set the x and y scrollbars for the canvas root
        root.hsb = tk.Scrollbar(self, orient='horizontal', command=root.xview)
        root.vsb = tk.Scrollbar(self, orient='vertical',   command=root.yview)
        root.config(xscrollcommand=root.hsb.set, yscrollcommand=root.vsb.set)
        
        root.hsb.pack(side=t_const.BOTTOM, fill='x')
        root.vsb.pack(side=t_const.RIGHT,  fill='y')
        root.pack(side='left', fill='both', expand=True)

    def destroy(self):
        '''
        Handles destroying this Toplevel and removing the tag from app_root.
        '''
        try:
            tag = self.tag
            del self.tag  # de-reference so that delete_tag doesnt cause a loop
            self.app_root.delete_tag(tag)
            del tag
        except Exception:
            pass
        tk.Toplevel.destroy(self)

    def update_title(self, title=None):
        if title is None:
            self.title(self.tag.filepath)
        else:
            self.title(title)
