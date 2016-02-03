#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, re
from copy import copy

from cdtx.mino import parser
from cdtx.mino.parser import inlinePatterns

import pygments
import pygments.styles
from pygments.lexers import get_lexer_by_name 
from pygments.formatters import HtmlFormatter

from pdb import set_trace

class mdFilter(object):
    def __init__(self, pattern, splitSymbol='/'):
        self.splitSymbol = splitSymbol
        self.pattern = pattern
        self.currentElements = []

    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            self.currentElements.append(issuer)
        elif event == 'mino/doc/stop':
            self.currentElements.pop()

    def test(self, issuer, event, message):
        # Every call to update will have build a list of current elements
        # hierarchy. The aim of the test will be to build a regex from this
        # list, that will be evaluated against the filter

        # Build the regex (based on the class names so far)
        elementPattern = self.splitSymbol.join([self.elementSubPattern(x) for x in self.currentElements])
        return bool(re.search(self.pattern, elementPattern))

    def elementSubPattern(self, issuer):
        '''
        Returns the content if object is a mdTitle, the class name otherwise
        '''
        classDesc = str(issuer.__class__).split('.')[-1]
        if isinstance(issuer, parser.mdTitle):
            return r'%s' % (issuer.content.lower())
        else:
            return r'%s' % (classDesc)

class filterableObserver(object):
    '''
        This is the base class for an observer that manages filters.
        It can be added acceptObservers, each evaluated and OR'ed
    '''
    def __init__(self):
        self.acceptFilters = []

    def addAcceptFilter(self, pattern, splitSymbol='/'):
        self.acceptFilters.append(mdFilter(pattern, splitSymbol))

    def update(self, issuer, event, message):
        if isinstance(issuer, parser.mdRootDoc):
            return
        for f in self.acceptFilters:
            f.update(issuer, event, message)

    def accept(self, issuer, event, message):
        if isinstance(issuer, parser.mdRootDoc):
            return True
        # An empty acceptFilter list means we accept everything
        if self.acceptFilters == []:
            return True

        for f in self.acceptFilters:
            if f.test(issuer, event, message):
                return True
        

class DumbObserver(filterableObserver):
    def __init__(self, **kwargs):
        filterableObserver.__init__(self)

    def update(self, issuer, event, message):
        super(DumbObserver, self).update(issuer, event, message)
        print issuer, event, message
        

class FactoryBasedFilterableObserver(filterableObserver):
    def __init__(self, localRessources=False):
        self.titleLevel = 1
        filterableObserver.__init__(self)

    def __str__(self):
        return self.str
    
    def toFile(self, fileName):
        with open(fileName, 'w') as f:
            f.write(self.str)

    def update(self, issuer, event, message):
        # Update the filters
        if event == 'mino/doc/start':
            filterableObserver.update(self, issuer, event, message)

        # If not accepted element, update the filter anyway then return
        if not filterableObserver.accept(self, issuer, event, message):
            if event == 'mino/doc/stop':
                filterableObserver.update(self, issuer, event, message)
            return

        # Distinct start and stop event
        if event == 'mino/doc/start':
            self.updateStart(issuer, event, message)
        elif event == 'mino/doc/stop':
            self.updateStop(issuer, event, message)

        # Update the filters
        if event == 'mino/doc/stop':
            filterableObserver.update(self, issuer, event, message)

    def updateStart(self, issuer, event, message):
        ''' update called on the start of an element, accepted by filter, 
        implementation can then choose to use the above factory'''
        pass
    def updateStop(self, issuer, event, message):
        ''' update called on the start of an element, accepted by filter, 
        implementation can then choose to use the above factory'''
        pass

    def functionFactory(self, issuer, event):
        if isinstance(issuer, parser.mdRootDoc):
            return self.mdRootDoc(issuer, event)
        elif isinstance(issuer, parser.mdEmptyLine):
            return self.mdEmptyLine(issuer, event)
        elif isinstance(issuer, parser.mdDocumentTitle):
            return self.mdDocumentTitle(issuer, event)
        elif isinstance(issuer, parser.mdTitle):
            if event == 'mino/doc/start':
                self.titleLevel += 1
            elif event == 'mino/doc/stop':
                self.titleLevel -= 1
            return self.mdTitle(issuer, self.titleLevel)
        elif isinstance(issuer, parser.mdTextLine):
            return self.mdTextLine(issuer, event)
            
        elif isinstance(issuer, parser.mdOrderedList):
            return self.mdOrderedList(issuer, event)
        elif isinstance(issuer, parser.mdOrderedListItem):
            return self.mdOrderedListItem(issuer, event)
            
        elif isinstance(issuer, parser.mdUnorderedList):
            return self.mdUnorderedList(issuer, event)
        elif isinstance(issuer, parser.mdUnorderedListItem):
            return self.mdUnorderedListItem(issuer, event)
            
        elif isinstance(issuer, parser.mdTable):
            return self.mdTable(issuer, event)
        elif isinstance(issuer, parser.mdTableLine):
            return self.mdTableLine(issuer, event)
        elif isinstance(issuer, parser.mdBlocOfCode):
            return self.mdBlocOfCode(issuer, event)
        elif isinstance(issuer, parser.mdPlugin):
            return self.mdPlugin(issuer, event)
        elif isinstance(issuer, parser.mdImage):
            return self.mdImage(issuer, event)
        elif isinstance(issuer, parser.mdLink):
            return self.mdLink(issuer, event)
        else:
            raise Exception('Unknown element [%s]' % str(issuer))


    def mdRootDoc(self, issuer, event):
        return ''
    def mdEmptyLine(self, issuer, event):
        return ''
    def mdTitle(self, issuer, level):
        return ''
    def mdDocumentTitle(self, issuer, event):
        return ''
    def mdTextLine(self, issuer, event):
        return ''
    def mdListItem(self, issuer, event):
        return ''
    def mdOrderedList(self, issuer, event):
        return ''
    def mdOrderedListItem(self, issuer, event):
        return ''
    def mdUnorderedList(self, issuer, event):
        return ''
    def mdUnorderedListItem(self, issuer, event):
        return ''
    def mdTable(self, issuer, event):
        return ''
    def mdTableLine(self, issuer, event):
        return ''
    def mdBlocOfCode(self, issuer, event):
        return ''
    def mdPlugin(self, issuer, event):
        return ''
    def mdLink(self, issuer, event):
        return ''
    def mdImage(self, issuer, event):
        return ''

