from xml.dom.minidom import parse
import codecs
import os
import shavianise
import sys
import StringIO

def skin(content, target='/dev/stdout', title='Shavian', crumb=None, extrahead=''):
    if crumb==None:
        crumb = [title]
    o = codecs.open(target, 'w', 'utf-8')
    o.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
    o.write('<html xmlns="http://www.w3.org/1999/xhtml" lang="en-GB" xml:lang="en-GB">\n')
    if not 'Shavian' in title:
        title += " - Shavian"
    o.write('<head><title>%s</title>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n%s\n' % (title, extrahead))
    if crumb==['']:
        o.write('<link rel="openid.server" href="http://www.livejournal.com/openid/server.bml" />\n')
        o.write('<link rel="openid.delegate" href="http://marnanel.livejournal.com/" />\n')

    o.write('<link rel="stylesheet" href="/static/eirastyle"/></head>\n')
    o.write('<body>\n')

    o.write('<div class="menu">')
    o.write('<a href="/learn/">learn</a> &middot; ')
    o.write('<a href="/translate/">translate</a> &middot; ')
    o.write('<a href="/wiki/Main_Page">wiki</a> &middot; ')
    o.write('<a href="/games/">games</a> &middot; ')
    o.write('<a href="/feeds">feeds</a> &middot; ')
    o.write('<a href="/shawscript/">archives</a> &middot; ')
    o.write('<a href="/film/sita/">film</a> &middot; ')
    o.write('<a href="/questions/">questions</a> &middot; ')
    o.write('<a href="/credits">credits</a>')
    o.write('</div>\n')

    o.write("""
<!-- Beginning of Project Wonderful ad code: -->
<!-- Ad box ID: 49208 -->
<div class="ads">
<script type="text/javascript">
<!--
var pw_d=document;
pw_d.projectwonderful_adbox_id = "49208";
pw_d.projectwonderful_adbox_type = "4";
pw_d.projectwonderful_foreground_color = "#777";
pw_d.projectwonderful_background_color = "#002";
//-->
</script>
<script type="text/javascript" src="http://www.projectwonderful.com/ad_display.js"></script>
<noscript><map name="admap49208" id="admap49208"><area href="http://www.projectwonderful.com/out_nojs.php?r=0&amp;c=0&amp;id=49208&amp;type=4" shape="rect" coords="0,0,125,125" title="" alt="" target="_blank" /></map>
<table cellpadding="0" border="0" cellspacing="0" width="125" bgcolor="#ffffff"><tr><td><img src="http://www.projectwonderful.com/nojs.php?id=49208&amp;type=4" width="125" height="125" usemap="#admap49208" border="0" alt="" /></td></tr><tr><td bgcolor="#ffffff" colspan="1"><center><a style="font-size:10px;color:#0000ff;text-decoration:none;line-height:1.2;font-weight:bold;font-family:Tahoma, verdana,arial,helvetica,sans-serif;text-transform: none;letter-spacing:normal;text-shadow:none;white-space:normal;word-spacing:normal;" href="http://www.projectwonderful.com/advertisehere.php?id=49208&amp;type=4" target="_blank">Ads by Project Wonderful!  Your ad here, right now: $0</a></center></td></tr></table>
</noscript>
<!-- End of Project Wonderful ad code. -->
</div>
""")


    if crumb==['']:
        o.write('<div class="breadcrumbs"><strong>Shavian</strong></div>\n')
    else:
        o.write('<div class="breadcrumbs"><a href="/">Shavian</a> &raquo; ')
        for c in crumb[:-1]:
            o.write('%s &raquo; ' % (c))
        o.write('<strong>%s</strong></div>\n' % (crumb[-1], ))

    o.write('<div class="photocredit"><a href="http://www.flickr.com/photos/stephoto/220381401/">Photo &copy; Steve Johnson, cc-by-sa.</a></div>\n')

    #o.write('<div class="smallad">')
    #o.write(file('pw-smallad.html').read())
    #o.write('</div>')

    o.write('<div class="content">\n')

    o.write(content)
    o.write('\n<br style="clear:both"/>\n')
    o.write('</div></body></html>\n')
    o.close()

