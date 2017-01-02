import tkinter as tk
import tkinter.ttk as ttk

from copy import deepcopy
from math import log, ceil
from tkinter import constants as t_const
from tkinter.font import Font
from tkinter.colorchooser import askcolor
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from supyr_struct.buffer import get_rawdata
from . import widgets
from . import editor_constants as e_c

# linked to through __init__.py
widget_picker = None


__all__ = (
    "fix_kwargs", "FieldWidget",
    "ContainerFrame", "ColorPickerFrame",
    "ArrayFrame", "DynamicArrayFrame",
    "DataFrame", "NullFrame", "VoidFrame", "PadFrame",
    "UnionFrame", "StreamAdapterFrame",
    "BoolFrame", "BoolSingleFrame",
    "EnumFrame", "DynamicEnumFrame",
    "EntryFrame", "HexEntryFrame", "TimestampFrame", "NumberEntryFrame",
    "TextFrame", "RawdataFrame",
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
    # the data or Block this widget exposes to viewing/editing
    node = None
    # the parent of the node
    parent = None
    # the provided descriptor of the node
    _desc = None
    # the index the node is in in the parent. If this is not None,
    # it must be valid to use parent[attr_index] to get the node.
    attr_index = None

    # whether or not to clone the node when exporting it
    export_clone = False
    # whether or not to calculate pointers for the node when exporting it
    export_calc_pointers = False

    tag_window = None

    # the FieldWidget that contains this one. If this is None,
    # it means that this is the root of the FieldWidget tree.
    f_widget_parent = None

    # a list of the id's of the widgets that are parented
    # to this widget, in the order that they were created
    f_widget_ids = None

    # a mapping that maps each field widget's id to the attr_index
    # it is under in its parent, which is this widgets node.
    f_widget_ids_map = None

    # the amount of external padding this widget needs
    pack_padx = 0
    pack_pady = 0

    # whether or not this FieldWidget's title is shown
    show_title = True

    dont_padx_fields = False

    # whether the widget is being oriented vertically or horizontally
    _vert_oriented = True

    show_button_style = None

    # whether or not this widget can use the scrollwheel when selected.
    # setting this to True prevents the TagWindow from scrolling when
    # using the mousewheel if this widget is the one currently in focus
    children_can_scroll = False

    # whether or not to disable using this widget and its children
    disabled = False

    # whether or not something in this FieldWidget has been edited.
    edited = False

    # whether or not a widget needs to have its content flushed to the node
    needs_flushing = False

    # whether or not the widget has been fully initialized
    _initialized = False

    def __init__(self, *args, **kwargs):
        self.node = kwargs.get('node', self.node)
        self._desc = kwargs.get('desc', self._desc)
        self.parent = kwargs.get('parent', self.parent)
        self.attr_index = kwargs.get('attr_index', self.attr_index)
        self.tag_window = kwargs.get('tag_window', None)
        self.f_widget_parent = kwargs.get('f_widget_parent', None)
        self._vert_oriented = bool(kwargs.get('vert_oriented', True))
        self.export_clone = bool(kwargs.get('export_clone', self.export_clone))
        self.export_calc_pointers = bool(kwargs.get('export_calc_pointers',
                                                    self.export_calc_pointers))
        self.dont_padx_fields = kwargs.get('dont_padx_fields',
                                           self.dont_padx_fields)
        self.disabled = kwargs.get('disabled', self.disabled)
        if 'EDITABLE' in self.desc:
            self.disabled = not self.desc['EDITABLE']

        if self.all_editable:
            self.disabled = False

        if self.node is None:
            assert self.parent is not None
            self.node = self.parent[self.attr_index]

        # make sure a button style exists for the 'show' button
        if FieldWidget.show_button_style is None:
            FieldWidget.show_btn_style = ttk.Style()
            FieldWidget.show_btn_style.configure('ShowButton.TButton',
                                                 background=self.frame_bg_color)

        # if custom padding is given, set it
        self.pack_padx = self.horizontal_padx
        self.pack_pady = self.horizontal_pady
        if 'pack_padx' in kwargs:
            self.pack_padx = kwargs['pack_padx']
        elif self._vert_oriented:
            self.pack_padx = self.vertical_padx

        if 'pack_pady' in kwargs:
            self.pack_pady = kwargs['pack_pady']
        elif self._vert_oriented:
            self.pack_pady = self.vertical_pady

        self.f_widget_ids = []
        self.f_widget_ids_map = {}

    @property
    def enforce_max(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.enforce_max)
        except Exception:
            return True

    @property
    def enforce_min(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.enforce_min)
        except Exception:
            return True

    @property
    def all_visible(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.show_invisible)
        except Exception:
            return False

    @property
    def all_editable(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.edit_uneditable)
        except Exception:
            return False

    @property
    def all_bools_visible(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.show_all_bools)
        except Exception:
            return False

    @property
    def show_comments(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.show_comments)
        except Exception:
            return False

    @property
    def show_sidetips(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.show_sidetips)
        except Exception:
            return False

    @property
    def show_tooltips(self):
        try:
            return bool(self.tag_window.app_root.config_file\
                        .data.header.tag_window_flags.show_tooltips)
        except Exception:
            return False

    @property
    def max_undos(self):
        try:
            return self.tag_window.app_root.\
                    config_file.data.header.max_undos
        except Exception:
            pass
        return 0

    @property
    def desc(self):
        if self._desc is not None:
            return self._desc
        elif hasattr(self.node, 'desc'):
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
    def widget_width(self):
        desc = self.desc
        if 'WIDGET_WIDTH' in desc:
            return desc['WIDGET_WIDTH']
        return 0

    @property
    def widget_picker(self):
        try:
            return self.tag_window.app_root.widget_picker
        except AttributeError:
            return widget_picker.def_widget_picker

    def display_comment(self, master=None):
        if not self.show_comments:
            return

        desc = self.desc
        comment = desc.get('COMMENT')
        try:
            self.comment_frame.destroy()
            self.comment_frame = None
        except Exception: pass

        if comment:
            if master is None:
                master = self
            self.comment_frame = tk.Frame(
                master, relief='sunken', bd=self.comment_depth,
                bg=self.comment_bg_color)
            self.comment = tk.Label(
                self.comment_frame, text=comment, anchor='nw',
                justify='left', font=self.tag_window.app_root.comment_font,
                bg=self.comment_bg_color)
            self.comment.pack(side='left', fill='both', expand=True)
            self.comment_frame.pack(fill='both', expand=True)

    def export_node(self):
        '''Prompts the user for a location to export the node and exports it'''
        try:
            initialdir = self.tag_window.app_root.last_load_dir
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
            initialdir = self.tag_window.app_root.last_load_dir
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
                self.node = self.parent[self.attr_index]

            self.populate()
            self.set_edited()
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

    def set_edited(self, new_value=True):
        self.edited = new_value
        try:
            if self.edited:
                # Tell all parents that there is are unsaved edits
                self.f_widget_parent.set_edited()
                return

            # Tell all children that there are no longer unsaved edits
            f_widgets = self.content.children
            for f_wid in self.f_widget_ids:
                w = f_widgets.get(str(f_wid))
                if w.edited:
                    w.set_edited(False)
        except Exception:
            pass

    def set_needs_flushing(self, new_value=True):
        self.needs_flushing = new_value
        try:
            if self.needs_flushing:
                # Tell all parents that there is are unsaved edits
                self.f_widget_parent.set_needs_flushing()
                return

            # Tell all children that there are no longer unsaved edits
            f_widgets = self.content.children
            for f_wid in self.f_widget_ids:
                w = f_widgets.get(str(f_wid))
                if w.needs_flushing:
                    w.set_needs_flushing(False)
        except Exception:
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
        if self.visible_field_count <= 1:
            self.pack_padx = self.pack_pady = 0
            kwargs['show_title'] = False
        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        assert orient in 'vh'

        show_frame = True
        self.content = self
        if self.f_widget_parent is not None:
            try:
                def_show = not self.tag_window.app_root.config_file.data.\
                           header.tag_window_flags.blocks_start_hidden
            except Exception:
                def_show = False
            show_frame = bool(kwargs.pop('show_frame', def_show))
        self.show_title = kwargs.pop('show_title', orient == 'v' and
                                     self.f_widget_parent is not None)

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))
        self.show = tk.IntVar(self)

        # if the orientation is vertical, make a title frame
        if self.show_title:
            self.show.set(show_frame)
            toggle_text = '-' if show_frame else '+'

            btn_kwargs = dict(
                bg=self.button_color, fg=self.text_normal_color,
                disabledforeground=self.text_disabled_color,
                bd=self.button_depth,
                )

            title_font = self.tag_window.app_root.container_title_font
            self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                                  bg=self.frame_bg_color)

            self.show_btn = ttk.Checkbutton(
                self.title, width=3, text=toggle_text,
                command=self.toggle_visible,
                variable=self.show, style='ShowButton.TButton')
            self.title_label = tk.Label(
                self.title, text=self.gui_name, anchor='w',
                width=self.title_size, justify='left', font=title_font,
                bg=self.frame_bg_color, fg=self.text_normal_color)
            self.import_btn = tk.Button(
                self.title, width=5, text='Import',
                command=self.import_node, **btn_kwargs)
            self.export_btn = tk.Button(
                self.title, width=5, text='Export',
                command=self.export_node, **btn_kwargs)

            self.show_btn.pack(side="left")
            if self.gui_name != '':
                self.title_label.pack(fill="x", expand=True, side="left")
            for w in (self.export_btn, self.import_btn):
                w.pack(side="right", padx=(0, 4), pady=2)

            self.title.pack(fill="x", expand=True)
        else:
            self.show.set(True)

        self.populate()
        self.initialized = True

    @property
    def visible_field_count(self):
        desc = self.desc
        try:
            total = 0
            node = self.node
            entries = range(desc.get('ENTRIES', 0))
            if hasattr(node, 'STEPTREE'):
                entries = tuple(entries) + ('STEPTREE',)

            if self.all_visible:
                return len(entries)

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
        try: del self.tag_window
        except Exception: pass
        tk.Frame.destroy(self)

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        vertical = True
        assert orient in 'vh'

        content = self
        if hasattr(self, 'content'):
            content = self.content
        if self.show_title and content in (None, self):
            content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                               bg=self.default_bg_color)

        self.content = content
        # clear the  list
        del self.f_widget_ids[:]
        del self.f_widget_ids_map

        f_widget_ids = self.f_widget_ids
        f_widget_ids_map = self.f_widget_ids_map = {}

        # destroy all the child widgets of the content
        for c in list(content.children.values()):
            c.destroy()

        node = self.node
        desc = node.desc
        picker = self.widget_picker
        tag_window = self.tag_window

        self.display_comment(self.content)

        # if the orientation is horizontal, remake its label
        if orient == 'h':
            vertical = False
            self.title_label = tk.Label(
                self, anchor='w', justify='left',
                width=self.title_size, text=self.gui_name,
                bg=self.default_bg_color, fg=self.text_normal_color)
            if self.gui_name != '':
                self.title_label.pack(fill="x", side="left")

            self.sidetip_label = tk.Label(
                self, anchor='w', justify='left',
                bg=self.default_bg_color, fg=self.text_normal_color)

        for w in (self, self.content):
            w.tooltip_string = self.desc.get('TOOLTIP')
        if hasattr(self, 'title'):
            self.title.tooltip_string = self.tooltip_string
        if hasattr(self, 'title_label'):
            self.title_label.tooltip_string = self.tooltip_string

        field_indices = range(len(node))
        # if the node has a steptree node, include its index in the indices
        if hasattr(node, 'STEPTREE'):
            field_indices = tuple(field_indices) + ('STEPTREE',)

        kwargs = dict(parent=node, tag_window=tag_window,
                      disabled=self.disabled, f_widget_parent=self,
                      vert_oriented=vertical)

        all_visible = self.all_visible
        visible_count = self.visible_field_count

        # if only one sub-widget being displayed, dont
        # display the title of the widget being displayed
        if all_visible:
            pass
        elif hasattr(node, 'STEPTREE'):
            s_node = node['STEPTREE']
            s_desc = desc['STEPTREE']
            if hasattr(s_node, 'desc'):
                s_desc = s_node.desc
            if visible_count <= 1:
                if not s_desc.get('VISIBLE', 1):
                    # only make the title not shown if the only
                    # visible widget will not be the subtree
                    kwargs['show_title'] = False
                kwargs['dont_padx_fields'] = True
        elif visible_count <= 1:
            kwargs['show_title'] = False
            kwargs['dont_padx_fields'] = True

        w_parent = self.f_widget_parent
        if w_parent and w_parent.dont_padx_fields and not self.show_title:
            # The parent isnt padding its children and this widget
            # has only one child and is displaying ONLY that child.
            # Dont pad the child so that it appears where this widget would.
            kwargs['pack_padx'] = 0

        if self.dont_padx_fields:
            kwargs['pack_padx'] = 0

        if field_indices:
            last_index = field_indices[-1]

        # loop over each field and make its widget
        for i in field_indices:
            sub_node = node[i]
            sub_desc = desc[i]
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            # if the field shouldnt be visible, dont make its widget
            if not(sub_desc.get('VISIBLE', True) or all_visible):
                continue

            widget_cls = picker.get_widget(sub_desc)
            if i == last_index and vertical:
                kwargs.update(pack_pady=0)

            try:
                widget = widget_cls(content, node=sub_node,
                                    attr_index=i, **kwargs)
            except Exception:
                print(format_exc())
                widget = NullFrame(content, node=sub_node,
                                   attr_index=i, **kwargs)

            f_widget_ids.append(id(widget))
            f_widget_ids_map[i] = id(widget)

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        try:
            for w in self.content.children.values():
                if w is None or not hasattr(w, 'flush'):
                    continue
                w.flush()
            self.edited = False
            self.set_needs_flushing(False)
        except Exception:
            print(format_exc())

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            node = self.node
            desc = self.desc
            f_widgets = self.content.children

            field_indices = range(len(node))
            # if the node has a steptree node, include its index in the indices
            if hasattr(node, 'STEPTREE'):
                field_indices = tuple(field_indices) + ('STEPTREE',)

            f_widget_ids_map = self.f_widget_ids_map
            all_visible = self.all_visible

            # if any of the descriptors are different between
            # the sub-nodes of the previous and new sub-nodes,
            # then this widget will need to be repopulated.
            for i in field_indices:
                sub_node = node[i]
                sub_desc = desc[i]
                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc

                w = f_widgets.get(str(f_widget_ids_map.get(i)))

                # if neither would be visible, dont worry about checking it
                if not(sub_desc.get('VISIBLE',1) or all_visible) and w is None:
                    continue

                # if the descriptors are different, gotta repopulate!
                if not hasattr(w, 'desc') or w.desc is not sub_desc:
                    self.populate()
                    return

            for wid in self.f_widget_ids:
                w = f_widgets[str(wid)]

                w.parent, w.node = node, node[w.attr_index]
                w.reload()
        except Exception:
            print(format_exc())

    def pose_fields(self):
        f_widget_ids = self.f_widget_ids
        content = self.content
        children = content.children
        orient = self.desc.get('ORIENT', 'v')[:1].lower()

        if self.desc.get("PORTABLE", True):
            if hasattr(self, "import_btn"): self.set_import_disabled(False)
            if hasattr(self, "export_btn"): self.set_export_disabled(False)
        else:
            if hasattr(self, "import_btn"): self.set_import_disabled()
            if hasattr(self, "export_btn"): self.set_export_disabled()

        side = 'left' if orient == 'h' else 'top'
        for wid in f_widget_ids:
            w = children[str(wid)]
            w.pack(fill='x', side=side, anchor='nw',
                   padx=w.pack_padx, pady=w.pack_pady)

        if self is not content:
            content.pack(fill='x', side=side, anchor='nw', expand=True)

        if not self.show_sidetips:
            return

        sidetip = self.desc.get('SIDETIP')
        if orient == 'h' and sidetip and hasattr(self, 'sidetip_label'):
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

    def set_import_disabled(self, disable=True):
        '''Disables the import button if disable is True. Enables it if not.'''
        if disable: self.import_btn.config(state="disabled")
        else:       self.import_btn.config(state="normal")

    def set_export_disabled(self, disable=True):
        '''Disables the export button if disable is True. Enables it if not.'''
        if disable: self.export_btn.config(state="disabled")
        else:       self.export_btn.config(state="normal")

    def toggle_visible(self):
        self.set_collapsed(bool(not self.show.get()))

    def set_collapsed(self, collapse=True):
        if self.content is self:
            # dont do anything if there is no specific "content" frame to hide
            return
        elif collapse:
            self.content.forget()
            self.show_btn.configure(text='+')
        else:
            self.pose_fields()
            self.show_btn.configure(text='-')
        self.show.set(not collapse)