class MarkdownObserver(FactoryBasedFilterableObserver):
    ''' Exports a mino written document to common markdown '''
    def __init__(self):
        FactoryBasedFilterableObserver.__init__(self)
        self.str = ''
        self.prepareTable = None
        self.nestedOrderedListIndex = -1
        self.nestedUnorderedListIndex = -1

    def updateStart(self, issuer, event, message):
        res = self.functionFactory(issuer, event)
        # functionFactory can return single string or (begin, end) tuple
        if isinstance(res, tuple) or isinstance(res, list):
            self.str += res[0]
        else:
            self.str += res
    def updateStop(self, issuer, event, message):
        res = self.functionFactory(issuer, event)
        # functionFactory can return single string or (begin, end) tuple
        if isinstance(res, tuple) or isinstance(res, list):
            self.str += res[1]

    def mdEmptyLine(self, issuer, event):
        return ''
    def mdTitle(self, issuer, level):
        return '\n'+'%s %s'% ('#'*level, self.replaceInline(issuer.content)) + '\n'
    def mdDocumentTitle(self, issuer, event):
        return ''
    def mdTextLine(self, issuer, event):
        return self.replaceInline(issuer.content) + '\n'

    def mdOrderedList(self, issuer, event):
        if event.endswith('start'):
            self.nestedOrderedListIndex += 1
        elif event.endswith('stop'):
            self.nestedOrderedListIndex -= 1
        return FactoryBasedFilterableObserver.mdOrderedList(self, issuer, event)

    def mdOrderedListItem(self, issuer, event):
        return '%s1. %s' % ('  '*self.nestedUnorderedListIndex, 
                            self.replaceInline(issuer.content)
        ) + '\n'
    
    def mdUnorderedList(self, issuer, event):
        if event.endswith('start'):
            self.nestedUnorderedListIndex += 1
        elif event.endswith('stop'):
            self.nestedUnorderedListIndex -= 1
        return FactoryBasedFilterableObserver.mdUnorderedList(self, issuer, event)

    def mdUnorderedListItem(self, issuer, event):
        return '%s- %s' % ('  '*self.nestedUnorderedListIndex,
                            self.replaceInline(issuer.content)
        ) + '\n'
    def mdTable(self, issuer, event):
        # Assume (strong) all rows have the same number of elements
        # Return nothing but prepare the table sub-header
        self.prepareTable = ' | '.join(['---'] * len(issuer.childs[0].elements))
        return ('', '\n')

    def mdTableLine(self, issuer, event):
        s = ' | '.join(issuer.elements) + '\n'
        if self.prepareTable:
            s += self.prepareTable + '\n'
            self.prepareTable = None
        return s

    def mdBlocOfCode(self, issuer, event):
        return '\n'.join( [
                            "```%s" % issuer.lang,
                            issuer.text,
                            "```",
        ]) + '\n\n'
    def mdPlugin(self, issuer, event):
        return ''
    def mdLink(self, issuer, event):
        return '[%s](%s)\n' % (issuer.caption, issuer.url) + '\n'
    def mdImage(self, issuer, event):
        return '![%s](%s)\n' % (issuer.caption, issuer.url) + '\n'

    def replaceInline(self, content):
        repl = {'bold':r'**\1**',
                'italic':r'_\1_',
                'underlined':r'\1',
                'link':r'[\2](\1)',
        }
                
        content = content.replace('\n', '<br/>')
        for (pat, opt, type) in inlinePatterns:
            if type in repl.keys():
                content = re.sub(pat, repl[type], content, flags=opt)
        return content

