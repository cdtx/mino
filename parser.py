#!/usr/bin/env python
import pdb
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

    
class mdElement:
    def __init__(self, inputs={}):
        self.id = None
        self.inputs = inputs
        self.opened = False
        self.childs = []
        
        self.extraParams = None
        self.extractExtraParams()

        
        self.indentSize = 4

        self.acceptList = []
        log(self, 'mino/parser/info', 'Created element [%s]'%type(self))
        
    def extractExtraParams(self):
        # If extraParam have been found on the same line, process it now
        if self.inputs.get('extra'):
            self.extraParams = mdExtraParams({'content': self.inputs['extra']})

    def accept(self, elem):
        if self.opened:
            if isinstance(elem, mdEmptyLine):
                return True
            else:
                if self.acceptList != []:
                    if type(elem) in self.acceptList:
                        return True
                    else:
                        self.opened = False
                        return False
                else:
                    return True
        else:
            if isinstance(elem, mdEmptyLine):
                return True
            else:
                return False
                
    def append(self, elem):
        if isinstance(elem, mdEmptyLine):
            if self.childs != [] and self.childs[-1].accept(elem):
                self.childs[-1].append(elem)
            else:
                self.merge(elem)
        else:
            # Elem destination is deeper in the tree
            if elem.indent() > self.indent():
                # Elem destination is just after this node
                if elem.indent() == self.indent() + 1:
                    # If there are already childs and the last one absorb this last element
                    if self.childs != [] and self.childs[-1].accept(elem):
                        # Merge the nodes
                        self.childs[-1].merge(elem)
                    else:
                        # Create the node a brother
                        self.childs.append(elem)
                else:
                    # append elem at a level under 
                    self.childs[-1].append(elem)
            
                        
    def indent(self):
        if self.inputs == {}:
            return 0
        return len(self.inputs['indent']) / self.indentSize
    
    def merge(self, elem):
        pass
    
    def doc(self):
        log(self, 'mino/doc/start')
        for x in self.childs:
            x.doc()
        log(self, 'mino/doc/stop')

class mdRootDoc(mdElement):
    def __init__(self):
        mdElement.__init__(self)
        self.pending = {}
                
    def indent(self):
        return -1
        
    def append(self, elem):
        if self.applyExtraParams(elem):
            mdElement.append(self, elem)
            
    def applyExtraParams(self, elem):
        if isinstance(elem, mdExtraParams):
            self.pending['Extra params'] = elem
            return False
        else:
            if self.pending.get('Extra params'):
                elem.extraParams = self.pending.get('Extra params')
                self.pending.pop('Extra params', 0)
            return True

