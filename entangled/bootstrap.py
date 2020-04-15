## ------ language="Python" file="entangled/bootstrap.py" project://lit/entangled-python.md#684
from panflute import (Element, Doc, Plain, CodeBlock, Div, Str, Image, Header,
                      Link, convert_text, run_filters, RawBlock)
from typing import (Optional)
from pathlib import (Path)

import subprocess
import pkg_resources
import json

from .typing import (JSONType)
from .tangle import get_name
from .annotate import action as annotate_action
from .annotate import prepare

data_path = Path(pkg_resources.resource_filename(__name__, "."))

def parse_dhall(content: str, cwd: Optional[Path] = None) -> JSONType:
    """Takes Dhall content and parses it to JSON compatible data."""
    cwd = cwd or Path(".")
    result = subprocess.run(
        ["dhall-to-json"], cwd=cwd,
        input=content, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, encoding="utf-8", check=True)
    return json.loads(result.stdout)

## ------ begin <<bootstrap-card-deck>>[0] project://lit/entangled-python.md#716
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
## ------ begin <<bootstrap-fold-code-block>>[0] project://lit/entangled-python.md#750
def fix_name(name: str) -> str:
    return name.replace(".", "-dot-").replace("/", "-slash-")


def bootstrap_fold_code(elem: Element, doc: Doc) -> Optional[Element]:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if "bootstrap-fold" in elem.classes and name is not None:
            fixed_name = fix_name(name)
            button_attrs = {
                "class": "btn btn-primary",
                "type": "button",
                "data-toggle": "collapse",
                "data-target": "#" + fixed_name + "-container",
                "aria-controls": fixed_name + "-container"
            }
            attr_str = " ".join(f"{k}=\"{v}\"" for k, v in button_attrs.items())
            button = RawBlock(f"<button {attr_str}>&lt;&lt;{name}&gt;&gt;=</button>")
            elem.classes.append("overflow-auto")
            elem.attributes["style"] = "max-height: 50vh"
            return Div(button, Div(elem, classes=["collapse"], identifier=fixed_name + "-container"))

        else:
            return annotate_action(elem, doc)

    return None
## ------ end

def main(doc: Optional[Doc] = None) -> None:
    run_filters([bootstrap_card_deck, bootstrap_fold_code], prepare=prepare, doc=doc)
## ------ end