class HtmlDocObserver(FactoryBasedFilterableObserver):
    def __init__(self, localRessources=False):
        FactoryBasedFilterableObserver.__init__(self)
        self.indent = 0
        self.style = 'default'
        self.str = ''
        self.basePath = os.path.abspath(os.path.dirname(__file__))
        self.localRessources = localRessources        

        self.generateResourcesPath()
    
    def generateResourcesPath(self):
        if not self.localRessources:
            self.cssPath = r'https://rawgit.com/cdtx/mino/master/styles/{style}/style.css'
        else:
            self.cssPath = r'%s/styles/{style}/style.css' % self.basePath

    def mdRootDoc(self, issuer, event):
        before =    [   '<!doctype html>',
                        '<html>',
                        '    <!-- Not supported yet -->',
                        '    <head>',
                        '        <meta http-equiv="content-type" content="text/html; charset=utf-8" />'
                        '        <!-- Latest compiled and minified CSS -->',
                        '        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">',
                        '',
                        '        <!-- Optional theme -->',
                        '        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css">',
                        '',
                        '        <!-- Latest compiled and minified JavaScript -->',
                        '        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>',
                        '',
                        '        <link rel="stylesheet" href="%s" />' % self.cssPath.format(style=self.style),
                        '    </head>',
                        '    <body>',
                        '        <article>',
                        '            <header>',
                        '                <div />',
                        '            </header>',
                        '            <div class="container-fluid">',
                        '                <div class="row">',
                        '                    <div class="panel panel-default">',
                        '                        <div class="panel-body">',
                    ]
        after =     [   '                        </div>',
                        '                    </div>',
                        '                </div>',
                        '            </div>',
                        '        </article>',
                        '    </body>',
                        '</html>',
                    ]
        return (before, after)
        
    def mdEmptyLine(self, issuer, event):
        return (['<br>'], [])
        
    def mdTitle(self, issuer, level):
        before =    [   
                        '    <div class="minoParagraph%d" %s>' % (level, self.groupExtraParams(issuer)),
                        '    <h%d %s>' % (level, self.extraParams(issuer)),
                        '        %s' % self.htmlReplaceInline(issuer.title),
                        '    </h%d>' % (level),
                    ]
        after =     [   '    </div>',
                    ]
        return (before, after)
        
    def mdDocumentTitle(self, issuer, event):
        before =    [   '<div class="page-header">',
                        '<h1>%s</h1>' % self.htmlReplaceInline(issuer.title),
                        '</div>',
                    ]
        after = []
        return (before, after)
        
    def mdTextLine(self, issuer, event):
        before =    [   '<p %s>' % self.extraParams(issuer),
                        '    %s' % (self.htmlReplaceInline(issuer.text) if issuer.inline else issuer.text)
                    ]
        after =     ['</p>']
        return (before, after)
    
    def mdListItem(self, issuer, event):
        before =    ['<li %s>' % self.extraParams(issuer),
                     '    %s' % (self.htmlReplaceInline(issuer.text))]
        after =     ['</li>']
        return (before, after)
        
    def mdOrderedList(self, issuer, event):
        before =    ['<ol %s>' % self.extraParams(issuer)]
        after =     ['</ol>']
        return (before, after)
    def mdOrderedListItem(self, issuer, event):
        return self.mdListItem(issuer, event)
        
    def mdUnorderedList(self, issuer, event):
        before =    ['<ul %s>' % self.extraParams(issuer) ]
        after =     ['</ul>']
        return (before, after)        
    def mdUnorderedListItem(self, issuer, event):
        return self.mdListItem(issuer, event)
        
    def mdTable(self, issuer, event):
        before =    ['<table %s>' % self.extraParams(issuer)]
        after =     ['</table>']
        return (before, after)
    
    def mdTableLine(self, issuer, event):
        before =    ['<tr %s>' % self.extraParams(issuer)]
        for c in issuer.elements:
            before.append('    <td> %s </td>' % self.htmlReplaceInline(c.strip()))
        after =     ['</tr>']
        return (before, after)
    
    def mdBlocOfCode(self, issuer, event):
        # See for using http://prismjs.com/index.html
        res = ([str(pygments.highlight(issuer.text, get_lexer_by_name(issuer.lang), HtmlFormatter(noclasses=True)))], [])
        return res
    
    def mdPlugin(self, issuer, event):
        before =    [   '<div %s>' % self.extraParams(issuer),
                    ]
        after =    ['</div>']
        return (before, after)
    
    def mdLink(self, issuer, event):
        before =    [   '<p %s>' % (self.extraParams(issuer)),  
                        '    <a href="%s">%s</a>' % (issuer.url, self.htmlReplaceInline(issuer.caption)),
                    ]
        after =     [   '</p>']
        return (before, after)
    
    def mdImage(self, issuer, event):
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

    def updateStart(self, issuer, event, message):
        linesBefore = self.functionFactory(issuer, event)[0]
        self.htmlAppend(linesBefore)
        self.indent += 1
    def updateStop(self, issuer, event, message):
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
                
        content = content.replace('\n', '<br/>')
        for (pat, opt, type) in inlinePatterns:
            if type in repl.keys():
                content = re.sub(pat, repl[type], content, flags=opt)
        return content
            
            
