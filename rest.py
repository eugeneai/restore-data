from PIL import Image
from PIL.ExifTags import TAGS

from glob import glob
import os.path as op
import os

SRCDIR = "/mnt/btrfs/restore/tmp"
TGTDIR = "/mnt/btrfs/restore/tgt"

PAT = op.join(SRCDIR, '.*', '*.jpg')

print(PAT)

files = glob(PAT, recursive=True)
print(files[:10])

# files = files[:1000]

for file in files:
    image = Image.open(file)
    exif = image.getexif()
    if not exif:
        print("NO EXIF DATA:", file)
        continue
    path, name = op.split(file)
    if name.startswith('f'):
        # print("EXIF:", name)
        make = exif.get(0x010f, None)
        model = exif.get(0x0110, None)
        date = exif.get(0x0132, None)
        if model is not None or make is not None:
        # if True:
            make,model,date = ['' if c is None else c
                               for c in [make,model,date]]
            date = date.replace(" ", "-").replace(":", "-")
            newname = "{}-{}-{}-{}".format(make, model, date, name)
            crs = [ord(c) for c in newname if ord(c) > 0]
            newname = ''.join([chr(c) for c in crs])
            newname = newname.replace(' ','_')
            newfile = op.join(TGTDIR, newname)
            try:
                print("RENAME: {}->{}".format(file, newfile))
                os.rename(file, newfile)
            except ValueError:
                try:
                    newname = "GOOD-{}-{}".format(make, name)
                    newfile = op.join(path, newname)
                    os.rename(file, newfile)
                except ValueError:
                    print("CANNOT RENAME:", newfile)
                    print(chr)
            print(newfile)


        # for tag_id in exif:
        #     tag = TAGS.get(tag_id, tag_id)
        #     data = exif.get(tag_id)
        #     print(f"{tag:25}: {data}")
