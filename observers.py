#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pdb
import os, re

from cdtx.mino import parser
from cdtx.mino.parser import inlinePatterns

from pygments import highlight
from pygments.lexers import get_lexer_by_name 
from pygments.formatters import HtmlFormatter
import weasyprint

class DumbObserver:
    def update(self, issuer, event, message):
        print issuer, event, message
        
class HtmlDocObserver:
    def __init__(self):
        self.indent = 0
        self.titleLevel = 1
        self.style = 'default'
        self.str = ''
        self.basePath = os.path.dirname(__file__)
        
    def __str__(self):
        return self.str
    
    def toFile(self, fileName):
        with open(fileName, 'w') as f:
            f.write(self.str)

    def mdRootDoc(self, issuer):
        # with open('%s/styles/%s/style.css' % (os.path.dirname(os.path.realpath(__file__)), self.style), 'r') as style:
        before =    [   '<!doctype html>',
                        '<html>',
                        '    <!-- Not supported yet -->',
                        '    <head>',
                        '        <meta http-equiv="content-type" content="text/html; charset=utf-8" />'
                        '        <link rel="stylesheet" href="%s/styles/%s/style.css" />' % (self.basePath, self.style),
                        # '    <style>',
                        # '     %s' % style.read(),
                        # '    </style>',
                        '    </head>',
                        '    <body>',
                        '        <article>',
                        '            <header>',
                        '                <div />',
                        '            </header>',
                    ]
        after =     [   '        </article>',
                        '    </body>',
                        '</html>',
                    ]
        return (before, after)
        
    def mdEmptyLine(self, issuer):
        return (['<br>'], [])
        
    def mdTitle(self, issuer):
        before =    [   
                        '    <div class="minoParagraph%d" %s>' % (self.titleLevel, self.groupExtraParams(issuer)),
                        '    <h%d %s>' % (self.titleLevel, self.extraParams(issuer)),
                        '        %s' % self.htmlReplaceInline(issuer.title),
                        '    </h%d>' % (self.titleLevel),
                    ]
        after =     [   '    </div>',
                    ]
        return (before, after)
        
    def mdDocumentTitle(self, issuer):
        return (['<!-- <doc_title> -->'], ['<!-- </doc_title> -->'])
        
    def mdTextLine(self, issuer):
        before =    [   '<p %s>' % self.extraParams(issuer),
                        '    %s' % (self.htmlReplaceInline(issuer.text))
                    ]
        after =     ['</p>']
        return (before, after)
    
    def mdListItem(self, issuer):
        before =    ['<li %s>' % self.extraParams(issuer),
                     '    %s' % (self.htmlReplaceInline(issuer.text))]
        after =     ['</li>']
        return (before, after)
        
    def mdOrderedList(self, issuer):
        before =    ['<ol %s>' % self.extraParams(issuer)]
        after =     ['</ol>']
        return (before, after)
    def mdOrderedListItem(self, issuer):
        return self.mdListItem(issuer)
        
    def mdUnorderedList(self, issuer):
        before =    ['<ul %s>' % self.extraParams(issuer) ]
        after =     ['</ul>']
        return (before, after)        
    def mdUnorderedListItem(self, issuer):
        return self.mdListItem(issuer)
        
    def mdTable(self, issuer):
        before =    ['<table %s>' % self.extraParams(issuer)]
        after =     ['</table>']
        return (before, after)
    
    def mdTableLine(self, issuer):
        before =    ['<tr %s>' % self.extraParams(issuer)]
        for c in issuer.elements:
            before.append('    <td> %s </td>' % self.htmlReplaceInline(c.strip()))
        after =     ['</tr>']
        return (before, after)
    
    def mdBlocOfCode(self, issuer):
        # See for using http://prismjs.com/index.html
        return ([highlight(issuer.text, get_lexer_by_name(issuer.lang), HtmlFormatter(noclasses=True))], [])
    
    def mdPlugin(self, issuer):
        before =    [   '<p %s>' % self.extraParams(issuer),
                        issuer.output.getvalue().replace('\n', '<br/>'),
                    ]
        after =    ['</p>']
        return (before, after)
    
    def mdLink(self, issuer):
        before =    [   '<p %s>' % (self.extraParams(issuer)),  
                        '    <a href="%s">%s</a>' % (issuer.url, self.htmlReplaceInline(issuer.caption)),
                    ]
        after =     [   '</p>']
        return (before, after)
    
    def mdImage(self, issuer):
        before =    [   '<figure>', 
                        '   <img src="%s" alt="missing" %s/>' % (issuer.url, self.extraParams(issuer)),
                        '   <figcaption>%s</figcaption>' % self.htmlReplaceInline(issuer.caption),
                    ]
        after =     [   '</figure>' ]
        return (before, after)
    
    def extraParams(self, issuer):
        if issuer.extraParams == None:
            return ''
        return ' '.join(['%s="%s"' % (k,v) for (k,v) in issuer.extraParams.all.iteritems()])
             
    def groupExtraParams(self, issuer):
        if issuer.groupExtraParams == None:
            return ''
        return ' '.join(['%s="%s"' % (k,v) for (k,v) in issuer.groupExtraParams.all.iteritems()])

    def functionFactory(self, issuer, event):
        if isinstance(issuer, parser.mdRootDoc):
            return self.mdRootDoc(issuer)
        elif isinstance(issuer, parser.mdEmptyLine):
            return self.mdEmptyLine(issuer)
        elif isinstance(issuer, parser.mdDocumentTitle):
            return self.mdDocumentTitle(issuer)
        elif isinstance(issuer, parser.mdTitle):
            if event == 'mino/doc/start':
                self.titleLevel += 1
            elif event == 'mino/doc/stop':
                self.titleLevel -= 1
            return self.mdTitle(issuer)
        elif isinstance(issuer, parser.mdTextLine):
            return self.mdTextLine(issuer)
            
        elif isinstance(issuer, parser.mdOrderedList):
            return self.mdOrderedList(issuer)
        elif isinstance(issuer, parser.mdListItem):
            return self.mdListItem(issuer)
            
        elif isinstance(issuer, parser.mdUnorderedList):
            return self.mdUnorderedList(issuer)
        elif isinstance(issuer, parser.mdListItem):
            return self.mdListItem(issuer)
            
        elif isinstance(issuer, parser.mdTable):
            return self.mdTable(issuer)
        elif isinstance(issuer, parser.mdTableLine):
            return self.mdTableLine(issuer)
        elif isinstance(issuer, parser.mdBlocOfCode):
            return self.mdBlocOfCode(issuer)
        elif isinstance(issuer, parser.mdPlugin):
            return self.mdPlugin(issuer)
        elif isinstance(issuer, parser.mdImage):
            return self.mdImage(issuer)
        elif isinstance(issuer, parser.mdLink):
            return self.mdLink(issuer)
        else:
            raise Exception('Unknown element [%s]' % str(issuer))
    
    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            linesBefore = self.functionFactory(issuer, event)[0]
            self.htmlAppend(linesBefore)
            self.indent += 1
        elif event == 'mino/doc/stop':
            self.indent -= 1
            linesAfter = self.functionFactory(issuer, event)[1]
            self.htmlAppend(linesAfter)

    def htmlAppend(self, lst):
        self.str += '\n'.join([(' '*4*self.indent + x) for x in lst]) + '\n'

    def htmlReplaceInline(self, content):
        repl = {'bold':r'<strong>\1</strong>',
                'italic':r'<em>\1</em>',
                'underlined':r'<u>\1</u>',
                'link':r'<a href="\1">\2</a>',
        }
                
        for (pat, opt, type) in inlinePatterns:
            if type in repl.keys():
                content = re.sub(pat, repl[type], content, flags=opt)
        return content
            
            