class mdExtraParams(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.all = {}
        for x in inputs['content'].replace('\n', ' ').split(','):
            m = re.match(r'(.+?)=(.*)', x.strip())
            if m:
                self.all[m.groups()[0].strip()] = m.groups()[1].strip()

    def __item__(self, key):
        return self.all[key]
 
class mdEmptyLine(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        
class mdTitle(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
               
        self.title = inputs['content']

class mdDocumentTitle(mdTitle):
    def __init__(self, inputs):
        mdTitle.__init__(self, inputs)

class mdTextLine(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = True
        self.acceptList = ['Text line', 'Empty line']
        
        self.text = inputs['content'].strip()

    def merge(self, elem):
        if isinstance(elem, mdTextLine):
            self.text += '\n'+elem.inputs['content'].strip()
        elif isinstance(elem, mdEmptyLine):
            self.opened = False
        
class mdList(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = True

        self.childs = [self.newItem(inputs)]
           
    def extractExtraParams(self):
        # If inline extra params are found here, there are for the listItem, not the list
        pass

    def accept(self, elem):
        return (isinstance(elem, type(self)) or (self.childs[-1].accept(elem)))
        
    def append(self, elem):
        return self.childs[-1].append(elem)
        
    def merge(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            self.childs.append(self.newItem(elem.inputs))
           
    def newItem(self, inputs):
        pass

class mdListItem(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = True
               
        self.text = inputs['content'].strip()

    def append(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            mdElement.append(self, elem)
        
class mdOrderedList(mdList):
    def __init__(self, inputs):
        mdList.__init__(self, inputs)
        self.childItem = 'Ordered list item'
                
    def newItem(self, inputs):
        return mdOrderedListItem(inputs)
    
class mdOrderedListItem(mdListItem):
    def __init__(self, inputs):
        mdListItem.__init__(self, inputs)
        
class mdUnorderedList(mdList):
    def __init__(self, inputs):
        mdList.__init__(self, inputs)
        self.childItem = 'Unordered list item'
        
    def newItem(self, inputs):
        return mdUnorderedListItem(inputs)
    
class mdUnorderedListItem(mdListItem):
    def __init__(self, inputs):
        mdListItem.__init__(self, inputs)

    
class mdTable(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = True

        self.childs = [mdTableLine(inputs)]

    def extractExtraParams(self):
        # If there are inline extraparams, there are for the line, not the table
        pass

    def accept(self, elem):
        return self.childs[-1].accept(elem)
            
    def append(self, elem):
        return mdElement.append(self, elem)
            
    def merge(self, elem):
        if isinstance(elem, mdTable):
            self.childs.append(mdTableLine(elem.inputs))
        elif isinstance(elem, mdEmptyLine):
            self.opened = False
    
    def display(self, pad=0):
        str = ''
        for x in self.childs:
            str += ' '*4*pad + x.display(pad) + '\n'
        return str

class mdTableLine(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = True
               
        self.elements = inputs['content'].strip().split('|')[1:-1]

    def append(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            mdElement.append(self, elem)
        
    def display(self, pad=0):
        return ' | '.join(self.elements)
    
class mdBlocOfCode(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = False
        
        self.lang = inputs['lang'].strip()
        self.text = '\n'.join(x[(self.indent() + 1) * self.indentSize:] for x in inputs['content'].split('\n'))

    def display(self, pad=0):
        return self.text + '\n'

class mdPlugin(mdElement):
    output = io.StringIO()
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = False
        
        self.pluginName = inputs['name']
        
        # Plugin content can be on the same line that the open , or several lines just under the open with indentation
        if self.inputs['content'].startswith('\r') or self.inputs['content'].startswith('\n'):
            self.content = '\n'.join(x[(self.indent() + 1) * self.indentSize:] for x in inputs['content'].split('\n'))
        else:
            self.content = self.inputs['content']

        self.plugin = imp.load_source('plugin_%s' % self.pluginName, os.path.dirname(os.path.realpath(__file__)) + '/plugins/%s/plugin.py' % self.pluginName)
    
    def run(self):
        self.output.truncate(0)
        output = self.output
        # If the aim is to execute python, it must be called inside this module so that it has 
        # access to the whole context
        if self.pluginName.lower() == 'python':
            exec(self.content, locals(), globals())
        else:
            self.plugin.run(self.content, self.output, globals(), locals())

class mdLink(mdElement):
    def __init__(self, inputs):
        mdElement.__init__(self, inputs)
        self.opened = False
            
        self.url = self.inputs['url']
        self.caption = self.inputs['caption']
        
    def display(self, pad=0):
        return '    '*pad + 'link : ' + self.url + '\n'

class mdImage(mdLink):
    def __init__(self, inputs):
        mdLink.__init__(self, inputs)
        
    def display(self, pad=0):
        return '    '*pad + 'Image : ' + self.url + '\n'
        
linePatterns = (
    # Regex, flags, description
    # Markdutr elements
    (r'(?P<indent>[\t ]*)\[(?P<content>.*?)\]\r?\n', re.IGNORECASE | re.DOTALL, mdExtraParams),
    (r'(?P<indent>)(?P<content>.*)\r?\n=+[\t ]*\r?\n', re.IGNORECASE, mdDocumentTitle),
    (r'(?P<indent>[\t ]*)#(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdTitle),
    (r'(?P<indent>[\t ]*)-(?!-)(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdUnorderedList),
    (r'(?P<indent>[\t ]*)\d+\.(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdOrderedList),
    (r'(?P<indent>[\t ]*)(?P<content>\|.*?)(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdTable),
    (r'(?P<indent>[\t ]*)```[\t ]*(?P<lang>.*?)\r?\n(?P<content>.*?)```[\t ]*\r?\n', re.IGNORECASE | re.DOTALL, mdBlocOfCode),
    (r'(?P<indent>[\t ]*)!\((?P<url>.*?)\)\((?P<caption>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdLink),
    (r'(?P<indent>[\t ]*)!!\((?P<url>.*?)\)\((?P<caption>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, mdImage),
    # (r'(?P<indent>[\t ]*)!#\((?P<url>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, 'Include'),
    
    # Plugin
    (r'(?P<indent>[\t ]*)_\{ *(?P<name>\w+)[\t ]*(?P<content>\r?\n?.*?)\}_[\t ]*(\[(?P<extra>.*?)\])?[\t ]*\r?\n', re.IGNORECASE | re.DOTALL, mdPlugin),
    
    # Decorative lines
    (r'(?P<indent>[\t ]*)(?P<content>\S.*)\r?\n', re.IGNORECASE, mdTextLine),
    (r'(?P<indent>)([\t ]*)\r?\n?', re.IGNORECASE, mdEmptyLine),
)
    
inlinePatterns = (
    (r'\*\*(.*?)\*\*', re.IGNORECASE, 'bold'),
    (r'//(.*?)//', re.IGNORECASE, 'italic'),
    (r'__(.*?)__', re.IGNORECASE, 'underlined'),
    (r'--(.*?)--', re.IGNORECASE, 'scratched'),
    (r'!\((.*?)\)\((.*?)\)', re.IGNORECASE, 'link'),
)

def parse(string):
    doc = mdRootDoc()
    while string:
        res = None
        for (pat, opt, cls) in linePatterns:
            res = re.match(pat, string, flags=opt)
            if res:
                doc.append(cls(res.groupdict()))
                break
        if (not res) or (len(res.group()) == 0):
            raise Exception('Parser is stuck :\n' + string)
        string = string[len(res.group()):]
    return doc

def load(fileName):
    with open(fileName, 'r') as file:
        content = file.read()
        return parse(content)

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
        

