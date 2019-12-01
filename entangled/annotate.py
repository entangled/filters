## ------ language="Python" file="entangled/annotate.py"
from collections import defaultdict
from .tangle import get_name
from panflute import (Span, Str, Para, CodeBlock, Div, Emph)

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
## ------ end
