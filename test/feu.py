#!/usr/bin/env python
from cdtx.mino import parser, observers
from jinja2 import Environment, PackageLoader

if __name__ == '__main__':
    env = Environment(loader=PackageLoader('cdtx.mino', 'styles/default'))
    basic = env.get_template('basic.html')
    reveal = env.get_template('reveal.html')

    doc = parser.load('test.mino')

    html = observers.HtmlObserver()
    slides = observers.HtmlRevealObserver()
    doc.addObserver(html)
    doc.addObserver(slides)
    doc.run()

    result = basic.render(content=html.str)
    with open('basic.html', 'w') as output:
        output.write(result)

    result = reveal.render(content=slides.str)
    with open('slides.html', 'w') as output:
        output.write(result)


