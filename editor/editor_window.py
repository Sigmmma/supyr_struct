import gc
import os

from copy import deepcopy
from time import time, sleep
from os.path import dirname
from tkinter import *
from tkinter import font

from supyr_struct.handler import Handler
from supyr_struct.defs.constants import pathdiv

from .widgets import *

class TagEditorWindow(Tk):

    loaded_tag = None
    def_selector_window = None
    
    curr_dir = os.path.abspath(os.curdir)

    last_load_dir = curr_dir
    last_imp_dir  = curr_dir
    last_defs_dir = curr_dir
    
    def __init__(self, **options):
        self.curr_dir = options.get('curr_dir', self.curr_dir)
        options['curr_dir'] = None; del options['curr_dir']
        
        Tk.__init__(self, **options )
        self.tag_handler = Handler(debug=3)
        
        self.title("Tag Editor v0.1")
        self.geometry("250x400+0+0")
        self.minsize(width=200, height=50)

        #create the main menu and add its commands
        self.main_menu = Menu(self)
        self.config(menu=self.main_menu)
        
        self.file_menu    = Menu(self.main_menu, tearoff=0)
        self.options_menu = Menu(self.main_menu, tearoff=0)
        self.debug_menu   = Menu(self.main_menu, tearoff=0)

        #add cascades and commands to the main_menu
        self.main_menu.add_cascade(label="File",    menu=self.file_menu)
        self.main_menu.add_cascade(label="Options", menu=self.options_menu)
        self.main_menu.add_cascade(label="Debug",   menu=self.debug_menu)
        self.main_menu.add_command(label="Help")
        self.main_menu.add_command(label="About")

        #add the commands to the file_menu
        self.file_menu.add_command(label="New",        command=self.new_tag)
        self.file_menu.add_command(label="Load",       command=self.load_tag)
        self.file_menu.add_command(label="Load as...", command=self.load_tag_as)
        self.file_menu.add_command(label="Save",       command=self.save_tag)
        self.file_menu.add_command(label="Save as...", command=self.save_tag_as)
        self.file_menu.add_command(label="Unload",     command=self.unload_tag)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit",       command=self.quit)
        
        #add the commands to the options_menu
        self.options_menu.add_command(label="Set definitions folder",
                                      command=self.select_defs)
        self.options_menu.add_separator()
        self.options_menu.add_command(label="Show defs", command=self.show_defs)
        
        self.debug_menu.add_command(label="Print tag", command=self.print_tag)

        #create the root_canvas and the root_frame within the canvas
        self.root_canvas = root = Canvas(self)
        self.root_frame  = BlockFrame(self, app_root=self)

        #create and set the x and y scrollbars for the canvas root
        root.hsb = Scrollbar(self, orient='horizontal', command=root.xview)
        root.vsb = Scrollbar(self, orient='vertical',   command=root.yview)
        root.config(xscrollcommand=root.hsb.set, yscrollcommand=root.vsb.set)
        
        root.hsb.pack(side=BOTTOM, fill='x')
        root.vsb.pack(side=RIGHT,  fill='y')
        root.pack(side='left', fill='both', expand=True)

        root.create_window((0,0), window=self.root_frame, anchor="nw")

        #fonts
        self.fixed_font = font.Font(root=self, family="Courier", size=8)


    def init_widgets(self):
        '''Builds the widgets for displaying and editing the tag'''
        try:
            if not hasattr(self.loaded_tag, 'tagdata'):
                raise AttributeError()
        except AttributeError:
            #The tag is either not loaded or has
            #been deleted. nothing to do, so return
            return
            
    def load_tag(self, filepath=None, def_id=None):
        '''Prompts the user for a tag to load and loads it.'''
        if filepath is None:
            filetypes = [('All','*')]
            defs = self.tag_handler.defs
            for id in sorted(defs.keys()):
                filetypes.append((id, defs[id].ext))
            filepath = askopenfilename(initialdir=self.last_load_dir,
                                       filetypes=filetypes,
                                       title="Select the tag to load")
            if filepath == "":
                return
            
        #try to load the new tag
        try:
            tag = self.tag_handler.build_tag(def_id=def_id, filepath=filepath)
            self.last_load_dir = dirname(filepath)
            
            #unload the currently loaded tag and reset the widgets
            self.unload_tag()
        except Exception:
            raise IOError("Could not load tag.")
        
        self.loaded_tag = tag
        
        try:
            #rebuild the window
            self.init_widgets()
        except Exception:
            raise IOError("Could not display loaded tag.")

            
    def load_tag_as(self):
        '''Prompts the user for a tag to load and loads it.'''
        if self.def_selector_window:
            return
        
        filetypes = [('All','*')]
        defs = self.tag_handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))
        fp = askopenfilename(initialdir=self.last_load_dir,
                             filetypes=filetypes,
                             title="Select the tag to load")
        if fp != "":
            self.last_load_dir = dirname(fp)
            dsw = DefSelectorWindow(self, title="Select a definition to use",
                                    action=lambda def_id:
                                    self.load_tag(filepath=fp, def_id=def_id))
            self.def_selector_window = dsw

    def new_tag(self):
        if self.def_selector_window:
            return
        
        dsw = DefSelectorWindow(self, title="Select a definition to use",
                                action=lambda def_id:
                                self.load_tag(filepath='', def_id=def_id))
        self.def_selector_window = dsw
        
    def show_defs(self):
        if self.def_selector_window:
            return
        
        self.def_selector_window = DefSelectorWindow(self, action=lambda x: x)
    
    def print_tag(self):
        '''Prints the currently loaded tag to the console.'''
        try:
            self.loaded_tag.pprint(printout=True)
        except:
            pass
        
    def quit(self):
        '''Exits the program.'''
        raise SystemExit()
        
    def save_tag(self):
        '''Saves the currently loaded tag.'''
        tag = self.loaded_tag
        if hasattr(tag, "write"):

            #if the tag has been freshly made it wont have a valid filepath
            if not(hasattr(tag, "filepath") and tag.filepath):
                self.save_tag_as()
                return
            
            try:
                tag.write(temp=False, backup=True)
            except Exception:
                raise IOError("Could not save tag.")

    def save_tag_as(self):
        '''Prompts the user for where to save the currently
        loaded tag to, writes it to the new location, and
        sets the filepath attribute to the new location.'''
        tag = self.loaded_tag
        if hasattr(tag, "write"):
            ext = tag.ext
            orig_filepath = tag.filepath
            filepath = asksaveasfilename(initialdir=dirname(orig_filepath),
                                         defaultextension=ext,
                                         title="Save tag as...",
                                         filetypes=[(ext[1:], "*"+ext),
                                                    ('All','*')] )
            if filepath != "":
                try:
                    tag.write(filepath=filepath, temp=False, backup=False)
                    tag.filepath = filepath
                except Exception:
                    raise IOError("Could not save tag.")
    
    def select_defs(self):
        '''Prompts the user to specify where to load the tag defs from.
        Reloads the tag definitions from the folder specified.'''
        #import_rootpath = askopenfilename(initialdir=self.last_imp_dir,
        #                                  title="Select the import root")
        #if import_rootpath == "":
        #    return
        
        defs_root  = askdirectory(initialdir=self.last_defs_dir,
                                  title="Select the tag definitions folder")
        if defs_root != "":
            try:
                defs_root = defs_root.replace('\\', pathdiv)\
                            .replace('/', pathdiv)
                defs_path = defs_root.split(self.curr_dir+pathdiv)[-1]
                defs_path = defs_path.replace(pathdiv, '.')
                self.tag_handler.reload_defs(defs_path=defs_path)
                #self.last_imp_dir  = import_rootpath
                self.last_defs_dir = defs_root

                #because we've changed the set of tag
                #definitions, we need to unload the tag
                self.unload_tag()
            except Exception:
                raise IOError("Could not load tag definitions.")
            
    def unload_tag(self):
        '''Deletes the currently loaded tag, runs
        garbage collection, and resets the widgets.'''
        try:
            del self.loaded_tag
        except Exception:
            pass
        self.loaded_tag = None
        gc.collect()
        self.init_widgets()


