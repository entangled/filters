---
title: Entangled
subtitle: Python module
footer: "Johan Hidding -- [Netherlands eScience Center](https://esciencecenter.nl/)"
version: 0.6.1
license: "[Apache 2](https://www.apache.org/licenses/LICENSE-2.0)"
---

``` {.dhall .bootstrap-card-deck}
let Card = ./schema/Card.dhall

in [ Card :: { title = "Literate Programming"
             , text =
                 ''
                 Write prose and code intermixed. This works great for scientific software,
                 tutorials, or any other software.
                 ''
             , link = Some { href = "http://entangled.github.io/"
                           , content = "About Entangled" }
             , image = Some "literate.jpg" }

   , Card :: { title = "Bootstrap"
             , text =
                ''
                Generate pretty Bootstrap websites. Your Markdown is translated to a snappy responsive
                website.
                ''
             , link = Some { href = "https://getbootstrap.com/", content = "About Bootstrap" }
             , image = Some "bootstrap.jpg" }

   , Card :: { title = "Jupyter"
             , text =
                ''
                Use Jupyter to evaluate code snippets on the fly. Great for writing documentation.
                ''
             , link = Some { href = "https://jupyter.org/", content = "About Jupyter" }
             , image = Some "jupiter.jpg" } ]
```

This is a set of Pandoc filters for literate programming written in Python. These filters are part of Entangled. They constitute a complete workflow for literate programming on them selves, but it is advised to use them in conjunction with Entangled. 

In particular, while you can tangle source files with the `entangled.tangle` Python module, it is much more convenient to use the `entangled` executable, which automatically tangles files upon saving the Markdown files, and more importantly, also does the reverse, keeping your files continuously in sync.

This module also acts as a test-bed and environment for rapid prototyping of features that may end up in the main (Haskell based part of) Entangled distribution. Currently we have:

- `tangle`, extract source files from embedded code blocks in Markdown.
- `annotate`, add name tags to code blocks.
- `doctest`, run documentation tests through Jupyter.
* `bootstrap`, expand some elements into Bootstrap widgets.

## Version

``` {.python file=pandoc_entangled/__init__.py}
from importlib import metadata
__version__ = metadata.version("pandoc-entangled")
```

## Demo

- This page uses the very same pandoc filters it implements. On the top you see a rendering of a Bootstrap card-deck. This deck is generated from a code block containing the Dhall description of the content.

- Sometimes, when you write literate code it cannot be avoided that you have to implement some boring stuff that doesn't warrant a detailed explanation. In this case you can collapse a code block behind a button.

``` {.python .bootstrap-fold #compute-pi}
import numpy as np

def compute_pi(sample_size):
    points = np.random.uniform(0, 1, size=[sample_size, 2])
    within_circle = np.count_nonzero((points**2).sum(axis=1) <= 1.0)
    return 4 * within_circle / sample_size
```

- If you're documenting a library you may want to have code blocks evaluated inline.

``` {.python .eval #compute-pi}
print("π ≈ {}".format(compute_pi(1000000)))
```


