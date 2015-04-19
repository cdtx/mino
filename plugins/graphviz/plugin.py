import pydot
import re

def run(content, output, globals=None, locals=None):
    strSVG = pydot.graph_from_dot_data(content)

    # Remove the annoying DTD url (not sure the best way to do this)
    s = strSVG.create_svg()
    s = re.sub(r'^.*?(?=<svg)', r'', s, 0, re.DOTALL|re.MULTILINE)
    locals['self'].append(globals['mdTextLine'](content=s))