class ColorPickerFrame(ContainerFrame):

    color_type = int

    def __init__(self, *args, **kwargs):
        ContainerFrame.__init__(self, *args, **kwargs)

        self.color_type = self.node.get_desc('TYPE', 'r').node_cls
        self.initialized = True
        self.reload()

    def reload(self):
        ContainerFrame.reload(self)
        if hasattr(self, 'color_btn'):
            if self.disabled:
                self.color_btn.config(state=tk.DISABLED)
            else:
                self.color_btn.config(state=tk.NORMAL)

            self.color_btn.config(bg=self.get_color()[1])

    def populate(self):
        ContainerFrame.populate(self)
        self.color_btn = tk.Button(
            self.content, width=4, command=self.select_color,
            bd=self.button_depth, bg=self.get_color()[1])
        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        side = 'left' if orient == 'h' else 'top'
        self.color_btn.pack(side=side)

        if self.disabled:
            self.color_btn.config(state=tk.DISABLED)
        else:
            self.color_btn.config(state=tk.NORMAL)

    def get_color(self):
        try:
            node = self.node
            if issubclass(self.color_type, float):
                int_color = (int(node.r*255), int(node.g*255), int(node.b*255))
            else:
                int_color = (node.r, node.g, node.b)
            return (int_color, '#%02x%02x%02x' % int_color)
        except Exception:
            return ((0, 0, 0), '#000000')

    def select_color(self):
        int_color, hex_color = askcolor(self.get_color()[1],
                                        parent=self.tag_window)

        if None in (int_color, hex_color):
            return

        int_color = [int(i) for i in int_color]

        if issubclass(self.color_type, float):
            int_color[0] /= 255
            int_color[1] /= 255
            int_color[2] /= 255

        node = self.node
        node.r, node.g, node.b = int_color[0], int_color[1], int_color[2]

        self.set_edited()
        self.reload()


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

        title_font = self.tag_window.app_root.container_title_font
        try:
            def_show = not self.tag_window.app_root.config_file.data.\
                       header.tag_window_flags.blocks_start_hidden
        except Exception:
            def_show = False
        show_frame = bool(kwargs.pop('show_frame', def_show))

        self.show = tk.IntVar()
        self.show.set(show_frame)
        self.options_sane = False

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

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth,
            )

        self.title_label = tk.Label(
            title, text=self.gui_name, justify='left', anchor='w',
            width=self.title_size, font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)

        self.show_btn = ttk.Checkbutton(
            title, width=3, text=toggle_text, command=self.toggle_visible,
            variable=self.show, style='ShowButton.TButton')
        self.sel_menu = widgets.ScrollMenu(
            title, f_widget_parent=self,
            sel_index=self.sel_index, max_index=node_len-1)

        self.shift_up_btn = tk.Button(
            title, width=6, text='Shift ▲',
            command=self.shift_entry_up, **btn_kwargs)
        self.shift_down_btn = tk.Button(
            buttons, width=6, text='Shift ▼',
            command=self.shift_entry_down, **btn_kwargs)
        self.add_btn = tk.Button(
            buttons, width=3, text='Add',
            command=self.add_entry, **btn_kwargs)
        self.insert_btn = tk.Button(
            buttons, width=5, text='Insert',
            command=self.insert_entry, **btn_kwargs)
        self.duplicate_btn = tk.Button(
            buttons, width=7, text='Duplicate',
            command=self.duplicate_entry, **btn_kwargs)
        self.delete_btn = tk.Button(
            buttons, width=5, text='Delete',
            command=self.delete_entry, **btn_kwargs)
        self.delete_all_btn = tk.Button(
            buttons, width=7, text='Delete all',
            command=self.delete_all_entries, **btn_kwargs)

        self.import_btn = tk.Button(
            buttons, width=5, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            buttons, width=5, text='Export',
            command=self.export_node, **btn_kwargs)

        # pack the title, menu, and all the buttons
        for w in (self.shift_down_btn, self.export_btn, self.import_btn,
                  self.delete_all_btn, self.delete_btn, self.duplicate_btn,
                  self.insert_btn, self.add_btn):
            w.pack(side="right", padx=(0, 4), pady=(2, 2))
        self.show_btn.pack(side="left")
        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.shift_up_btn.pack(side="right", padx=(4, 4), pady=(2, 2))

        self.title.pack(fill="x", expand=True)
        self.buttons.pack(fill="x", expand=True)
        self.controls.pack(fill="x", expand=True)

        self.populate()
        self.initialized = True

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
        # sort the options by value(values are integers)
        options = {i: n for n, i in self.desc.get('NAME_MAP', {}).items()}

        node, desc = self.node, self.desc
        sub_desc = desc['SUB_STRUCT']
        def_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])

        for i in range(len(node)):
            if i in options:
                continue
            sub_node = node[i]
            if not hasattr(sub_node, 'desc'):
                continue
            sub_desc = sub_node.desc
            sub_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])
            if sub_struct_name == def_struct_name:
                continue

            options[i] = sub_struct_name

        self.options_sane = True
        self.option_cache = options

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = self.sel_index
        if opt_index < 0:
            return None

        return self.options.get(opt_index)

    def set_shift_up_disabled(self, disable=True):
        '''
        Disables the move up button if disable is True. Enables it if not.
        '''
        if disable: self.shift_up_btn.config(state="disabled")
        else:       self.shift_up_btn.config(state="normal")

    def set_shift_down_disabled(self, disable=True):
        '''
        Disables the move down button if disable is True. Enables it if not.
        '''
        if disable: self.shift_down_btn.config(state="disabled")
        else:       self.shift_down_btn.config(state="normal")

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

    def shift_entry_up(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 2:
            return

        node = self.node
        index = self.sel_index
        if index <= 0:
            return

        node[index], node[index - 1] = node[index - 1], node[index]

        self.sel_index = self.sel_menu.sel_index = index - 1
        self.options_sane = self.sel_menu.options_sane = False
        self.sel_menu.update_label()
        self.set_edited()

    def shift_entry_down(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 2:
            return

        node = self.node
        index = self.sel_index
        if index >= len(node) - 1:
            return

        node[index], node[index + 1] = node[index + 1], node[index]

        self.sel_index = self.sel_menu.sel_index = index + 1
        self.options_sane = self.sel_menu.options_sane = False
        self.sel_menu.update_label()
        self.set_edited()

    def add_entry(self):
        if not hasattr(self.node, '__len__'):
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        self.node.append()

        self.sel_menu.max_index = len(self.node) - 1
        self.options_sane = self.sel_menu.options_sane = False

        if self.sel_menu.max_index == 0:
            self.sel_index = -1
            self.select_option(0)
        self.enable_all_buttons()
        self.disable_unusable_buttons()
        self.set_edited()

    def insert_entry(self):
        if not hasattr(self.node, '__len__'):
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        self.sel_index = self.sel_menu.sel_index = max(self.sel_index, 0)

        if self.sel_index < len(self.node):
            self.node.insert(self.sel_index)
        else:
            self.node.append()

        self.sel_menu.max_index = len(self.node) - 1
        self.options_sane = self.sel_menu.options_sane = False

        self.enable_all_buttons()
        self.disable_unusable_buttons()
        self.set_edited()
        self.select_option()  # select the new entry

    def duplicate_entry(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 1:
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        self.sel_index = self.sel_menu.sel_index = max(self.sel_index, 0)

        new_subnode = deepcopy(self.node[self.sel_index])
        self.node.append(new_subnode)
        self.sel_menu.max_index = len(self.node) - 1
        self.options_sane = self.sel_menu.options_sane = False
        self.enable_all_buttons()
        self.disable_unusable_buttons()
        self.set_edited()
        self.select_option(self.sel_menu.max_index)  # select the new entry

    def delete_entry(self):
        if not hasattr(self.node, '__len__') or len(self.node) == 0:
            return

        field_min = self.field_min
        if field_min is None:
            field_min = 0

        if len(self.node) <= field_min:
            if self.enforce_min:
                return
        if not len(self.node):
            self.sel_menu.disable()
            return

        self.sel_index = max(self.sel_index, 0)

        del self.node[self.sel_index]
        self.sel_menu.max_index = len(self.node) - 1
        if not len(self.node):
            self.sel_index = -1
        elif self.sel_index > self.sel_menu.max_index:
            self.sel_index -= 1

        self.sel_menu.sel_index = self.sel_index
        self.sel_menu.update_label()

        self.options_sane = self.sel_menu.options_sane = False
        self.select_option()
        self.enable_all_buttons()
        self.disable_unusable_buttons()
        self.set_edited()

    def delete_all_entries(self):
        if not hasattr(self.node, '__len__') or len(self.node) == 0:
            return

        field_min = self.field_min
        if field_min is None:
            field_min = 0

        if len(self.node) <= field_min:
            if self.enforce_min:
                return

        if not len(self.node):
            self.sel_menu.disable()
            return

        del self.node[:]
        self.sel_index = self.sel_menu.sel_index = self.sel_menu.max_index = -1
        self.sel_menu.update_label()
        self.select_option()

        self.options_sane = self.sel_menu.options_sane = False
        self.enable_all_buttons()
        self.disable_unusable_buttons()
        self.set_edited()

    def enable_all_buttons(self):
        buttons = (self.add_btn, self.insert_btn, self.duplicate_btn,
                   self.delete_btn, self.delete_all_btn,
                   self.shift_up_btn, self.shift_down_btn)
        if self.disabled:
            for btn in buttons:
                btn.config(state=tk.DISABLED)
        else:
            for btn in buttons:
                btn.config(state=tk.NORMAL)

    def disable_unusable_buttons(self):
        if isinstance(self.desc.get('SIZE'), int):
            self.set_add_disabled()
            self.set_insert_disabled()
            self.set_duplicate_disabled()
            self.set_delete_disabled()
            self.set_delete_all_disabled()
            return

        node = self.node
        empty_node = not hasattr(node, '__len__')
        field_max = self.field_max
        field_min = self.field_min
        if field_min is None: field_min = 0

        if empty_node or (field_max is not None and len(node) >= field_max):
            if self.enforce_max:
                self.set_add_disabled()
                self.set_insert_disabled()
                self.set_duplicate_disabled()

        if empty_node or len(node) <= field_min:
            if self.enforce_min or len(node) == 0:
                self.set_delete_disabled()
                self.set_delete_all_disabled()

        if empty_node or not len(node):
            self.set_duplicate_disabled()

        if empty_node or len(node) < 2:
            self.set_shift_up_disabled()
            self.set_shift_down_disabled()

    def populate(self):
        node = self.node
        desc = self.desc
        sel_index = self.sel_index

        if self.content in (None, self):
            self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                    bg=self.default_bg_color)

        del self.f_widget_ids[:]
        del self.f_widget_ids_map

        f_widget_ids = self.f_widget_ids
        f_widget_ids_map = self.f_widget_ids_map = {}

        # destroy all the child widgets of the content
        for c in list(self.content.children.values()):
            c.destroy()

        self.display_comment(self.content)

        for w in (self, self.content, self.title, self.title_label,
                  self.controls, self.buttons):
            w.tooltip_string = self.desc.get('TOOLTIP')

        self.populated = False
        sub_desc = desc['SUB_STRUCT']
        sub_struct_name = sub_desc.get('GUI_NAME')

        # if there is no GUI_NAME or the GUI_NAME is '', use the NAME instead
        if not sub_struct_name:
            sub_struct_name = sub_desc['NAME']

        self.sel_menu.default_entry_text = sub_struct_name
        self.sel_menu.update_label()
        if len(node) == 0:
            self.sel_menu.disable()
        else:
            self.sel_menu.enable()

        self.disable_unusable_buttons()

        if not hasattr(node, '__len__') or len(node) == 0:
            self.sel_index = -1
            self.sel_menu.max_index = -1
            self.sel_menu.disable()
            if self.show.get():
                self.pose_fields()
            return

        if sel_index >= 0:
            sub_node = node[sel_index]
            sub_desc = desc['SUB_STRUCT']
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            widget_cls = self.widget_picker.get_widget(sub_desc)
            try:
                widget = widget_cls(
                    self.content, node=sub_node, parent=node, show_title=False,
                    attr_index=sel_index, tag_window=self.tag_window,
                    f_widget_parent=self, disabled=self.disabled,
                    dont_padx_fields=True)
            except Exception:
                print(format_exc())
                widget = NullFrame(
                    self.content, node=sub_node, parent=node, show_title=False,
                    attr_index=sel_index, tag_window=self.tag_window,
                    f_widget_parent=self, disabled=self.disabled,
                    dont_padx_fields=True)

            f_widget_ids.append(id(widget))
            f_widget_ids_map[sel_index] = id(widget)
            self.populated = True

            self.reload()

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            self.enable_all_buttons()

            node = self.node
            node_empty = (not hasattr(node, '__len__'))
            field_max = self.field_max
            field_min = self.field_min
            if field_min is None: field_min = 0

            self.disable_unusable_buttons()

            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled or node_empty or len(node) == 0:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            if node_empty or len(node) == 0:
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
            sub_desc = self.desc['SUB_STRUCT']
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            for wid in self.f_widget_ids:
                w = self.content.children[str(wid)]

                # if the descriptors are different, gotta repopulate!
                if w.desc is not sub_desc:
                    self.populate()
                    return
                    
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

            # by adding a fixed amount of padding, we fix a problem
            # with difficult to predict padding based on nesting
            w.pack(fill='x', side='top', expand=True,
                   padx=self.vertical_padx, pady=self.vertical_pady)

        # if there are no children in the content, we need to
        # pack in SOMETHING, update the idletasks, and then
        # destroy that something to resize the content frame
        if not self.content.children:
            f = tk.Frame(self.content, width=0, height=0, bd=0)
            a, b, c = f.pack(), self.content.update_idletasks(), f.destroy()

        self.content.pack(fill='both', side='top', anchor='nw', expand=True)

    def select_option(self, opt_index=None, force_reload=False):
        node = self.node
        desc = self.desc
        curr_index = self.sel_index
        if opt_index is None:
            opt_index = curr_index

        if opt_index == curr_index and self.options_sane and not force_reload:
            return
        elif opt_index >= len(node) and len(node):
            opt_index = len(node) - 1
        elif not len(node):
            self.sel_index = -1
            self.populate()
            return

        # flush any lingering changes
        self.flush()

        if opt_index < 0 or opt_index is None:
            self.sel_index = -1
            self.populate()
            return

        self.sel_index = opt_index

        if curr_index >= len(node):
            self.populate()
            return

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

    @property
    def visible_field_count(self):
        # array frames only display one item at a time
        return 1


class DynamicArrayFrame(ArrayFrame):
    def __init__(self, *args, **kwargs):
        ArrayFrame.__init__(self, *args, **kwargs)

        self.sel_menu.bind('<FocusIn>', self.set_not_sane)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.set_not_sane)

    def cache_options(self):
        node, desc = self.node, self.desc
        dyn_name_path = desc.get('DYN_NAME_PATH')

        options = {}
        if dyn_name_path:
            try:
                for i in range(len(node)):
                    name = str(node[i].get_neighbor(dyn_name_path))
                    if name:
                        options[i] = name
            except Exception:
                pass

        if not dyn_name_path:
            # sort the options by value(values are integers)
            options.update({i: n for n, i in
                            self.desc.get('NAME_MAP', {}).items()
                            if i not in options})
            sub_desc = desc['SUB_STRUCT']
            def_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])

            for i in range(len(node)):
                if i in options:
                    continue
                sub_node = node[i]
                if not hasattr(sub_node, 'desc'):
                    continue
                sub_desc = sub_node.desc
                sub_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])
                if sub_struct_name == def_struct_name:
                    continue

                options[i] = sub_struct_name

        for i, v in options.items():
            options[i] = '%s. %s' % (i, v)

        self.options_sane = True
        self.option_cache = options
        self.sel_menu.update_label()

    def set_not_sane(self, e=None):
        self.options_sane = self.sel_menu.options_sane = False


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
        try: del self.tag_window
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

    def flush(self): pass

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.field_type_name = tk.Label(
            self, text='<%s>'%self.desc['TYPE'].name,
            anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)

        for w in (self, self.title_label, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')

        # now that the field widgets are created, position them
        self.pose_fields()
        self.initialized = True

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")

    def reload(self): pass


class RawdataFrame(DataFrame):

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()
        self.initialized = True

    def flush(self): pass

    @property
    def field_ext(self):
        '''The export extension of this FieldWidget.'''
        desc = self.desc
        parent_name = tag_ext = ''
        try:
            if self.parent is None:
                tag_ext = self.node.get_root().ext
            else:
                tag_ext = self.parent.get_root().ext
        except Exception: pass

        try: parent_name = '.' + self.parent.desc['NAME']
        except Exception: pass

        return desc.get('EXT', '%s%s.%s' %
                        (tag_ext, parent_name, desc['NAME']))

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)

        self.tooltip_string = self.desc.get('TOOLTIP')
        self.title_label.tooltip_string = self.tooltip_string
        for w in (self, self.title_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, bd=self.button_depth)
        self.import_btn = tk.Button(
            self, width=5, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            self, width=5, text='Export',
            command=self.export_node, **btn_kwargs)

        # now that the field widgets are created, position them
        self.pose_fields()

    def import_node(self):
        '''Prompts the user for an exported node file.
        Imports data into the node from the file.'''
        try:
            initialdir = self.tag_window.app_root.last_load_dir
        except AttributeError:
            initialdir = None

        ext = self.field_ext

        filepath = askopenfilename(
            initialdir=initialdir, defaultextension=ext,
            filetypes=[(self.name, "*" + ext), ('All', '*')],
            title="Import '%s' from..." % self.name)

        if not filepath:
            return

        curr_size = None
        index = self.attr_index

        try:
            rawdata = get_rawdata(filepath=filepath)
            if hasattr(self.node, 'parse'):
                curr_size = self.node.get_size()
                self.node.set_size(len(rawdata))

                self.node.parse(rawdata=rawdata)
            else:
                # the node isnt a block, so we need to call its parents
                # parse method with the attr_index necessary to import.
                curr_size = self.parent.get_size(attr_index=index)
                self.parent.set_size(len(rawdata), attr_index=index)

                self.parent.parse(rawdata=rawdata, attr_index=index)
                self.node = self.parent[index]

            # until i come up with a better method, i'll have to rely on
            # reloading the root field widget so stuff(sizes) will be updated
            root = self.f_widget_parent
            while hasattr(root, 'f_widget_parent'):
                if root.f_widget_parent is None:
                   break
                root = root.f_widget_parent

            try:
                root.reload()
                self.set_edited()
            except Exception:
                print(format_exc())
                print("Could not reload after importing '%s' node." % self.name)
        except Exception:
            print(format_exc())
            print("Could not import '%s' node." % self.name)
            if curr_size is None:
                pass
            elif hasattr(self.node, 'parse'):
                self.node.set_size(curr_size)
            else:
                self.parent.set_size(curr_size, attr_index=index)
                

    def pose_fields(self):
        padx, pady, side= self.horizontal_padx, self.horizontal_pady, 'top'
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.import_btn.pack(side='left', fill="x", padx=padx, pady=pady)
        self.export_btn.pack(side='left', fill="x", padx=padx, pady=pady)

    def reload(self): pass


