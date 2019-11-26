## ------ language="Python" file="entangled/tangle.py"
from panflute import *

## ------ begin <<get-code-block>>[0]
from typing import (Dict, List)
import re

## ------ begin <<replace-expr>>[0]
def replace_expr(expr, replace, text):
    """Matches (fullmatch) `text` using the expression `expr`. If the expression
    matches, then returns the result of passing named sub-matches as
    keyword arguments to `replace`. Returns `text` otherwise."""
    match = re.fullmatch(expr, text)
    if match:
        return replace(**match.groupdict())
    else:
        return text
## ------ end

def get_code(code_map: Dict[str, List[CodeBlock]], name: str) -> str:
    ## ------ begin <<expand>>[0]
    def expand(code: CodeBlock) -> str:
        pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
        return "\n".join(
            replace_expr(pattern, look_up, line)
            for line in code.text.splitlines())
    ## ------ end
    ## ------ begin <<look-up>>[0]
    from textwrap import indent
    
    def look_up(*, name: str, prefix: str) -> str:
        blocks = code_map[name]
        if not blocks:
            raise ValueError(f"No code with name `{name}` found.")
        result = "\n".join(expand(code) for code in blocks)
        return indent(result, prefix)
    ## ------ end
    return look_up(name=name, prefix="")
## ------ end

## ------ begin <<tangle-prepare>>[0]
from collections import defaultdict

def prepare(doc):
    doc.code_map = defaultdict(list)
## ------ end
## ------ begin <<tangle-action>>[0]
## ------ begin <<get-name>>[0]
def get_name(elem):
    if elem.identifier:
        return elem.identifier

    if "file" in elem.attributes:
        return elem.attributes["file"]

    return None
## ------ end

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.code_map[name].append(elem)
## ------ end
## ------ begin <<tangle-finalize>>[0]
import sys

def finalize(doc):
    for k in doc.code_map:
        print(k, ':\n', get_code(doc.code_map, k), file=sys.stderr)
    doc.content = []
## ------ end

def main(doc=None):
    return run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
## ------ end
