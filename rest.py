from PIL import Image
from PIL.ExifTags import TAGS

from glob import glob
import os.path as op
import os
from rdflib import Graph, Namespace, RDF
import subprocess

SRCDIR = "/mnt/btrfs/restore/tmp"
TGTDIR = "/mnt/btrfs/restore/tgt"

NCO = Namespace('http://tracker.api.gnome.org/ontology/v3/nco#')
NFO = Namespace('http://tracker.api.gnome.org/ontology/v3/nfo#')
NIE = Namespace('http://tracker.api.gnome.org/ontology/v3/nie#')


def getfiles(ext, debug=False):
    PAT = op.join(SRCDIR, '.*', ext)
    print("Processing pattern:", PAT)
    files = glob(PAT, recursive=True)
    if debug:
        print(files[:10])
    return files


TRACKER = "/usr/lib/tracker3/extract"


def tracker(pathname):
    answer = subprocess.run([TRACKER, pathname], stdout=subprocess.PIPE)
    if answer.returncode == 0:
        g = newtrackergraph(answer.stdout)
        return g
    else:
        return None


def newtrackergraph(openfile):
    g = Graph()
    g.parse(openfile)
    # print(len(g))
    # print(g.serialize(format="n3"))
    return g


QUERY_DOC = """
prefix nco: <http://tracker.api.gnome.org/ontology/v3/nco#>
prefix nfo: <http://tracker.api.gnome.org/ontology/v3/nfo#>
prefix nie: <http://tracker.api.gnome.org/ontology/v3/nie#>

SELECT ?user ?created ?text ?title
WHERE {

?file a nfo:PaginatedTextDocument .
?file nco:creator ?creator .
?creator a nco:Contact .
?creator nco:fullname ?user .
?file nie:contentCreated ?created .
?file nie:plainTextContent ?text .

OPTIONAL { ?file nie:title ?title. }
}
"""


def proc_doc():
    # for file in getfiles('f15213088.doc'):
    for file in getfiles('*.doc*'):
        g = tracker(file)

        def _rep():
            print("INFO: Cannot analyze '{}'".format(file))

        if g is None:
            _rep()
        for row in g.query(QUERY_DOC):
            user, created, text, title = [str(_) for _ in row]
            text = text.replace('\r', '\n')
            created = created.replace(':', "-")
            path, name = op.split(file)
            _, ext = op.splitext(name)
            if title:
                name = title[:100]
                newname = "{}-{}-{}".format(user, name, created) + ext
            else:
                newname = "{}-{}-{}".format(user, created, name)
            movefile(file, newname, debug=False)
            break
        else:
            _rep()



def movefile(oldname, newname, targetdir=TGTDIR, debug=False):
    crs = [ord(c) for c in newname if ord(c) > 0]
    newname = ''.join([chr(c) for c in crs])
    newname = newname.replace(' ', '_')
    newfile = op.join(targetdir, newname)
    try:
        if not debug:
            os.rename(oldname, newfile)
        print("INFO: Renamed {}->{}".format(oldname, newfile))
    except ValueError:
        print("ERROR: Cannot rename '{}' to '{}' ".format(oldname, newname))


def proc_jpg():
    for file in getfiles('*.jpg'):
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
                make, model, date = [
                    '' if c is None else c for c in [make, model, date]
                ]
                date = date.replace(" ", "-").replace(":", "-")
                newname = "{}-{}-{}-{}".format(make, model, date, name)
                movefile(file, newname)

if __name__ == "__main__":
    # proc_jpg()
    proc_doc()
