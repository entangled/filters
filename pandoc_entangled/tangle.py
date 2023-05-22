# ~\~ language=Python filename=pandoc_entangled/tangle.py
# ~\~ begin <<lit/filters.md|pandoc_entangled/tangle.py>>[init]
from panflute import (run_filter, Doc, Element, CodeBlock)
from typing import (Optional, Dict, Callable)
from .typing import (CodeMap)
import sys

# ~\~ begin <<lit/filters.md|get-code-block>>[init]
import re

# ~\~ begin <<lit/filters.md|replace-expr>>[init]
def replace_expr(expr: str, replace: Callable[..., str], text: str) -> str:
    """Matches (fullmatch) `text` using the expression `expr`. If the expression
    matches, then returns the result of passing named sub-matches as
    keyword arguments to `replace`. Returns `text` otherwise."""
    match = re.fullmatch(expr, text)
    if match:
        return replace(**match.groupdict())
    else:
        return text
# ~\~ end

def get_code(code_map: CodeMap, name: str) -> str:
    # ~\~ begin <<lit/filters.md|expand>>[init]
    def expand(code: CodeBlock) -> str:
        pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
        return "\n".join(
            replace_expr(pattern, look_up, line)
            for line in code.text.splitlines())
    # ~\~ end
    # ~\~ begin <<lit/filters.md|look-up>>[init]
    from textwrap import indent

    def look_up(*, name: str, prefix: str) -> str:
        blocks = code_map[name]
        if not blocks:
            raise ValueError(f"No code with name `{name}` found.")
        result = "\n".join(expand(code) for code in blocks)
        return indent(result, prefix)
    # ~\~ end
    return look_up(name=name, prefix="")

def expand_code_block(code_map: CodeMap, code_block: CodeBlock) -> str:
    # ~\~ begin <<lit/filters.md|expand>>[init]
    def expand(code: CodeBlock) -> str:
        pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
        return "\n".join(
            replace_expr(pattern, look_up, line)
            for line in code.text.splitlines())
    # ~\~ end
    # ~\~ begin <<lit/filters.md|look-up>>[init]
    from textwrap import indent

    def look_up(*, name: str, prefix: str) -> str:
        blocks = code_map[name]
        if not blocks:
            raise ValueError(f"No code with name `{name}` found.")
        result = "\n".join(expand(code) for code in blocks)
        return indent(result, prefix)
    # ~\~ end
    return expand(code_block)
# ~\~ end

# ~\~ begin <<lit/filters.md|tangle-prepare>>[init]
from collections import defaultdict

def prepare(doc: Doc) -> None:
    doc.code_map = defaultdict(list)
# ~\~ end
# ~\~ begin <<lit/filters.md|tangle-action>>[init]
# ~\~ begin <<lit/filters.md|get-name>>[init]
def get_name(elem: Element) -> Optional[str]:
    if elem.identifier:
        return elem.identifier

    if "file" in elem.attributes:
        return elem.attributes["file"]

    return None
# ~\~ end

def action(elem: Element, doc: Doc) -> None:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.code_map[name].append(elem)
# ~\~ end
# ~\~ begin <<lit/filters.md|tangle-finalize>>[init]
def get_file_map(code_map: CodeMap) -> Dict[str, str]:
    """Extracts all file references from `code_map`."""
    return { code[0].attributes["file"]: codename 
             for codename, code in code_map.items()
             if "file" in code[0].attributes }
# ~\~ end
# ~\~ begin <<lit/filters.md|tangle-finalize>>[1]
def write_file(filename: str, text: str) -> None:
    """Writes `text` to file `filename`, only if `text` is different
    from contents of `filename`."""
    try:
        content = open(filename).read()
        if content == text:
            return
    except FileNotFoundError:
        pass
    print(f"Writing `{filename}`.", file=sys.stderr)
    open(filename, 'w').write(text)

def finalize(doc: Doc) -> None:
    """Writes all file references found in `doc.code_map` to disk.
    This only overwrites a file if the content is different."""
    file_map = get_file_map(doc.code_map)
    for filename, codename in file_map.items():
        write_file(filename, get_code(doc.code_map, codename))
    doc.content = []
# ~\~ end

def main(doc: Optional[Doc] = None) -> None:
    run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)
# ~\~ end
