import gc
import os

from copy import deepcopy
from time import time, sleep
from os.path import dirname
from tkinter import *

from supyr_struct.handler import Handler
from supyr_struct.defs.constants import pathdiv

from .widgets import *


class TagEditorWindow(Tk):

    loaded_tag = None
    curr_dir   = os.path.abspath(os.curdir)
    
    def __init__(self, **options):
        self.curr_dir = options.get('curr_dir', self.curr_dir)
        options['curr_dir'] = None; del options['curr_dir']
        
        Tk.__init__(self, **options )
        self.tag_handler = Handler()
        
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
        self.file_menu.add_command(label="Unload",     command=self.unload_tag)
        self.file_menu.add_command(label="Save",       command=self.save_tag)
        self.file_menu.add_command(label="Save as...", command=self.save_tag_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit",       command=self.quit)
        
        #add the commands to the options_menu
        self.options_menu.add_command(label="Set definitions folder",
                                      command=self.select_defs)
        
        self.debug_menu.add_command(label="Print tag", command=self.print_tag)
        self.debug_menu.add_command(label="Print defs",command=self.print_defs)

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


    def init_widgets(self):
        '''Builds the widgets for displaying and editing the tag'''
        try:
            if not hasattr(self.loaded_tag, 'tagdata'):
                raise AttributeError()
        except AttributeError:
            #The tag is either not loaded or has
            #been deleted. nothing to do, so return
            return
            
    def load_tag(self):
        '''Prompts the user for a tag to load and loads it.'''
        filepath = askopenfilename(initialdir=self.curr_dir,
                                   title="Select the tag to load")
        if filepath != "":
            #try to load the new tag
            try:
                tag = self.tag_handler.build_tag(filepath=filepath)
                
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

    def new_tag(self):
        pass
        
    def print_defs(self):
        '''Prints a list of the currently loaded definitions to the console'''
        try:
            defs_root = self.tag_handler.defs_path
            defs = self.tag_handler.defs
            pad = ' '*4
            
            print('root:'+defs_root)

            id_pad = ext_pad = 0
            for def_id in defs:
                if len(def_id) > id_pad:
                    id_pad = len(def_id)
                if len(defs[def_id].ext) > ext_pad:
                    ext_pad = len(defs[def_id].ext)

            #loop over all the definitions
            for def_id in defs:
                this_def = defs[def_id]
                print( '%sid:%s  %sext:%s  %spath:%s'%
                      (pad, def_id, ' '*(id_pad-len(def_id)),
                       this_def.ext, ' '*(ext_pad-len(this_def.ext)),
                       type(this_def).__module__.split(defs_root+'.')[-1]))
        except:
            pass
        print()
    
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
        if hasattr(self.loaded_tag, "write"):
            try:
                self.loaded_tag.write(temp=False, backup=True)
            except Exception:
                raise IOError("Could not save tag.")

    def save_tag_as(self):
        '''Prompts the user for where to save the currently
        loaded tag to, writes it to the new location, and
        sets the tagpath attribute to the new location.'''
        tag = self.loaded_tag
        if hasattr(tag, "write"):
            ext = tag.ext
            orig_filepath = tag.tagpath
            filepath = asksaveasfilename(initialdir=dirname(orig_filepath),
                                         defaultextension=ext,
                                         title="Save tag as...",
                                         filetypes=[(ext[1:], "*"+ext),
                                                    ('All','*')] )
            if filepath != "":
                try:
                    tag.write(filepath=filepath, temp=False, backup=False)
                    tag.tagpath = filepath
                except Exception:
                    raise IOError("Could not save tag.")
    
    def select_defs(self):
        '''Prompts the user to specify where to load the tag defs from.
        Reloads the tag definitions from the folder specified.'''
        folderpath = askdirectory(initialdir=self.curr_dir,
                                  title="Select the tag definitions folder")
        if folderpath != "":
            try:
                folderpath = folderpath.replace('\\', pathdiv)\
                             .replace('/', pathdiv)
                defs_path = folderpath.split(self.curr_dir+pathdiv)\
                            [-1].replace(pathdiv, '.')
                self.tag_handler.reload_defs(defs_path=defs_path)

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
