#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, re, io
import imp, traceback

from patterns import Borg


class subject(object):
    def __init__(self):
        self.observers = []
        
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

# def addObserver(obs):
#     subject().addObserver(obs)
# 
# def log(issuer=None, event='', message=''):
#     subject().update(issuer, event, message)

    
class mdElement:
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            ========   ================= 
             name       default value
            ========   =================
             indent     ''
             extra      None
            ========   =================
        '''
        for (p, d) in(  
                        ('indent', ''),
                        ('extra', None),
                    ):
            setattr(self, p, kwargs.get(p, d))

        # Observability
        self.subject = subject()

        self.id = None
        self.opened = False
        self.childs = []
        
        self.extraParams = None
        self.groupExtraParams = None
        self.extractExtraParams()
        
        self.indentSize = 4

        self.acceptList = []
        self.log('mino/parser/info', 'Created element [%s]'%type(self))
        
    def addObserver(self, obs):
        self.subject.addObserver(obs)
        for c in self.childs:
            c.addObserver(obs)

    def log(self, event='', message=''):
        self.subject.update(self, event, message)

    def extractExtraParams(self):
        # If extraParam have been found on the same line, process it now
        if self.extra:
            self.extraParams = mdExtraParams(content=self.extra)

    def accept(self, elem):
        if self.opened:
            if isinstance(elem, mdEmptyLine):
                return True
            else:
                if self.acceptList != []:
                    if elem.__class__ in self.acceptList:
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
                
    def spread(self, elem):
        if isinstance(elem, mdEmptyLine):
            if self.childs != [] and self.childs[-1].accept(elem):
                self.childs[-1].spread(elem)
            else:
                self.merge(elem)
        else:
            # Elem destination is deeper in the tree
            if elem._indent() > self._indent():
                # Elem destination is just after this node
                if elem._indent() == self._indent() + 1:
                    # If there are already childs and the last one absorb this last element
                    if self.childs != [] and self.childs[-1].accept(elem):
                        # Merge the nodes
                        self.childs[-1].merge(elem)
                    else:
                        # Create the node a brother
                        self.childs.append(elem)
                else:
                    # append elem at a level under 
                    self.childs[-1].spread(elem)
            
    def append(self, elem):
        self.childs.append(elem)
                        
    def _indent(self):
        return len(self.indent) / self.indentSize
    
    def merge(self, elem):
        pass
    
    def doc(self):
        self.log('mino/doc/start')
        for x in self.childs:
            x.doc()
        self.log('mino/doc/stop')

class mdRootDoc(mdElement):
    def __init__(self, **kwargs):
        mdElement.__init__(self, **kwargs)
        self.pending = {}
                
    def _indent(self):
        return -1
        
    def spread(self, elem):
        if self.applyGroupExtraParams(elem):
            mdElement.spread(self, elem)
            
    def applyGroupExtraParams(self, elem):
        if isinstance(elem, mdExtraParams):
            self.pending['Group extra params'] = elem
            return False
        else:
            if self.pending.get('Group extra params'):
                elem.groupExtraParams = self.pending.get('Group extra params')
                self.pending.pop('Group extra params', 0)
            return True

class mdExtraParams(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))

        mdElement.__init__(self, **kwargs)
                
        self.all = {}
        for x in self.content.replace('\n', ' ').split(','):
            m = re.match(r'(.+?)=(.*)', x.strip())
            if m:
                self.all[m.groups()[0].strip()] = m.groups()[1].strip()

    def __item__(self, key):
        return self.all[key]
 
class mdEmptyLine(mdElement):
    def __init__(self, **kwargs):
        mdElement.__init__(self, **kwargs)
        
class mdTitle(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))

        mdElement.__init__(self, **kwargs)
               
        self.content = self.content.strip()
        self.title = self.content

class mdDocumentTitle(mdTitle):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        mdTitle.__init__(self, **kwargs)

class mdTextLine(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
             inline     True
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                        ('inline', True),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)

        self.opened = True
        self.acceptList = [mdTextLine, mdEmptyLine]
        
        self.text = self.content.strip()

    def merge(self, elem):
        if isinstance(elem, mdTextLine):
            self.text += '\n'+elem.text
        elif isinstance(elem, mdEmptyLine):
            self.opened = False
        
class mdList(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = True
        self.acceptList = [self.__class__]

        self.childs = [self.newItem(**kwargs)]
           
    def extractExtraParams(self):
        # If inline extra params are found here, there are for the listItem, not the list
        pass

    # def accept(self, elem):
    #     return (isinstance(elem, self.__class__) or (self.childs[-1].accept(elem)))
        
    def spread(self, elem):
        return self.childs[-1].spread(elem)
        
    def merge(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            self.childs.append(self.newItem(content=elem.content, indent=elem.indent, extra=elem.extra))
           
    def newItem(self, **kwargs):
        pass

class mdListItem(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = True

               
        self.text = self.content.strip()

    def spread(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            mdElement.spread(self, elem)
        
class mdOrderedList(mdList):
    def __init__(self, **kwargs):
        mdList.__init__(self, **kwargs)
                
    def newItem(self, **kwargs):
        return mdOrderedListItem(**kwargs)
    
class mdOrderedListItem(mdListItem):
    def __init__(self, **kwargs):
        mdListItem.__init__(self, **kwargs)
        
class mdUnorderedList(mdList):
    def __init__(self, **kwargs):
        mdList.__init__(self, **kwargs)
        
    def newItem(self, **kwargs):
        return mdUnorderedListItem(**kwargs)
    
class mdUnorderedListItem(mdListItem):
    def __init__(self, **kwargs):
        mdListItem.__init__(self, **kwargs)

    
class mdTable(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = True
        self.acceptList = [self.__class__]

        self.childs = [mdTableLine(**kwargs)]

    def extractExtraParams(self):
        # If there are inline extraparams, there are for the line, not the table
        pass

    # def accept(self, elem):
    #     return (isinstance(elem, self.__class__) or (self.childs[-1].accept(elem)))
            
    def spread(self, elem):
        return mdElement.spread(self, elem)
            
    def merge(self, elem):
        if isinstance(elem, mdTable):
            self.childs.append(mdTableLine(content=elem.content))
        elif isinstance(elem, mdEmptyLine):
            self.opened = False
    
class mdTableLine(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = True
               
        self.elements = self.content.strip().split('|')[1:-1]

    def spread(self, elem):
        if isinstance(elem, mdEmptyLine):
            self.opened = False
        else:
            mdElement.spread(self, elem)
    

class mdBlocOfCode(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             lang       'text'
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('lang', 'text'),
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = False
        
        self.lang = self.lang.strip()
        self.text = '\n'.join(x[(self._indent() + 1) * self.indentSize:] for x in self.content.split('\n'))


class mdPlugin(mdElement):
    output = io.StringIO()
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             name       'python'
             content    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('name', 'python'),
                        ('content', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = False
        
        self.pluginName = self.name
        
        # Plugin content can be on the same line that the open , or several lines just under the open with indentation
        if self.content.startswith('\r') or self.content.startswith('\n'):
            self.content = '\n'.join(x[(self._indent() + 1) * self.indentSize:] for x in self.content.split('\n'))
        else:
            self.content = self.content
    
        # DEBUG
        self.run()

    def run(self):
        self.output.truncate(0)
        output = self.output
        # If the aim is to execute python, it must be called inside this module so that it has 
        # access to the whole context
        if self.pluginName.lower() == 'python':
            exec(self.content, locals(), globals())
        else:
            self.plugin = imp.load_source('plugin_%s' % self.pluginName, os.path.dirname(os.path.realpath(__file__)) + '/plugins/%s/plugin.py' % self.pluginName)
            self.plugin.run(self.content, self.output, globals(), locals())


class mdLink(mdElement):
    def __init__(self, **kwargs):
        ''' Constructor parameters :
        
            =========  ================= 
             name       default value
            =========  =================
             url        ''
             caption    ''
            =========  =================
        '''
        for (p, d) in(  
                        ('url', ''),
                        ('caption', ''),
                    ):
            setattr(self, p, kwargs.get(p, d))
                
        mdElement.__init__(self, **kwargs)
        self.opened = False


class mdImage(mdLink):
    def __init__(self, **kwargs):
        mdLink.__init__(self, **kwargs)
        
linePatterns = (
    # Regex, flags, description
    # mino elements
    (r'(?P<indent>[\t ]*)\[(?P<content>.*?)\]\r?(\n|$)', re.IGNORECASE | re.DOTALL, mdExtraParams),
    (r'(?P<indent>)(?P<content>.*)\r?\n=+[\t ]*\r?(\n|$)', re.IGNORECASE, mdDocumentTitle),
    (r'(?P<indent>[\t ]*)#(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdTitle),
    (r'(?P<indent>[\t ]*)-(?!-)(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdUnorderedList),
    (r'(?P<indent>[\t ]*)\d+\.(?P<content>.*?)(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdOrderedList),
    (r'(?P<indent>[\t ]*)(?P<content>\|.*?)(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdTable),
    (r'(?P<indent>[\t ]*)```[\t ]*(?P<lang>.*?)\r?\n(?P<content>.*?)```[\t ]*\r?(\n|$)', re.IGNORECASE | re.DOTALL, mdBlocOfCode),
    (r'(?P<indent>[\t ]*)!\((?P<url>.*?)\)\((?P<caption>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdLink),
    (r'(?P<indent>[\t ]*)!!\((?P<url>.*?)\)\((?P<caption>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?(\n|$)', re.IGNORECASE, mdImage),
    # (r'(?P<indent>[\t ]*)!#\((?P<url>.*?)\)[\t ]*(\[(?P<extra>.*?)\])?\r?\n', re.IGNORECASE, 'Include'),
    
    # Plugin
    (r'(?P<indent>[\t ]*)_\{ *(?P<name>\w+)[\t ]*(?P<content>\r?\n?.*?)\}_[\t ]*(\[(?P<extra>.*?)\])?[\t ]*\r?(\n|$)', re.IGNORECASE | re.DOTALL, mdPlugin),
    
    # Decorative lines
    (r'(?P<indent>[\t ]*)(?P<content>\S.*)\r?(\n|$)', re.IGNORECASE, mdTextLine),
    (r'(?P<indent>)([\t ]*)\r?(\n|$)', re.IGNORECASE, mdEmptyLine),
)
    
inlinePatterns = (
    (r'\*\*(.*?)\*\*', re.IGNORECASE, 'bold'),
    (r'(?<!:)//(.*?)(?<!:)//', re.IGNORECASE, 'italic'), # Ensure // aren't part of urls
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
                doc.spread(cls(**res.groupdict()))
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
    from cdtx.mino.observers import DumbObserver, HtmlDocObserver, PdfDocObserver
    
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
        





