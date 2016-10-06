import os
from traceback import format_exc

from supyr_struct.editor.editor_window import TagEditorWindow

try:
    if __name__ == "__main__":
        supyrdir = ''.join(__file__.replace('/', '\\').split(
            '\\supyr_struct\\tests\\')[0]+'\\supyr_struct\\')
        main_window = TagEditorWindow(curr_dir=supyrdir)
        main_window.mainloop()

except Exception:
    print(format_exc())
    input()
