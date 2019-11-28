# Code block annotation

``` {.python file=entangled/weave.py}
from collections import defaultdict
from .tangle import get_name
from .codeblock import CodeBlock
import pandocfilters as pf

def annotate_action():
    code_count = defaultdict(lambda: 0)
    def action(key, value, fmt, meta):
        if key == "CodeBlock":
            c = CodeBlock.from_json(value)
            if code_count[c.name] == 0:
                label = pf.Span(["", [], []], [pf.Str(f"«{c.name}»=")])
                code_count[c.name] += 1
            else:
                label = pf.Span(["", [], []], [pf.Str(f"«{c.name}»+")])
            return [pf.Div(["", ["annotated-code"], []],
                           [pf.Para([label]), pf.CodeBlock(*value)])]
    return action
```
