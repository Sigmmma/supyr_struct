import tkinter as tk
import tkinter.ttk as ttk

from tkinter import constants as t_const
from tkinter.font import Font
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from . import widgets
from . import editor_constants as e_c

# linked to through __init__.py
widget_picker = None


__all__ = (
    "fix_kwargs", "FieldWidget",
    "ContainerFrame", "ArrayFrame",
    "DataFrame", "NullFrame", "VoidFrame",
    "BoolFrame", "EntryFrame", "TextFrame", "EnumFrame",
    )


def fix_kwargs(**kw):
    '''Returns a dict where all items in the provided keyword arguments
    that use keys found in WIDGET_KWARGS are removed.'''
    return {s:kw[s] for s in kw if s not in e_c.WIDGET_KWARGS}


# These classes are used for laying out the visual structure
# of many sub-widgets, and effectively the whole window.
class FieldWidget(widgets.BinillaWidget):
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

    # whether or not to clone the node when exporting it
    export_clone = False
    # whether or not to calculate pointers for the node when exporting it
    export_calc_pointers = False

    app_root = None

    # The FieldWidget that contains this one. If this is None,
    # it means that this is the root of the FieldWidget tree.
    f_widget_parent = None

    # A list of the id's of the widgets that are parented
    # to this widget, in the order that they were created
    f_widget_ids = None

    # The amount of external padding this widget needs
    pack_padx = 0
    pack_pady = 0

    # Whether the widget is being oriented vertically or horizontally
    _vert_oriented = True

    show_button_style = None

    # Whether or not this widget can use the scrollwheel when selected.
    # Setting this to True prevents the TagWindow from scrolling when
    # using the mousewheel if this widget is the one currently in focus 
    can_scroll = False


    def __init__(self, *args, **kwargs):
        self.node = kwargs.get('node', self.node)
        self.parent = kwargs.get('parent', self.parent)
        self.attr_index = kwargs.get('attr_index', self.attr_index)
        self.app_root = kwargs.get('app_root', None)
        self.f_widget_parent = kwargs.get('f_widget_parent', None)
        self._vert_oriented = bool(kwargs.get('vert_oriented', True))
        self.export_clone = bool(kwargs.get('export_clone', self.export_clone))
        self.export_calc_pointers = bool(kwargs.get('export_calc_pointers',
                                                    self.export_calc_pointers))

        if self.node is None:
            assert self.parent is not None
            self.node = self.parent[self.attr_index]

        # make sure a button style exists for the 'show' button
        if FieldWidget.show_button_style is None:
            FieldWidget.show_btn_style = ttk.Style()
            FieldWidget.show_btn_style.configure('ShowButton.TButton',
                                                 background=self.frame_bg_color)

        # if custom padding is given, set it
        self.pack_padx = self.horizontal_pad_x
        self.pack_pady = self.horizontal_pad_y
        if 'pack_padx' in kwargs:
            self.pack_padx = kwargs['pack_padx']
        elif self._vert_oriented:
            self.pack_padx = self.vertical_pad_x

        if 'pack_pady' in kwargs:
            self.pack_pady = kwargs['pack_pady']
        elif self._vert_oriented:
            self.pack_pady = self.vertical_pad_y

        self.f_widget_ids = []

    @property
    def desc(self):
        if hasattr(self.node, 'desc'):
            return self.node.desc
        elif hasattr(self.parent, 'desc') and self.attr_index is not None:
            desc = self.parent.desc
            if desc['TYPE'].is_array:
                return desc['SUB_STRUCT']
            return desc[self.attr_index]
        raise AttributeError("Cannot locate a descriptor for this node.")

    @property
    def field_default(self):
        desc = self.desc
        return desc.get('DEFAULT', desc['TYPE'].default())

    @property
    def field_ext(self):
        '''The export extension of this FieldWidget.'''
        desc = self.desc
        try:
            # try to get the extension of the 
            if self.parent is None:
                tag_ext = self.node.get_root().ext
            else:
                tag_ext = self.parent.get_root().ext
        except Exception:
            tag_ext = ''
        return desc.get('EXT', '%s.%s' % (tag_ext, desc['NAME']))

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
    def title_size(self):
        if self._vert_oriented:
            return self.title_width
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
                self.node.serialize(filepath=filepath, clone=self.export_clone,
                                    calc_pointers=self.export_calc_pointers)
            else:
                # the node isnt a block, so we need to call its parents
                # serialize method with the attr_index necessary to export.
                self.parent.serialize(filepath=filepath,
                                      clone=self.export_clone,
                                      calc_pointers=self.export_calc_pointers,
                                      attr_index=self.attr_index)
        except Exception:
            print(format_exc())
            print("Could not export '%s' node." % self.name)

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
                self.parent.parse(filepath=filepath, attr_index=self.attr_index)
                self.node = parent[attr_index]

            if self.show.get():
                self.populate()
        except Exception:
            print(format_exc())
            print("Could not import '%s' node." % self.name)

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        raise NotImplementedError("This method must be overloaded")

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
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


