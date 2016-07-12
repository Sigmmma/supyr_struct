'''
This module provides a base Tag class for a OLECF file.
'''
from supyr_struct.tag import *

class OlecfTag(Tag):
    '''
    '''
    def __init__(self, **kwargs):
        '''Initializes an Olecf Tag'''

        # These next lists are used for quickly jumping around
        # the DIFAT, FAT, miniFAT, and directory sectors without
        # having to follow chains in the FAT or DIFAT.

        # A list of the DIFAT sector numbers IN ORDER for quick reference.
        # If none exist, this list will be empty.
        # This excludes the array of 109 DIFAT entries in the header.
        self.difat_sectors = []

        # A list of the FAT sector numbers IN ORDER for quick reference.
        self.fat_sectors = []

        # A list of the miniFAT sector numbers IN ORDER for quick reference.
        self.minifat_sectors = []

        # A list of the directory sector numbers IN ORDER for quick reference.
        self.dir_sectors = []

        Tag.__init__(self, **kwargs)
