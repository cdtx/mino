import re
import plantuml

def run(content, output, globals=None, locals=None):
    # Add each line as a standard text line
    for line in content.split('\n'):
        locals['self'].append(globals['mdTextLine'](content=line))