class ContainerFrame(tk.Frame, FieldWidget):
    show = None
    content = None

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        # if only one sub-widget being displayed, dont display the title
        if self.visible_child_count <= 1:
            self.pack_padx = self.pack_pady = 0
            kwargs['show_title'] = False
        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        assert orient in 'vh'

        show_frame = True
        self.show = tk.IntVar()
        self.content = self
        if self.f_widget_parent is not None:
            show_frame = bool(kwargs.pop('show_frame', 0))
        self.show_title = kwargs.pop('show_title', orient == 'v' and
                                     self.f_widget_parent is not None)

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        # if the orientation is vertical, make a title frame
        if self.show_title:
            self.show.set(show_frame)
            if show_frame:
                toggle_text = '-'
            else:
                toggle_text = '+'
            try:
                title_font = self.app_root.container_title_font
            except AttributeError:
                title_font = Font(family="Courier", size=10, weight='bold')
            self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                                 bg=self.frame_bg_color)
            self.show_btn = ttk.Checkbutton(
                self.title, width=3, text='+', command=self.toggle_visible,
                variable=self.show, style='ShowButton.TButton')
            self.title_label = tk.Label(self.title, text=self.gui_name,
                                        anchor='w', width=self.title_size,
                                        justify='left', font=title_font,
                                        bg=self.frame_bg_color)
            self.import_btn = tk.Button(
                self.title, width=5, text='Import', command=self.import_node,
                bd=self.button_depth, bg=self.default_bg_color)
            self.export_btn = tk.Button(
                self.title, width=5, text='Export', command=self.export_node,
                bd=self.button_depth, bg=self.default_bg_color)

            self.show_btn.pack(side="left")
            self.title_label.pack(fill="x", expand=True, side="left")
            for w in (self.export_btn, self.import_btn):
                w.pack(side="right", padx=(0, 4), pady=2)

            self.title.pack(fill="x", expand=True)
        else:
            self.show.set(True)

        self.populate()

    @property
    def visible_child_count(self):
        desc = self.desc
        try:
            total = 0
            node = self.node
            entries = range(desc.get('ENTRIES', 0))
            if hasattr(node, 'STEPTREE'):
                entries = tuple(entries) + ('STEPTREE',)

            for i in entries:
                sub_node = node[i]
                sub_desc = desc[i]
                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc

                if sub_desc.get('VISIBLE', True):
                    total += 1
            return total
        except (IndexError, KeyError, AttributeError):
            return 0

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        try: del self.node
        except Exception: pass
        try: del self.parent
        except Exception: pass
        try: del self.f_widget_parent
        except Exception: pass
        try: del self.app_root
        except Exception: pass
        tk.Frame.destroy(self)

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation
        vertical = True
        assert orient in 'vh'

        content = self
        if hasattr(self, 'content'):
            content = self.content
        if self.show_title and content in (None, self):
            content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                               bg=self.default_bg_color)

        self.content = content
        f_widget_ids = self.f_widget_ids

        # clear the f_widget_ids list
        del f_widget_ids[:]

        # destroy all the child widgets of the content
        for c in list(content.children.values()):
            c.destroy()

        # if the orientation is horizontal, remake its label
        if orient == 'h':
            vertical = False
            self.title_label = tk.Label(self, text=self.gui_name,
                                        anchor='w', justify='left',
                                        width=self.title_size)
            self.title_label.pack(fill="x", side="left")

        node = self.node
        desc = node.desc
        picker = self.widget_picker
        app_root = self.app_root

        field_indices = range(len(node))
        # if the node has a steptree node, include its index in the indices
        if hasattr(node, 'STEPTREE'):
            field_indices = tuple(field_indices) + ('STEPTREE',)

        kwargs = dict(parent=node, app_root=app_root,
                      f_widget_parent=self, vert_oriented=vertical)

        # if only one sub-widget being displayed, dont
        # display the title of the widget being displayed
        if self.visible_child_count <= 1:
            kwargs['show_title'] = False

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
            widget = widget_cls(content, node=sub_node, attr_index=i, **kwargs)

            f_widget_ids.append(id(widget))

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            node = self.node
            for wid in self.f_widget_ids:
                w = self.content.children[str(wid)]

                w.parent, w.node = node, node[w.attr_index]
                w.reload()
        except Exception:
            print(format_exc())

    def pose_fields(self):
        f_widget_ids = self.f_widget_ids
        content = self.content
        children = content.children
        orient = self.desc.get('ORIENT', 'v')[:1].lower()  # get the orientation

        if self.desc.get("PORTABLE", True):
            if hasattr(self, "import_btn"): self.set_import_disabled(False)
            if hasattr(self, "export_btn"): self.set_export_disabled(False)
        else:
            if hasattr(self, "import_btn"): self.set_import_disabled()
            if hasattr(self, "export_btn"): self.set_export_disabled()

        side = {'v': 'top', 'h': 'left'}.get(orient)
        for wid in f_widget_ids:
            w = children[str(wid)]
            w.pack(fill='x', side=side, anchor='nw',
                   padx=w.pack_padx, pady=w.pack_pady)

        if self is not content:
            content.pack(fill='x', side=side, anchor='nw', expand=True)

    def set_import_disabled(self, disable=True):
        '''Disables the import button if disable is True. Enables it if not.'''
        if disable: self.import_btn.config(state="disabled")
        else:       self.import_btn.config(state="normal")

    def set_export_disabled(self, disable=True):
        '''Disables the export button if disable is True. Enables it if not.'''
        if disable: self.export_btn.config(state="disabled")
        else:       self.export_btn.config(state="normal")

    def set_show_disabled(self, disable=True):
        '''Disables the show button if disable is True. Enables it if not.'''
        if disable: self.show_btn.config(state="disabled")
        else:       self.show_btn.config(state="normal")

    def toggle_visible(self):
        if self.content is self:
            # dont do anything if there is no specific "content" frame to hide
            return
        elif self.show.get():
            self.pose_fields()
            self.show_btn.configure(text='-')
        else:
            self.content.forget()
            self.show_btn.configure(text='+')


