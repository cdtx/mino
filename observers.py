import os, re

from cdtx.mino import parser
from mino.parser import inlinePatterns

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
        self.style = 'default'
        self.str = ''
        
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
                        '        <link rel="stylesheet" href="styles/%s/style.css" />' % self.style,
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
        before =    [   '    <h%d %s>' % (issuer._indent()+1, self.extraParams(issuer)),
                        '        %s' % self.htmlReplaceInline(issuer.title),
                        '    </h%d>' % (issuer._indent()+1),
                    ]
        return (before, [])
        
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
             

    def functionFactory(self, issuer):
        if isinstance(issuer, parser.mdRootDoc):
            return self.mdRootDoc(issuer)
        elif isinstance(issuer, parser.mdEmptyLine):
            return self.mdEmptyLine(issuer)
        elif isinstance(issuer, parser.mdDocumentTitle):
            return self.mdDocumentTitle(issuer)
        elif isinstance(issuer, parser.mdTitle):
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
        elif isinstance(issuer, parser.mdLink):
            return self.mdLink(issuer)
        elif isinstance(issuer, parser.mdImage):
            return self.mdImage(issuer)
        else:
            raise Exception('Unknown element [%s]' % str(issuer))
    
    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            linesBefore = self.functionFactory(issuer)[0]
            self.str += '\n'.join([(' '*4*self.indent + x) for x in linesBefore]) + '\n'
            self.indent += 1
        elif event == 'mino/doc/stop':
            self.indent -= 1
            linesAfter = self.functionFactory(issuer)[1]
            self.str += '\n'.join([(' '*4*self.indent + x) for x in linesAfter]) + '\n'

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
                        '        <link rel="stylesheet" href="styles/%s/pdf.css" />' % self.style,
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

    
class SlidesObserver(HtmlDocObserver):
    '''
    Using reveal.js, slides generation becomes a special case of html generation
    Except the header that changes
    '''
    def __init__(self):
        HtmlDocObserver.__init__(self)
        self.slidesInProgress=0

    def mdRootDoc(self, issuer):
        before = [
            '''<!doctype html>''',
            '''<html lang="en">''',
            '''''',
            '''	<head>''',
            '''		<meta charset="utf-8">''',
            '''''',
            '''		<meta name="apple-mobile-web-app-capable" content="yes" />''',
            '''		<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />''',
            '''''',
            '''		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, minimal-ui">''',
            '''''',
            '''		<link rel="stylesheet" href="css/reveal.css">''',
            '''		<link rel="stylesheet" href="css/theme/black.css" id="theme">''',
            '''''',
            '''		<!-- Code syntax highlighting -->''',
            '''		<link rel="stylesheet" href="lib/css/zenburn.css">''',
            '''''',
            '''		<!--[if lt IE 9]>''',
            '''		<script src="lib/js/html5shiv.js"></script>''',
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
            '''     <script src="lib/js/head.min.js"></script>''',
            '''		<script src="js/reveal.js"></script>''',
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
            '''					{ src: 'lib/js/classList.js', condition: function() { return !document.body.classList; } },''',
            '''					{ src: 'plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''',
            '''					{ src: 'plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },''',
            '''					{ src: 'plugin/highlight/highlight.js', async: true, condition: function() { return !!document.querySelector( 'pre code' ); }, callback: function() { hljs.initHighlightingOnLoad(); } },''',
            '''					{ src: 'plugin/zoom-js/zoom.js', async: true },''',
            '''					{ src: 'plugin/notes/notes.js', async: true }''',
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
        if issuer.name == 'rootDoc':
            HtmlDocObserver.update(self, issuer, event, message)

        if issuer.extraParams:
            _type = issuer.extraParams.all.get('type')
            if (_type == 'summary') and (event == 'mino/doc/start'):
                self.slidesInProgress += 1
                self.str += '<section>'

        if self.slidesInProgress > 0:
            if event == 'mino/doc/start':
                linesBefore = self.functionFactory(issuer)[0]
                self.str += '\n'.join([(' '*4*self.indent + x) for x in linesBefore]) + '\n'
                self.indent += 1
            elif event == 'mino/doc/stop':
                self.indent -= 1
                linesAfter = self.functionFactory(issuer)[1]
                self.str += '\n'.join([(' '*4*self.indent + x) for x in linesAfter]) + '\n'
        
        if issuer.extraParams:
            _type = issuer.extraParams.all.get('type')
            if (_type == 'summary') and (event == 'mino/doc/stop'):
                self.slidesInProgress -= 1
                self.str += '</section>'