class VoidFrame(DataFrame):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()
        self.initialized = True

    def flush(self): pass

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.field_type_name = tk.Label(
            self, text='<VOIDED>', anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)

        for w in (self, self.title_label, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')

        # now that the field widgets are created, position them
        self.pose_fields()

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")

    def reload(self): pass


class PadFrame(VoidFrame):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color, pack_padx=0, pack_pady=0)
        DataFrame.__init__(self, *args, **kwargs)
        self.initialized = True

    def populate(self): pass

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")
        for w in (self, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')


class EntryFrame(DataFrame):
    value_max = None
    value_min = None

    _flushing = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        size = self.parent.get_size(self.attr_index)

        # make the widgets
        self.entry_string = tk.StringVar(self)
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)

        self.entry_string.trace('w', self.update_node)

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left', anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, width=self.title_size)

        self.data_entry = tk.Entry(
            self.content, textvariable=self.entry_string,
            justify='left', bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)

        self.data_entry.bind('<Return>', self.full_flush)
        self.data_entry.bind('<FocusIn>', self.touch_field)
        self.data_entry.bind('<FocusOut>', self.full_flush)

        self.entry_string.trace('w', self.edit_field)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color)

        self.populate()
        self.initialized = True

    def touch_field(self, e=None):
        self.set_needs_flushing()

    def edit_field(self, *args):
        self.needs_flushing = True
        self.flush()

    def full_flush(self, *args):
        if self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            node = self.node
            unit_scale = self.desc.get('UNIT_SCALE')
            curr_val = self.entry_string.get()
            try:
                new_node = self.sanitize_input()
            except Exception:
                # Couldnt cast the string to the node class. This is fine this
                # kind of thing happens when entering data. Just dont flush it
                self._flushing = False
                self.set_needs_flushing(False)
                return

            # dont need to flush anything since the nodes are the same
            if node == new_node:
                self._flushing = False
                return

            if self.parent[self.attr_index] != new_node:
                if unit_scale is not None and isinstance(new_node, (int, float)):
                    str_node = str(new_node * unit_scale)
                else:
                    str_node = str(new_node)
                self.parent[self.attr_index] = new_node
                self.entry_string.set(str_node)
                self.set_edited()

            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            # an error occurred so replace the entry with the last valid string
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    def flush(self, *args):
        if self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            curr_val = self.entry_string.get()
            try:
                new_node = self.sanitize_input()
            except Exception:
                # Couldnt cast the string to the node class. This is fine this
                # kind of thing happens when entering data. Just dont flush it
                self._flushing = False
                return

            if self.parent[self.attr_index] != new_node:
                self.parent[self.attr_index] = new_node
                self.set_edited()
            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            # an error occurred so replace the entry with the last valid string
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    def sanitize_input(self):
        desc = self.desc
        field_max = self.field_max
        node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)
        new_node = node_cls(self.entry_string.get())

        sizecalc = desc['TYPE'].sizecalc
        node_size = sizecalc(new_node)
        if field_max is None:
            field_max = desc.get('SIZE')

        if isinstance(field_max, int) and node_size > field_max:
            if self.enforce_max:
                changed = True
                while node_size > field_max:
                    new_node = new_node[:-1]
                    node_size = sizecalc(new_node)


        return new_node

    @property
    def entry_width(self):
        entry_width = self.widget_width

        if entry_width:
            return entry_width

        desc = self.desc
        node = self.node
        f_type = desc['TYPE']

        parent = self.parent
        node_size = parent.get_size(self.attr_index)

        value_max = desc.get('MAX', f_type.max)
        value_min = desc.get('MIN', f_type.min)
        if value_max is None: value_max = 0
        if value_min is None: value_min = 0

        max_width = self.max_string_entry_width

        # if the size is not fixed using an int, dont rely on it
        if not isinstance(desc.get('SIZE', f_type.size), int):
            node_size = self.def_string_entry_width

        value_width = max(abs(value_max), abs(value_min), node_size)
        entry_width = max(self.min_entry_width,
                          min(value_width, max_width))
        if isinstance(node, str) and isinstance(f_type.size, int):
            entry_width = (entry_width - 1 + f_type.size)//f_type.size
        return entry_width

    def populate(self):
        self.display_comment()
        self.data_entry.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        sidetip = self.desc.get('SIDETIP')
        if self.show_sidetips and sidetip:
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

        for w in (self, self.content, self.title_label,
                  self.data_entry, self.sidetip_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        self.reload()

    def reload(self):
        try:
            self._prev_str_val = ''
            node = self.node
            unit_scale = self.desc.get('UNIT_SCALE')

            if unit_scale is not None and isinstance(node, (int, float)):
                node *= unit_scale

            self.needs_flushing = False
            self.data_entry.config(state=tk.NORMAL)
            self.data_entry.config(width=self.entry_width)
            self.data_entry.delete(0, tk.END)
            self.data_entry.insert(0, str(node))

            self._prev_str_val = self.entry_string.get()
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.data_entry.config(state=tk.DISABLED)
            else:
                self.data_entry.config(state=tk.NORMAL)

    def update_node(self, *args, **kwargs):
        if self._flushing:
            return
        self.flush()


class NumberEntryFrame(EntryFrame):

    def sanitize_input(self):
        desc = self.desc
        field_max, field_min = self.field_max, self.field_min
        node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)
        new_node = node_cls(self.entry_string.get())

        unit_scale = desc.get('UNIT_SCALE')
        desc_size = desc.get('SIZE')

        if unit_scale is None:
            pass
        elif isinstance(new_node, int):
            new_node = new_node // unit_scale
        else:
            new_node /= unit_scale

        if isinstance(new_node, float):
            pass
        elif field_max is None and isinstance(desc_size, int):
            if not desc['TYPE'].is_bit_based:
                field_max = 2**(desc_size * 8)
            else:
                field_max = 2**desc_size

        if field_max is not None and new_node >= field_max:
            if self.enforce_max:
                new_node = field_max
                changed = True
                if not desc.get('ALLOW_MAX', True):
                    raise ValueError("Enter a value below %s" % field_max)
        elif field_min is not None and new_node <= field_min:
            if self.enforce_min:
                new_node = field_min
                changed = True
                if not desc.get('ALLOW_MIN', True):
                    raise ValueError("Enter a value above %s" % field_min)

        if isinstance(new_node, float):
            new_node = round(
                new_node, self.parent.get_size(self.attr_index)*2 - 2)

        return new_node

    @property
    def entry_width(self):
        entry_width = self.widget_width

        if entry_width:
            return entry_width

        desc = self.desc
        node = self.node
        f_type = desc['TYPE']
        unit_scale = desc.get('UNIT_SCALE')

        if unit_scale is not None and isinstance(node, (int, float)):
            node *= unit_scale

        parent = self.parent
        node_size = parent.get_size(self.attr_index)
        fixed_size = isinstance(desc.get('SIZE', f_type.size), int)

        value_max = desc.get('MAX', f_type.max)
        value_min = desc.get('MIN', f_type.min)

        if isinstance(node, float):
            # floats are hard to choose a reasonable entry width for
            max_width = self.max_float_entry_width
            value_width = int(ceil(node_size * 5/2))
            node = round(node, node_size*2 - 2)
        else:
            max_width = self.max_int_entry_width
            if not f_type.is_bit_based:
                node_size *= 8

            adjust = 0
            if value_min is None: value_min = 0
            if value_max is None: value_max = 0

            if isinstance(value_max, int):
                if value_max < 0:
                    adjust = 1
                    value_max *= -1
            if isinstance(value_min, int):
                if value_min < 0:
                    adjust = 1
                    value_min *= -1
            value_max = max(value_min, value_max)

            if 2**node_size > value_max:
                value_max = 2**node_size
                if min(value_min, value_max) < 0:
                    adjust = 1

            if unit_scale is not None:
                value_max *= unit_scale

            value_width = int(ceil(log(value_max, 10))) + adjust

        entry_width = max(self.min_entry_width,
                          min(value_width, max_width))
        return entry_width


