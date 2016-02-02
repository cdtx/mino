#!/usr/bin/env python
from cdtx.mino import parser, observers

if __name__ == '__main__':
    doc = parser.load('README.mino')
    html = observers.HtmlDocObserver(localRessources=True)
    md = observers.MarkdownObserver()
    doc.addObserver(html)
    doc.addObserver(md)
    doc.addObserver(observers.DumbObserver())
    doc.run()

    md.toFile('README.md')
    html.toFile('index.html')



