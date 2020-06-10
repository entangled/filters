# ~\~ language=Python filename=entangled/inject.py
# ~\~ begin <<lit/inject.md|entangled/inject.py>>[0]
from typing import (Optional)
from panflute import (Doc, CodeBlock, Div, Link, Str, Plain, RawBlock, Emph)
from . import tangle

def action(elem, doc):
    if isinstance(elem, CodeBlock) and "inject" in elem.attributes:
        name = elem.identifier
        label = Emph(Str(f"«{name}»="))
        itemNav = Link(Str(f"{name} output"), url=f"#{name}", classes=["nav-item", "nav-link", "active"],
                         identifier="nav-source-tab", attributes={
                            "data-toggle": "tab", "aria-controls": f"{name}", "aria-selected": "true"})
        sourceNav = Link(label, url="#nav-source", classes=["nav-item", "nav-link"],
                         identifier="nav-source-tab", attributes={
                            "data-toggle": "tab", "aria-controls": "nav-source", "aria-selected": "false"})
        nav = Div(Plain(itemNav, sourceNav), classes=["nav", "nav-tabs"], identifier=f"{name}-nav")

        elem.identifier = f"{name}-source"
        elem.attributes["annotated"] = "true"
        targetPane = Div(classes=["tab-pane", "fade", "show", "active"], identifier=name)
        sourcePane = Div(elem, classes=["tab-pane", "fade"], identifier="nav-source")
        content = Div(targetPane, sourcePane, classes=["tab-content"], identifier=f"{name}-content")
        expanded_source = tangle.get_code(doc.code_map, name)
        script = RawBlock(f"<script>\n{expanded_source}\n</script>")
        return Div(nav, content, script, classes=["entangled-inject"])

def main(doc: Optional[Doc] = None) -> None:
    import sys
    import io
    import panflute

    json_input = sys.stdin.read()
    json_stream = io.StringIO(json_input)
    doc = panflute.load(json_stream)
    tangle.prepare(doc)
    doc = doc.walk(tangle.action)
    doc = doc.walk(action)
    panflute.dump(doc)
# ~\~ end
