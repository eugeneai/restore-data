from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS

from glob import glob
import os.path as op
import os
from rdflib import Graph, Namespace, RDF
import subprocess
import docx
import zipfile

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
?file nie:contentCreated ?created .
OPTIONAL { ?file nie:plainTextContent ?text . }
OPTIONAL {
?file nco:creator ?creator .
?creator a nco:Contact .
?creator nco:fullname ?user .
}
OPTIONAL { ?file nie:title ?title. }
}
"""


def proc_docx():
    for file in getfiles('*.docx'):

        def _err():
            print("ERROR: Cannot process '{}'".format(file))

        try:
            doc = docx.Document(file)
        except ValueError:
            _err()
            continue

        props = doc.core_properties

        path, name = op.split(file)
        base, ext = op.splitext(name)

        user = props.author
        created = props.created
        name = props.title[:100] if props.title else base

        newname = "{}-{}-{}".format(user, name, created) + ext
        movefile(file, newname, debug=False)


def proc_tr(ext, debug=False):
    # for file in getfiles('f15213088.doc'):
    for file in getfiles(ext):
        g = tracker(file)

        def _rep():
            print("INFO: Cannot analyze '{}'".format(file))

        if g is None:
            _rep()

        for row in g.query(QUERY_DOC):
            user, created, text, title = row

            path, name = op.split(file)
            base, ext = op.splitext(name)

            text = text[:100] if text else text
            filetitle = (title or text or base) + ext
            user, created, text, title = [str(_) for _ in row]
            text = text.replace('\r', '\n')
            # print(("'{}' " * 4).format(user, created, text, title))
            created = created.replace(':', "-")

            user = user or "NONE"

            newname = "{}-{}-{}".format(user, created, filetitle)

            movefile(file, newname, debug=debug)
            break
        else:
            _rep()


def movefile(oldname, newname, targetdir=TGTDIR, debug=False):
    crs = [ord(c) for c in newname if ord(c) > 0]
    newname = ''.join([chr(c) for c in crs])

    def cl(s):
        if s in ' ()[]/\\\n\r\t':
            return '_'
        else:
            return s

    sl = [cl(c) for c in newname]
    newname = ''.join(sl)

    newfile = op.join(targetdir, newname)
    try:
        if not debug:
            os.rename(oldname, newfile)
        print("INFO: Renamed {}->{}".format(oldname, newfile))
    except ValueError:
        print("ERROR: Cannot rename '{}' to '{}' ".format(oldname, newname))

def proc_zip():
    for file in getfiles("*.zip"):
        obj = zipfile.ZipFile(file, 'r')
        try:
            t = obj.testzip()
        except RuntimeError:
            print("ERROR: Cannot test '{}".format(file))
            continue
        except OSError:
            print("ERROR: Cannot test, oserror '{}".format(file))
            continue
        if t is not None:
            print("ERROR: Corrupt at '{}':{}".format(t, file))
            continue
        print("Content of the ZIP file {}: ".format(file))

        content_list = obj.namelist()
        for fname in content_list:
            print(fname)
            break
        path, name = op.split(file)
        base, ext = op.splitext(name)
        newname = name + fname.replace('/', '-').replace('.', '-') + ext
        movefile(file, newname, debug=False)
        # content_list = obj.infolist()
        # for info in content_list:
        #     print(info)

def proc_img(ext):
    for file in getfiles(ext):
        try:
            image = Image.open(file)
        except UnidentifiedImageError:
            print("ERROR: image cannot be identified '{}'".format(file))
            continue

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
                movefile(file, newname, debug=True)


if __name__ == "__main__":
    # proc_img('*.jpg')
    # proc_docx()
    # proc_tr('*.doc')
    # proc_tr('*.xls*')
    # proc_img('*.tif*')
    # proc_tr('*.pdf')
    # proc_tr('*.docx', debug=True)
    proc_zip()


# TODO: zip, 7z, rar
