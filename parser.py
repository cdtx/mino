#!/usr/bin/env python
import sys, os, re, io
import imp, traceback

# from xhtml2pdf import pisa

from patterns import Borg

class subject(Borg):
    def __init__(self):
        Borg.__init__(self)
        if not hasattr(self, 'observers'):
            setattr(self, 'observers', [])
        
    def addObserver(self, obs):
        self.observers.append(obs)
        
    def removeObserver(self, obs):
        if obs in self.observers:
            self.observers.remove(obs)
        
    def update(self, issuer=None, event='', message=''):
        ''' slash based event description, message
            ---------
            mino
                parser
                    info
                    warning
                    error
                doc
                    start
                    stop
        '''
        for obs in self.observers:
            obs.update(issuer, event, message)

def log(issuer=None, event='', message=''):
    subject().update(issuer, event, message)

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
        log(self, 'mino/parser/info', 'Created element [%s]'%name)
        
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
    
    def getExtraParams(self):
        if self.extraParams:
            return ' '.join(['%s="%s"'%(k,d) for k,d in self.extraParams.all.iteritems()])
        else:
            return ''
    
    def doc(self):
        log(self, 'mino/doc/start')
        for x in self.childs:
            x.doc()
        log(self, 'mino/doc/stop')
    
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
        mdElement.__init__(self, 'rootDoc')
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
        
class mdTitle(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
               
        self.title = inputs[1]

class mdDocumentTitle(mdTitle):
    def __init__(self, name, inputs):
        mdTitle.__init__(self, name, inputs)

class mdTextLine(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = True
        self.acceptList = ['Text line', 'Empty line']
        
        self.text = inputs[1].strip()
            
    def merge(self, elem):
        if elem.name == 'Text line':
            self.text += '\n'+elem.inputs[1].strip()
        elif elem.name == 'Empty line':
            self.opened = False
        
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
                
    def display(self, pad=0):
        str = ''
        for x in self.childs:
            str += ' '*4*pad + x.display(pad+1) + '\n'
        return str

class mdListItem(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = True
               
        self.text = inputs[1].strip()

    def append(self, elem):
        if elem.name == 'Empty line':
            self.opened = False
        else:
            mdElement.append(self, elem)
        
    def display(self, pad=0):
        return self.text + mdElement.display(self, pad)
        
class mdOrderedList(mdList):
    def __init__(self, name, inputs):
        mdList.__init__(self, 'Ordered list', inputs)
        self.childItem = 'Ordered list item'
                
    def newItem(self, inputs):
        return mdOrderedListItem(inputs)
    
class mdOrderedListItem(mdListItem):
    def __init__(self, inputs):
        mdListItem.__init__(self, 'Unordered list item', inputs)
        
class mdUnorderedList(mdList):
    def __init__(self, name, inputs):
        mdList.__init__(self, 'Unordered list', inputs)
        self.childItem = 'Unordered list item'
        
    def newItem(self, inputs):
        return mdUnorderedListItem(inputs)
    
class mdUnorderedListItem(mdListItem):
    def __init__(self, inputs):
        mdListItem.__init__(self, 'Ordered list item', inputs)

    
class mdTable(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, 'Table', inputs)
        self.opened = True

        self.childs = [mdTableLine(inputs)]

    def accept(self, elem):
        return self.childs[-1].accept(elem)
            
    def append(self, elem):
        return mdElement.append(self, elem)
            
    def merge(self, elem):
        if elem.name == 'Table':
            self.childs.append(mdTableLine(elem.inputs))
        elif elem.name == 'Empty line':
            self.opened = False
    
    def display(self, pad=0):
        str = ''
        for x in self.childs:
            str += ' '*4*pad + x.display(pad) + '\n'
        return str

class mdTableLine(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, 'Table line', inputs)
        self.opened = True
               
        self.elements = inputs[1].strip().split('|')[1:-1]

    def append(self, elem):
        if elem.name == 'Empty line':
            self.opened = False
        else:
            mdElement.append(self, elem)
        
    def display(self, pad=0):
        return ' | '.join(self.elements)
    
class mdBlocOfCode(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = False
        
        self.lang = inputs[1].strip()
        self.text = '\n'.join(x[(self.indent() + 1) * self.indentSize:] for x in inputs[2].split('\n'))

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
        self.output.truncate(0)
        output = self.output
        if self.pluginName.lower() == 'python':
            exec(self.content, locals(), globals())
        else:
            self.plugin.run(self.content, self.output, globals(), locals())
        
    def display(self, pad=0):
        self.output.truncate(0)
        self.run()
        return 'Plugin execution...'        

class mdLink(mdElement):
    def __init__(self, name, inputs):
        mdElement.__init__(self, name, inputs)
        self.opened = False
            
        self.url = self.inputs[1]
        self.caption = self.inputs[2]
        
    def display(self, pad=0):
        return '    '*pad + 'link : ' + self.url + '\n'

class mdImage(mdLink):
    def __init__(self, name, inputs):
        mdLink.__init__(self, name, inputs)
        
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
    from mino.observers import DumbObserver, HtmlDocObserver, PdfDocObserver
    
    subject().addObserver(DumbObserver())
    html = HtmlDocObserver()
    pdf = PdfDocObserver()
    subject().addObserver(html)
    subject().addObserver(pdf)
    
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]):
            doc = load(sys.argv[1])
            # Run a doc loop
            doc.doc()
            html.toFile('index.html')
            pdf.toFile('out.pdf')
        else:
            usage()
    else:
        usage()
        

