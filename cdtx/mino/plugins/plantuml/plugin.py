import re
import plantuml
import urllib

def run(content, output, globals=None, locals=None):
    url = plantuml.PlantUML().get_url(content)
    # SVG is better quality
    url = re.sub(r'http://www.plantuml.com/plantuml/img/', r'http://www.plantuml.com/plantuml/svg/', url)
    # Get the content at this url
    content = urllib.urlopen(url).read()

    # Remove the annoying xml header (not sure the best way to do this)
    content = re.sub(r'^.*?<svg', r'<svg', content, 0, re.DOTALL|re.MULTILINE)
    locals['self'].append(globals['mdTextLine'](content=content, inline=False))
