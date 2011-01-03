import sqlite3
import os
from xml.sax import ContentHandler, make_parser

sqlite_filename = 'shavian-set.sqlite'

if os.path.exists(sqlite_filename):
    os.unlink(sqlite_filename)

db = sqlite3.connect(sqlite_filename)
c = db.cursor()

print 'Creating database.'
c.execute('create table words (latn text, dab text, pos text, shaw text, source integer)')
print 'Creating index.'
c.execute('create unique index wordidx on words (latn, dab)')

#print 'You will see some warnings below.'
#print 'These are normal; they are caused by words which'
#print 'cannot be disambiguated.'
#print

print 'Populating database...'

class docHandler(ContentHandler):
    def startElement(self, name, attrs):
        if name!='w':
            return

        latn = attrs.get('l', '')
        dab = attrs.get('d', '')
        pos = attrs.get('p', 'n')
        shaw = attrs.get('s', '')
        source = attrs.get('f', '1')

        self.count += 1
        if self.count%10000==0:
            print 'Word %d is %s' % (self.count, latn)

        try:
            c.execute('insert into words values (?, ?, ?, ?, ?)',
                      (latn, dab, pos, shaw, source))
        except:
            pass
            #print 'Couldn\'t store '+latn+'_'+dab

dh = docHandler()
dh.count = 0

parser = make_parser()
parser.setContentHandler(dh)
parser.parse('shavian-set.xml')

print '%d words stored.  Writing changes.' % (dh.count)

db.commit()
c.close()

print 'Done.'

