'''
A module to test the supyr_struct library and definitions.
When called by itself it will run a pre-configured test.
The test parameters can be modified by providing keyword
arguments when creating a class instance.

'Tag_Tag_Class' is intended to be an easy way to test
Definitions, Constructors, tags, blocks,
Tag_Types, Readers, Writers, Encoders, and Decoders
by providing your own Constructor to the class upon
creating an instance.
'''

from traceback import format_exc
from time import time
from copy import copy

'''the default parameters are at the
top of the module for easy access'''
print_test = True
save_test = False
int_test = True
allow_corrupt = True
temp = True
backup = True
valid_tag_ids = None
debug = 10

def_print_opts = {'indent':4, 'precision':3,
                  'printout':True,
                  'show':set(('field', 'value', 'size', 'name', 'offset',
                              'children', 'flags',# 'unique',
                              'filepath','ramsize', 'binsize', 'index'
                              ))}

try:
            
    from supyr_struct import library
    
    class TagTestLibrary(library.Library):
        '''
        A simple module test which can be programmed by providing
        keyword arguments when creating a class instance.

        This 'TagTestLibrary' is intended to be an easy way to test TagDefs,
        Tags, Blocks, Fields, readers, writers, encoders, and decoders.
        
        Refer to this classes __init__.__doc__ for descriptions of
        the properties in this class that aren't described below.
        
        Refer to supyr_struct.library.Library.__init__.__doc__
        for the rest of the properties and methods of this class.

        object properties:
            dict:
                print_options
            bool:
                save_test
                print_test
                
        object methods:
            load_tags_and_run()
            run_test(prompt[bool] = True)
        '''

        #initialize the class
        def __init__(self, **kwargs):
            '''
            Refer to supyr_struct.Library.Library.__init__.__doc__
            for the rest of the keyword arguments of this function.

            Keyword arguments:
            
            #bool
            save_test ------- Whether or not to call self.write_tags() to save
                              all tags after they are loaded.
                              Default is False
            print_test ------ Whether or not to loop over all tags after they
                              are loaded and print each one.
                              Default is True

            #dict
            print_options --- A dict containing keywords that determine how
                              to print the tags if 'print_test' is True.
                #bool
                printout -------- If True, prints the tags line by line rather
                                  than the whole tag at once. This is done so
                                  that even if certain sections of the tag
                                  fail to properly print, most of it will.
                                  Default is True

                #int
                indent ---------- The number of spaces indent each level of
                                  hierarchy when printing nested structures.
                                  Default is 4 spaces.
                orecision ------- The number of trailing zeros to print floats
                                  to by using str.format(). Default is 3.
                                  If set to None, no formatting will be done.

                #set
                show ------------ A set of keywords that determine what is
                                  shown when a tag is printed. A keyword being
                                  present in the set means it is printed.
                    Keywords:
                    
                    filepath ---- Prints the tag.filepath
                    binsize ---- Prints the tag size if it were written
                    ramsize ---- Prints the amount of ram the tag takes up.
                                  Two lines will be printed, one which shows
                                  the size of just the Tag_Data, and another
                                  which shows the size of the Tag_Data and
                                  the tag that contains it.
                    
                    name -------- Prints the name of the attribute
                    field ------- Prints the name of the tag_id
                    value ------- Prints the data itself
                    offset ------ Prints the offset(if it applies)
                    size -------- Prints the datas size
                    unique ------ Prints if the descriptor is unique
                    children ---- Prints all of the children in a tag
                    flags ------- Prints the flags, their masks, and names


                    If bin_size and Ram_Size are both true, an extra two lines
                    will be printed which compare the bin_size to the Ram_Size
                    The printout will look like this:
                    "In-memory tag object" tag is X.XXX times as large.
                    "In-memory tag data" tag is X.XXX times as large.

                    Where X.XXX is a float whose precision is determined by
                    the Print_Option 'Precision'.
            '''
            if not hasattr(self, "print_options"):
                self.print_options = kwargs.get("print_options", def_print_opts)
            self.save_test  = bool(kwargs.get("save_test", save_test))
            self.print_test = bool(kwargs.get("print_test", print_test))
            
            super().__init__(**kwargs)


        def load_tags_and_run(self):
            '''
            Indexes all valid tags in self.tagsdir,
            loads them, writes them back to their files,
            and prints the contents of all loaded tags.

            If self.save_test is False, the tag writing test will be skipped
            If self.print_test is False, the tag printing test will be skipped
            
            If self.print_options["printout"] exists and is True, each tag
            will be printed using tag.pprint(). This mode is slower than simply
            print(tag), but has the advantage of not causing an exception that
            will prevent the entire tag from being shown. This usually occurs if
            a character in the stringified tag maps to an undefined character.
            This mode prints the tag almost line by line and any exceptions
            that occur are noted in the printed tag.
            '''

            #clear all the tags and make sure there are dicts for each tag_id
            self.reset_tags()

            #index the tags and make sure the number found isnt 0
            if self.index_tags():

                #load all the indexed tags
                self.load_tags()

                #if saving, write all the tags back to their files
                if self.save_test:
                    self.write_tags(int_test = self.int_test)

                #loop through all the tags in the collection and print them
                if self.print_test:
                    
                    for tag_id in sorted(self.tags):
                        for filepath in sorted(self.tags[tag_id]):
                            
                            tag = self.tags[tag_id][filepath]

                            if self.print_options.get('printout'):
                                tag.pprint(**self.print_options)
                            else:
                                try:
                                    print(tag.__str__(**self.print_options))
                                except:
                                    print("\n\n" + format_exc() + "\n" +
                                          "The above exception occurred "+
                                          "while trying to print the tag:"+
                                          "\n    " + str(filepath) + '\n\n')
            else:
                print("The tags directory is either empty, doesnt " +
                      "exist, or cannot be accessed.\nDirectory " +
                      "names are case sensitive.")
                

    
        def run_test(self, prompt=True):
            '''
            A timer function that records how long the test took to run.
            Returns the time the test took to run as a float.

            Optional arguments:
                prompt(bool)
            
            If 'prompt' is True, displays console prompts letting the user
            begin the test when ready, tells the user the tagsdir path,
            displays the completion time, and waits for input before quitting.
            '''
            
            if prompt:
                print("Press Enter to begin loading tags from:"+
                      "\n    " + self.tagsdir)
                input()
                
            start = time()
            self.load_tags_and_run()

            end = time()
            if prompt:
                print('-'*80 + '\nCompletion time: '+ str(end-start) + '\n' +
                      '-'*80 + '\nPress enter to exit.')
                input()
                
            return end-start
      

    #if this file is being called as the main then run the test
    if __name__ == '__main__':
        test = TagTestLibrary(print_test=print_test, save_test=save_test,
                              write_as_temp=temp, backup=backup,
                              debug=debug, valid_tag_ids=valid_tag_ids,
                              allow_corrupt=allow_corrupt, int_test=int_test)
        test.run_test()
except Exception:
    print(format_exc())
    input()
