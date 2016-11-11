import tkinter as tk
import tkinter.ttk

from .widgets import *
from .widget_picker import *


class TagWindow(tk.Toplevel):
    tag = None

    def __init__(self, master, tag, *args, **kwargs):
        self.tag = tag
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.update_title()

    def update_title(self, title=None):
        if title is None:
            self.title(self.tag.filepath)
        else:
            self.title(title)
