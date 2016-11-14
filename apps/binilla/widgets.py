import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_const
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from . import constants as const
from . import editor_constants as e_const

__all__ = (
    "fix_widget_kwargs", "FieldWidget",
    "NodeFrame", "NullFrame", "ArrayMenu", "BoolFrame",
    "DataCanvas", "DataFieldWidget", "DataEntry",
    "DataText", "BoolCheckbutton", "EnumMenu",
    )


def fix_widget_kwargs(**kw):
    '''Returns a dict where all items in the provided keyword arguments
    that use keys found in e_const.WIDGET_KWARGS are removed.'''
    return {s:kw[s] for s in kw if s not in e_const.WIDGET_KWARGS}


# These classes are used for laying out the visual structure
# of many sub-widgets, and effectively the whole window.
class FieldWidget():
    '''
    Provides the basic methods and attributes for widgets
    to utilize and interact with supyr_structs node trees.

    This class is meant to be subclassed, and is
    not actually a tkinter widget class itself.
    '''
    # The data or Block this widget exposes to viewing/editing
    node = None
    # The parent of the node
    parent = None
    # The index the node is in in the parent. If this is not None,
    # it must be valid to use parent[attr_index] to get the node.
    attr_index = None

    # The amount of padding this widget needs on each side
    pad_l = 0
    pad_r = 0
    pad_t = 0
    pad_b = 0

    def __init__(self, *args, **kwargs):
        self.node = kwargs.get('node', self.node)
        self.parent = kwargs.get('parent', self.parent)
        self.attr_index = kwargs.get('attr_index', self.attr_index)
        self.index = kwargs.get('index', 0)
        self.app_root = kwargs.get('app_root', None)

        if self.node is None:
            assert self.parent is not None
            self.node = self.parent[self.attr_index]

        # if custom padding were given, set it
        self.pad_l = kwargs.get('pad_l', self.pad_l)
        self.pad_r = kwargs.get('pad_r', self.pad_r)
        self.pad_t = kwargs.get('pad_t', self.pad_t)
        self.pad_b = kwargs.get('pad_b', self.pad_b)

        # a list of the id's of the widgets that are parented
        # to this widget, in the order that they were created
        self.field_widget_ids = []

    @property
    def desc(self):
        if hasattr(self.node, 'desc'):
            return self.node.desc
        elif hasattr(self.parent, 'get_desc') and self.attr_index is not None:
            return self.parent.get_desc(self.attr_index)
        raise AttributeError("Cannot locate a descriptor for this node.")

    def export_node(self):
        '''Prompts the user for a location to export the node and exports it'''
        try:
            initialdir = self.root_app.curr_dir
        except AttributeError:
            initialdir = None

        if hasattr(self.node, 'desc'):
            nodename = self.node.NAME.lower()
        else:
            # the node isnt a block, so we need to use
            # its parent to know the name of the node.
            nodename = self.parent.get_desc('NAME', self.attr_index).lower()

        filepath = asksaveasfilename(
            initialdir=initialdir, defaultextension='.' + nodename,
            filetypes=[(nodename, "*." + nodename), ('All', '*')],
            title="Export '%s' to..." % nodename)

        if not filepath:
            return

        try:
            if hasattr(self.node, 'serialize'):
                self.node.serialize(filepath=filepath)
            else:
                # the node isnt a block, so we need to call its parents
                # serialize method with the attr_index necessary to export.
                self.parent.serialize(filepath=filepath,
                                      attr_index=self.attr_index)
        except Exception:
            print(format_exc())

    def import_node(self):
        '''Prompts the user for an exported node file.
        Imports data into the node from the file.'''
        try:
            initialdir = self.root_app.curr_dir
        except AttributeError:
            initialdir = None

        if hasattr(self.node, 'desc'):
            nodename = self.node.NAME.lower()
        else:
            # the node isnt a block, so we need to use
            # its parent to know the name of the node.
            nodename = self.parent.get_desc('NAME', self.attr_index).lower()

        filepath = askopenfilename(
            initialdir=initialdir, defaultextension='.' + nodename,
            filetypes=[(nodename, "*." + nodename), ('All', '*')],
            title="Import '%s' from..." % nodename)

        if not filepath:
            return

        try:
            if hasattr(self.node, 'parse'):
                self.node.parse(filepath=filepath)
            else:
                # the node isnt a block, so we need to call its parents
                # parse method with the attr_index necessary to import.
                self.parent.parse(filepath=filepath,
                                  attr_index=self.attr_index)
            self.build_widgets(True)
        except Exception:
            print(format_exc())

    def build_widgets(self, rebuild=False):
        '''Destroys and rebuilds this widgets children.'''

        # destroy all the child widgets
        # c.destroy also removes each widget from self.children
        for c in list(self.children.values()):
            c.destroy()

        # clear the field_widget_ids list
        del self.field_widget_ids[:]

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

