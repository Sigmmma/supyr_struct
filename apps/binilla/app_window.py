import gc
import os
import tkinter as tk

from copy import deepcopy
from time import time, sleep
from os.path import dirname
from tkinter import font
from tkinter.constants import *
from tkinter.filedialog import askopenfilenames, askopenfilename, askdirectory,\
     asksaveasfilename
from traceback import format_exc

from . import constants as const
from . import editor_constants as e_const
from .tag_window import *
from .widget_picker import *
from ..handler import Handler

'''
TODO:
'''

class Binilla(tk.Tk):
    # the def_id of the currently in-focus tag
    selected_def_id = None
    # the filepath of the currently in-focus tag
    selected_tag_path = None

    # a window that displays and allows selecting loaded definitions
    def_selector_window = None

    # the default WidgetPicker instance to use for selecting widgets
    widget_picker = WidgetPicker()

    # the list of TagWindow instances that are open
    tag_windows = None

    default_tag_window_class = TagWindow
    
    curr_dir = os.path.abspath(os.curdir)

    last_load_dir = curr_dir
    last_imp_dir  = curr_dir
    last_defs_dir = curr_dir

    '''Miscellaneous properties'''
    app_name = "Binilla"  # the name of the app(used in window title)
    version = '0.1'
    untitled_num = 0  # when creating a new, untitled tag, this is its name

    '''
    TODO:
        Finish incomplete methods(marked by #### INCOMPLETE ####)
    '''
    
    def __init__(self, **options):
        #### INCOMPLETE ####
        self.curr_dir = options.pop('curr_dir', self.curr_dir)
        self.app_name = options.pop('app_name', self.app_name)
        self.version = str(options.pop('version', self.version))

        tk.Tk.__init__(self, **options)
        self.tag_handler = Handler(debug=3)
        self.tag_windows = []
        
        self.title('%s v%s' % (self.app_name, self.version))
        self.geometry("640x480+0+0")
        self.minsize(width=200, height=50)
        self.protocol("WM_DELETE_WINDOW", self.exit)

        ######################################################################
        ######################################################################
        # MAKE METHODS FOR CREATING/DESTROYING MENUS SO THEY CAN BE CUSTOMIZED
        # This includes creating a system to manage the menus and keep track
        # of which ones exist, their order on the menu bar, their names, etc.
        # Once that is done, replace the below code with code that uses them.
        ######################################################################
        ######################################################################

        #create the main menu and add its commands
        self.main_menu    = tk.Menu(self)
        self.file_menu    = tk.Menu(self.main_menu, tearoff=0)
        self.options_menu = tk.Menu(self.main_menu, tearoff=0)
        self.debug_menu   = tk.Menu(self.main_menu, tearoff=0)
        self.windows_menu = tk.Menu(self.main_menu, tearoff=0)

        self.config(menu=self.main_menu)

        #add cascades and commands to the main_menu
        self.main_menu.add_cascade(label="File",    menu=self.file_menu)
        self.main_menu.add_cascade(label="Options", menu=self.options_menu)
        self.main_menu.add_cascade(label="Debug",   menu=self.debug_menu)
        self.main_menu.add_cascade(label="Windows", menu=self.windows_menu)
        self.main_menu.add_command(label="Help")
        self.main_menu.add_command(label="About")

        #add the commands to the file_menu
        fm_ac = self.file_menu.add_command
        fm_ac(label="New",        command=self.new_tag)
        fm_ac(label="Load",       command=self.load_tags)
        fm_ac(label="Load as...", command=self.load_tag_as)
        fm_ac(label="Save",       command=self.save_tag)
        fm_ac(label="Save as...", command=self.save_tag_as)
        fm_ac(label="Save all",   command=self.save_all)
        self.file_menu.add_separator()
        fm_ac(label="Exit",       command=self.exit)
        
        #add the commands to the options_menu
        self.options_menu.add_command(
            label="Set definitions folder", command=self.select_defs)
        self.options_menu.add_separator()
        self.options_menu.add_command(
            label="Show defs", command=self.show_defs)
        
        self.debug_menu.add_command(label="Print tag", command=self.print_tag)

        #add the commands to the windows_menu
        self.windows_menu.add_command(
            label="Minimize all", command=self.minimize_all)
        self.windows_menu.add_command(
            label="Sort by path", command=lambda: self.sort_windows_by('path'))
        self.windows_menu.add_command(
            label="Sort by def id", command=lambda: self.sort_windows_by('id'))
        self.windows_menu.add_separator()


        #fonts
        self.fixed_font = tk.font.Font(root=self, family="Courier", size=8)

    def delete_tag(self, tag):
        #### INCOMPLETE ####
        #########################################################
        #########################################################
        # NEED A WAY TO DELETE A Tag FROM THE handler AND Binilla
        #########################################################
        #########################################################
        # This will also need to destroy the TagWindow displaying
        # the given tag if the TagWindow's tag attribute isnt None
        pass
        
    def exit(self):
        '''Exits the program.'''
        raise SystemExit()

    def get_tag(self, def_id, filepath):
        '''
        Returns the tag from the handler under the given def_id and filepath.
        '''
        #### INCOMPLETE ####
        pass

    def get_tag_window_by_tag(self, tag):
        #### INCOMPLETE ####

        ####################################################
        ####################################################
        # NEED A WAY TO GET A TagWindow INSTANCE GIVEN A Tag
        ####################################################
        ####################################################
        pass
            
    def load_tags(self, filepaths=None, def_id=None):
        '''Prompts the user for a tag(s) to load and loads it.'''
        if filepaths is None:
            filetypes = [('All', '*')]
            defs = self.tag_handler.defs
            for id in sorted(defs.keys()):
                filetypes.append((id, defs[id].ext))
            filepaths = askopenfilenames(initialdir=self.last_load_dir,
                                         filetypes=filetypes,
                                         title="Select the tag to load")
            if not filepaths:
                return

        if isinstance(filepaths, str):
            filepaths = (filepaths,)

        self.last_load_dir = dirname(filepaths[-1])

        for path in filepaths:
            #try to load the new tags
            try:
                new_tag = self.tag_handler.load_tag(path, def_id)
            except Exception:
                print("Could not load tag '%s'" % path)
                continue

            # if the path is blank(new tag), give it a unique name
            if not path:
                # remove the tag from the handlers tag collection
                tags_coll = self.tag_handler.tags[new_tag.def_id]
                tags_coll.pop(new_tag.filepath, None)

                ext = str(new_tag.ext)
                new_tag.filepath = ('untitled%s' + ext) % self.untitled_num
                # re-index the tag under its new filepath
                tags_coll[new_tag.filepath] = new_tag
                self.untitled_num += 1

            try:
                #build the window
                self.make_tag_window(new_tag)
            except Exception:
                raise IOError("Could not display tag '%s'." % path)
            
    def load_tag_as(self):
        '''Prompts the user for a tag to load and loads it.'''
        if self.def_selector_window:
            return
        
        filetypes = [('All', '*')]
        defs = self.tag_handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))
        fp = askopenfilename(initialdir=self.last_load_dir,
                             filetypes=filetypes,
                             title="Select the tag to load")
        if fp != "":
            self.last_load_dir = dirname(fp)
            dsw = DefSelectorWindow(
                self, title="Select a definition to use", action=lambda def_id:
                self.load_tags(filepaths=fp, def_id=def_id))
            self.def_selector_window = dsw

    def make_tag_window(self, tag, focus=True):
        '''
        Creates a TagWindow instance for the supplied tag and
        sets the current focus to the new TagWindow.
        '''
        new_window = self.default_tag_window_class(self, tag, app_root=self)
        self.tag_windows.append(new_window)
        self.update_windows_menu()
        if focus:
            # set the focus to the new tag
            self.select_tag_window(tag)

    def minimize_all(self):
        '''Minimizes all open TagWindows.'''
        #### INCOMPLETE ####
        pass

    def new_tag(self):
        if self.def_selector_window:
            return
        
        dsw = DefSelectorWindow(
            self, title="Select a definition to use", action=lambda def_id:
            self.load_tags(filepaths='', def_id=def_id))
        self.def_selector_window = dsw
    
    def print_tag(self):
        '''Prints the currently selected tag to the console.'''
        try:
            self.tag_handler.tags[self.selected_def_id]\
                  [self.selected_tag_path].pprint(printout=True,
                                                  show=const.MOST_SHOW)
        except Exception:
            print(format_exc())
        
    def save_tag(self, tag=None):
        if tag is None:
            try:
                tag = self.tag_handler.tags[self.selected_def_id]\
                      [self.selected_tag_path]
            except Exception:
                return

        if hasattr(tag, "serialize"):
            #if the tag has been freshly made it wont have a valid filepath
            if not(hasattr(tag, "filepath") and tag.filepath):
                self.save_tag_as(tag)
                return
            
            try:
                tag.serialize(temp=False, backup=True)
            except Exception:
                raise IOError("Could not save tag.")

    def save_tag_as(self, tag=None):
        if tag is None:
            try:
                tag = self.tag_handler.tags[self.selected_def_id]\
                      [self.selected_tag_path]
            except Exception:
                return

        if hasattr(tag, "serialize"):
            ext = tag.ext
            orig_filepath = tag.filepath
            filepath = asksaveasfilename(
                initialdir=dirname(orig_filepath), defaultextension=ext,
                title="Save tag as...", filetypes=[
                    (ext[1:], "*" + ext), ('All', '*')] )
            if filepath != "":
                try:
                    tags_coll = self.tag_handler.tags[tag.def_id]
                    assert filepath not in tags_coll,\
                           "A tag with that name is already open."
                    # and re-index the tag under its new filepath
                    tags_coll[filepath] = tag
                    tag.serialize(filepath=filepath, temp=False, backup=False)
                    tag.filepath = filepath
                except Exception:
                    raise IOError("Could not save tag.")

                try:
                    # remove the tag from the handlers tag collection
                    tags_coll.pop(filepath, None)
                    self.get_tag_window_by_tag(tag).update_title()
                except Exception:
                    # this isnt really a big deal
                    pass
                    #print(format_exc())

    def save_all(self):
        '''
        Saves all currently loaded tags to their files.
        '''
        tags = self.tag_handler.tags
        for def_id in tags:
            tag_coll = tags[def_id]
            for tag_path in tag_coll:
                try:
                    self.save_tag(tag_coll[tag_path])
                except Exception:
                    print(format_exc())
                    print("Exception occurred while trying to save '%s'" %
                          tag_path)

    def select_tag_window(self, tag):
        #### INCOMPLETE ####
        self.selected_def_id = tag.def_id
        self.selected_tag_path = tag.filepath

    def select_defs(self):
        '''Prompts the user to specify where to load the tag defs from.
        Reloads the tag definitions from the folder specified.'''
        #### INCOMPLETE ####
        defs_root  = askdirectory(initialdir=self.last_defs_dir,
                                  title="Select the tag definitions folder")
        if defs_root != "":
            try:
                defs_root = defs_root.replace('\\', const.PATHDIV)\
                            .replace('/', const.PATHDIV)
                defs_path = defs_root.split(self.curr_dir+const.PATHDIV)[-1]
                defs_path = defs_path.replace(const.PATHDIV, '.')
                self.tag_handler.reload_defs(defs_path=defs_path)
                #self.last_imp_dir  = import_rootpath
                self.last_defs_dir = defs_root
            except Exception:
                raise IOError("Could not load tag definitions.")
        
    def show_defs(self):
        if self.def_selector_window:
            return
        
        self.def_selector_window = DefSelectorWindow(self, action=lambda x: x)

    def sort_windows_by(self, method):
        '''Sorts the order of self.tag_windows by the given criteria.'''

        sort_map = {}  # stores the tag windows by the criteria
        new_order = []  # newly sorted tag_windows list

        windows = self.tag_windows
        if method.lower() == 'path':
            for w in windows:
                sort_map[str(w.tag.filepath) + str(w.tag.def_id)] = w
        elif method.lower() == 'id':
            for w in windows:
                sort_map[str(w.tag.def_id) + str(w.tag.filepath)] = w
        else:
            return

        # There should be no TagWindows displaying tags that have the
        # same def_id and filepath. Make sure to check anyway though.
        assert len(windows) == len(sort_map)

        for key in sorted(sort_map.keys()):
            new_order.append(sort_map[key])

        self.tag_windows = new_order
        self.update_windows_menu()

    def update_windows_menu(self):
        '''Updates the windows_menu to reflect changes to self.tag_windows.'''
        pass
        #### INCOMPLETE ####

        #self.windows_menu.add_command(label='', command=lambda :None)
        #self.windows_menu.entryconfig(x, label='')


