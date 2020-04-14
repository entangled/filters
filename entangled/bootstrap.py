## ------ language="Python" file="entangled/bootstrap.py" project://lit/entangled-python.md#680
from panflute import (Element, Doc, Plain, CodeBlock, Div, Str, Image, Header,
                      Link, convert_text, run_filter)
from typing import (Optional)
from pathlib import (Path)

import subprocess
import pkg_resources
import json

from .typing import (JSONType)

data_path = Path(pkg_resources.resource_filename(__name__, "."))

def parse_dhall(content: str, cwd: Optional[Path] = None) -> JSONType:
    """Takes Dhall content and parses it to JSON compatible data."""
    cwd = cwd or Path(".")
    result = subprocess.run(
        ["dhall-to-json"], cwd=cwd,
        input=content, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, encoding="utf-8", check=True)
    return json.loads(result.stdout)

## ------ begin <<bootstrap-action>>[0] project://lit/entangled-python.md#709
def bootstrap_card_deck(elem: Element, doc: Doc) -> Optional[Element]:
    def outer_container(*elements: Element):
        return Div(Div(*elements, classes=["row"]), classes=["container-fluid"])

    def card(card_data: JSONType) -> Element:
        assert "title" in card_data and "text" in card_data
        title = card_data["title"]
        text = convert_text(card_data["text"])

        content = []
        if "image" in card_data:
            content.append(Plain(Image(url=card_data["image"], title=title, classes=["card-image"])))
        content.append(Header(Str(title), level=3, classes=["card-title"]))
        content.append(Div(*text, classes=["card-text"]))

        content = [Div(*content, classes=["card-body"])]

        if "link" in card_data:
            content.append(Plain(Link(Str(card_data["link"]["content"]),
                                url=card_data["link"]["href"],
                                classes=["btn", "btn-primary", "mt-auto", "mx-4"])))
        content = Div(Div(*content, classes=["card", "h-100"]), classes=["col"])
        return content

    if isinstance(elem, CodeBlock) and "bootstrap-card-deck" in elem.classes:
        content = map(card, parse_dhall(elem.text, cwd=data_path))
        return outer_container(*content)

    return None
## ------ end

def main(doc: Optional[Doc] = None) -> None:
    run_filter(bootstrap_card_deck, doc=doc)
## ------ end
