import sqlite3
import re
import codecs
import hashlib

stdout = codecs.open('/dev/stdout', 'w', 'utf-8')

class ShavianReplacer:
    def __init__(self):
        self.db = sqlite3.connect('shavian-set.sqlite')
        self.c = self.db.cursor()
        self.previous_pos = u'n'

    def __del__(self):
        self.c.close()

    def fetch_word (self, word):
        self.c.execute('select shaw, pos, dab from words where latn=?', (word.lower(), ))
        shaw = self.c.fetchall()
        if not shaw:
            self.previous_pos = u'n'
            return unicode(word)
        elif len(shaw)>1:
            for pron in shaw:
                if self.previous_pos in pron[2]:
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

sr = ShavianReplacer()

result = re.sub('\\b([A-Za-z]|[A-Za-z][A-Za-z'']*[A-Za-z])\\b',
                sr,
                file('demo-input.txt').read())

stdout.write(result)
stdout.close()