class TimestampFrame(EntryFrame):

    def flush(self):
        if self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            desc = self.desc
            node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)

            new_node = node_cls(self.entry_string.get())
            if self.parent[self.attr_index] != new_node:
                self.parent[self.attr_index] = new_node
                self.set_edited()
            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    @property
    def entry_width(self):
        entry_width = self.widget_width
        if not entry_width:
            entry_width = self.def_string_entry_width
        return entry_width

    
class HexEntryFrame(EntryFrame):

    def flush(self):
        try:
            self.parent[self.attr_index] = self.entry_string.get()
        except Exception:
            print(format_exc())

    def flush(self):
        if self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            new_node = self.entry_string.get()
            if self.parent[self.attr_index] != new_node:
                self.parent[self.attr_index] = new_node
                self.set_edited()
            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    @property
    def entry_width(self):
        entry_width = self.widget_width
        if entry_width is not None:
            return entry_width

        desc = self.desc
        node_size = self.parent.get_size(self.attr_index)

        value_max = desc.get('MAX', 0)
        value_min = desc.get('MIN', 0)

        # if the size is not fixed using an int, dont rely on it
        if not isinstance(desc.get('SIZE', desc['TYPE'].size), int):
            node_size = self.def_string_entry_width

        value_width = max(abs(value_max), abs(value_min), node_size) * 2

        return max(self.min_entry_width,
                   min(value_width, self.max_string_entry_width))