'''
TODO:
    Make the widgets friggen work obviously
    Widgets will need to use the place command to position their children
    Make a Null widget to use when a field doesnt have a widget to display it


NODES:
    Use Menu.post() and Menu.unpost to allow displaying cascade menus anywhere
'''

class NodeFrame(tk.Frame, FieldWidget):
    '''Used for any node which needs to display more
    than one type of widget at a time. Examples include
    structs, containers, arrays, and sets of booleans.'''

    # NEED TO MAKE FIELD LABEL NAMES A SINGLE LONG CANVAS THAT
    # RUNS VERTICALLY IN PARALLEL WITH THE SUB-WIDGETS.
    # THIS WILL MAKE THE PROGRAM A BIT FASTER SINCE THE NAMES
    # WONT NEED TO BE REDRAWN WHEN THE SUBWIDGETS ARE REDRAWN
    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        # set the amount of padding this widget needs on each side
        self.pad_l = e_const.NODE_FRAME_PAD_L
        self.pad_r = e_const.NODE_FRAME_PAD_R
        self.pad_t = e_const.NODE_FRAME_PAD_T
        self.pad_b = e_const.NODE_FRAME_PAD_B
        self.build_widgets()

    # easier to remember aliases for
    height = tk.Misc.winfo_height
    width = tk.Misc.winfo_width
    pos_x = tk.Misc.winfo_x
    pos_y = tk.Misc.winfo_y


class NullFrame(NodeFrame):
    pass


class ArrayMenu(NodeFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''
    # use ttk.Combobox for the dropdown list
    # also make the array collapsable

    # ONLY CALL reload(repose_only=False) IF THE DESCRIPTOR FOR
    # THE SELECTED ARRAY ELEMENT ISN'T THE SAME AS THE PREVIOUS
    # OTHERWISE, CALL reload(repose_only=True)

    def __init__(self, *args, **kwargs):
        NodeFrame.__init__(self, *args, **kwargs)


class BoolFrame(NodeFrame):
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
class DataFieldWidget(FieldWidget):
    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        # set the amount of padding this widget needs on each side
        self.pad_l = e_const.DATA_PAD_L
        self.pad_r = e_const.DATA_PAD_R
        self.pad_t = e_const.DATA_PAD_T
        self.pad_b = e_const.DATA_PAD_B


class DataEntry(tk.Entry, DataFieldWidget):
    '''Used for strings/bytes/bytearrays that
    fit on one line as well as ints and floats.'''

    def __init__(self, *args, **kwargs):
        DataFieldWidget.__init__(self, *args, **kwargs)
        tk.Entry.__init__(self, *args, **fix_widget_kwargs(**kwargs))


class DataText(tk.Text, DataFieldWidget):
    '''Used for strings that likely will not fit on one line.
    NEED TO FIGURE OUT HOW TO DETERMINE WHETHER TO
    USE A DataEntry OR A DataText FOR STRINGS.'''

    def __init__(self, *args, **kwargs):
        DataFieldWidget.__init__(self, *args, **kwargs)
        tk.Text.__init__(self, *args, **fix_widget_kwargs(**kwargs))


class BoolCheckbutton(tk.Checkbutton, DataFieldWidget):
    '''Used inside a BoolFrame for each of
    the individual boolean options available.'''

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")

        DataFieldWidget.__init__(self, *args, **kwargs)

        kwargs["command"] = lambda: self.check(i)
        tk.CheckButton.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def check(self, i):
        self._func(self, i)


class EnumMenu(tk.Button, FieldWidget):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''
    # use ttk.Combobox for the dropdown list

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")

        FieldWidget.__init__(self, *args, **kwargs)
        tk.Button.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.populate()

    def populate(self):
        for i in range(0):
            self.menu.add_command(
                label='SOMELABEL', command=lambda: self.option_select(i))

    def option_select(self, i=None):
        if i is None:
            self._func(self, self.index)
            return
        self.index = i
        self._func(self, i)
