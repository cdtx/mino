import re
import plantuml

def run(content, output, globals=None, locals=None):
    url = plantuml.PlantUML().get_url(content)
    # SVG is better quality
    url = re.sub(r'http://www.plantuml.com/plantuml/img/', r'http://www.plantuml.com/plantuml/png/', url)
    locals['self'].append(globals['mdImage'](url=url))
