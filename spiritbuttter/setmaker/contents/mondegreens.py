import sqlite3
import sys

db = sqlite3.connect('shavian-set.sqlite')
c = db.cursor()

def find_prefixes(shaw, so_far):

    sys.stdout.write('.')
    sys.stdout.flush()

    d = db.cursor()
    d.execute('SELECT latn, SUBSTR(?,LENGTH(shaw)+1) FROM words WHERE shaw = SUBSTR(?,1,LENGTH(shaw))', (shaw, shaw))
    result = []
    for w in d.fetchall():
        word = w[0].lower()
        remaining = w[1]

        sf = '%s %s' % (so_far, word)
        if remaining=='':
            # got the whole thing
            print sf
            result.append([word])
        else:
            # there are still some sounds to match
            prefixes = find_prefixes(remaining, sf)
            r = []
            for w in prefixes:
                # prepend them all
                x = [word]
                x.extend(w)
                r.append(x)
            if r:
                result.extend(r)

    d.close()
    return result

keyword = 'RECOGNISE SPEECH'
shaw = u''

# This could be improved a lot by allowing voiced and unvoiced letters to match

for w in keyword.split(' '):
    c.execute('SELECT latn, shaw FROM words WHERE latn=?', (w,))
    shaw += c.fetchone()[1]
    print shaw

print 'The phrase %s sounds a bit like...' % (keyword),

find_prefixes(shaw, '')

c.close()
