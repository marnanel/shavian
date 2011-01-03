import sqlite3
import re
import hashlib

# The traditional ASCII mapping.
# We are using this to represent Shavian text in the XML
# so that it can be edited with any editor.
mapdown = 'ptkfTsScjNbdgvHzZJwhlmieAaoUQyrnIEFuOMqYRPXxDCWVG'

def unascii(mapped):
    "Convert ASCII-mapped text to real Unicode Shavian."
    result = ''
    for letter in mapped:
        if letter=='G':
            # naming dot
            result += unichr(0xB7)
        elif letter not in mapdown:
            result += letter
        else:
            result += unichr(66640+mapdown.index(letter))
    return result

class ShavianReplacer:
    def __init__(self):
        self.db = sqlite3.connect('/service/website/shavian.org.uk/htdocs/set/shavian-set.sqlite')
        self.c = self.db.cursor()
        self.previous_pos = u'n'

    def __del__(self):
        self.c.close()

    def fetch_word (self, word):
        if word=='Sita':
            return unascii('GsItA') # temporary hack
        cap = word[0]>='A' and word[0]<='Z'
        self.c.execute('select shaw, pos, dab from words where latn=?', (word.lower(), ))
        shaw = self.c.fetchall()
        if not shaw:
            self.previous_pos = u'n'
            return unicode(word)
        elif len(shaw)>1:
            for pron in shaw:
                dabrule = pron[2]
                if (dabrule=='g' and cap) or (dabrule=='h' and not cap) or (self.previous_pos in dabrule):
                    self.previous_pos = pron[1]
                    return pron[0]
            # fallback
            self.previous_pos = shaw[0][1]
            return shaw[0][0]
        else:
            self.previous_pos = shaw[0][1]
            return shaw[0][0]

    def __call__(self, w):
        return self.fetch_word(w.group(1))

def shavianise(s):
    sr = ShavianReplacer()

    return re.sub('\\b([A-Za-z]|[A-Za-z][A-Za-z'']*[A-Za-z])\\b',
                  sr,
                  s)



