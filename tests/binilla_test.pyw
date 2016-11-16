import os
from traceback import format_exc

try:
    from supyr_struct.apps.binilla.app_window import Binilla

    if __name__ == "__main__":
        supyrdir = ''.join(__file__.replace('/', '\\').split(
            '\\supyr_struct\\tests\\')[0]+'\\supyr_struct\\')
        main_window = Binilla(curr_dir=supyrdir)
        main_window.mainloop()

except Exception:
    print(format_exc())
    input()
