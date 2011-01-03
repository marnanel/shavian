#!/usr/bin/python
from xml.dom.minidom import parse, parseString
import codecs
import shavianise
import cgi
import re
import os
import time

root = '/service/website/shavian.org.uk/htdocs'

# If the source RSS is older than this many seconds,
# it will be refreshed.
maxage = 60*60

translatable = {
    'title': 'translate',
    'category': 'translate',
    'description': 'unescape',
    }

skin = codecs.open(root+'/learn/img/skin.html', 'r', 'utf-8').read()

def shavianise_html(t, escape=False):
    r = ''
    for s in re.split('(<[^>]*>|&[^;];)', t):
        if s.startswith('<') or s.startswith('&'):
            if s.startswith('<'):
                s = s.replace('&','&amp;') # very hacky
            if escape:
                r += cgi.escape(s, True)
            else:
                r += s
        else:
            if escape:
                r += shavianise.shavianise(cgi.escape(s))
            else:
                r += shavianise.shavianise(s)
    return r

def inner_xml(c, translate, parent='', src='#'):
    r = u''
    if c.nodeType == c.TEXT_NODE:
        if translate == 'translate':
            r += shavianise.shavianise(cgi.escape(c.data))
        elif translate == 'unescape':
            # we cannot risk a DOM parse here.
            r += shavianise_html(c.data, True)
        else:
            r += cgi.escape(c.data, True)
            
    elif c.nodeType == c.ELEMENT_NODE:
        a = ''
        for attr in c._attrs.keys():
            a += ' %s="%s"' % (attr, c._attrs[attr].value)

        inner = ''

        for e in c.childNodes:
            if translate=='all':
                inner += inner_xml(e, 'all', c.nodeName, src=src)
            else:
                inner += inner_xml(e, translatable.get(c.nodeName, ''), c.nodeName, src=src)

        if c.nodeName == 'generator':
            inner = 'http://shavian.org.uk/feeds/ after '+inner
        elif c.nodeName == 'language':
            inner = 'en-shaw<!-- was '+inner+' -->'
        elif c.nodeName == 'description' and parent=='channel':
            inner = inner + 'This feed was automatically translated into the Shavian alphabet by a computer.  The original feed is at %s .  Please visit http://shavian.org.uk/feeds/ for more information.' % (src,)

        if inner:
            r += '<%s%s>%s</%s>' % (c.nodeName, a, inner, c.nodeName)
        else:
            r += '<%s%s/>' % (c.nodeName, a)

    return r

def translate_feed(id, src='#', lj=None, credit=''):
    if '.' in id:
        return
    dom1 = parse(root+'/feeds/%s/source.xml' % (id))

    f = codecs.open(root+'/feeds/%s/feed.xml' % (id), 'w', 'utf-8')
    f.write('<?xml version="1.0" encoding="UTF-8"  ?>')
    f.write(inner_xml(dom1.documentElement, False, src=src))
    f.close()

    texts = {}
    entries = []

    for h in dom1.documentElement.childNodes:
        if h.nodeType!=h.TEXT_NODE:
            for g in h.childNodes:
                if g.nodeType!=g.TEXT_NODE:
                    c = None
                    if len(g.childNodes)>0:
                        c = g.childNodes[0]
                    if c and c.nodeType==c.TEXT_NODE:
                        texts[g.nodeName] = c.data

                    if g.nodeName == 'item':
                        subtexts = {}
                        for k in g.childNodes:
                            if k.nodeType==k.TEXT_NODE: continue
                            if len(k.childNodes)>0:
                                if k.childNodes[0].nodeType == k.TEXT_NODE:
                                    subtexts[k.nodeName] = k.childNodes[0].data
                        entries.append(subtexts)

    links = []

    url = 'http://shavian.org.uk/feeds/%s/feed' % (id)

    body = ''

    body += '<div class="breadcrumbs"><a href="/">Shavian</a> &raquo; <a href="/feeds/">Feeds</a> &raquo; '
    body += '<strong>%s</strong></div>' % (id)
    body += '<div style="float:right">'
    body += '<a href="%s"><img src="../shaw-rss" width="100" height="100" style="border:0; float:right" alt=""/></a>' % (url)

    links.append([url, 'This feed, in Shavian'])
    links.append([texts['link'], 'The website which owns this feed'])
    links.append([src, 'The original feed'])
    links.append(['http://feedvalidator.org/check.cgi?url=http://shavian.org.uk/feeds/%s/feed' % (id), 'Validate the Shavian feed'])

    if lj:
        links.append(['http://syndicated.livejournal.com/%s/profile' % (lj), 'Read this feed on LiveJournal'])

    body += '<ul>' + ''.join(['<li><a href="%s">%s</a></li>' % (r[0],r[1]) for r in links]) + '</ul>'
    body += '</div>'

    body += '<h1>%s</h1>' % (texts.get('title', id))
    if texts.has_key('description'):
        body += '<blockquote>%s</blockquote>' % (texts['description'])
    body += '<p>%s</p>' % (credit)

    for entry in entries:
        body += '<h2><a href="%s">%s</a></h2><p>%s<blockquote>%s</blockquote></p>' % (entry['link'],
                                                                                      shavianise.shavianise(entry['title']),
                                                                                      entry.get('pubDate', ''),
                                                                                      shavianise_html(entry['description']))

    i = codecs.open(root+'/feeds/%s/index.html' % (id), 'w', 'utf-8')
    i.write(skin % {'title': cgi.escape(texts.get('title'), id) + ' - Shavian feeds',
                    'body': body,
                    # this may not always be correct, e.g. if they're using Atom
                    'headers': '<link rel="alternate" type="application/rss+xml" href="feed">'})
    i.close()

    dom1.unlink()

dom2 = parse(root+'/src/feedlist.xml')
for c in dom2.documentElement.childNodes:
    if c.nodeType != c.TEXT_NODE:
        id = c.getAttribute('id')
        #print 'Updating %s feed.' % (id)
        src = c.getAttribute('src')
        lj = c.getAttribute('lj')
        credit = c.getAttribute('credit')
        sourcexml = root+'/feeds/'+id+'/source.xml'
        if time.time()-os.path.getmtime(sourcexml) > maxage:
            os.system("wget %s -q -O %s" % (src, sourcexml))
        translate_feed(id, src=src, lj=lj, credit=credit)
dom2.unlink()