def inner_html(e, translate=False, locals={}):
    r = ''
    t = ''
    for c in e.childNodes:
        if c.nodeType == c.TEXT_NODE:
            r += c.data
            t += shavianise.shavianise(c.data)
        elif c.nodeType == c.ELEMENT_NODE and c.nodeName=='e':
            shaw = c.getAttribute('shaw')
            latn = c.getAttribute('latn')
            if not shaw:
                shaw = latn
            elif shaw[0]<='z':
                shaw = shavianise.unascii(shaw)
            r += latn
            t += shaw
        elif c.nodeType == c.ELEMENT_NODE and c.nodeName=='just':
            alphabet = c.getAttribute('a')
            if alphabet == 'shaw':
                t += inner_html(c, translate, locals)[1]
            elif alphabet == 'latn':
                r += inner_html(c, translate, locals)[0]
        elif c.nodeType == c.ELEMENT_NODE and c.nodeName=='exec':
            saved = sys.stdout
            sys.stdout = StringIO.StringIO()
            exec(inner_html(c, 0, locals)[0], locals)
            b = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = saved

            r += b
            t += ''

        elif c.nodeType == c.ELEMENT_NODE:
            a = ''
            for attr in c._attrs.keys():
                a += ' %s="%s"' % (attr, c._attrs[attr].value)
            inner = inner_html(c, translate, locals)

            if inner:
                r += '<%s%s>%s</%s>' % (c.nodeName, a, inner[0], c.nodeName)
                t += '<%s%s>%s</%s>' % (c.nodeName, a, inner[1], c.nodeName)
            else:
                r += '<%s%s/>' % (c.nodeName, a)
                t += '<%s%s/>' % (c.nodeName, a)
    return (r, t)

def search_and_skin(sourcepath, prefix):

    # local variables for <exec/>
    locals = {'shavianise': shavianise.shavianise}

    for d in os.walk(sourcepath):
        for f in d[2]:
            if '..' in f:
                print 'Ignoring ',f
                continue

            target = (prefix+'/'+f).replace('.ss.xml', '.html').replace('_','/').replace('//','_')
            if not f.endswith('.ss.xml'):
                f = d[0]+'/'+f
                open(target, 'wb').write(open(f,'rb').read())
                continue

            dom1 = parse(d[0]+'/'+f)
            content = ''
            title = dom1.documentElement.getAttribute('title')
            crumb = dom1.documentElement.getAttribute('crumb')
            if crumb==None:
                crumb = title
            crumb = [crumb]
            for c in dom1.documentElement.childNodes:
                    if c.nodeType == c.TEXT_NODE: continue
                    if c.nodeName == 'text':
                        translate = c.getAttribute('only')
                        i = inner_html(c, translate, locals)
                        t = title
                        alphabet = c.getAttribute('a')
                        if not translate and alphabet=='shaw':
                            t = shavianise.shavianise(t)
                        if c.getAttribute('notitle'):
                            content += '<div style="clear:all" lang="en-%s">\n%s\n</div>' % (alphabet, i[0])
                            if translate:
                                content += '<div style="clear:all" lang="en-shaw">\n%s\n</div>' % (i[1])
                        else:
                            content += '<div lang="en-%s">\n<h1>%s</h1>\n%s\n</div>' % (alphabet, t, i[0])
                            if translate:
                                content += '<div lang="en-shaw">\n<h1>%s</h1>\n%s\n</div>' % (shavianise.shavianise(t), i[1])
                    elif c.nodeName == 'crumb':
                        crumb.insert(0, inner_html(c, False, locals)[0])

            skin(content, title=title, target=target, crumb=crumb)
            dom1.unlink()

