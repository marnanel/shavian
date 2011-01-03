import sqlite3
import codecs
import os
import sys
import gd
from pyPgSQL import PgSQL

targetdir = '/service/website/shavian.org.uk/htdocs/set/'

prepname = '/tmp/shavian-set-prep.sqlite'
if os.path.exists(prepname):
    os.unlink(prepname)
db = sqlite3.connect(prepname)

version = 'UNKNOWN'

def debug(str):
    if 1:
        print str

def create_db():
    debug('Creating database.')
    c = db.cursor()
    c.execute('create table words (latn text, dab text, pos text, shaw text, source integer)')
    c.execute('create index wordidx on words (latn)')
    c.close()

def populate_from_cmudict():
    debug('Populating from cmudict.')

    c = db.cursor()

    cmucodes = {}
    for line in file('external/cmudict.codes.txt').readlines():
        s = line[:-1].split(' ')
        cmucodes[s[0]] = s[1]

    # This could be improved slightly by checking that
    # we only put "ado" in unstressed syllables
    for line in file('external/cmudict.db.txt').readlines():
        s = line[:-1].split(' ')
        word = s[0]

        s = [x[0:2] for x in s[2:]]
        shavian = ''.join(cmucodes.get(x,'') for x in s)

        if '(' in word:
            continue

        try:
            c.execute('insert into words values (?, ?, ?, ?, ?)',
                      (word.lower(), '', '', shavian, 1))
        except:
            pass

    db.commit()
    c.close()

def finish():
    debug('Cleaning up.')
    os.unlink(prepname)
    os.system('rm -rf /tmp/shavian-set-%s/' % (version))

def populate_from_wiki():
    debug('Populating from wiki.')
    
    c = db.cursor()

    distribution = {}

    wikisettings = {}
    for setting in file('/service/website/shavian.org.uk/htdocs/w/LocalSettings.php','r').readlines():
        if not setting.startswith('$wgDB'):
            continue
        setting = setting[5:-3].split('=')
        wikisettings[setting[0].strip()] = setting[1].replace('"','').strip()

    def store(latn, wikitext):

        for letter in latn:
            if ord(letter)>127:
                return

        wikitext = wikitext.lower()
        if '{{abbreviation|shaw|' in wikitext:
            p = wikitext.index('{{abbreviation|shaw|')
            shaw = wikitext[p+20:]
            shaw = shaw[:shaw.index('}}')]
        else:
            if not '{{shaw|' in wikitext:
                return
            shawpos = wikitext.index('{{shaw|')
            shaw = wikitext[shawpos+7:]
            shaw = shaw[:shaw.index('}}')]

        dabrule = ''
        if '{{dabrule|' in wikitext:
            dabpos = wikitext.index('{{dabrule|')
            dabrule = wikitext[dabpos+10:]
            dabrule = dabrule[:dabrule.index('}}')]

        if dabrule=='x':
            return

        source = 0
        if '{{androcles}}' in wikitext:
            source = 2
            for letter in shaw:
                if ord(letter)>66639:
                    distribution[letter] = distribution.get(letter,0)+1
                    distribution['total'] = distribution.get('total',0)+1

        if '_' in latn:
            latn = latn[:latn.index('_')]

        c.execute('insert into words values (?, ?, ?, ?, ?)',
                  (latn.lower(), dabrule, '', shaw, source))

    cnx = PgSQL.connect('',
                        wikisettings['user'],
                        wikisettings['password'],
                        wikisettings['server'],
                        '',
                        wikisettings['port'],
                        client_encoding='utf-8',
                        unicode_results=True)

    d = cnx.cursor()

    d.execute("select max(rev_id) from page, revision where page_namespace=0 and page_latest=rev_id")
    version = '%08d' % (d.fetchone()[0])

    if os.path.exists('%sshavian-set-%s.tar.bz2' % (targetdir, version)):
        debug('It already exists; aborting.')
        finish()
        sys.exit(0)

    d.execute("select page_title, old_text from page, revision, pagecontent where page_namespace=0 and page_latest=rev_id and rev_text_id=old_id order by page_title")

    while 1:
        v = d.fetchone()
        if not v:
            break
        store(v[0], v[1])

    db.commit()
    c.close()

    ad = codecs.open('../androcles-distribution.txt', 'w', 'utf-8')
    for letter in distribution.keys():
        ad.write('%s %f\n' % (letter, (float(distribution[letter])/float(distribution['total']))))
    ad.close()

    return version

def include_pos():
    debug('Including part-of-speech data.')

    c = db.cursor()

    # everything defaults to noun
    c.execute('update words set pos=?', ('N',))

    for line in open('external/brown.db.txt','r').readlines():
        s = line.split()
        c.execute('update words set pos=? where latn=?',
                  (s[1][0].lower(), s[0].lower()))

    db.commit()
    c.close()

