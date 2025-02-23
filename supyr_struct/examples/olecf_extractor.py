'''
Need to document this thing
'''
import os
import gc
import tkinter as tk
import tkinter.filedialog

from pathlib import Path
from traceback import format_exc

from supyr_struct.defs.filesystem.olecf import olecf_def
from supyr_struct.defs.filesystem.objs.olecf import OlecfTag


TAGS_DIR = Path(__file__).parent.joinpath('test_tags')

INVALID_PATH_CHARS = set(
    "".join(str(i.to_bytes(1, 'little'), 'latin-1')
            for i in (*range(32), *range(128, 256))) + '<>:"|?*'
    )
RESERVED_WINDOWS_FILENAME_MAP = {
    **{name: '_%s' % name for name in ('COM', 'PRN', 'AUX', 'NUL')},
    **{'COM%s' % i: '_COM%s' %i for i in range(10)},
    **{'LPT%s' % i: '_LPT%s' %i for i in range(10)},
    }


class OlecfExtractor(tk.Tk):
    filepath = None
    loaded_tag = None
    listbox_entries = None

    initial_dir = TAGS_DIR

    # each index in the listbox_map maps linearly to the entries in
    # the listbox and each stores the SID of the dir_entry it points to
    listbox_map = ()

    tag_def_cls = olecf_def
    tag_cls = OlecfTag

    def __init__(self, **kwargs):
        filepath = kwargs.pop('filepath', '')

        tk.Tk.__init__(self, **kwargs)

        self.title("OLECF File Extractor v1.1")
        self.geometry("368x243+0+0")
        self.resizable(1, 1)

        self.filepath = tk.StringVar(self, filepath)
        self.listbox_entries = {}
        self.listbox_map = []
        self.populating_listbox = False
        self.loaded_tag = None

        # add the filepath box
        self.filepath_entry = tk.Entry(self, textvariable=self.filepath)
        self.filepath_entry.insert(tk.INSERT, self.filepath.get())
        self.filepath_entry.config(width=59, state=tk.DISABLED)

        # add the buttons and listbox
        self.btn_load = tk.Button(
            self, text="Select file", width=15, command=self.browse)
        self.btn_extract = tk.Button(
            self, text="Extract selected", width=15,
            command=lambda: self.extract(extract_selected=True))
        self.btn_extract_all = tk.Button(
            self, text="Extract all", width=15, command=self.extract_all)
        self.file_listbox = tk.Listbox(self, selectmode=tk.EXTENDED)

        self.columnconfigure(3, weight = 1)
        self.rowconfigure(2, weight = 1)

        # place the buttons and filepath field
        self.filepath_entry.grid(row=0, column=0, columnspan=3, sticky="EW")
        self.btn_load.grid(row=1, column=0)
        self.btn_extract.grid(row=1, column=1)
        self.btn_extract_all.grid(row=1, column=2)

        self.file_listbox.grid(row=2, column=0, columnspan=4, sticky="NSEW")

        if filepath:
            self.load_tag(filepath)

    def browse(self):
        filepath = tkinter.filedialog.askopenfilename(
            filetypes=[(self.tag_def_cls.def_id, self.tag_def_cls.ext),
                       ('All', '*')],
            initialdir=self.initial_dir, title='Select a file to load')
        filepath = filepath.replace('/', '\\')

        if filepath:
            self.initial_dir = os.path.dirname(filepath)
            self.load_tag(filepath)

    def extract(self, file_indices=(), extract_selected=False):
        '''
        Extracts the specified files from the given loaded_tag to a folder
        with the same name as the OLECF file in the same parent folder.
        '''
        if not isinstance(self.loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return

        # get the filepath of the tag without the extension
        tag_path = Path(self.loaded_tag.filepath).with_suffix("")

        if extract_selected:
            file_indices = [self.listbox_map[i] for i in
                            self.file_listbox.curselection()]
        else:
            file_indices = self.listbox_entries

        print('extracting %s thumbnails' % len(file_indices))

        # loop over every entry in the catalog, get the raw
        # thumbnail stream data, and write it to a file
        for i in file_indices:
            try:
                name = Path(self.sanitize_filename(self.listbox_entries[i]))
                print('    %s' % name)

                data = self.get_item_data(i)

                # make sure an output folder exists
                tag_path.mkdir(parents=True, exist_ok=True)

                with tag_path.joinpath(name).open('w+b') as f:
                    f.write(data)

            except Exception:
                print('FAILED TO EXTRACT FILE STREAM AT INDEX %s' % i)
                print(format_exc())
                continue

        print('\n%s\n%s\n%s' % ('-'*79, 'Finished extracting', '-'*79))

    def extract_all(self):
        loaded_tag = self.loaded_tag
        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return
        self.extract(range(len(loaded_tag.dir_names)))

    def get_item_data(self, index):
        return self.loaded_tag.get_stream_by_index(index).read()

    def get_listbox_entries(self):
        loaded_tag = self.loaded_tag
        if not loaded_tag:
            return {}, ()

        listbox_entries = {}
        listbox_map = []

        # loop over every directory entry
        for i in range(len(loaded_tag.dir_names)):
            dir_entry = loaded_tag.get_dir_entry_by_index(i)
            if dir_entry.storage_type.enum_name == 'unallocated':
                continue
            listbox_entries[i] = dir_entry.name
            listbox_map.append(i)
        return listbox_entries, listbox_map

    def load_tag(self, filepath=None):
        filepath = filepath or self.filepath.get()
        if not filepath:
            return

        del self.loaded_tag
        self.loaded_tag = None
        gc.collect()

        try:
            self.loaded_tag = self.tag_def_cls.build(filepath=filepath)
            self.filepath.set(filepath)
        except Exception:
            self.filepath.set('')
        self.populate_listbox()

    def populate_listbox(self):
        if not self.populating_listbox:
            self.file_listbox.delete(0, tk.END)
            self.populating_listbox = True

            listbox_entries, listbox_map = self.get_listbox_entries()
            self.listbox_entries = listbox_entries
            self.listbox_map = listbox_map

            for i in listbox_map:
                self.file_listbox.insert(tk.END, listbox_entries[i])
            self.populating_listbox = False

    def sanitize_filename(self, name):
        if not name:
            return 'EMPTY FILENAME'

        # make sure to rename reserved windows filenames to a valid one
        if name in RESERVED_WINDOWS_FILENAME_MAP:
            return RESERVED_WINDOWS_FILENAME_MAP[name]
        
        return ''.join(
            "".join("%%%02x" % b for b in c.encode("utf8")).upper()
            if c in INVALID_PATH_CHARS else c
            for c in name
            )

try:
    if __name__ == '__main__':
        extractor = OlecfExtractor(
            filepath=TAGS_DIR.joinpath('documents/test.doc')
            )
        extractor.mainloop()
except Exception:
    print(format_exc())
    input()
