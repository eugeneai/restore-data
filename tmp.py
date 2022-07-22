from requests import get
from libextract.api import extract

r = get('http://en.wikipedia.org/wiki/Information_extraction')
textnodes = list(extract(r.content))
print(textnodes[0].text_content())