class DefSelectorWindow(Toplevel):

    def __init__(self, master, action, *args, **kwargs):
        try:
            title = master.tag_handler.defs_filepath
        except AttributeError:
            title = "Tag definitions"
        
        if 'title' in kwargs:
            title = kwargs.pop('title')
            
        Toplevel.__init__(self, master, *args, **kwargs)
        
        self.title(title)
        
        self.action = action
        self.def_id = None
        self.sorted_def_ids = []
        self.geometry("250x150+"+self.winfo_geometry().split('+', 1)[-1])
        self.minsize(width=250, height=200)
        self.protocol("WM_DELETE_WINDOW", self.destruct)

        self.list_canvas = Canvas(self)
        self.button_canvas = Canvas(self, height=50)
        
        #create and set the y scrollbar for the canvas root
        self.def_listbox = Listbox(self.list_canvas, selectmode=SINGLE,
                                   highlightthickness=0, font=master.fixed_font)
        self.ok_btn = Button(self.button_canvas, text='OK', width=16,
                             command=self.complete_action)
        self.cancel_btn = Button(self.button_canvas, text='Cancel', width=16,
                                 command=self.destruct)
        self.hsb = Scrollbar(self.button_canvas, orient='horizontal')
        self.vsb = Scrollbar(self.list_canvas,   orient='vertical')
        
        self.def_listbox.config(xscrollcommand=self.hsb.set,
                                yscrollcommand=self.vsb.set)
        
        self.hsb.config(command=self.def_listbox.xview)
        self.vsb.config(command=self.def_listbox.yview)
        
        self.list_canvas.pack(side=TOP,   fill='both', expand=True)
        self.button_canvas.pack(side=TOP, fill='x')
        
        self.vsb.pack(side=RIGHT, fill='y')
        self.def_listbox.pack(side=TOP, fill='both', expand=True)
        
        self.hsb.pack(side=TOP,   fill='x')
        self.ok_btn.pack(side=LEFT,      padx=9)
        self.cancel_btn.pack(side=RIGHT, padx=9)
        
        self.def_listbox.bind('<<ListboxSelect>>', self.set_selected_def )
        
        self.def_listbox.focus_set()
        self.transient(self.master)
        self.grab_set()

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
                                    (def_id, ' '*(id_pad-len(def_id)), d.ext ) )

        '''Old code that doesnt work since definition source paths default
         to supyr_struct.tag_def with the new method of writing them'''
        #map the def_ids by import path
        #for def_id in defs:
        #    d = defs[def_id]
        #    
        #    if len(def_id) > id_pad:
        #        id_pad = len(def_id)
        #    if len(d.ext) > ext_pad:
        #        ext_pad = len(d.ext)
        #        
        #    full_path = type(d).__module__
        #    def_ids_by_path[full_path.split(defs_root+'.')[-1]] = def_id

        #sorted_ids = sorted(def_ids_by_path.keys())
        #del self.sorted_def_ids[:]
        
        #for def_id in sorted_ids:
        #    self.sorted_def_ids.append(def_ids_by_path[def_id])

        #loop over all the definitions
        #for def_path in sorted_ids:
        #    def_id = def_ids_by_path[def_path]
        #    d = defs[def_id]
        #    self.def_listbox.insert(END, 'ID:%s  %sExt:%s  %sPath:%s'%
        #    self.def_listbox.insert(END, 'ID:%s  %sExt:%s  %sPath:%s'%
        #                            (def_id, ' '*(id_pad-len(def_id)),
        #                             d.ext, ' '*(ext_pad-len(d.ext)),
        #                             def_path))
        

    def set_selected_def(self, event=None):
        index = self.def_listbox.curselection()
        
        if len(index) == 1:
            self.def_id = self.sorted_def_ids[int(index[0])]
