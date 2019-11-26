# Tangle

The global structure of a filter in `panflute` runs `run_filter` from a `main` function. We'll keep a global registry of all code-blocks entered. In `panflute` a global variable is passed on top of the `doc` parameter that is passed to all involved functions.

``` {.python file=entangled/tangle.py}
from panflute import *

<<get-code-block>>

<<tangle-prepare>>
<<tangle-action>>
<<tangle-finalize>>

def main(doc=None):
    return run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
```

We prepare a global variable `doc.codes` with a `defaultdict` for empty lists.

``` {.python #tangle-prepare}
from collections import defaultdict

def prepare(doc):
    doc.code_map = defaultdict(list)
```

In the action, we store whatever code block we can find a name for.

``` {.python #tangle-action}
<<get-name>>

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.code_map[name].append(elem)
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

To expand code references we match a regular expression with a reference line. Every reference is then replaced with the expanded code block matching it. This is implemented as a doubly recursive function.

``` {.python #get-code-block}
from typing import (Dict, List)
import re

<<replace-expr>>

def get_code(code_map: Dict[str, List[CodeBlock]], name: str) -> str:
    <<expand>>
    <<look-up>>
    return look_up(name=name, prefix="")
```

The `replace_expr` function does one of two things. If the input is not a match, the input is returned unchanged. If it is a match, all named sub-matches are taken out and given as keyword argument to the given `replace` function, the result of which is returned. 

``` {.python #replace-expr}
def replace_expr(expr, replace, text):
    """Matches (fullmatch) `text` using the expression `expr`. If the expression
    matches, then returns the result of passing named sub-matches as
    keyword arguments to `replace`. Returns `text` otherwise."""
    match = re.fullmatch(expr, text)
    if match:
        return replace(**match.groupdict())
    else:
        return text
```

In our case the `replace` function is called `look_up`; it looks up the given name and indents the result with a given prefix.

``` {.python #look-up}
from textwrap import indent

def look_up(*, name: str, prefix: str) -> str:
    blocks = code_map[name]
    if not blocks:
        raise ValueError(f"No code with name `{name}` found.")
    result = "\n".join(expand(code) for code in blocks)
    return indent(result, prefix)
```

The function `expand` takes a `CodeBlock` object and expands all references using the given regex. Decomposing this particular regex:

- `(?P<prefix>[ \t]*)` matches the indentation, either tabs or spaces.
- `<<(?P<name>[^ >]*)>>` matches the named reference, surrounded by `<<...>>`.
- `\Z` matches the end of input.

``` {.python #expand}
def expand(code: CodeBlock) -> str:
    pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
    return "\n".join(
        replace_expr(pattern, look_up, line)
        for line in code.text.splitlines())
```

Together, `expand` and `look_up` form a doubly recursive pair of functions, evaluating the contents of any code block found in the input.

## Finalize

To finalize, we write out all files that we can find.

``` {.python #get-file-map}
def get_file_map(code_map: Dict[str, List[CodeBlock]]) -> Dict[str, str]:
    result = {}
    for k, v in code_map.items():
        if "file" in v.attributes:
            result[v.attributes["file"]] = k

    return result
```

Only files that are different from those on disk should be overwritten.

::: {.TODO}
Complete this script.
:::

``` {.python #tangle-finalize}
import sys

def finalize(doc):
    for k in doc.code_map:
        print(k, ':\n', get_code(doc.code_map, k), file=sys.stderr)
    doc.content = []
```