class PdfDocObserver(HtmlDocObserver):
    '''
    Using weasyprint, pdf generation becomes a special case of html generation
    Except the header that changes
    '''
    def generateResourcesPath(self):
        if not self.localRessources:
            self.cssPath = r'https://rawgit.com/cdtx/mino/master/styles/{style}/pdf.css'
        else:
            self.cssPath = r'file://localhost/%s/styles/{style}/pdf.css' % self.basePath


    def mdRootDoc(self, issuer, event):
        before =    [   '<!doctype html>',
                        '<html>',
                        '    <!-- Not supported yet -->',
                        '    <head>',
                        '        <meta http-equiv="content-type" content="text/html; charset=utf-8" />'
                        '        <link rel="stylesheet" href="%s" />' % self.cssPath.format(style=self.style),
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
    def __init__(self, localRessources=False):
        HtmlDocObserver.__init__(self, localRessources)
        self.slidesList = [] 
        self.slidesInProgress = 0

    def generateResourcesPath(self):
        if self.localRessources:
            self.revealPath = r'%s/styles/default/reveal'%self.basePath
        else:
            self.revealPath = r'https://rawgit.com/hakimel/reveal.js/3.0.0'

    def mdRootDoc(self, issuer, event):
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
            '''		<link rel="stylesheet" href="%s/css/reveal.css">''' % self.revealPath,
            '''		<link rel="stylesheet" href="%s/css/theme/black.css" id=theme">''' % self.revealPath,
            '''''',
            '''		<!-- Code syntax highlighting -->''',
            '''		<link rel="stylesheet" href="%s/lib/css/zenburn.css">''' % self.revealPath,
            '''''',
            '''		<!--[if lt IE 9]>''',
            '''		<script src="%s/lib/js/html5shiv.js"></script>''' % self.revealPath,
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
            '''     <script src="%s/lib/js/head.min.js"></script>''' % self.revealPath,
            '''		<script src="%s/js/reveal.js"></script>''' % self.revealPath,
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
            '''					{ src: '%s/lib/js/classList.js', condition: function() { return !document.body.classList; } },''' % self.revealPath,
            '''					{ src: '%s/plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''' % self.revealPath,
            '''					{ src: '%s/plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''' % self.revealPath,
            '''					{ src: '%s/plugin/highlight/highlight.js', async: true, condition: function() { return !!document.querySelector( 'pre code' ); }, callback: function() { hljs.initHighlightingOnLoad(); } },''' % self.revealPath,
            '''					{ src: '%s/plugin/zoom-js/zoom.js', async: true },''' % self.revealPath,
            '''					{ src: '%s/plugin/notes/notes.js', async: true }''' % self.revealPath,
            '''				]''',
            '''			});''',
            '''''',
            '''		</script>''',
            '''''',
            '''	</body>''',
            '''</html>''',
               ]

        return (before, after)

    def updateStart(self, issuer, event, message):
        if ((issuer.groupExtraParams and issuer.groupExtraParams.all.get('type') == 'summary') or
             (issuer.extraParams and issuer.extraParams.all.get('type') == 'summary') ):

            if self.slidesInProgress == 0:
                self.slidesInProgress = 1
                self.slidesList.append([issuer, []])
            elif self.slidesInProgress == 1:
                self.slidesList[-1][1].append(issuer)
            else:
                print '[SlidesObserver] Warning, cannot manage more than 2 levels of slides'
                
    def updateStop(self, issuer, event, message):
        if self.slidesInProgress == 1 and issuer == self.slidesList[-1][0]:
            self.slidesInProgress = 0

    def toFile(self, fileName):
        self.createHtml()
        HtmlDocObserver.toFile(self, fileName)

    def createHtml(self):
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





