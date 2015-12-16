import sys
import os

from importlib import import_module
from mmap import mmap
from os.path import splitext, split
from traceback import format_exc
from types import ModuleType

from supyr_struct.Defs import Tag_Def
from supyr_struct.Defs.Tag_Obj import Tag_Obj
from supyr_struct.Defs.Constants import *


class Constructor():
    '''docstring'''
    Default_Defs_Path = "supyr_struct\\Defs\\"
    Default_Tag_Obj   = Tag_Obj

    def __init__(self, Handler=None, **kwargs):
        '''docstring'''
        #this is the filepath to the tag currently being constructed
        self.Current_Tag = ''
        self.Allow_Corrupt = False
        self.Debug = 0
        
        self.Handler = Handler
        self.Defs_Path = ''

        self._Sanitizer = Tag_Def.Tag_Def()

        self.ID_Ext_Mapping = {}
        self.Definitions = {}
        
        self.Allow_Corrupt = kwargs.get("Allow_Corrupt",self.Allow_Corrupt)
        self.Debug = kwargs.get("Debug",self.Debug)
    
        self.Reload(**kwargs)


    def Reload(self, **kwargs):
        """ this function is used to dynamically load and index
        all tag definitions for all valid tags. This allows
        functionality to be extended simply by creating a new
        definition and dropping it into the Defs folder."""

        Module_IDs = []
        
        self.Definitions.clear()
        
        if not self.Defs_Path:
            self.Defs_Path = self.Default_Defs_Path


        Valid_Tag_IDs = kwargs.get("Valid_Tag_IDs")
        if not hasattr(Valid_Tag_IDs, '__iter__'):
            Valid_Tag_IDs = None

        #get the path to the tag definitions folder
        self.Defs_Path = kwargs.get("Defs_Path", self.Defs_Path)
        #convert this path into an import path
        self.Defs_Import_Path = self.Defs_Path.replace('\\', '.')
        #cut off the trailing '.' if it exists
        if self.Defs_Import_Path[-1] == '.':
            self.Defs_Import_Path = self.Defs_Import_Path[:-1]

        #import the root definitions module to get its absolute path
        Defs_Root_Module = import_module(self.Defs_Import_Path)
        
        '''try to get the absolute folder path of the Defs module'''
        try:
            #Try to get the filepath of the module 
            Defs_Root = split(Defs_Root_Module.__file__)[0]
        except Exception:
            #If the module doesnt have an __init__.py in the folder then an
            #exception will occur trying to get '__file__' in the above code.
            #This method must be used instead(which I think looks kinda hacky)
            Defs_Root = tuple(Defs_Root_Module.__path__)[0]

        '''Log the location of every python file in the defs root'''
        #search for possibly valid definitions in the defs folder
        for root, directories, files in os.walk(Defs_Root):
            for module_path in files:
                base, ext = splitext(module_path)
                
                Folder = root.split(Defs_Root)[-1]
                
                #make sure the file name ends with .py and isn't already loaded
                if ext.lower() == ".py" and not(base in Module_IDs):
                    Module_IDs.append((Folder + '.' + base).replace('\\', '.'))

        #load the defs that were found 
        for Module_ID in Module_IDs:
            Def_Module = None
            
            #try to import the Definition module
            try:
                Def_Module = import_module(self.Defs_Import_Path + Module_ID)
            except Exception:
                if self.Debug >= 1:
                    print(format_exc() + "\nThe above exception occurred " +
                          "while trying to import a tag definition.")
                    continue

            #make sure this is a valid tag module by making a few checks
            if hasattr(Def_Module, 'Construct'):
                '''finally, try to add the definition
                and its constructor to the lists'''
                try:
                    Def = Def_Module.Construct()
                    
                    try:
                        '''if a def doesnt have a usable Cls_ID then skip it'''
                        Cls_ID = Def.Cls_ID
                        if not bool(Cls_ID):
                            continue

                        '''if it does though, add it to the definitions'''
                        if Valid_Tag_IDs is None or Cls_ID in Valid_Tag_IDs:
                            self.Add_Def(Def)
                    except Exception:
                        if self.Debug >= 3:
                            print(format_exc())
                            
                except Exception:
                    if self.Debug >= 2:
                        print(format_exc() + "\nThe above exception occurred "+
                              "while trying to load a tag definition.")


    def Construct_Tag(self, **kwargs):
        '''builds and returns a tag object'''        
        Cls_ID = kwargs.get("Cls_ID", None)
        Filepath = kwargs.get("Filepath", '')
        Raw_Data = kwargs.get("Raw_Data", None)
        Allow_Corrupt = kwargs.get("Allow_Corrupt", self.Allow_Corrupt)
        kwargs["Test"] = kwargs.get("Test", False)

        #set the current tag path so outside processes
        #have some info on what is being constructed
        self.Current_Tag = Filepath

        if not Cls_ID:
            Cls_ID = self.Get_Cls_ID(Filepath)
            if not Cls_ID:
                raise LookupError('Unable to determine Cls_ID for:' +
                                  '\n' + ' '*BPI + self.Current_Tag)

        Def = self.Get_Def(Cls_ID)
        
        #if it couldn't find a Tag_Def, Def is None
        if Def:
            New_Tag = Def.Tag_Obj(Tag_Path = Filepath, Definition = Def,
                                  Raw_Data = Raw_Data, Constructor = self,
                                  Allow_Corrupt=Allow_Corrupt,
                                  Handler = self.Handler)
            return New_Tag
        
        raise TypeError(("Unable to locate definition for " +
                        "tag type '%s' for file:\n%s'%s'") %
                        (Cls_ID, ' '*BPI, self.Current_Tag))
            

    def Construct_Block(self, **kwargs):
        '''builds a tag block'''
        Parent = None
        Desc = None
        
        Tag = kwargs.get("Tag", None)
        Offset = kwargs.get("Offset", 0)
        Root_Offset = kwargs.get("Root_Offset", 0)
        Attr_Index = kwargs.get("Attr_Index", 0)
        Raw_Data = kwargs.get("Raw_Data", None)
        
        Test = kwargs.get("Test", False)
        Filepath = kwargs.get("Filepath", False)
        Allow_Corrupt = kwargs.get("Allow_Corrupt", self.Allow_Corrupt)

        if isinstance(kwargs.get('Parent'), List_Block):
            Parent = kwargs["Parent"]

        try:
            #if a descriptor was provided, use it
            if kwargs.get("Descriptor"):
                #Descriptors provided may need to be sanitized
                if kwargs.get("Sanitize"):
                      Desc = self.Desc_Sanitize(kwargs["Descriptor"])
                else: Desc = kwargs["Descriptor"]
            else:
                #if not, try to get it from the parent
                Desc = Parent.Get_Desc(Attr_Index)
        except Exception: pass
                
        if Desc is None:
            raise TypeError("Unable to build Tag_Block without a descriptor.")

        try:
            if Parent is not None and Attr_Index is not None:
                '''The Parent and Attr_Index are valid, so
                we can just call the Reader for that block.'''
                Parent.Get_Desc(TYPE,Attr_Index).Reader(Parent, Raw_Data,
                                                        Attr_Index, Root_Offset,
                                                        Offset, Tag=Tag,
                                                        Test=Test)
                return Parent[Attr_Index]
            else:
                '''if the Parent or Attr_Index are None, then 
                this block is being built without a parent,
                meaning we need to figure out how to build it'''
                #See what type of Tag_Block we need to make
                try:
                    New_Attr_Type = Desc[TYPE].Py_Type
                except AttributeError:
                    raise AttributeError('Could not locate Field_Type in' +
                                         'descriptor to build Tag_Block from.')

                '''If the attribute has a child block, but the
                Tag_Block type that we will make it from doesnt
                support holding one, create a P_List_Block instead.'''
                if 'CHILD' in Desc and not hasattr(New_Attr_Type, 'CHILD'):
                      New_Attr_Type = P_List_Block

                New_Attr = New_Attr_Type(Desc, Raw_Data=Raw_Data,
                                         Filepath=Filepath, Test=Test,
                                         Offset=Offset, Root_Offset=Root_Offset,
                                         Allow_Corrupt=Allow_Corrupt)
                return New_Attr
        except Exception:
            raise Exception("Exception occurred while trying "+
                            " to construct Tag_Block.")


    def Add_Def(self, Def, Cls_ID=None, Ext=None, Endian=None, Obj=None):
        '''docstring'''
        if isinstance(Def, dict):
            if Cls_ID is None or Ext is None:
                raise TypeError("Could not add new Tag_Def to constructor. "+
                                "Neither 'Cls_ID' or 'Ext' can be None if "+
                                "'Def' is a dict based structure.")
                
            Def = Tag_Def.Tag_Def(Structure=Def, Ext=Ext, Cls_ID=Cls_ID)
        elif isinstance(Def, type):
            #the actual Tag_Def class was provided
            if issubclass(Def, Tag_Def.Tag_Def):
                Def = Def()
            else:
                raise TypeError("The provided 'Def' is a class, but not "+
                                "a subclass of 'Tag_Def.Tag_Def'.")
        elif isinstance(Def, ModuleType):
            #a whole module was provided
            if hasattr(Def, "Construct"):
                Def = Def.Construct()
            else:
                raise AttributeError("The provided module does not have "+
                                     "a 'Construct' method to get the "+
                                     "Tag_Def class from.")
        elif isinstance(Def, Tag_Def.Tag_Def):
            #a Tag_Def was provided. nothing to do
            pass
        else:
            #no idea what was provided, but we dont care. ERROR!
            raise TypeError("Incorrect type for the provided 'Def'.\n"+
                            "Expected %s, %s, or %s, but got %s" %
                            (type(Tag_Def.Tag_Def.Tag_Structure),
                             type, ModuleType, type(Def)) )

        if isinstance(Obj, Tag_Obj):
            Def.Tag_Obj = Obj
        #if no Tag_Obj is associated with this Tag_Def, use the default one
        if Def.Tag_Obj is None:
            Def.Tag_Obj = self.Default_Tag_Obj
            
        self.Definitions[Def.Cls_ID] = Def
        self.ID_Ext_Mapping[Def.Cls_ID] = Def.Ext

        return Def
    

    def Get_Def(self, Cls_ID):
        return self.Definitions.get(Cls_ID)


    def Get_Cls_ID(self, Filepath):
        '''docstring'''
        if '.' in Filepath and not Filepath.startswith('.'):
            ext = splitext(Filepath)[1].lower()
        else:
            ext = Filepath
            
        for Cls_ID in self.ID_Ext_Mapping:
            if self.ID_Ext_Mapping[Cls_ID].lower() == ext:
                return Cls_ID


    def Desc_Sanitize(self, Desc):
        '''This function will sanitize the provided
        dictionary so it can be used as a descriptor'''
        return self._Sanitizer.Sanitize(Desc)
