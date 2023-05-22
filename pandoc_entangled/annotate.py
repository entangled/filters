# ~\~ language=Python filename=entangled/annotate.py
# ~\~ begin <<lit/filters.md|entangled/annotate.py>>[0]
from collections import defaultdict
from .tangle import get_name
from panflute import (Span, Str, Para, CodeBlock, Div, Emph, Doc, run_filter)
from typing import (Optional)

def prepare(doc):
    doc.code_count = defaultdict(lambda: 0)

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name is None:
            return
        if doc.code_count[name] == 0:
            label = Span(Emph(Str(f"«{name}»=")))
            doc.code_count[name] += 1
        else:
            label = Span(Emph(Str(f"«{name}»+")))
        return Div(Para(label), elem, classes=["annotated-code"])

def main(doc: Optional[Doc] = None) -> None:
    return run_filter(action, prepare=prepare)
# ~\~ end
