#!/usr/bin/env python


import sys, os, re, io
import imp, traceback

# from xhtml2pdf import pisa
import weasyprint
from pygments import highlight
from pygments.lexers import get_lexer_by_name 
from pygments.formatters import HtmlFormatter
        
linePatterns = (
    # Regex, flags, description
    # Markdutr elements
    (r'([\t ]*)\[(.*?)\]\r?\n', re.IGNORECASE, 'Extra params'),
    (r'()(.*)\r?\n=+[\t ]*\r?\n', re.IGNORECASE, 'Document title'),
    (r'([\t ]*)#(.*?)(\[.*?\])?\r?\n', re.IGNORECASE, 'Title'),
    (r'([\t ]*)-(?!-)(.*?)(\[.*?\])?\r?\n', re.IGNORECASE, 'Unordered list item'),
    (r'([\t ]*)\d+\.(.*?)(\[.*?\])?\r?\n', re.IGNORECASE, 'Ordered list item'),
    (r'([\t ]*)(\|.*?)(\[.*?\])?\r?\n', re.IGNORECASE, 'Table line'),
    (r'([\t ]*)```[\t ]*(.*?)\r?\n(.*?)```[\t ]*\r?\n', re.IGNORECASE | re.DOTALL, 'Bloc of code'),
    (r'([\t ]*)!\((.*?)\)\((.*?)\)[\t ]*(\[.*?\])?\r?\n', re.IGNORECASE, 'Link'),
    (r'([\t ]*)!!\((.*?)\)\((.*?)\)[\t ]*(\[.*?\])?\r?\n', re.IGNORECASE, 'Image'),
    (r'([\t ]*)!#\((.*?)\)[\t ]*(\[.*?\])?\r?\n', re.IGNORECASE, 'Include'),
    
    # Plugin
    (r'([\t ]*)_\{(\w+)[\t ]*(\r?\n?.*?)\}_[\t ]*(\[.*?\])?[\t ]*\r?\n', re.IGNORECASE | re.DOTALL, 'Plugin'),
    
    # Decorative lines
    (r'([\t ]*)(\S.*)\r?\n', re.IGNORECASE, 'Text line'),
    (r'()([\t ]*)\r?\n?', re.IGNORECASE, 'Empty line'),
)
    
inlinePatterns = (
    (r'\*\*(.*?)\*\*', re.IGNORECASE, 'bold'),
    (r'//(.*?)//', re.IGNORECASE, 'italic'),
    (r'__(.*?)__', re.IGNORECASE, 'underlined'),
    (r'--(.*?)--', re.IGNORECASE, 'scratched'),
    (r'!\((.*?)\)\((.*?)\)', re.IGNORECASE, 'link'),
)
    
    
class ElementsFactory:
    def get(self, name, *args):
        if name == 'Extra params':
            return mdExtraParams(name, *args)
        elif name == 'rootDoc':
            return mdRootDoc()
        elif name == 'Empty line':
            return mdEmptyLine(name, *args)

        elif name == 'Document title':
            return mdDocumentTitle(name, *args)
        elif name == 'Title':
            return mdTitle(name, *args)
        elif name == 'Title':
            return mdTitle(name, *args)
        elif name == 'Text line':
            return mdTextLine(name, *args)
        elif name == 'Unordered list item':
            return mdUnorderedList(name, *args)
        elif name == 'Ordered list item':
            return mdOrderedList(name, *args)
        elif name == 'Table line':
            return mdTable(name, *args)
        elif name == 'Bloc of code':
            return mdBlocOfCode(name, *args)
        elif name == 'Plugin':
            return mdPlugin(name, *args)
        elif name == 'Link':
            return mdLink(name, *args)
        elif name == 'Image':
            return mdImage(name, *args)
        else:
            return mdElement('mdElement', *args)

