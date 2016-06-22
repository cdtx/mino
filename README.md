_This README.md is itself a demo, as it's generated automatically from mino ;-)_

## Intro
_mino_ is a custom markdown syntax for writing documentation, notes, memos.
-  It's purely text based, so:
  -  Doesn't requires heavy software for writing
  -  Allows managing revisions as usual with git or others tools.

-  _mino_ is indentation based so documents can even be read from the text editor without formating

-  It supports mixing python code and doc, so the document can be dynamically fed at runtime
-  It supports various plugins
-  It's independant from any output format. So one input can generate several outputs (complete pdf paper and summary slides for example)

### Why Mino ?
Because _mino_ Is Not Office ;-)

## How to write MINO

### MINO Tags
-  Document title
Example :
```text
My doc title
============

```

-  Chapter title
The nested level is based on the element indentation
```text
# Chaper title

```

-  Simple text
As simple as it looks.
-  Unordered list
Example :
```text
- one
- two
- three

```

-  Ordered list
The numbering has no actual impact
```text
1. one
1. two
1. three

```

-  Table
Example :
```text
| x | y |
| 1 | 1 |
| 2 | 4 |
| 3 | 9 |

```

-  Bloc of code
Example :
```text
` ` ` the-language-name (cpp, python, javascript, text, ...)
    #include <xxx>
    ...
` ` `

```

-  Link
Example :
```text
!(www.google.fr)(Visit Google)

```

-  Image
Example :
```text
!!(https://i.ytimg.com/vi/oM1EVAYahFE/maxresdefault.jpg)(Visit me)

```

-  Plugin invokation
Example :
```text
_{ python
    x = 3 + 3
}_
...
_{ python
    print 'x = ', x 
}_

```


## MINO plugins
Documentation coming soon...

## Observability
Documentation coming soon...

### Output formats
-  html

-  Presentation slides, thanks to reveal.js

## Filtering
Documentation coming soon...

## Dependencies
 Name  |  Usage 
--- | ---
 pygments  |  source code syntax coloring 
 Reveal.js  |  slide presentation output 
 plantuml python package  |  plantuml plugin 
 pydot2 python package, and graphviz installed  |  for graphviz plugin 
 weasyprint python package  |  pdf output 

<<<<<<< Temporary merge branch 1
- weasyprint (for pdf output)
- pygments (for source syntax coloring)
- Reveal.js
- plantuml python package (for plantuml plugin)
- pydot2 python package, and graphviz installed (for graphviz plugin)
- aafigure for ascii art drawing
=======
>>>>>>> Temporary merge branch 2