class ArrayFrame(ContainerFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''

    sel_index = None
    populated = False
    option_cache = None
    options_sane = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        self.show = tk.IntVar()
        self.show.set(0)
        try:
            title_font = self.app_root.container_title_font
        except AttributeError:
            title_font = Font(family="Courier", size=10, weight='bold')

        node_len = 0
        try: node_len = len(self.node)
        except Exception: pass

        self.sel_index = (node_len > 0) - 1

        # make the title, element menu, and all the buttons
        self.controls = tk.Frame(self, relief='raised', bd=self.frame_depth,
                                 bg=self.frame_bg_color)
        self.title = title = tk.Frame(self.controls, relief='flat', bd=0,
                                      bg=self.frame_bg_color)
        self.buttons = buttons = tk.Frame(self.controls, relief='flat', bd=0,
                                          bg=self.frame_bg_color)

        self.show_btn = ttk.Checkbutton(
            title, width=3, text='+', command=self.toggle_visible,
            variable=self.show, style='ShowButton.TButton')
        self.title_label = tk.Label(
            title, text=self.gui_name, bg=self.frame_bg_color, anchor='w',
            width=self.title_size, justify='left', font=title_font)
        self.sel_menu = widgets.ScrollMenu(
            title, f_widget_parent=self,
            sel_index=self.sel_index, max_index=node_len-1)
        self.add_btn = tk.Button(
            buttons, width=3, text='Add', command=self.add_entry,
            bd=self.button_depth, bg=self.default_bg_color)
        self.insert_btn = tk.Button(
            buttons, width=5, text='Insert', command=self.insert_entry,
            bd=self.button_depth, bg=self.default_bg_color)
        self.duplicate_btn = tk.Button(
            buttons, width=7, text='Duplicate', command=self.duplicate_entry,
            bd=self.button_depth, bg=self.default_bg_color)
        self.delete_btn = tk.Button(
            buttons, width=5, text='Delete', command=self.delete_entry,
            bd=self.button_depth, bg=self.default_bg_color)
        self.delete_all_btn = tk.Button(
            buttons, width=7, text='Delete all',
            command=self.delete_all_entries,
            bd=self.button_depth, bg=self.default_bg_color)

        self.import_btn = tk.Button(
            buttons, width=5, text='Import', command=self.import_node,
            bd=self.button_depth, bg=self.default_bg_color)
        self.export_btn = tk.Button(
            buttons, width=5, text='Export', command=self.export_node,
            bd=self.button_depth, bg=self.default_bg_color)

        # pack the title, menu, and all the buttons
        for w in (self.export_btn, self.import_btn,
                  self.delete_all_btn, self.delete_btn, self.duplicate_btn,
                  self.insert_btn, self.add_btn):
            w.pack(side="right", padx=(0, 4), pady=(2, 2))
        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x", expand=True)

        self.title.pack(fill="x", expand=True)
        self.buttons.pack(fill="x", expand=True)
        self.controls.pack(fill="x", expand=True)

        self.populate()

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        try: del self.option_cache
        except Exception: pass
        tk.Frame.destroy(self)

    def export_node(self):
        try:
            # pass call to the export_node method of the array entry's widget
            w = self.content.children[str(self.f_widget_ids[0])]
        except Exception:
            return
        w.export_node()

    def import_node(self):
        try:
            # pass call to the import_node method of the array entry's widget
            w = self.content.children[str(self.f_widget_ids[0])]
        except Exception:
            return
        w.import_node()

    @property
    def options(self):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if not self.options_sane or self.option_cache is None:
            self.cache_options()
        return self.option_cache

    def cache_options(self):
        ############################
        # OPTIMIZE THIS CRAP SOMEHOW
        ############################
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
            node = self.node
            desc = self.desc
            option_len = len(options)

            options.extend([None]*(node_len - option_len))
            # otherwise pad the name_map with integer incremented names
            for i in range(option_len, node_len):
                sub_node = node[i]
                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc
                else:
                    sub_desc = desc['SUB_STRUCT']
                    
                options[i] = "%s. %s" % (i, sub_desc['NAME'])

        self.options_sane = True
        self.option_cache = tuple(options)

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = self.sel_index
        if opt_index < 0:
            return None

        try:
            ############################
            # OPTIMIZE THIS CRAP SOMEHOW
            ############################
            return self.options[opt_index]
        except Exception:
            return None

    def set_add_disabled(self, disable=True):
        '''Disables the add button if disable is True. Enables it if not.'''
        if disable: self.add_btn.config(state="disabled")
        else:       self.add_btn.config(state="normal")

    def set_insert_disabled(self, disable=True):
        '''Disables the insert button if disable is True. Enables it if not.'''
        if disable: self.insert_btn.config(state="disabled")
        else:       self.insert_btn.config(state="normal")

    def set_duplicate_disabled(self, disable=True):
        '''
        Disables the duplicate button if disable is True. Enables it if not.
        '''
        if disable: self.duplicate_btn.config(state="disabled")
        else:       self.duplicate_btn.config(state="normal")

    def set_delete_disabled(self, disable=True):
        '''Disables the delete button if disable is True. Enables it if not.'''
        if disable: self.delete_btn.config(state="disabled")
        else:       self.delete_btn.config(state="normal")

    def set_delete_all_disabled(self, disable=True):
        '''
        Disables the delete_all button if disable is True. Enables it if not.
        '''
        if disable: self.delete_all_btn.config(state="disabled")
        else:       self.delete_all_btn.config(state="normal")

    def add_entry(self):
        # DONT FORGET TO MODIFY self.sel_menu.max_index
        self.options_sane = self.sel_menu.options_sane = False

    def insert_entry(self):
        # DONT FORGET TO MODIFY self.sel_menu.max_index
        self.options_sane = self.sel_menu.options_sane = False

    def duplicate_entry(self):
        # DONT FORGET TO MODIFY self.sel_menu.max_index
        self.options_sane = self.sel_menu.options_sane = False

    def delete_entry(self):
        # DONT FORGET TO MODIFY self.sel_menu.max_index
        self.options_sane = self.sel_menu.options_sane = False

    def delete_all_entries(self):
        # DONT FORGET TO MODIFY self.sel_menu.max_index
        self.options_sane = self.sel_menu.options_sane = False

    def populate(self):
        node = self.node
        desc = self.desc
        sel_index = self.sel_index
        f_widget_ids = self.f_widget_ids

        if self.content in (None, self):
            self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                    bg=self.default_bg_color)

        del f_widget_ids[:]

        # destroy all the child widgets of the content
        for c in list(self.content.children.values()):
            c.destroy()

        self.populated = False
        self.sel_menu.update_label()
        if len(node) == 0:
            self.sel_menu.disable()
        else:
            self.sel_menu.enable()

        if not hasattr(node, '__len__') or len(node) == 0:
            self.sel_menu.disable()
            self.sel_index = -1
            if self.show.get():
                self.pose_fields()
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
            self.populated = True

            self.reload()

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            node = self.node
            if len(node) == 0:
                self.sel_menu.sel_index = -1
                self.sel_menu.max_index = -1
                # if there is no index to select, destroy the content
                if self.sel_index != -1:
                    self.sel_index = -1
                    self.populate()
                return

            # reset the selected index to zero if it's -1
            # or if its greater than the length of the node
            curr_index = self.sel_index
            if curr_index < 0 or curr_index >= len(node):
                curr_index = self.sel_index = 0

            self.sel_menu.sel_index = curr_index
            self.sel_menu.max_index = len(node) - 1

            # if the widget is unpopulated we need to populate it
            if not self.populated:
                self.populate()
                return

            sub_node = node[curr_index]

            for wid in self.f_widget_ids:
                w = self.content.children[str(wid)]
                w.parent, w.node, w.attr_index = node, sub_node, curr_index
                w.f_widget_parent = self
                w.reload()

                if w.desc.get("PORTABLE", True):
                    self.set_import_disabled(False)
                    self.set_export_disabled(False)
                else:
                    self.set_import_disabled()
                    self.set_export_disabled()

            if len(node) == 0:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            self.sel_menu.update_label()

        except Exception:
            print(format_exc())

    def pose_fields(self):
        children = self.content.children

        # there should only be one wid in here, but for
        # the sake of consistancy we'll loop over them.
        for wid in self.f_widget_ids:
            w = children[str(wid)]
            w.pack(fill='x', side='top', expand=True,
                   padx=w.pack_padx, pady=w.pack_pady)

        # if there are no children in the content, we need to
        # pack in SOMETHING, update the idletasks, and then
        # destroy that something to resize the content frame
        if not self.content.children:
            f = tk.Frame(self.content, width=0, height=0, bd=0)
            a, b, c = f.pack(), self.content.update_idletasks(), f.destroy()

        self.content.pack(fill='both', side='top', anchor='nw', expand=True)

    def select_option(self, opt_index=None):
        node = self.node
        desc = self.desc
        curr_index = self.sel_index
        if opt_index == curr_index:
            return

        if opt_index < 0 or opt_index is None:
            self.sel_index = -1
            self.populate()
            return

        self.sel_index = opt_index

        sub_node = node[curr_index]
        new_sub_node = node[opt_index]

        # if neither of the sub-nodes being switched between have descriptors
        # then dont worry about repopulating as the descriptors are the same.
        if not(hasattr(sub_node, 'desc') or hasattr(new_sub_node, 'desc')):
            self.reload()
            return

        # get the descs to compare them
        sub_desc = new_sub_desc = desc['SUB_STRUCT']
        if hasattr(sub_node, 'desc'):
            sub_desc = sub_node.desc

        if hasattr(new_sub_node, 'desc'):
            new_sub_desc = new_sub_node.desc

        # if the sub-descs are the same, dont repopulate either, just reload
        if sub_desc is new_sub_desc:
            self.reload()
            return

        # if there is no way around it, repopulate the widget
        self.populate()


