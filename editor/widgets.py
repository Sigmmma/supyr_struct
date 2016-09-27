
import tkinter as tk
import tkinter.ttk

from tkinter.filedialog import asksaveasfilename, askopenfilename, askdirectory
from traceback import format_exc

from . import editor_constants as const


def fix_widget_kwargs(kwargs):
    for string in const.WIDGET_KWARGS:
        try:
            kwargs.pop(string)
        except KeyError:
            pass
    return kwargs


# These classes are used for laying out the visual structure
# of many sub-widgets, and effectively the whole window.
class NodeWidget():
    '''Provides the basic methods and attributes for widgets
    to utilize and interact with supyr_structs node trees.

    This class is meant to be subclassed, and is
    not actually a tkinter widget class itself.'''

    desc = None

    # the amount of padding this widget needs on each side
    pad_l = 0
    pad_r = 0
    pad_t = 0
    pad_b = 0

    def __init__(self, *args, **kwargs):
        self.node = kwargs.get('node', None)
        self.index = kwargs.get('index', 0)
        self.app_root = kwargs.get('app_root', None)

        # if custom padding were given, set it
        if 'pad_l' in kwargs:
            self.pad_l = kwargs['pad_l']
        if 'pad_r' in kwargs:
            self.pad_r = kwargs['pad_r']
        if 'pad_t' in kwargs:
            self.pad_t = kwargs['pad_t']
        if 'pad_b' in kwargs:
            self.pad_b = kwargs['pad_b']

        # a list of the id's of the widgets that are parented
        # to this widget, in the order that they were created
        self.field_widgets = []

    def _export(self):
        '''Prompts the user for a location to export the node.
        Exports the node to the file.'''
        node = self.node
        if hasattr(node, 'NAME'):
            try:
                initialdir = self.root_app.curr_dir
            except AttributeError:
                initialdir = None
            nodename = node.NAME
            filetypes = [(nodename, "*." + nodename), ('All', '*')]
            filepath = asksaveasfilename(initialdir=initialdir,
                                         defaultextension='.' + nodename,
                                         filetypes=filetypes,
                                         title="Export %s to..." % nodename)
            if filepath != "":
                try:
                    node.serialize(filepath=filepath)
                except Exception:
                    print(format_exc())

    def _import(self):
        '''Prompts the user for an exported node file.
        Imports data into the node from the file.'''
        node = self.node
        if hasattr(node, 'NAME'):
            try:
                initialdir = self.root_app.curr_dir
            except AttributeError:
                initialdir = None
            nodename = node.NAME
            filetypes = [(nodename, "*." + nodename), ('All', '*')]
            filepath = askopenfilename(initialdir=initialdir,
                                       defaultextension='.' + nodename,
                                       filetypes=filetypes,
                                       title="Import %s from..." % nodename)
            if filepath != "":
                try:
                    node.parse(filepath=filepath)
                    self.build_widgets(True)
                except Exception:
                    print(format_exc())

    def build_widgets(self, rebuild=False):
        '''Destroys and rebuilds this widgets children.'''

        # destroy all the child widgets
        # c.destroy also removes each widget from self.children
        for c in list(self.children.values()):
            c.destroy()

        # clear the field_widgets list
        del self.field_widgets[:]

        #################################
        '''DO THE WIDGET BUILDING HERE'''
        #################################

        self.repose_widgets(rebuild)

    def repose_widgets(self, repose_master=False):
        '''Recalculates and sets the positions of the
        widgets directly parented to this widget.'''

        # If one of this widgets children was reposed, it and
        # its neighboring siblings may need to be repositioned.
        if repose_master:
            try:
                self.master.repose_widgets(True)
            except AttributeError:
                pass

    def update_widgets(self):
        '''Goes through this widgets children, supplies them with
        their node, and sets the value of their fields properly.'''
        pass


