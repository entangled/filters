## ------ language="Python" file="entangled/annotate.py"
from collections import defaultdict
from .tangle import get_name
from .codeblock import CodeBlock
from panflute import (Span, Str, Para, CodeBlock, Div)

def prepare(doc):
    doc.code_count = defaultdict(lambda: 0)

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if doc.code_count[name] == 0:
            label = Span(Str(f"«{name}»="))
            doc.code_count[name] += 1
        else:
            label = Span(Str(f"«{name}»+"))
        return Div(Para(label), elem, classes=["annotated-code"])
## ------ end
