import os, re

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
        return self.html(['<br>'])
        
    def mdTitle(self, issuer):
        before =    [   '<h%d>' % (issuer.indent()+1),
                        '    %s' % self.htmlReplaceInline(issuer.title),
                        '</h%d>' % (issuer.indent()+1),
                    ]
        return (before, [])
        
    def mdDocumentTitle(self, issuer):
        return (['<!-- <doc_title> -->'], ['<!-- </doc_title> -->'])
        
    def mdTextLine(self, issuer):
        before =    [   '<p>',
                        '    %s' % self.htmlReplaceInline(issuer.text)
                    ]
        after =     ['</p>']
        return (before, after)
    
    def mdListItem(self, issuer):
        before =    ['<li>',
                     '    %s' % self.htmlReplaceInline(issuer.text)]
        after =     ['</li>']
        return (before, after)
        
    def mdOrderedList(self, issuer):
        before =    ['<ol>' ]
        after =     ['</ol>']
        return (before, after)
    def mdOrderedListItem(self, issuer):
        return self.mdListItem(issuer)
        
    def mdUnorderedList(self, issuer):
        before =    ['<ul>' ]
        after =     ['</ul>']
        return (before, after)        
    def mdUnorderedListItem(self, issuer):
        return self.mdListItem(issuer)
        
    def mdTable(self, issuer):
        before =    ['<table %s>' % issuer.getExtraParams()]
        after =     ['</table>']
        return (before, after)
    
    def mdTableLine(self, issuer):
        before =    ['<tr>']
        for c in issuer.elements:
            before.append('    <td> %s </td>' % self.htmlReplaceInline(c.strip()))
        after =     ['</tr>']
        return (before, after)
    
    def mdBlocOfCode(self, issuer):
        # See for using http://prismjs.com/index.html
        return ([highlight(issuer.text, get_lexer_by_name(issuer.lang), HtmlFormatter(noclasses=True))], [])
    
    def mdPlugin(self, issuer):
        before =    [   '<p>',
                        issuer.output.getvalue().replace('\n', '<br/>'),
                    ]
        after =    ['</p>']
        return (before, after)
    
    def mdLink(self, issuer):
        before =    [   '<p>',  
                        '    <a href="%s">%s</a>' % (issuer.url, self.htmlReplaceInline(issuer.caption)),
                    ]
        after =     [   '</p>']
        return (before, after)
    
    def mdImage(self, issuer):
        before =    [   '<figure>', 
                        '   <img src="%s" alt="missing" %s/>' % (issuer.url, issuer.getExtraParams()),
                        '   <figcaption>%s</figcaption>' % self.htmlReplaceInline(issuer.caption),
                    ]
        after =     [   '</figure>' ]
        return (before, after)

    
    def functionFactory(self, name):
        if name == 'rootDoc':
            return self.mdRootDoc
        elif name == 'Empty line':
            return self.mdEmptyLine
        elif name == 'Document title':
            return self.mdDocumentTitle
        elif name == 'Title':
            return self.mdTitle
        elif name == 'Text line':
            return self.mdTextLine
            
        elif name == 'Ordered list':
            return self.mdOrderedList
        elif name == 'Ordered list item':
            return self.mdListItem
            
        elif name == 'Unordered list':
            return self.mdUnorderedList
        elif name == 'Unordered list item':
            return self.mdListItem
            
        elif name == 'Table':
            return self.mdTable
        elif name == 'Table line':
            return self.mdTableLine
        elif name == 'Bloc of code':
            return self.mdBlocOfCode
        elif name == 'Plugin':
            return self.mdPlugin
        elif name == 'Link':
            return self.mdLink
        elif name == 'Image':
            return self.mdImage
        else:
            raise Exception('Unknown element [%s]' % name)
    
    def update(self, issuer, event, message):
        if event == 'mino/doc/start':
            linesBefore = self.functionFactory(issuer.name)(issuer)[0]
            self.str += '\n'.join([(' '*4*self.indent + x) for x in linesBefore]) + '\n'
            self.indent += 1
        elif event == 'mino/doc/stop':
            self.indent -= 1
            linesAfter = self.functionFactory(issuer.name)(issuer)[1]
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

    def toFile(self, fileName):
        weasyprint.HTML(string=self.str, base_url=os.path.abspath(__file__)).write_pdf(target=fileName)
    
    
