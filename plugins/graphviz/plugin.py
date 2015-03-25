import pydot

def run(content, output, globals=None, locals=None):
    strSVG = pydot.graph_from_dot_data(content).create_svg()
    locals['self'].append(globals['mdTextLine'](content=strSVG))
