'''
Need to document this thing
'''
import os
import gc
import tkinter as tk
import tkinter.filedialog

from traceback import format_exc

from supyr_struct.defs.filesystem.olecf import olecf_def
from supyr_struct.defs.filesystem.objs.olecf import OlecfTag

test_path = (__file__.split('\\olecf_extractor.py')[0] +
    '\\test_tags\\documents\\test.doc')
curr_dir = os.path.abspath(os.curdir)

RESERVED_WINDOWS_FILENAME_MAP = {}
INVALID_PATH_CHARS = set([str(i.to_bytes(1, 'little'), 'ascii')
                          for i in range(32)])
for name in ('CON', 'PRN', 'AUX', 'NUL'):
    RESERVED_WINDOWS_FILENAME_MAP[name] = '_' + name
for i in range(1, 9):
    RESERVED_WINDOWS_FILENAME_MAP['COM%s' % i] = '_COM%s' % i
    RESERVED_WINDOWS_FILENAME_MAP['LPT%s' % i] = '_LPT%s' % i
INVALID_PATH_CHARS.update(('<', '>', ':', '"', '/', '\\', '|', '?', '*'))


class OlecfExtractor(tk.Tk):
    filepath = None
    loaded_tag = None
    listbox_entries = None

    initial_dir = curr_dir

    # each index in the listbox_map maps linearly to the entries in
    # the listbox and each stores the SID of the dir_entry it points to
    listbox_map = ()

    tag_def_cls = olecf_def
    tag_cls = OlecfTag

    def __init__(self, **kwargs):
        filepath = kwargs.pop('filepath', '')

        tk.Tk.__init__(self, **kwargs)

        self.title("OLECF File Extractor v1.0")
        self.geometry("368x243+0+0")
        self.resizable(0, 0)

        self.filepath = tk.StringVar(self, filepath)
        self.listbox_entries = {}
        self.listbox_map = []
        self.populating_listbox = False
        self.loaded_tag = None

        # add the filepath box
        self.filepath_entry = tk.Entry(self, textvariable=self.filepath)
        self.filepath_entry.insert(tk.INSERT, self.filepath.get())
        self.filepath_entry.config(width=59, state=tk.DISABLED)

        # add the buttons
        self.btn_load = tk.Button(
            self, text="Select file", width=15, command=self.browse)
        self.btn_extract = tk.Button(
            self, text="Extract selected", width=15,
            command=lambda: self.extract(extract_selected=True))
        self.btn_extract_all = tk.Button(
            self, text="Extract all", width=15, command=self.extract_all)

        # add the listbox
        self.listbox_canvas = tk.Canvas(self, highlightthickness=0)
        self.file_listbox = tk.Listbox(
            self.listbox_canvas, width=61, height=13,
            selectmode=tk.EXTENDED, highlightthickness=0)

        # place the buttons and filepath field
        self.filepath_entry.place(x=5, y=5, anchor=tk.NW)
        self.btn_load.place(x=15, y=30, anchor=tk.NW)
        self.btn_extract.place(x=150, y=30, anchor=tk.NW)
        self.btn_extract_all.place(x=250, y=30, anchor=tk.NW)

        # pack the listbox and scrollbars
        self.listbox_canvas.place(x=0, y=60)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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
        loaded_tag = self.loaded_tag
        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return

        # faster local reference and shortens line lengths
        get_stream = loaded_tag.get_stream_by_index
        dirname = os.path.dirname
        exists = os.path.exists
        makedirs = os.makedirs

        # get the filepath of the tag without the extension
        tag_path = os.path.splitext(loaded_tag.filepath)[0]
        output_path_template = tag_path + '\\%s.stream'

        # make sure an output folder exists
        makedirs(tag_path + '\\', exist_ok=True)

        if extract_selected:
            file_indices = [self.listbox_map[i] for i in
                            self.file_listbox.curselection()]

        print('extracting %s files' % len(file_indices))

        # loop over every directory entry
        for i in file_indices:
            try:
                dir_entry = loaded_tag.get_dir_entry_by_index(i)
                if dir_entry.storage_type.enum_name == 'unallocated':
                    continue

                print('    %s' % dir_entry.name)

                # get the filename
                name = self.sanitize_filename(dir_entry.name)

                # make the output path for the thumbnail
                output_path = output_path_template % name
                output_folder = dirname(output_path)

                # make sure an output folder exists
                if not exists(output_folder):
                    makedirs(output_folder, exist_ok=True)

                # open the output file
                with open(output_path_template % name, 'w+b') as f:
                    # Get a stream buffer to read the data
                    # from and write it to the output file
                    f.write(get_stream(i).read())
            except Exception:
                print('        FAILED TO EXTRACT FILE STREAM AT INDEX %s' % i)
                print(format_exc())
                continue

        print('\n%s\n%s\n%s' % ('-'*79, 'Finished extracting', '-'*79))

    def extract_all(self):
        loaded_tag = self.loaded_tag
        if not isinstance(loaded_tag, self.tag_cls):
            print('Loaded tag is not an instance of %s' % self.tag_cls)
            return
        self.extract(range(len(loaded_tag.dir_names)))

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
        if filepath is None:
            filepath = self.filepath.get()
        if filepath:
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
        # make sure to rename reserved windows filenames to a valid one
        if name in RESERVED_WINDOWS_FILENAME_MAP:
            return RESERVED_WINDOWS_FILENAME_MAP[name]
        final_name = ''
        for c in name:
            if c not in INVALID_PATH_CHARS:
                final_name += c
        if final_name == '':
            return 'BAD %s CHAR FILENAME' % len(name)
        return final_name

try:
    if __name__ == '__main__':
        extractor = OlecfExtractor(filepath=test_path)
        extractor.mainloop()
except:
    print(format_exc())
    input()
