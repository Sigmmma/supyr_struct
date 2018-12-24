import traceback

from os.path import join, dirname, normpath
from supyr_struct.defs.bitmaps import bmp, dds, tga, gif, wmf
from supyr_struct.defs.crypto import keyblob
from supyr_struct.defs.documents import doc
from supyr_struct.defs.filesystem import thumbs

folder = normpath(join(dirname(__file__), "test_tags"))
images_folder = join(folder, "images")
keyblobs_folder = join(folder, "keyblobs")

def test(tags):
    for bmp_name in ("test16color", "test24_dibv2", "test24_dibv3",
                     "test32_dibv4", "test32_dibv5", "test32_unknown_dib",
                     "test256color", "testmono_os2"):
        tags.append(bmp.bmp_def.build(
            filepath=join(images_folder, bmp_name + ".bmp")))

    for tga_name in ("test16", "test24", "test32",
                     "test24_rle", "test24_rle_origin_ll"):
        tags.append(tga.tga_def.build(
            filepath=join(images_folder, tga_name + ".tga")))
        
    tags.append(dds.dds_def.build(filepath=join(images_folder, "testcube.dds")))
    tags.append(gif.gif_def.build(filepath=join(images_folder, "test.gif")))
    tags.append(wmf.wmf_def.build(filepath=join(images_folder, "test24.wmf")))
    tags.append(thumbs.thumbs_def.build(
        filepath=join(images_folder, "test_thumbs.db")))

    tags.append(doc.doc_def.build(
        filepath=join(folder, "documents", "test.doc")))

    for tga_name in ("aeskey", "rsaprikey", "rsapubkey"):
        tags.append(keyblob.keyblob_def.build(
            filepath=join(keyblobs_folder, tga_name + ".bin")))

if __name__ == "__main__":
    try:
        tags = []
        try:
            test(tags)
        except Exception:
            print(traceback.format_exc())

        for tag in tags:
            print(tag)
    except Exception:
        print(traceback.format_exc())

    input("Finished")
