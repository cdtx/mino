import re
from aafigure import render

def run(content, output, globals=None, locals=None):
    # http://docutils.sourceforge.net/sandbox/aafigure/README.txt
    options = {'format':'svg', 'proportional':True, 'scale':0.9}
    # SVG is better quality
    content = render(input=unicode(content), options=options)[1].getvalue().replace(r'\n', r'\r\n')

    # Remove the annoying xml header (not sure the best way to do this)
    content = re.sub(r'^.*?(?=<svg)', r'', content, 0, re.DOTALL|re.MULTILINE)
    locals['self'].append(globals['mdTextLine'](content=content, inline=False))
