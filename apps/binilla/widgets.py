'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import tkinter as tk


class BoolCheckbutton(tk.Checkbutton):
    '''Used inside a BoolCanvas for each of
    the individual boolean options available.'''

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")

        DataFieldWidget.__init__(self, *args, **kwargs)

        kwargs["command"] = lambda: self.check(i)
        tk.CheckButton.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def check(self, i):
        self._func(self, i)