class mdElement:
    def __init__(self, name, inputs=[]):
        self.id = None
        self.name = name
        self.inputs = inputs
        self.opened = False
        self.childs = []
        
        self.extraParams = None
        
        self.indentSize = 4

        self.acceptList = []
        
    def accept(self, elem):
        if self.opened:
            if elem.name == 'Empty line':
                return True
            else:
                if self.acceptList != []:
                    if elem.name in self.acceptList:
                        return True
                    else:
                        self.opened = False
                        return False
                else:
                    return True
        else:
            if elem.name == 'Empty line':
                return True
            else:
                return False
                
    def append(self, elem):
        if elem.name == 'Empty line':
            if self.childs != [] and self.childs[-1].accept(elem):
                self.childs[-1].append(elem)
            else:
                self.merge(elem)
        else:
            # Elem destination is deeper in the tree
            if elem.indent() > self.indent():
                # Elem destination is just after this node
                if elem.indent() == self.indent() + 1:
                    if self.childs != [] and self.childs[-1].accept(elem):
                        # Merge the nodes
                        self.childs[-1].merge(elem)
                    else:
                        # Create the node a brother
                        self.childs.append(elem)
                else:
                    self.childs[-1].append(elem)
            
                        
    def indent(self):
        if self.inputs == []:
            return 0
        return len(self.inputs[0]) / self.indentSize
    
    def merge(self, elem):
        pass
    
    def html(self, pad=0, linesBefore=[], linesAfter=[]):
        str = '\n'.join([(' '*4*pad + x) for x in linesBefore]) + '\n'
        for c in self.childs:
            str += c.html(pad+1) + '\n'
        str += '\n' + '\n'.join([(' '*4*pad + x) for x in linesAfter])
        return str
        
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
    
    def getExtraParams(self):
        if self.extraParams:
            return ' '.join(['%s="%s"'%(k,d) for k,d in self.extraParams.all.iteritems()])
        else:
            return ''
    
    def display(self, pad=0):
        str = ''
        str += '    '*pad + self.name
        if self.id:
            str += ' - %s' % self.id
        str += '\n'
        for x in self.childs:
            str += x.display(pad+1)
        return str

class mdRootDoc(mdElement):
    def __init__(self):
        mdElement.__init__(self, '__root__')
        self.style = 'default'        
        self.pending = {}
                
    def indent(self):
        return -1
        
    def append(self, elem):
        if self.processExtraParams(elem):
            mdElement.append(self, elem)
            
    def processExtraParams(self, elem):
        if elem.name == 'Extra params':
            self.pending['Extra params'] = elem
            return False
        else:
            if self.pending.get('Extra params'):
                elem.extraParams = self.pending.get('Extra params')
                self.pending.pop('Extra params', 0)
            return True
        
    def html(self, fileName=None, pad=0):
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
        
        html = mdElement.html(self, pad, before, after)
        
        if fileName:
            with open(fileName, 'w') as file:
                file.write(html)
        
        return html
        
    def pdf(self, fileName=None):
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
        
        html = mdElement.html(self, 0, before, after)
        
        if fileName:
            weasyprint.HTML(string=html, base_url=os.path.abspath(__file__)).write_pdf(target=fileName)
        return html
        
        
        

