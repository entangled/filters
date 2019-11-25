---
title: Running doc-tests
---

This Pandoc filter runs doc-tests from Python. All this requires is a REPL to be available: a REPL reads commands from standard input and gives output on standard output. Cells with the same identifier are passed through a REPL in a single session. If a cell is marked with a `.doctest` class, the output is checked against the given output.

# Panflute

The global structure of a filter in `panflute` runs `run_filter` from a `main` function. We'll keep a global registry of all code-blocks entered. In `panflute` a global variable is passed on top of the `doc` parameter that is passed to all involved functions.

``` {.python file=doctest/pandoc-test posix-perm=755}
#!python3
# vim: ft=python

from panflute import *

<<expand>>
<<session>>

<<prepare>>
<<action>>
<<finalize>>

def main(doc=None):
    return run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
```

## Tangle

We prepare a global variable `doc.codes` with a `defaultdict` for empty lists.

``` {.python #prepare}
from collections import defaultdict

def prepare(doc):
    doc.codes = defaultdict(lambda _: [])
```

In the action, we store whatever code block we can find a name for.

``` {.python #action}
<<get-name>>

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.codes[name].append(elem)
```

In the finalisation we need to expand code blocks, and run those blocks that are marked as `.doctest`.

### Getting a name

If the code block contains an identifier, that is used as the name. Alternatively, if a the code-block has an attribute `file=...`, the given filename is used as a name.

``` {.python #get-name}
def get_name(elem):
    if elem.identifier:
        return elem.identifier

    if "file" in elem.attributes:
        return elem.attributes["file"]

    return None
```

## Expand code references

To expand code references we match a regular expression with a reference line.

``` {.python #expand}
from typing import (Dict)
import re

def replace_expr(expr, replace, text):
    """Matches (fullmatch) `text` using the expression `expr`. If the expression
    matches, then returns the result of passing named sub-matches as
    keyword arguments to `replace`. Returns `text` otherwise."""
    match = re.fullmatch(expr, text)
    if match:
        return f(**match.groupdict())
    else:
        return text
```

The function `expand` takes a `CodeBlock` object and expands all references using the given regex.

``` {.python #expand}
def expand(code: CodeBlock, code_map: Dict[str, List[CodeBlock]]) -> str:
    pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
    <<define-look-up>>
    return "\n".join(
        replace_expr(pattern, look_up, line)
        for line in code.text.splitlines())
```

To feed this function we need a `look_up` that looks up the correct code reference. This is just a closure on the `code_map` dictionary. The `look_up` function calls `expand`, a matter of double recursion.

``` {.python #define-look-up}
from textwrap import indent

def look_up(*, name, prefix):
    blocks = code_map[name]
    if not blocks:
        raise ValueError(f"No code with name `{name}` found.")
    result = "\n".join(expand(code, code_map) for code in blocks)
    return textwrap.indent(result, prefix)
```

## Finalize

``` {.python #finalize}
def finalize(doc):
    for k, v in doc.codes.items():
        print(k, v)
```

## Sessions

A session has a list of input blocks, a line to the REPL, and a method to add new code. Code is only passed to the actual REPL at the time a `.doctest` class code block is pushed.

``` {.python #session}
class Session:
    history: List[str]
    input_queue: List[str]
```
