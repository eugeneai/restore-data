
from PIL import Image
from PIL.ExifTags import TAGS

from glob import glob
import os.path as op
import os

files = glob('/mnt/data/storage/rest/jpg/f*.jpg')

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
        make = exif.get(0x010f,'NONE')
        date = exif.get(0x0132,None)
        # if date is not None:
        if True:
            if date is None:
                date = ""
            date = date.replace(" ","-").replace(":","-")
            newname = "{}-{}-{}".format(make,date,name)
            crs = [ord(c) for c in newname if ord(c)>0]
            newname = ''.join([chr(c) for c in crs])
            newfile = op.join(path,newname)
            try:
                os.rename(file, newfile)
            except ValueError:
                try:
                    newname = "GOOD-{}-{}".format(make,name)
                    newfile = op.join(path,newname)
                    os.rename(file, newfile)
                except ValueError:
                    print("CANNOT RENAME:",newfile)
                    print(chr)
            print(newfile)


        # for tag_id in exif:
        #     tag = TAGS.get(tag_id, tag_id)
        #     data = exif.get(tag_id)
        #     print(f"{tag:25}: {data}")