class PdfDocObserver(HtmlDocObserver):
    '''
    Using weasyprint, pdf generation becomes a special case of html generation
    Except the header that changes
    '''
    def mdRootDoc(self, issuer):
        before =    [   '<!doctype html>',
                        '<html>',
                        '    <!-- Not supported yet -->',
                        '    <head>',
                        '        <meta http-equiv="content-type" content="text/html; charset=utf-8" />'
                        '        <link rel="stylesheet" href="%s/styles/%s/pdf.css" />' % (self.basePath, self.style),
                        '    </head>',
                        '    <body>',
                        '        <article>',
                        '            <header>',
                        '                <div />',
                        '            </header>',
                    ]
        after =     [   '        </article>',
                        '    </body>',
                        '</html>',
                    ]
        
        return (before, after)

    def toFile(self, fileName):
        weasy = weasyprint.HTML(string=self.str, base_url=os.path.abspath(__file__))    
        x = weasy.render()
        weasy.write_pdf(fileName)

class SlidesObserver(HtmlDocObserver):
    '''
    Using reveal.js, slides generation becomes a special case of html generation
    Except the header that changes
    '''
    def __init__(self):
        HtmlDocObserver.__init__(self)
        self.slidesList = [] 
        self.slidesInProgress = 0

    def mdRootDoc(self, issuer):
        before = [
            '''<!doctype html>''',
            '''<html lang="en">''',
            '''''',
            '''	<head>''',
            '''     <meta http-equiv="content-type" content="text/html; charset=utf-8" />''',
            '''''',
            '''		<meta name="apple-mobile-web-app-capable" content="yes" />''',
            '''		<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />''',
            '''''',
            '''		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, minimal-ui">''',
            '''''',
            '''		<link rel="stylesheet" href="%s/styles/%s/reveal/css/reveal.css">''' % (self.basePath, self.style),
            '''		<link rel="stylesheet" href="%s/styles/%s/reveal/css/theme/black.css" id=theme">''' % (self.basePath, self.style),
            '''''',
            '''		<!-- Code syntax highlighting -->''',
            '''		<link rel="stylesheet" href="%s/styles/%s/reveal/lib/css/zenburn.css">''' % (self.basePath, self.style),
            '''''',
            '''		<!--[if lt IE 9]>''',
            '''		<script src="%s/styles/%s/reveal/lib/js/html5shiv.js"></script>''' % (self.basePath, self.style),
            '''		<![endif]-->''',
            '''	</head>''',
            '''''',
            '''	<body>''',
            '''''',
            '''		<div class="reveal">''',
            '''''',
            '''			<!-- Any section element inside of this container is displayed as a slide -->''',
            '''			<div class="slides">''',
               ] 

        after = [
            '''         </div>''',
            '''     </div>''',
            '''     <script src="%s/styles/%s/reveal/lib/js/head.min.js"></script>''' % (self.basePath, self.style),
            '''		<script src="%s/styles/%s/reveal/js/reveal.js"></script>''' % (self.basePath, self.style),
            '''''',
            '''		<script>''',
            '''''',
            '''			// Full list of configuration options available at:''',
            '''			// https://github.com/hakimel/reveal.js#configuration''',
            '''			Reveal.initialize({''',
            '''				controls: true,''',
            '''				progress: true,''',
            '''				history: true,''',
            '''				center: true,''',
            '''''',
            '''				transition: 'slide', // none/fade/slide/convex/concave/zoom''',
            '''''',
            '''				// Optional reveal.js plugins''',
            '''				dependencies: [''',
            '''					{ src: '%s/styles/%s/reveal/lib/js/classList.js', condition: function() { return !document.body.classList; } },''' % (self.basePath, self.style),
            '''					{ src: '%s/styles/%s/reveal/plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''' % (self.basePath, self.style),
            '''					{ src: '%s/styles/%s/reveal/plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''' % (self.basePath, self.style),
            '''					{ src: '%s/styles/%s/reveal/plugin/highlight/highlight.js', async: true, condition: function() { return !!document.querySelector( 'pre code' ); }, callback: function() { hljs.initHighlightingOnLoad(); } },''' % (self.basePath, self.style),
            '''					{ src: '%s/styles/%s/reveal/plugin/zoom-js/zoom.js', async: true },''' % (self.basePath, self.style),
            '''					{ src: '%s/styles/%s/reveal/plugin/notes/notes.js', async: true }''' % (self.basePath, self.style),
            '''				]''',
            '''			});''',
            '''''',
            '''		</script>''',
            '''''',
            '''	</body>''',
            '''</html>''',
               ]

        return (before, after)

    def update(self, issuer, event, message):
        # Here in the update method, we only build a list of elements that will participate in the slide set
        if event == 'mino/doc/start':
            if ((issuer.groupExtraParams and issuer.groupExtraParams.all.get('type') == 'summary') or
                 (issuer.extraParams and issuer.extraParams.all.get('type') == 'summary') ):

                if self.slidesInProgress == 0:
                    self.slidesInProgress = 1
                    self.slidesList.append([issuer, []])
                elif self.slidesInProgress == 1:
                    self.slidesList[-1][1].append(issuer)
                else:
                    print '[SlidesObserver] Warning, cannot manage more than 2 levels of slides'
                

        if event == 'mino/doc/stop':
            if self.slidesInProgress == 1 and issuer == self.slidesList[-1][0]:
                    self.slidesInProgress = 0

    def toFile(self, fileName):
        self.createHtml()
        HtmlDocObserver.toFile(self, fileName)

    def createHtml(self):
        pdb.set_trace()
        self.htmlAppend(self.mdRootDoc(None)[0])

        for slide in self.slidesList:
            if slide[1] == []:
                # There is no subslide, so create only one <section> level
                self.htmlAppend(['<section>'])
                self.recursiveDoc(slide[0])
                self.htmlAppend(['</section>'])
            else:
                # The root element is only used for delimiting the section
                self.htmlAppend(['<section>'])
                
                for sub in slide[1]:
                    self.htmlAppend(['<section>'])
                    self.recursiveDoc(sub)
                    self.htmlAppend(['</section>'])

                self.htmlAppend(['</section>'])
        
        self.htmlAppend(self.mdRootDoc(None)[1])

    def recursiveDoc(self, elem):
        self.htmlAppend(self.functionFactory(elem, 'mino/doc/start')[0])
        for sub in elem.childs:
            self.recursiveDoc(sub)
        self.htmlAppend(self.functionFactory(elem, 'mino/doc/stop')[1])





