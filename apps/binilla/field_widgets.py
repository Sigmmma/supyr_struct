import tkinter as tk
import tkinter.ttk

from tkinter import constants as t_const
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from . import constants as const
from . import editor_constants as e_const
from . import widgets

__all__ = (
    "fix_widget_kwargs", "FieldWidget",
    "NodeFrame", "NullFrame", "ArrayMenu", "BoolCanvas",
    "DataFieldWidget", "DataEntry", "DataText", "EnumMenu",
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

    # The FieldWidget that contains this one. If this is None,
    # it means that this is the root of the FieldWidget tree.
    f_widget_parent = None

    # A list of the id's of the widgets that are parented
    # to this widget, in the order that they were created
    f_widget_ids = None

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
        self.f_widget_parent = kwargs.get('f_widget_parent', None)

        if self.node is None:
            assert self.parent is not None
            self.node = self.parent[self.attr_index]

        # if custom padding is given, set it
        self.pad_l = kwargs.get('pad_l', self.pad_l)
        self.pad_r = kwargs.get('pad_r', self.pad_r)
        self.pad_t = kwargs.get('pad_t', self.pad_t)
        self.pad_b = kwargs.get('pad_b', self.pad_b)

        self.f_widget_ids = []

    @property
    def desc(self):
        if hasattr(self.node, 'desc'):
            return self.node.desc
        elif hasattr(self.parent, 'get_desc') and self.attr_index is not None:
            return self.parent.get_desc(self.attr_index)
        raise AttributeError("Cannot locate a descriptor for this node.")

    @property
    def gui_name(self):
        '''The gui_name of the node of this FieldWidget.'''
        desc = self.desc
        return desc.get('GUI_NAME',
                        desc.get('NAME', '<UNNAMED>').replace('_', ' '))

    @property
    def name(self):
        '''The name of the node of this FieldWidget.'''
        return self.desc['NAME']

    @property
    def node_ext(self):
        '''The export extension of this FieldWidget.'''
        desc = self.desc
        return desc.get('NODE_EXT', '.%s' % desc['NAME'])

    def export_node(self):
        '''Prompts the user for a location to export the node and exports it'''
        try:
            initialdir = self.root_app.curr_dir
        except AttributeError:
            initialdir = None

        ext = self.node_ext

        filepath = asksaveasfilename(
            initialdir=initialdir, defaultextension=ext,
            filetypes=[(self.name, "*" + ext), ('All', '*')],
            title="Export '%s' to..." % self.name)

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

        ext = self.node_ext

        filepath = askopenfilename(
            initialdir=initialdir, defaultextension=ext,
            filetypes=[(self.name, "*" + ext), ('All', '*')],
            title="Import '%s' from..." % self.name)

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
            self.populate(True)
        except Exception:
            print(format_exc())

    def populate(self, rebuild=False):
        '''Destroys and rebuilds this widgets children.'''

        # destroy all the child widgets
        # c.destroy also removes each widget from self.children
        for c in list(self.children.values()):
            c.destroy()

        # clear the f_widget_ids list
        del self.f_widget_ids[:]

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

    def update_widgets(self, attr_index=None):
        '''Goes through this widgets children, supplies them with
        their node, and sets the value of their fields properly.'''
        pass

    # Make some of the tkinter methods into properties for cleaner access
    @property
    def height(self): return self.winfo_height(self)
    @property
    def width(self): return self.winfo_width(self)
    @property
    def pos_x(self): return self.winfo_x(self)
    @property
    def pos_y(self): return self.winfo_y(self)

'''
TODO:
    Make the widgets friggen work obviously
    Widgets will need to use the place command to position their children
    Make a Null widget to use when a field doesnt have a widget to display it


NODES:
    Use Menu.post() and Menu.unpost to allow displaying cascade menus anywhere
'''

class NodeFrame(tk.Frame, FieldWidget):
    # NEED TO MAKE FIELD LABEL NAMES A SINGLE LONG CANVAS THAT
    # RUNS VERTICALLY IN PARALLEL WITH THE SUB-WIDGETS.
    # THIS WILL MAKE THE PROGRAM A BIT FASTER SINCE THE NAMES
    # WONT NEED TO BE REDRAWN WHEN THE SUBWIDGETS ARE REDRAWN
    pad_l = e_const.NODE_FRAME_PAD_L
    pad_r = e_const.NODE_FRAME_PAD_R
    pad_t = e_const.NODE_FRAME_PAD_T
    pad_b = e_const.NODE_FRAME_PAD_B

    pack_options = None
    show = None

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the first char
        kwargs.setdefault('relief', 'sunken')
        kwargs.setdefault('borderwidth', 1)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.pack_options = kwargs.get(
            'pack_options', {})  # options to pack the subframe
        self.show = tk.IntVar()
        self.show.set(0)

        # if the orientation is vertical, make a title frame
        if orient == 'v':
            self.title = tk.Frame(self)
            title_label = tk.Label(self.title, text=self.name)
            self.import_btn = tk.Button(
                self.title, width=5, text='import', command=self.import_node)
            self.export_btn = tk.Button(
                self.title, width=5, text='export', command=self.export_node)
            self.toggle_btn = ttk.Checkbutton(
                self.title, width=4, text='show', command=self.toggle,
                variable=self.show, style='Toolbutton')

            title_label.pack(fill="x", expand=1, side="left")
            self.toggle_btn.pack(side="right")
            self.export_btn.pack(side="right")
            self.import_btn.pack(side="right")
            self.title.pack(fill="x", expand=1)
        else:
            pass

        self.populate()

    def populate(self):
        self.content = tk.Frame(self, relief="sunken", borderwidth=1)

    def toggle(self):
        if self.show.get():
            self.populate()
            self.toggle_btn.configure(text='hide')
        else:
            self.content.forget()
            self.toggle_btn.configure(text='show')


class NullFrame(NodeFrame):

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.show = tk.IntVar(); self.show.set(0)
        self.populate()

    def populate(self):
        pass


class ArrayMenu(NodeFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''
    # use ttk.Combobox for the dropdown list
    # also make the array collapsable

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('relief', 'sunken')
        kwargs.setdefault('borderwidth', 1)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.pack_options = kwargs.get(
            'pack_options', {})  # options to pack the subframe
        self.show = tk.IntVar()
        self.show.set(0)

        # make the title, element menu, and all the buttons
        title_label = tk.Label(self, text=self.name)
        self.content = tk.Frame(self, relief="raised", borderwidth=1)
        # MAKE THE ENTRY SELECTION MENU
        self.add_btn = tk.Button(
            self, width=3, text='add', command=self.add_entry)
        self.insert_btn = tk.Button(
            self, width=6, text='insert', command=self.insert_entry)
        self.duplicate_btn = tk.Button(
            self, width=9, text='duplicate', command=self.duplicate_entry)
        self.delete_btn = tk.Button(
            self, width=6, text='delete', command=self.delete_entry)
        self.delete_all_btn = tk.Button(
            self, width=10, text='delete all', command=self.delete_all_entries)

        self.import_btn = tk.Button(
            self, width=5, text='import', command=self.import_node)
        self.export_btn = tk.Button(
            self, width=5, text='export', command=self.export_node)
        self.toggle_btn = ttk.Checkbutton(
            self, width=4, text='show', command=self.toggle,
            variable=self.show, style='Toolbutton')

        # pack the title, element menu, and all the buttons
        title_label.pack(fill="x", expand=1, side="left")
        # PACK THE ENTRY SELECTION MENU
        self.toggle_btn.pack(side="right")
        self.export_btn.pack(side="right")
        self.import_btn.pack(side="right")

        self.delete_all_btn.pack(side="right")
        self.delete_btn.pack(side="right")
        self.duplicate_btn.pack(side="right")
        self.insert_btn.pack(side="right")
        self.add_btn.pack(side="right")
        self.title.pack(fill="x", expand=1)
        self.content.pack(fill="both", expand=1)

        self.populate()

    def add_entry(self):
        pass

    def insert_entry(self):
        pass

    def duplicate_entry(self):
        pass

    def delete_entry(self):
        pass

    def delete_all_entries(self):
        pass

    def populate(self):
        pass


class BoolCanvas(tk.Canvas, FieldWidget):
    '''Used for bool type nodes. Creates checkbuttons for
    each boolean option and resizes itself to fit them.'''
    # use a listbox for the names running parallel to the
    # checkboxes and give the frame a vertical scrollbar.
    pad_l = e_const.NODE_CANVAS_PAD_L
    pad_r = e_const.NODE_CANVAS_PAD_R
    pad_t = e_const.NODE_CANVAS_PAD_T
    pad_b = e_const.NODE_CANVAS_PAD_B

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Canvas.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.populate()


# These classes are the widgets that are actually
# interacted with to edit the data in a node.
class DataFieldWidget(NodeFrame):
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
    '''Used for strings that likely will not fit on one line.'''

    def __init__(self, *args, **kwargs):
        DataFieldWidget.__init__(self, *args, **kwargs)
        tk.Text.__init__(self, *args, **fix_widget_kwargs(**kwargs))


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