def remove_cmudict_dupes():
    debug('Removing CMUdict lexemes which are also in the wiki.')

    c = db.cursor()
    c.execute('delete from words where source=1 and latn in (select latn from words where source!=1)')

    db.commit()
    c.close()

def remove_non_y_dabs():
    debug('Removing homophones where another homophone is marked "y".')

    c = db.cursor()
    c.execute('delete from words where dab!="y" and latn in (select latn from words where dab="y")')
    c.execute('update words set dab="" where dab="y"')

    db.commit()
    c.close()

def check_for_bad_dupes():
    debug('Looking for irreconcilable duplicates.')
    c = db.cursor()
    c.execute('select count(*) as c, latn from words group by latn, dab having c>1')
    problems = c.fetchall()
    for problem in problems:
        print 'Disambiguation problem: http://shavian.org.uk/wiki/'+problem[1].title()

    if problems:
        print "Can't continue."
        finish()
        sys.exit(255)
    c.close()

def build_archive():
    debug('Building archive.')
    os.system('rm -rf /tmp/shavian-set-%s' % (version))
    os.system('cp -R contents /tmp/shavian-set-%s' % (version))

def output_xml():
    debug('Producing XML.')

    output = codecs.open('/tmp/shavian-set-%s/shavian-set.xml' % (version), 'w', 'utf-8')
    for skel in open('set-skeleton.xml', 'r').readlines():
        if skel.startswith('<!-- CONTENTS -->'):
            c = db.cursor()
            c.execute('select latn, shaw, pos, dab, source from words order by latn, dab')
            for l in c:
                line = '<w l="%s" s="%s" p="%s" d="%s" f="%d"/>\n' % (l)
                line = line.replace(' d=""','').replace(' f="1"','').replace(' p="N"','')
                output.write(line)
            c.close()
        else:
            output.write(skel.replace('$version', version))
    output.close()

def build_tarball():
    debug('Creating tarball.')
    os.chdir('/tmp')
    os.system('tar cjf shavian-set-%s.tar.bz2 shavian-set-%s' % (version, version))

def draw_graphs():
    debug('Drawing graphs.')
    c = db.cursor()

    c.execute('select source, count(*) from words group by source order by source')
    results = {}
    total = 0.0
    for r in c.fetchall():
        results[r[0]] = float(r[1])
        total += r[1]
    c.close()

    size = 300
    linespacing = 25
    fontname = targetdir+'../static/fonts/Constructium.ttf'
    g = gd.image((size, size))
    white = g.colorAllocate((255, 255, 255))
    black = g.colorAllocate((0, 0, 0))

    degrees = 0
    y = size - linespacing
    sourcenames = ['Wiki', 'CMUDict', 'Androcles']
    colours = [(0, 0, 255), (0, 255, 0), (0xFD, 0x4B, 0x3F)]
    for slice in results.keys():

        col = g.colorAllocate(colours[slice])
        g.string_ttf(fontname, 10, 0, (0,y), sourcenames[slice], col)
        y -= linespacing

        if results[slice]!=0:
            portion = int((results[slice]/total)*360.0)
            g.filledArc((size/2,size/2),(size/2,size/2), degrees, degrees+portion, col, gd.gdPie)
            degrees += portion

    g.string_ttf(fontname, 10, 0, (0,size), 'Sources of words in the Shavian Set v.%s' % (version), black)
    g.writePng(targetdir+'/sources.png')

def test_it():
    debug('Testing the result.')
    os.chdir('/tmp/shavian-set-%s' % (version))
    os.system('make > /dev/null')
    os.system('python read-back.py > received.txt')
    contents = []
    for content in ('received.txt', 'expected.txt'):
        contents.append(codecs.open(content, 'r', 'utf-8').read())
    if contents[0]!=contents[1]:
        print 'FAILED: Output does not match.'
        sys.exit(254)

def copy_to_usrshare():
    # This will be temporary, because shavianise needs to
    # start reading out of Postgres.
    debug('Copying to /usr/share.')
    os.system('cp /tmp/shavian-set-%s/shavian-set.sqlite /usr/share/shavianset/' % (version))

def copy_it_in():
    debug('Moving it in.')
    os.system('mv /tmp/shavian-set-%s.tar.bz2 %s ' % (version, targetdir))

create_db()
version = populate_from_wiki()
populate_from_cmudict()
remove_cmudict_dupes()
remove_non_y_dabs()
check_for_bad_dupes()
include_pos()
draw_graphs()
build_archive()
output_xml()
build_tarball()
test_it()
copy_it_in()
copy_to_usrshare()
finish()
