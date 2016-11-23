import tkinter as tk
import tkinter.ttk as ttk

from tkinter import constants as t_const
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from . import constants as const
from . import widgets
from .editor_constants import *

# linked to through __init__.py
widget_picker = None


__all__ = (
    "fix_widget_kwargs", "FieldWidget",
    "NodeFrame", "NullFrame", "VoidFrame", "ArrayFrame", "BoolCanvas",
    "DataFieldWidget", "DataEntry", "DataText", "EnumMenu",
    )


def fix_widget_kwargs(**kw):
    '''Returns a dict where all items in the provided keyword arguments
    that use keys found in WIDGET_KWARGS are removed.'''
    return {s:kw[s] for s in kw if s not in WIDGET_KWARGS}


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

    # The amount of external padding this widget needs
    padx = 0
    pady = 0

    # whether the widget is being oriented vertically or horizontally
    _vert_oriented = True

    def __init__(self, *args, **kwargs):
        self.node = kwargs.get('node', self.node)
        self.parent = kwargs.get('parent', self.parent)
        self.attr_index = kwargs.get('attr_index', self.attr_index)
        self.app_root = kwargs.get('app_root', None)
        self.f_widget_parent = kwargs.get('f_widget_parent', None)
        self._vert_oriented = bool(kwargs.get('vert_oriented', True))

        if self.node is None:
            assert self.parent is not None
            self.node = self.parent[self.attr_index]

        # if custom padding is given, set it
        self.padx = kwargs.get('padx', self.padx)
        self.pady = kwargs.get('pady', self.pady)

        self.f_widget_ids = []

    @property
    def desc(self):
        if hasattr(self.node, 'desc'):
            return self.node.desc
        elif hasattr(self.parent, 'get_desc') and self.attr_index is not None:
            return self.parent.get_desc(self.attr_index)
        raise AttributeError("Cannot locate a descriptor for this node.")

    @property
    def field_default(self):
        desc = self.desc
        return desc.get('DEFAULT', desc['TYPE'].default())

    @property
    def field_ext(self):
        '''The export extension of this FieldWidget.'''
        desc = self.desc
        return desc.get('EXT', '.%s' % desc['NAME'])

    @property
    def field_max(self):
        desc = self.desc
        return desc.get('MAX', desc['TYPE'].max)

    @property
    def field_min(self):
        desc = self.desc
        return desc.get('MIN', desc['TYPE'].min)

    @property
    def gui_name(self):
        '''The gui_name of the node of this FieldWidget.'''
        desc = self.desc
        return desc.get('GUI_NAME', desc['NAME'].replace('_', ' '))

    @property
    def name(self):
        '''The name of the node of this FieldWidget.'''
        return self.desc['NAME']

    @property
    def title_width(self):
        if self._vert_oriented:
            return 40
        return 0

    @property
    def widget_picker(self):
        try:
            return self.app_root.widget_picker
        except AttributeError:
            return widget_picker.def_widget_picker

    def export_node(self):
        '''Prompts the user for a location to export the node and exports it'''
        try:
            initialdir = self.root_app.curr_dir
        except AttributeError:
            initialdir = None

        ext = self.field_ext

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

        ext = self.field_ext

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
            self.populate()
        except Exception:
            print(format_exc())

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        raise NotImplementedError("This method must be overloaded")

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

    @property
    def padded_height(self):
        '''The widgets padded height'''
        return self.winfo_height(self) + self.pady

    @property
    def padded_width(self):
        '''The widgets padded width'''
        return self.winfo_width(self) + self.padx

'''
TODO:
NOTES:
    Use Menu.post() and Menu.unpost to allow displaying cascade menus anywhere
'''