class TextFrame(DataFrame):
    '''Used for strings that likely will not fit on one line.'''
    '''Used for ints, floats, and strings that
    fit on one line as well as ints and floats.'''

    value_max = None
    value_min = None

    children_can_scroll = True
    _flushing = False

    replace_map = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        size = self.parent.get_size(self.attr_index)

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left', anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, width=self.title_size)

        self.data_text = tk.Text(
            self.content, bd=self.entry_depth, wrap=tk.NONE,
            height=self.textbox_height, maxundo=self.max_undos, undo=1,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color,)

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color)

        self.hsb = tk.Scrollbar(self.content, orient='horizontal',
                                command=self.data_text.xview)
        self.vsb = tk.Scrollbar(self.content, orient='vertical',
                                command=self.data_text.yview)
        self.data_text.config(xscrollcommand=self.hsb.set,
                              yscrollcommand=self.vsb.set)

        self.hsb.can_scroll = self.children_can_scroll
        self.vsb.can_scroll = self.children_can_scroll
        self.data_text.can_scroll = self.children_can_scroll
        self.data_text.bind('<FocusIn>', self.touch_field)

        if self.gui_name != '':
            self.title_label.pack(fill="x")
        self.hsb.pack(side="bottom", fill='x', expand=True)
        self.data_text.pack(side="left", fill="x")
        self.vsb.pack(side="left",  fill='y')
        self.content.pack(fill="both", expand=True)

        self.build_replace_map()

        self.reload()
        self.initialized = True

    def touch_field(self, e=None):
        self.set_needs_flushing()

    def build_replace_map(self):
        desc = self.desc
        enc = desc['TYPE'].enc
        c_size = desc['TYPE'].size

        endian = 'big' if desc['TYPE'].endian == '>' else 'little'

        self.replace_map = {}
        # this is the header what the first 16
        # characters will be replaced with.
        hex_head = '\\0x0'

        # add a null and return character to the end of it so it can
        # be distinguished from users typing \x00 or \xff and whatnot.
        hex_foot = b'\x00' * c_size
        if endian == 'little':
            hex_foot = b'\x00' * (c_size - 1) + b'\x0d'
            hex_foot = b'\x00' * (c_size - 1) + b'\x0a'
        else:
            hex_foot = b'\x0d' + (b'\x00' * (c_size - 1))
            hex_foot = b'\x0a' + (b'\x00' * (c_size - 1))
        hex_foot = hex_foot.decode(encoding=enc)

        for i in range(0, 32):
            if i in (9, 10, 13):
                # formatting characters
                continue
            elif i == 16:
                hex_head = '\\0x'

            byte_str = i.to_bytes(c_size, endian).decode(encoding=enc)
            self.replace_map[byte_str] = hex_head + hex(i)[2:] + hex_foot

    def flush(self):
        if self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            desc = self.desc
            node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)
            new_node = self.data_text.get(1.0, tk.END)

            # NEED TO DO THIS SORTED cause the /x00 we inserted will be mesed up
            for b in sorted(self.replace_map.keys()):
                new_node = new_node.replace(self.replace_map[b], b)

            new_node = node_cls(new_node)
            if self.parent[self.attr_index] != new_node:
                self.parent[self.attr_index] = new_node
                self.set_edited()
            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            print(format_exc())

    def reload(self):
        try:
            new_text = self.node
            # NEED TO DO THIS SORTED cause the /x00 we insert will be mesed up
            for b in sorted(self.replace_map.keys()):
                new_text = new_text.replace(b, self.replace_map[b])
            self.data_text.config(state=tk.NORMAL)
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(1.0, new_text)
            self.data_text.edit_reset()
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.data_text.config(state=tk.DISABLED)
            else:
                self.data_text.config(state=tk.NORMAL)

        sidetip = self.desc.get('SIDETIP')
        if self.show_sidetips and sidetip:
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

        for w in (self, self.content, self.title_label,
                  self.data_text, self.sidetip_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

    populate = reload


class UnionFrame(ContainerFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        try:
            def_show = not self.tag_window.app_root.config_file.data.\
                       header.tag_window_flags.blocks_start_hidden
        except Exception:
            def_show = False
        show_frame = bool(kwargs.pop('show_frame', def_show))

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        self.show = tk.IntVar(self)
        self.show.set(show_frame)
        self.content = self

        max_u_index = len(self.desc['CASE_MAP'])
        u_index = self.node.u_index
        if u_index is None:
            u_index = max_u_index

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth,
            )

        title_font = self.tag_window.app_root.container_title_font
        self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                              bg=self.frame_bg_color)
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            variable=self.show, style='ShowButton.TButton')
        self.title_label = tk.Label(
            self.title, text=self.gui_name, anchor='w',
            width=self.title_size, justify='left', font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color)
        self.sel_menu = widgets.ScrollMenu(
            self.title, f_widget_parent=self, sel_index=u_index,
            max_index=max_u_index, disabled=self.disabled)

        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")

        self.title.pack(fill="x", expand=True)

        self.populate()
        self.initialized = True

    @property
    def options(self):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None:
            self.cache_options()
        return self.option_cache

    def cache_options(self):
        options = {i: c for c, i in self.desc['CASE_MAP'].items()}
        options[len(options)] = e_c.RAW_BYTES
        self.option_cache = options

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = self.node.u_index
            if opt_index is None:
                opt_index = len(self.options) - 1
        if opt_index is None:
            opt_index = -1

        return self.options.get(opt_index, e_c.INVALID_OPTION)

    def select_option(self, opt_index=None):
        self.flush()
        node = self.node
        curr_index = self.sel_menu.sel_index

        if (opt_index < 0 or opt_index > self.sel_menu.max_index or
            opt_index is None):
            return

        if opt_index == self.sel_menu.max_index:
            # setting to rawdata
            self.node.set_active()
        else:
            self.node.set_active(opt_index)
        self.set_edited()

        self.sel_menu.sel_index = opt_index
        self.reload()
        try:
            u_index = self.node.u_index
            if u_index is None:
                return
        except Exception:
            print(format_exc())

    def populate(self):
        try:
            old_content = self.content
            new_content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                   bg=self.default_bg_color)
            self.content = new_content

            # clear the f_widget_ids list
            del self.f_widget_ids[:]
            del self.f_widget_ids_map

            f_widget_ids = self.f_widget_ids
            f_widget_ids_map = self.f_widget_ids_map = {}

            self.sel_menu.update_label()
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            node = self.node
            desc = self.desc

            for w in (self, self.content, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            self.display_comment(self.content)

            u_node = node.u_node
            if u_node is None:
                btn_kwargs = dict(
                    bg=self.button_color, fg=self.text_normal_color,
                    disabledforeground=self.text_disabled_color,
                    bd=self.button_depth,
                    )
                self.raw_label = tk.Label(
                    new_content, text='DataUnion: %s raw bytes' % node.get_size(),
                    width=self.title_size, anchor='w',
                    bg=self.default_bg_color, fg=self.text_normal_color,
                    disabledforeground=self.text_disabled_color)
                # make the rawdata inner frame
                self.import_btn = tk.Button(
                    new_content, width=5, text='Import',
                    command=self.import_node, **btn_kwargs)
                self.export_btn = tk.Button(
                    new_content, width=5, text='Export',
                    command=self.export_node, **btn_kwargs)
                self.raw_label.pack(padx=self.vertical_padx,
                                    side="left", expand=True, fill='x')
                for w in (self.export_btn, self.import_btn):
                    w.pack(side="left", padx=(0, 4), pady=2)
            else:
                if hasattr(self, 'import_btn'):
                    del self.import_btn
                    del self.export_btn

                u_desc = desc[node.u_index]
                if hasattr(u_node, 'desc'):
                    u_desc = u_node.desc

                widget_cls = self.widget_picker.get_widget(u_desc)
                kwargs = dict(
                    node=u_node, parent=node, show_title=False,
                    tag_window=self.tag_window, attr_index='u_node',
                    disabled=self.disabled, f_widget_parent=self,
                    desc=u_desc, show_frame=self.show.get(),
                    dont_padx_fields=True)
                try:
                    widget = widget_cls(new_content, **kwargs)
                except Exception:
                    print(format_exc())
                    widget = NullFrame(new_content, **kwargs)

                f_widget_ids.append(id(widget))
                f_widget_ids_map['u_node'] = id(widget)

            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()

            # do things in this order to prevent the window from scrolling up
            if old_content not in (None, self):
                old_content.destroy()
        except Exception:
            print(format_exc())

    reload = populate

    def pose_fields(self):
        children = self.content.children
        for wid in self.f_widget_ids:
            w = children[str(wid)]

            # by adding a fixed amount of padding, we fix a problem
            # with difficult to predict padding based on nesting
            w.pack(fill='x', anchor='nw',
                   padx=self.vertical_padx, pady=self.vertical_pady)

        self.content.pack(fill='x', anchor='nw', expand=True)


class StreamAdapterFrame(ContainerFrame):

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        try:
            def_show = not self.tag_window.app_root.config_file.data.\
                       header.tag_window_flags.blocks_start_hidden
        except Exception:
            def_show = False
        show_frame = bool(kwargs.pop('show_frame', def_show))

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        self.show = tk.IntVar(self)
        self.show.set(show_frame)

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth,
            )

        title_font = self.tag_window.app_root.container_title_font
        self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                              bg=self.frame_bg_color)
        self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                bg=self.default_bg_color)
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            variable=self.show, style='ShowButton.TButton')
        self.title_label = tk.Label(
            self.title, text=self.gui_name, anchor='w',
            width=self.title_size, justify='left', font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color)
        self.import_btn = tk.Button(
            self.title, width=5, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            self.title, width=5, text='Export',
            command=self.export_node, **btn_kwargs)

        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)

        self.title.pack(fill="x", expand=True)
        for w in (self.export_btn, self.import_btn):
            w.pack(side="right", padx=(0, 4), pady=2)

        self.populate()
        self.initialized = True

    def populate(self):
        try:
            # clear the f_widget_ids list
            del self.f_widget_ids[:]
            del self.f_widget_ids_map

            f_widget_ids = self.f_widget_ids
            f_widget_ids_map = self.f_widget_ids_map = {}

            # destroy all the child widgets of the content
            for c in list(self.content.children.values()):
                c.destroy()

            node = self.node
            desc = self.desc
            data = node.data

            for w in (self, self.content, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            self.display_comment(self.content)

            data_desc = desc['SUB_STRUCT']
            if hasattr(data, 'desc'):
                data_desc = data.desc

            widget_cls = self.widget_picker.get_widget(data_desc)
            kwargs = dict(node=data, parent=node, show_title=False,
                          tag_window=self.tag_window, attr_index='SUB_STRUCT',
                          disabled=self.disabled, f_widget_parent=self,
                          desc=data_desc, show_frame=self.show.get(),
                          dont_padx_fields=True)
            try:
                widget = widget_cls(self.content, **kwargs)
            except Exception:
                print(format_exc())
                widget = NullFrame(self.content, **kwargs)

            f_widget_ids.append(id(widget))
            f_widget_ids_map['data'] = id(widget)

            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()
        except Exception:
            print(format_exc())

    reload = populate

    pose_fields = UnionFrame.pose_fields


class EnumFrame(DataFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        try:
            sel_index = self.node.get_index()
        except Exception:
            sel_index = -1

        label_width = self.widget_width
        if not label_width:
            label_width = self.enum_menu_width
            for s in self.options.values():
                label_width = max(label_width, len(s))

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)

        self.display_comment()

        self.title_label = tk.Label(
            self.content, text=self.gui_name,
            justify='left', anchor='w', width=self.title_size,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.sel_menu = widgets.ScrollMenu(
            self.content, f_widget_parent=self, menu_width=label_width,
            sel_index=sel_index, max_index=self.desc.get('ENTRIES', 0) - 1,
            disabled=self.disabled, default_entry_text="<INVALID>")

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.reload()
        self.initialized = True

    def flush(self): pass

    @property
    def options(self):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None:
            self.cache_options()
        return self.option_cache

    def cache_options(self):
        desc = self.desc
        options = {}
        # sort the options by value(values are integers)
        for i in range(desc.get('ENTRIES', 0)):
            opt = desc[i]
            if 'GUI_NAME' in opt:
                options[i] = opt['GUI_NAME']
            else:
                options[i] = opt.get('NAME', '<UNNAMED %s>' % i)\
                             .replace('_', ' ')
        self.option_cache = options

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = self.sel_menu.sel_index
        return self.options.get(opt_index)

    def reload(self):
        try:
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            for w in (self, self.content, self.sel_menu, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            options = self.options
            option_count = len(options)
            if not option_count:
                self.sel_menu.sel_index = -1
                self.sel_menu.max_index = -1
                return

            try:
                curr_index = self.node.get_index()
            except Exception:
                curr_index = -1

            self.sel_menu.sel_index = curr_index
            self.sel_menu.max_index = option_count - 1
            self.sel_menu.update_label()
        except Exception:
            print(format_exc())

    populate = reload

    def pose_fields(self): pass

    def select_option(self, opt_index=None):
        node = self.node
        curr_index = self.sel_menu.sel_index

        if (opt_index < 0 or opt_index > self.sel_menu.max_index or
            opt_index is None):
            return

        self.sel_menu.sel_index = opt_index

        self.node.set_to(opt_index)
        self.sel_menu.update_label()
        self.set_edited()


class DynamicEnumFrame(EnumFrame):
    options_sane = False

    # make options not sane once focus is given to the enum's sel_menu

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        label_width = self.widget_width
        if not label_width:
            label_width = self.enum_menu_width
            for s in self.options.values():
                label_width = max(label_width, len(s))

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)

        self.title_label = tk.Label(
            self.content, text=self.gui_name,
            justify='left', anchor='w', width=self.title_size,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.sel_menu = widgets.ScrollMenu(
            self.content, f_widget_parent=self, menu_width=label_width,
            sel_index=self.node + 1, max_index=0,
            disabled=self.disabled, default_entry_text="<INVALID>")
        self.sel_menu.bind('<FocusIn>', self.set_not_sane)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.set_not_sane)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.reload()
        self.initialized = True

    @property
    def options(self):
        if not self.options_sane:
            self.cache_options()
            self.options_sane = True
        return self.option_cache

    def set_not_sane(self, e=None):
        if self.desc.get('DYN_NAME_PATH'):
            self.options_sane = self.sel_menu.options_sane = False

    def cache_options(self):
        desc = self.desc
        options = {0: "-1: NONE"}

        dyn_name_path = desc.get('DYN_NAME_PATH')
        if not dyn_name_path:
            print("Missing DYN_NAME_PATH path in dynamic enumerator.")
            print(self.parent.get_root().def_id, self.name)
            self.option_cache = options
            return
        try:
            p_out, p_in = dyn_name_path.split('[DYN_I]')

            # We are ALWAYS going to go to the parent, so we need to slice
            if p_out.startswith('..'): p_out = p_out.split('.', 1)[-1]
            array = self.parent.get_neighbor(p_out)
            for i in range(len(array)):
                name = array[i].get_neighbor(p_in)
                if isinstance(name, list):
                    name = repr(name).strip("[").strip("]")
                else:
                    name = str(name)

                options[i + 1] = '%s. %s' % (i, name)
        except Exception:
            print(format_exc())
            dyn_name_path = False

        try:
            self.sel_menu.max_index = len(options) - 1
        except Exception:
            pass
        self.option_cache = options

    def reload(self):
        try:
            self.options_sane = False
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            self.cache_options()
            self.sel_menu.sel_index = self.node + 1
            self.sel_menu.update_label()
        except Exception:
            print(format_exc())

    def select_option(self, opt_index=None):
        if opt_index is None:
            return

        self.sel_menu.sel_index = opt_index

        # since the node value is actually signed and can be -1, we'll
        # set entry 0 to be a node value of -1 and all other values
        # are one less than the entry index they are located in.
        self.node = self.parent[self.attr_index] = opt_index - 1
        self.sel_menu.update_label()
        self.set_edited()


class BoolFrame(DataFrame):
    children_can_scroll = True

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)

        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,)

        if self.gui_name != '':
            self.title_label.pack(side='left')

        self.display_comment()

        self.content = tk.Frame(
            self, bg=self.default_bg_color, bd=self.listbox_depth,
            relief='sunken', highlightthickness=0)
        self.check_canvas = tk.Canvas(
            self.content, bg=self.entry_normal_color, highlightthickness=0)
        self.check_frame = tk.Frame(
            self.check_canvas, bg=self.entry_normal_color, highlightthickness=0)

        self.scrollbar_y = tk.Scrollbar(self.content, orient='vertical',
                                        command=self.check_canvas.yview)

        self.check_canvas.config(yscrollcommand=self.scrollbar_y.set)
        self.check_frame_id = self.check_canvas.create_window(
            (0, 0), window=self.check_frame, anchor='nw')

        self.check_frame.bind('<MouseWheel>', self.mousewheel_scroll_y)
        self.check_canvas.bind('<MouseWheel>', self.mousewheel_scroll_y)

        self.populate()
        self.initialized = True

    def flush(self): pass

    def populate(self):
        bit_opt_map = {}

        # destroy all the child widgets of the content
        for c in list(self.check_frame.children.values()):
            c.destroy()

        desc = self.desc
        data = self.node.data
        value_index_map = desc['VALUE_MAP']

        # get how many bits there can possibly be
        size = self.parent.get_size(self.attr_index)
        if not desc['TYPE'].is_bit_based:
            size *= 8

        for w in (self, self.content, self.check_canvas,
                  self.check_frame, self.title_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        all_visible = self.all_bools_visible

        # loop over each possible boolean(even unused ones)
        for bit in range(size):
            opt = desc.get(value_index_map.get(1 << bit))

            if opt is None:
                if not all_visible:
                    continue
                name = e_c.UNKNOWN_BOOLEAN % bit
                opt = dict(GUI_NAME=name, NAME=name)
            else:
                opt = dict(opt)
                defname = opt.get('NAME', e_c.UNNAMED_FIELD).replace('_', ' ')
                opt.setdefault('GUI_NAME', defname)

            bit_opt_map[bit] = opt
        
        for bit in sorted(bit_opt_map):
            opt = bit_opt_map[bit]
            name = opt.get('GUI_NAME', opt['NAME'])
            check_var = tk.IntVar(self.check_frame)
            check_var.set(bool(data & (1 << bit)))

            check_btn = tk.Checkbutton(
                self.check_frame, variable=check_var, padx=0, pady=0,
                text=name, anchor='nw', justify='left', borderwidth=0,
                command=lambda i=bit, v=check_var: self.set_bool_to(i, v),

                disabledforeground=self.text_disabled_color,
                bg=self.entry_normal_color, fg=self.text_normal_color,
                activebackground=self.entry_highlighted_color,
                activeforeground=self.text_highlighted_color,)

            check_btn.pack(anchor='nw', fill='x', expand=True)
            check_btn.bind('<MouseWheel>', self.mousewheel_scroll_y)
            check_btn.tooltip_string = opt.get('TOOLTIP')

        self.pose_fields()

    reload = populate

    def set_bool_to(self, bit, new_val_var):
        self.set_edited()
        desc, node = self.desc, self.node
        mask, data = 1 << bit, node.data
        node.data = data - (data & mask) + mask*bool(new_val_var.get())

    def pose_fields(self):
        self.content.pack(side='left', anchor='nw')
        self.check_canvas.pack(side='left', fill='both')
        self.update()

        width = self.check_frame.winfo_reqwidth()
        height = self.check_frame.winfo_reqheight()

        self.check_canvas.config(scrollregion="0 0 %s %s" % (width, height))

        width = max(width, self.bool_frame_min_width)
        height = max(height, self.bool_frame_min_height)
        if height > self.bool_frame_max_height:
            height = self.bool_frame_max_height
            self.scrollbar_y.pack(side='left', fill="y")
            self.children_can_scroll = True
        else:
            self.scrollbar_y.forget()
            self.children_can_scroll = False

        self.check_canvas.can_scroll = self.children_can_scroll
        self.check_frame.can_scroll = self.children_can_scroll
        self.scrollbar_y.can_scroll = self.children_can_scroll
        for w in self.check_frame.children.values():
            w.can_scroll = self.children_can_scroll

        width = min(self.bool_frame_max_width, width)
        height = min(self.bool_frame_max_height, height)
        self.content.config(width=width + self.frame_depth*2,
                            height=height + self.frame_depth*2)
        self.check_canvas.config(width=width, height=height)

    def mousewheel_scroll_y(self, e):
        self.check_canvas.yview_scroll(e.delta//-120, "units")


class BoolSingleFrame(DataFrame):
    checked = None

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)

        self.checked = tk.IntVar(self)
        self.checkbutton = tk.Checkbutton(
            self, variable=self.checked, command=self.check,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            activebackground=self.entry_highlighted_color,
            activeforeground=self.text_highlighted_color)

        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,)

        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.checkbutton.pack(side='left')

        self.reload()
        self.initialized = True

    def flush(self): pass

    def check(self):
        try:
            desc = self.desc
            self.set_edited()
            self.node = self.parent[self.attr_index] = self.checked.get()
        except Exception:
            print(format_exc())

    def reload(self):
        try:
            for w in (self, self.checkbutton, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')
            if self.disabled:
                self.checkbutton.config(state=tk.NORMAL)
            self.checked.set(bool(self.node))
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.checkbutton.config(state=tk.DISABLED)

    populate = reload