class DefSelectorWindow(tk.Toplevel):

    def __init__(self, master, action, *args, **kwargs):
        try:
            title = master.tag_handler.defs_filepath
        except AttributeError:
            title = "Tag definitions"

        title = kwargs.pop('title', title)
            
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        
        self.title(title)
        
        self.action = action
        self.def_id = None
        self.sorted_def_ids = []
        self.geometry("250x150+"+self.winfo_geometry().split('+', 1)[-1])
        self.minsize(width=250, height=200)
        self.protocol("WM_DELETE_WINDOW", self.destruct)

        self.list_canvas = tk.Canvas(self, highlightthickness=0)
        self.button_canvas = tk.Canvas(self, height=50, highlightthickness=0)
        
        #create and set the y scrollbar for the canvas root
        self.def_listbox = tk.Listbox(
            self.list_canvas, selectmode=SINGLE, highlightthickness=0,
            font=master.fixed_font)
        self.ok_btn = tk.Button(self.button_canvas, text='OK', width=16,
                                command=self.complete_action)
        self.cancel_btn = tk.Button(self.button_canvas, text='Cancel',
                                    width=16, command=self.destruct)
        self.hsb = tk.Scrollbar(self.button_canvas, orient='horizontal')
        self.vsb = tk.Scrollbar(self.list_canvas,   orient='vertical')
        
        self.def_listbox.config(xscrollcommand=self.hsb.set,
                                yscrollcommand=self.vsb.set)
        
        self.hsb.config(command=self.def_listbox.xview)
        self.vsb.config(command=self.def_listbox.yview)
        
        self.list_canvas.pack(side=TOP,   fill='both', expand=True)
        self.button_canvas.pack(side=TOP, fill='x')
        
        self.vsb.pack(side=RIGHT, fill='y')
        self.def_listbox.pack(side=TOP, fill='both', expand=True)
        
        self.hsb.pack(side=TOP, fill='x')
        self.ok_btn.pack(side=LEFT,      padx=9)
        self.cancel_btn.pack(side=RIGHT, padx=9)
        
        self.def_listbox.bind('<<ListboxSelect>>', self.set_selected_def )
        
        self.transient(self.master)
        self.grab_set()

        self.cancel_btn.focus_set()
        self.populate_listbox()


    def destruct(self):
        try:
            self.master.def_selector_window = None
        except AttributeError:
            pass
        self.destroy()

    def complete_action(self):
        if self.def_id is not None:
            self.action(self.def_id)
        self.destruct()

    def populate_listbox(self):
        defs_root = self.master.tag_handler.defs_path
        defs = self.master.tag_handler.defs
        
        def_ids_by_path = {}
        id_pad = ext_pad = 0

        #loop over all the defs and find the max amount of
        #padding needed between the ID and the Ext strings
        for def_id in defs:
            d = defs[def_id]
            
            if len(def_id) > id_pad:
                id_pad = len(def_id)
        sorted_ids = self.sorted_def_ids = tuple(sorted(defs.keys()))

        #loop over all the definitions
        for def_id in sorted_ids:
            d = defs[def_id]
            
            self.def_listbox.insert(END, 'ID=%s  %sExt=%s'%
                                    (def_id, ' '*(id_pad-len(def_id)), d.ext ))

    def set_selected_def(self, event=None):
        index = self.def_listbox.curselection()
        
        if len(index) == 1:
            self.def_id = self.sorted_def_ids[int(index[0])]