class NodeFrame(tk.Frame, FieldWidget):
    padx = NODE_FRAME_PADX
    pady = NODE_FRAME_PADY

    show = None
    content = None

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        kwargs['highlightthickness'] = 0
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation
        if self.f_widget_parent is None:
            self.padx = self.pady = 0
        kwargs['padx'] = self.padx
        kwargs['pady'] = self.pady
        kwargs['relief'] = 'flat'
        kwargs['bd'] = 0
            
        assert orient in 'vh'

        show_frame = True
        self.show = tk.IntVar()
        self.content = self
        if self.f_widget_parent is not None:
            show_frame = bool(kwargs.pop('show_frame', 0))
        self.show_title = kwargs.pop('show_title', orient == 'v' and
                                     self.f_widget_parent is not None)

        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        # if the orientation is vertical, make a title frame
        if self.show_title:
            self.show.set(show_frame)
            if show_frame:
                toggle_text = 'Hide'
            else:
                toggle_text = 'Show'
            self.title = tk.Frame(self, relief='raised', bd=FRAME_DEPTH)
            self.title_label = tk.Label(self.title, text=self.gui_name,
                                        anchor='w', width=self.title_width,
                                        justify='left')
            self.import_btn = tk.Button(
                self.title, width=5, text='Import', command=self.import_node)
            self.export_btn = tk.Button(
                self.title, width=5, text='Export', command=self.export_node)
            self.toggle_btn = ttk.Checkbutton(
                self.title, width=5, text=toggle_text, command=self.toggle,
                variable=self.show, style='Toolbutton')

            self.title_label.pack(fill="x", expand=True, side="left")
            self.toggle_btn.pack(side="right")
            self.export_btn.pack(side="right")
            self.import_btn.pack(side="right")
            self.title.pack(fill="x", expand=True)
        else:
            self.show.set(True)

        self.populate()

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation
        vertical = True
        assert orient in 'vh'

        content = self
        if self.show_title:
            content = tk.Frame(self, relief="sunken", bd=FRAME_DEPTH)

        self.content = content
        f_widget_ids = self.f_widget_ids

        # destroy all the child widgets of the content
        # c.destroy also removes each widget from self.children
        for c in list(content.children.values()):
            c.destroy()

        # clear the f_widget_ids list
        del f_widget_ids[:]

        # if the orientation is horizontal, remake its label
        if orient == 'h':
            vertical = False
            self.title_label = tk.Label(self, text=self.gui_name, anchor='w',
                                        justify='left', width=self.title_width)
            self.title_label.pack(fill="x", expand=True, side="left")

        node = self.node
        desc = node.desc
        picker = self.widget_picker
        app_root = self.app_root

        field_indices = range(len(node))
        # if the node has a steptree node, include its index in the indices
        if hasattr(node, 'STEPTREE'):
            field_indices = tuple(field_indices) + ('STEPTREE',)

        # loop over each field and make its widget
        for i in field_indices:
            sub_node = node[i]
            sub_desc = desc[i]
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            # if the field shouldnt be visible, dont make its widget
            if not sub_desc.get('VISIBLE', True):
                continue

            widget_cls = picker.get_widget(sub_desc)
            widget = widget_cls(content, node=sub_node, parent=node,
                                attr_index=i, app_root=app_root,
                                f_widget_parent=self, vert_oriented=vertical)

            f_widget_ids.append(id(widget))

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def pose_fields(self):
        f_widget_ids = self.f_widget_ids
        content = self.content
        children = content.children
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation
        side = {'v': 'top', 'h': 'left'}.get(orient)

        for wid in f_widget_ids:
            widget = children[str(wid)]
            widget.pack(fill='x', side=side, anchor='nw', expand=True)

        if self is not content:
            content.pack(fill='x', side=side, anchor='nw', expand=True)

    def toggle(self):
        if self.content is self:
            # dont do anything if there is no specific "content" frame to hide
            return
        elif self.show.get():
            self.pose_fields()
            self.toggle_btn.configure(text='Hide')
        else:
            self.content.forget()
            self.toggle_btn.configure(text='Show')


class NullFrame(tk.Frame, FieldWidget):
    '''This FieldWidget is is meant to represent an unknown field.'''
    padx = NODE_FRAME_PADX
    pady = NODE_FRAME_PADY

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        kwargs['padx'] = self.padx
        kwargs['pady'] = self.pady
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.populate()

    def populate(self):
        self.name_label = tk.Label(self, text=self.gui_name, justify='left',
                                   width=self.title_width, anchor='w')
        self.warning_label = tk.Label(
            self, text='<"%s">' %
            self.desc['TYPE'].name, anchor='w', justify='left')

        # now that the field widgets are created, position them
        self.pose_fields()

    def pose_fields(self):
        self.name_label.pack(side='left', fill="x")
        self.warning_label.pack(side='left', fill="x", expand=True)


class VoidFrame(tk.Frame, FieldWidget):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        kwargs['padx'] = self.padx
        kwargs['pady'] = self.pady
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def populate(self):
        pass

    def pose_fields(self):
        pass


