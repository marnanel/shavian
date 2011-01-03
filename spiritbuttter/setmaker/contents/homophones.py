import sqlite3

db = sqlite3.connect('shavian-set.sqlite')
c = db.cursor()

# make this not crawl
c.execute('CREATE INDEX IF NOT EXISTS shawidx ON words(shaw)')

c.execute('SELECT latn, shaw FROM words WHERE shaw IN (SELECT shaw FROM words GROUP BY shaw HAVING COUNT(latn)>1) ORDER BY shaw')
last = ''
for words in c.fetchall():
    if words[1]!=last:
        last = words[1]
        print
    print words[0].lower(),

c.close()
