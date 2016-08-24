#!/usr/bin/env python
from cdtx.mino import parser, observers

if __name__ == '__main__':
    doc = parser.load('README.mino')

    md = observers.MarkdownObserver()
    doc.addObserver(md)
    doc.run()

    md.toFile('README.md')