class ArrayFrame(NodeFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''
    # use ttk.Combobox for the dropdown list
    # also make the array collapsable

    sel_index = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('relief', 'sunken')
        kwargs.setdefault('borderwidth', 1)
        kwargs['padx'] = self.padx
        kwargs['pady'] = self.pady
        kwargs['relief'] = 'flat'
        kwargs['bd'] = 0
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.show = tk.IntVar()
        self.show.set(0)
        self.sel_index = tk.IntVar()

        try:
            self.sel_index.set((len(self.node) > 0) - 1)
        except:
            self.sel_index.set(-1)

        # make the title, element menu, and all the buttons
        self.title = title = tk.Frame(self, relief='raised', bd=FRAME_DEPTH)
        self.content = tk.Frame(self, relief="sunken", bd=FRAME_DEPTH)
        self.title_label = tk.Label(title, text=self.gui_name,
                                    anchor='w', width=self.title_width,
                                    justify='left')
        self.sel_menu = widgets.ScrollMenu(
            title, f_widget_parent=self, sel_index=self.sel_index)
        self.add_btn = tk.Button(
            title, width=3, text='Add', command=self.add_entry)
        self.insert_btn = tk.Button(
            title, width=5, text='Insert', command=self.insert_entry)
        self.duplicate_btn = tk.Button(
            title, width=7, text='Duplicate', command=self.duplicate_entry)
        self.delete_btn = tk.Button(
            title, width=5, text='Delete', command=self.delete_entry)
        self.delete_all_btn = tk.Button(
            title, width=7, text='Delete all', command=self.delete_all_entries)

        self.import_btn = tk.Button(
            title, width=5, text='Import', command=self.import_node)
        self.export_btn = tk.Button(
            title, width=5, text='Export', command=self.export_node)
        self.toggle_btn = ttk.Checkbutton(
            title, width=5, text='Show', command=self.toggle,
            variable=self.show, style='Toolbutton')

        # pack the title, menu, and all the buttons
        for w in (self.toggle_btn, self.export_btn, self.import_btn,
                  self.delete_all_btn, self.delete_btn, self.duplicate_btn,
                  self.insert_btn, self.add_btn):
            w.pack(side="right")
        self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x", expand=True)

        self.title.pack(fill="x", expand=True)

        self.populate()

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = self.sel_index.get()
        if opt_index < 0:
            return None

        name_map = self.desc.get('NAME_MAP', {})
        for opt, index in name_map.items():
            if index == opt_index:
                return opt
        return None

    def options(self):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        name_map = self.desc.get('NAME_MAP', {})
        node_len = len(self.node)
        options = ['<INVALID NAME>']*len(name_map)
        if options:
            # sort the options by value(values are integers)
            for opt, index in name_map.items():
                try:
                    options[index] = opt
                except IndexError:
                    pass

        if len(options) > node_len:
            # trim the name_map to make sure it isnt longer than
            # the number of nodes that can actually be accessed.
            options = options[:node_len]
        elif len(options) < node_len:
            # otherwise pad the name_map with integers
            options += list(len(options), range(node_len))

        return options

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
        node = self.node
        desc = self.desc
        sel_index = self.sel_index.get()
        f_widget_ids = self.f_widget_ids

        if not hasattr(node, '__len__') or len(node) == 0:
            self.sel_menu.disable()
            return

        if sel_index >= 0:
            sub_node = node[sel_index]
            sub_desc = desc['SUB_STRUCT']
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            widget_cls = self.widget_picker.get_widget(sub_desc)
            widget = widget_cls(self.content, node=sub_node, parent=node,
                                attr_index=sel_index, app_root=self.app_root,
                                f_widget_parent=self, show_title=False)

            f_widget_ids.append(id(widget))

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def pose_fields(self):
        children = self.content.children

        # there should only be one wid in here, but for
        # the sake of consistancy we'll loop over them.
        for wid in self.f_widget_ids:
            children[str(wid)].pack(
                fill='x', side='top', anchor='nw', expand=True)

        self.content.pack(fill='x', side='top', anchor='nw', expand=True)


class BoolCanvas(tk.Canvas, FieldWidget):
    '''Used for bool type nodes. Creates checkbuttons for
    each boolean option and resizes itself to fit them.'''
    # use a listbox for the names running parallel to the
    # checkboxes and give the frame a vertical scrollbar.
    padx = NODE_CANVAS_PADX
    pady = NODE_CANVAS_PADY

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Canvas.__init__(self, *args, **fix_widget_kwargs(**kwargs))

        self.populate()

    def populate(self):
        pass

# These classes are the widgets that are actually
# interacted with to edit the data in a node.
class DataFieldWidget(NodeFrame):
    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        # set the amount of padding this widget needs on each side
        self.padx = DATA_PADX
        self.pady = DATA_PADY

    def populate(self):
        pass


class DataEntry(tk.Entry, DataFieldWidget):
    '''Used for strings/bytes/bytearrays that
    fit on one line as well as ints and floats.'''

    def __init__(self, *args, **kwargs):
        DataFieldWidget.__init__(self, *args, **kwargs)
        tk.Entry.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def populate(self):
        pass


class DataText(tk.Text, DataFieldWidget):
    '''Used for strings that likely will not fit on one line.'''

    def __init__(self, *args, **kwargs):
        DataFieldWidget.__init__(self, *args, **kwargs)
        tk.Text.__init__(self, *args, **fix_widget_kwargs(**kwargs))

    def populate(self):
        pass


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

# TEMPORARELY MAKE THEM NULL
BoolCanvas = DataEntry = DataText = EnumMenu = NullFrame