class NodeFrame(tk.Frame, NodeWidget):
    '''Used for any node which needs to display more
    than one type of widget at a time. Examples include
    structs, containers, arrays, and sets of booleans.'''

    # NEED TO MAKE FIELD LABEL NAMES A SINGLE LONG CANVAS THAT
    # RUNS VERTICALLY IN PARALLEL WITH THE SUB-WIDGETS.
    # THIS WILL MAKE THE PROGRAM A BIT FASTER SINCE THE NAMES
    # WONT NEED TO BE REDRAWN WHEN THE SUBWIDGETS ARE REDRAWN
    def __init__(self, *args, **kwargs):
        NodeWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(kwargs))

        # set the amount of padding this widget needs on each side
        self.pad_l = const.NODE_FRAME_PAD_L
        self.pad_r = const.NODE_FRAME_PAD_R
        self.pad_t = const.NODE_FRAME_PAD_T
        self.pad_b = const.NODE_FRAME_PAD_B
        self.build_widgets()

    # easier to remember aliases for
    height = tk.Misc.winfo_height
    width = tk.Misc.winfo_width
    pos_x = tk.Misc.winfo_x
    pos_y = tk.Misc.winfo_y


class ArrayNodeMenu(NodeFrame):
    '''Used for array nodes. Displays a single element of
    the ArrayBlock linked to it, and contains a combobox
    for selecting which array element is displayed.'''
    # use ttk.Combobox for the dropdown list
    # also make the array collapsable

    # ONLY CALL reload(repose_only=False) IF THE DESCRIPTOR FOR
    # THE SELECTED ARRAY ELEMENT ISN'T THE SAME AS THE PREVIOUS
    # OTHERWISE, CALL reload(repose_only=True)

    def __init__(self, *args, **kwargs):
        NodeFrame.__init__(self, *args, **kwargs)

        try:
            self.desc = self.node.desc
        except AttributeError:
            pass


class BoolNodeFrame(NodeFrame):
    '''Used for bool type nodes. Creates checkbuttons for
    each boolean option and resizes itself to fit them.'''
    # use a listbox for the names running parallel to the
    # checkboxes and give the frame a vertical scrollbar.

    def __init__(self, *args, **kwargs):
        NodeFrame.__init__(self, *args, **kwargs)


class DataCanvas():
    pass


# These classes are the widgets that are actually
# interacted with to edit the data in a node.
class DataWidget(NodeWidget):
    def __init__(self, *args, **kwargs):
        NodeWidget.__init__(self, *args, **kwargs)

        # set the amount of padding this widget needs on each side
        self.pad_l = const.DATA_PAD_L
        self.pad_r = const.DATA_PAD_R
        self.pad_t = const.DATA_PAD_T
        self.pad_b = const.DATA_PAD_B


class NodeEntry(tk.Entry, DataWidget):
    '''Used for strings/bytes/bytearrays that
    fit on one line as well as ints and floats.

    NEED TO FIGURE OUT HOW TO DETERMINE WHETHER TO
    USE A NodeEntry OR A NodeText FOR STRINGS.'''

    def __init__(self, *args, **kwargs):
        DataWidget.__init__(self, *args, **kwargs)
        tk.Entry.__init__(self, *args, **fix_widget_kwargs(kwargs))


class NodeText(tk.Text, DataWidget):
    '''Used for strings that likely will not fit on one line.
    NEED TO FIGURE OUT HOW TO DETERMINE WHETHER TO
    USE A NodeEntry OR A NodeText FOR STRINGS.'''

    def __init__(self, *args, **kwargs):
        DataWidget.__init__(self, *args, **kwargs)
        tk.Text.__init__(self, *args, **fix_widget_kwargs(kwargs))


class BoolCheckbutton(tk.Checkbutton, DataWidget):
    '''Used inside a BoolNodeFrame for each of
    the individual boolean options available.'''

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")

        DataWidget.__init__(self, *args, **kwargs)

        kwargs["command"] = lambda: self.check(i)
        tk.CheckButton.__init__(self, *args, **fix_widget_kwargs(kwargs))

    def check(self, i):
        self._func(self, i)


class EnumNodeMenu(tk.Button, NodeWidget):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''
    # use ttk.Combobox for the dropdown list

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")

        NodeWidget.__init__(self, *args, **kwargs)
        tk.Button.__init__(self, *args, **fix_widget_kwargs(kwargs))

        self.populate()

    def populate(self):
        for i in range(0):
            self.menu.add_command(label='SOMELABEL',
                                  command=lambda: self.option_select(i))

    def option_select(self, i=None):
        if i is None:
            self._func(self, self.index)
        else:
            self.index = i
            self._func(self, i)