class mdExtraParams(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.all = {}
        for x in inputs[1].split(','):
            m = re.match(r'(.+?)=(.*)', x.strip())
            if m:
                self.all[m.groups()[0].strip()] = m.groups()[1].strip()
 
class mdEmptyLine(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        
    def html(self, pad=0):
        return mdElement.html(self, pad, ['<br>'])

class mdTitle(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
               
        self.title = inputs[1]
        
    def html(self, pad=0):
        open = '<h%d>'%(self.indent()+1)
        close = '</h%d>'%(self.indent()+1)
    
        return mdElement.html(self, pad, [open + self.htmlReplaceInline(self.title) + close])

class mdDocumentTitle(mdTitle):
    def __init__(self, name, inputs):
        mdTitle.__init__(self, name, inputs)
                
    def html(self, pad=0):
        return mdElement.html(self, pad, ['<!-- <doc_title> -->'], ['<!-- </doc_title> -->'])

class mdTextLine(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = True
        self.acceptList = ['Text line', 'Empty line']
        
        self.htmlOpenClose = 'p'
        
        self.text = inputs[1].strip()
            
    def merge(self, elem):
        if elem.name == 'Text line':
            self.text += '\n'+elem.inputs[1].strip()
        elif elem.name == 'Empty line':
            self.opened = False
        
    def html(self, pad=0):
        before =    [   '<p>',
                        '    %s' % self.htmlReplaceInline(self.text)
                    ]
        after =     ['</p>']
    
        return mdElement.html(self, pad, before, after)
        
    def display(self, pad=0):
        return '    '*pad + self.text + '\n'
        
class mdList(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = True

        self.childs = [mdUnorderedListItem(inputs)]
           
    def accept(self, elem):
        return self.childs[-1].accept(elem)
        
    def append(self, elem):
        return self.childs[-1].append(elem)
        
    def merge(self, elem):
        if elem.name == self.childItem:
            self.childs.append(self.newItem(elem.inputs))
        elif elem.name == 'Empty line':
            self.opened = False

           
    def newItem(self, inputs):
        pass

    def html(self, pad=0):
        before =    [   '<' + self.htmlOpenClose + '>' ]
        after =     ['</' + self.htmlOpenClose + '>']
    
        return mdElement.html(self, pad, before, after)
                
    def display(self, pad=0):
        str = ''
        for x in self.childs:
            str += ' '*4*pad + x.display(pad+1) + '\n'
        return str

class mdListItem(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, 'mdUnorderedListItem', inputs)
        self.opened = True
               
        self.text = inputs[1].strip()
        
        self.htmlOpenClose = 'li'

    def append(self, elem):
        if elem.name == 'Empty line':
            self.opened = False
        else:
            mdElement.append(self, elem)
        
    def html(self, pad=0):
        before =    ['<li>',
                     '    %s' % self.htmlReplaceInline(self.text)]
        after =     ['</li>']
    
        return mdElement.html(self, pad, before, after)
        
    def display(self, pad=0):
        return self.text + mdElement.display(self, pad)
        
class mdOrderedList(mdList):
    def __init__(self, name, inputs):
        mdList.__init__(self, name, inputs)
        self.childItem = "Ordered list item"
        
        self.htmlOpenClose = 'ol'
        
    def newItem(self, inputs):
        return mdOrderedListItem(inputs)
    
class mdOrderedListItem(mdListItem):
    pass
        
class mdUnorderedList(mdList):
    def __init__(self, name, inputs):
        mdList.__init__(self, name, inputs)
        self.childItem = "Unordered list item"
        
        self.htmlOpenClose = 'ul'
        
    def newItem(self, inputs):
        return mdUnorderedListItem(inputs)
    
class mdUnorderedListItem(mdListItem):
    pass

    
class mdTable(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = True

        self.childs = [mdTableLine(inputs)]

    def accept(self, elem):
        return self.childs[-1].accept(elem)
            
    def append(self, elem):
        return mdElement.append(self, elem)
            
    def merge(self, elem):
        if elem.name == 'Table line':
            self.childs.append(mdTableLine(elem.inputs))
        elif elem.name == 'Empty line':
            self.opened = False
            
    def html(self, pad=0):
        return mdElement.html(self, pad, ['<table %s>' % self.getExtraParams()], ['</table>'])

    def display(self, pad=0):
        str = ''
        for x in self.childs:
            str += ' '*4*pad + x.display(pad) + '\n'
        return str

class mdTableLine(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, 'mdTableLine', inputs)
        self.opened = True
               
        self.elements = inputs[1].strip().split('|')[1:-1]

    def append(self, elem):
        if elem.name == 'Empty line':
            self.opened = False
        else:
            mdElement.append(self, elem)
        
    def display(self, pad=0):
        return ' | '.join(self.elements)
        
    def html(self, pad=0):
        before =    ['<tr>']
        for c in self.elements:
            before.append('    <td> %s </td>' % self.htmlReplaceInline(c.strip()))
        after =     ['</tr>']
        return mdElement.html(self, pad, before, after)
    
class mdBlocOfCode(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = False
        
        self.lang = inputs[1].strip()
        self.text = '\n'.join(x[(self.indent() + 1) * self.indentSize:] for x in inputs[2].split('\n'))
                
    def html(self, pad=0):
        # See for using http://prismjs.com/index.html
        return highlight(self.text, get_lexer_by_name(self.lang), HtmlFormatter(noclasses=True))
        # return ' '*4*pad + '<p class="%s">'%self.lang + self.text.replace('\n', '<br/>') + '</p>'
        
    def display(self, pad=0):
        return self.text + '\n'

class mdPlugin(mdElement):
    output = io.StringIO()
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = False
        
        self.pluginName = inputs[1]
        
        # Plugin content can be on the same line that the open , or several lines just under the open with indentation
        if self.inputs[2].startswith('\r') or self.inputs[2].startswith('\n'):
            self.content = '\n'.join(x[(self.indent() + 1) * self.indentSize:] for x in inputs[2].split('\n'))
        else:
            self.content = self.inputs[2]

        self.plugin = imp.load_source('plugin_%s' % self.pluginName, os.path.dirname(os.path.realpath(__file__)) + '/plugins/%s/plugin.py' % self.pluginName)
    
    def run(self):
        output = self.output
        if self.pluginName.lower() == 'python':
            exec(self.content, locals(), globals())
        else:
            self.plugin.run(self.content, self.output, globals(), locals())
        
    def display(self, pad=0):
        self.output.truncate(0)
        self.run()
        return 'Plugin execution...'
        
    def html(self, pad=0):
        self.output.truncate(0)
        try:
            self.run()
            return mdElement.html(self, pad, [  '<p>', 
                                                self.output.getvalue().replace('\n', '<br/>'),
                                                '</p>'
                                             ])
            
        except:
            print traceback.print_exc()
            return mdElement.html(self, pad, [  '<warning>', 
                                                '    Plugin execution have failed', 
                                                '</warning>'
                                             ])
        

class mdLink(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = False
            
        self.url = self.inputs[1]
        self.caption = self.inputs[2]
        
    def html(self, pad=0):
        before =    [   '<p>',  
                        '    <a href="%s">%s</a>' % (self.url, self.htmlReplaceInline(self.caption)),
                        '</p>'
                    ]
        return mdElement.html(self, pad, before)
        
    def display(self, pad=0):
        return '    '*pad + 'link : ' + self.url + '\n'

class mdImage(mdLink):
    def __init__(self, name, inputs):
        mdLink.__init__(self, name, inputs)
    
    def html(self, pad=0):
        before =    [   '<figure>', 
                        '   <img src="%s" alt="missing" %s/>' % (self.url, self.getExtraParams()),
                        '   <figcaption>%s</figcaption>' % self.htmlReplaceInline(self.caption),
                        '</figure>'
                    ]
        return mdElement.html(self, pad, before)

        
    def display(self, pad=0):
        return '    '*pad + 'Image : ' + self.url + '\n'
        
def load(fileName):
    with open(fileName, 'r') as file:
        content = file.read()
        doc = ElementsFactory().get('rootDoc')
        while content:
            res = None
            for (pat, opt, type) in linePatterns:
                res = re.match(pat, content, flags=opt)
                if res:
                    # print 'Found [%s] -> ' % type, res.groups()
                    doc.append(ElementsFactory().get(type, res.groups()))
                    break
            if (not res) or (len(res.group()) == 0):
                raise Exception('Parser is stuck :\n' + content)
            content = content[len(res.group()):]

    return doc
            
def usage():
    print '''mino.py FILE'''

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]):
            doc = load(sys.argv[1])
            # print doc.display()
            # doc.html('index.html')
            # doc.pdf('output.pdf')
        else:
            usage()
    else:
        usage()
        