class DataFrame(FieldWidget, tk.Frame):

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        try: del self.node
        except Exception: pass
        try: del self.parent
        except Exception: pass
        try: del self.f_widget_parent
        except Exception: pass
        try: del self.app_root
        except Exception: pass
        tk.Frame.destroy(self)

    def populate(self):
        pass

    def pose_fields(self):
        pass

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        raise NotImplementedError("This method must be overloaded")


class NullFrame(DataFrame):
    '''This FieldWidget is is meant to represent an unknown field.'''
    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def populate(self):
        self.name_label = tk.Label(
            self, text=self.gui_name, bg=self.default_bg_color,
            width=self.title_size, anchor='w')
        self.field_type_name = tk.Label(
            self, bg=self.default_bg_color, text='<%s>' %
            self.desc['TYPE'].name, anchor='w', justify='left'
            )

        # now that the field widgets are created, position them
        self.pose_fields()

    def pose_fields(self):
        self.name_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")

    def flush(self): pass

    def reload(self): pass


class VoidFrame(DataFrame):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color, pack_padx=0, pack_pady=0)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

    def flush(self): pass

    def reload(self): pass


class BoolFrame(DataFrame):
    '''Used for bool type nodes. Creates checkbuttons for
    each boolean option and resizes itself to fit them.'''

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def populate(self):
        pass


class EntryFrame(DataFrame):
    '''Used for strings/bytes/bytearrays that
    fit on one line as well as ints and floats.'''

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def populate(self):
        pass


class TextFrame(DataFrame):
    '''Used for strings that likely will not fit on one line.'''

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def populate(self):
        pass


class EnumFrame(DataFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''
    # use ttk.Combobox for the dropdown list

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop("func")
        DataFrame.__init__(self, *args, **kwargs)
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
BoolFrame = EntryFrame = TextFrame = EnumFrame = NullFrame

