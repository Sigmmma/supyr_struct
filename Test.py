'''
A module to test the supyr_struct library and definitions.
When called by itself it will run a pre-configured test.
The test parameters can be modified by providing keyword
arguments when creating a class instance.

'Tag_Tag_Class' is intended to be an easy way to test
Definitions, Constructors, Tag_Objs, Tag_Blocks,
Tag_Types, Readers, Writers, Encoders, and Decoders
by providing your own Constructor to the class upon
creating an instance.
'''

from traceback import format_exc
from time import time
from copy import copy

'''the default parameters are at the
top of the module for easy access'''
Print_Test = True
Save_Test = False
Allow_Corrupt = False
Temp = True
Backup = True
Valid_Tag_IDs = None
Debug = 10

Def_Print_Opts = {'Indent':4, 'Precision':3,
                  'Printout':True, 'Print_Raw':False,
                  'Show':set(('Type', 'Offset', 'Value', 'Size', 'Name',
                              'Unique', 'Elements', 'Flags','Ram_Size',
                              'Children', 'Tag_Path', 'Bin_Size', 'Index'))}

try:
            
    from supyr_struct import Library
    
    class Tag_Test_Library(Library.Library):
        '''
        A simple module test which can be programmed by providing
        keyword arguments when creating a class instance.

        This 'Tag_Tag_Class' is intended to be an easy way to test
        Definitions, Constructors, Tag_Objs, Tag_Blocks, Tag_Types,
        Readers, Writers, Encoders, and Decoders by providing your
        own Constructor to the class upon creating an instance.
        
        Refer to this classes __init__.__doc__ for descriptions of
        the properties in this class that aren't described below.
        
        Refer to supyr_struct.Library.Library.__init__.__doc__
        for the rest of the properties and methods of this class.

        Object Properties:
            dict:
                Print_Options
            bool:
                Save_Test
                Print_Test
                
        Object Methods:
            Load_Tags_and_Run()
            Run_Test(Prompt[bool] = True)
        '''

        #initialize the class
        def __init__(self, **kwargs):
            '''
            Refer to supyr_struct.Library.Library.__init__.__doc__
            for the rest of the keyword arguments of this function.

            Keyword arguments:
            
            #bool
            Save_Test ------- Whether or not to call self.Write_Tags() to save
                              all tags after they are loaded.
                              Default is False
            Print_Test ------ Whether or not to loop over all tags after they
                              are loaded and print each one.
                              Default is True

            #dict
            Print_Options --- A dict containing keywords that determine how
                              to print the tags if 'Print_Test' is True.
                #bool
                Printout -------- If True, prints the tags line by line rather
                                  than the whole tag at once. This is done so
                                  that even if certain sections of the tag
                                  fail to properly print, most of it will.
                                  Default is True
                                  
                Print_Raw ------- If True, prints 'Raw' Tag_Types. Raw data is
                                  unencoded and would take up unnecessarily
                                  large amounts of screen space is shown.
                                  Default is False

                #int
                Indent ---------- The number of spaces indent each level of
                                  hierarchy when printing nested structures.
                                  Default is 4 spaces.
                Precision ------- The number of trailing zeros to print floats
                                  to by using str.format(). Default is 3.
                                  If set to None, no formatting will be done.

                #set
                Show ------------ A set of keywords that determine what is
                                  shown when a tag is printed. A keyword being
                                  present in the set means it is printed.
                    Keywords:
                    
                    Tag_Path ---- Prints the Tag.Tag_Path
                    Bin_Size ---- Prints the tag size if it were written
                    Ram_Size ---- Prints the amount of ram the tag takes up.
                                  Two lines will be printed, one which shows
                                  the size of just the Tag_Data, and another
                                  which shows the size of the Tag_Data and
                                  the Tag_Obj that contains it.
                    
                    Name -------- Prints the name of the attribute
                    Type -------- Prints the name of the Tag_Type
                    Value ------- Prints the data itself
                    Offset ------ Prints the offset(if it applies)
                    Size -------- Prints the datas size
                    Unique ------ Prints if the descriptor is unique
                    Children ---- Prints all of the children in a tag
                    Elements ---- Prints the enumerator meaning of the value
                    Flags ------- Prints the flags, their masks, and names


                    If Bin_Size and Ram_Size are both true, an extra two lines
                    will be printed which compare the Bin_Size to the Ram_Size
                    The printout will look like this:
                    "In-Memory Tag Object" tag is X.XXX times as large.
                    "In-Memory Tag Data" tag is X.XXX times as large.

                    Where X.XXX is a float whose precision is determined by
                    the Print_Option 'Precision'.
            '''
            if not hasattr(self, "Print_Options"):
                self.Print_Options = kwargs.get("Print_Options", Def_Print_Opts)
            self.Save_Test  = bool(kwargs.get("Save_Test", Save_Test))
            self.Print_Test = bool(kwargs.get("Print_Test", Print_Test))
            
            super().__init__(**kwargs)


        def Load_Tags_and_Run(self):
            '''
            Indexes all valid tags in self.Tags_Dir,
            loads them, writes them back to their files,
            and prints the contents of all loaded tags.

            If self.Save_Test is False, the tag writing test will be skipped
            If self.Print_Test is False, the tag printing test will be skipped
            
            If self.Print_Options["Printout"] exists and is True, each Tag
            will be printed using Tag.Print(). This mode is slower than simply
            print(Tag), but has the advantage of not causing an exception that
            will prevent the entire tag from being shown. This usually occurs if
            a character in the stringified Tag maps to an undefined character.
            This mode prints the tag almost line by line and any exceptions
            that occur are noted in the printed tag.
            '''

            #clear all the tags and make sure there are dicts for each Cls_ID
            self.Reset_Tags()

            #index the tags and make sure the number found isnt 0
            if self.Index_Tags():

                #load all the indexed tags
                self.Load_Tags()

                #if saving, write all the tags back to their files
                if self.Save_Test:
                    self.Write_Tags()

                #loop through all the tags in the collection and print them
                if self.Print_Test:
                    
                    for Tag_Type in sorted(self.Tags):
                        for Tag_Path in sorted(self.Tags[Tag_Type]):
                            
                            Tag = self.Tags[Tag_Type][Tag_Path]

                            if self.Print_Options.get('Printout'):
                                Tag.Print(**self.Print_Options)
                            else:
                                try:
                                    print(Tag)
                                except:
                                    print(format_exc() + "\n" +
                                          "The above exception occurred "+
                                          "while trying to print the tag:"+
                                          "\n    " + str(Tag_Path) + '\n')
            else:
                print("The tags directory is either empty, doesnt " +
                      "exist, or cannot be accessed.\nDirectory " +
                      "names are case sensitive.")
                

    
        def Run_Test(self, Prompt=True):
            '''
            A timer function that records how long the test took to run.
            Returns the time the test took to run as a float.

            Optional arguments:
                Prompt(bool)
            
            If 'Prompt' is True, displays console prompts letting the user
            begin the test when ready, tells the user the Tags_Dir path,
            displays the completion time, and waits for input before quitting.
            '''
            
            if Prompt:
                print("Press Enter to begin loading tags from:"+
                      "\n    " + self.Tags_Dir)
                input()
                
            Start = time()
            self.Load_Tags_and_Run()

            End = time()
            if Prompt:
                print('-'*80 + '\nCompletion time: '+ str(End-Start) + '\n' +
                      '-'*80 + '\nPress enter to exit.')
                input()
                
            return End-Start
      

    #if this file is being called as the main then run the test
    if __name__ == '__main__':
        Test = Tag_Test_Library(Print_Test=Print_Test, Save_Test=Save_Test,
                               Write_as_Temp=Temp, Backup_Old_Tags=Backup,
                               Debug=Debug, Valid_Tag_IDs=Valid_Tag_IDs,
                               Allow_Corrupt=Allow_Corrupt)
        Test.Run_Test()
except Exception:
    print(format_exc())
    input()
