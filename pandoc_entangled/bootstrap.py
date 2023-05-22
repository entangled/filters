# ~\~ language=Python filename=entangled/bootstrap.py
# ~\~ begin <<lit/filters.md|entangled/bootstrap.py>>[0]
from panflute import (Element, Doc, Plain, CodeBlock, Div, Str, Image, Header,
                      Link, convert_text, run_filters, RawBlock, Space, LineBreak, MetaInlines)
from typing import (Optional)
from pathlib import (Path)

import subprocess
import pkg_resources
import json

from .typing import (JSONType)
from .tangle import get_name
from . import annotate

data_path = Path(pkg_resources.resource_filename(__name__, "."))

def parse_dhall(content: str, cwd: Optional[Path] = None) -> JSONType:
    """Takes Dhall content and parses it to JSON compatible data."""
    cwd = cwd or Path(".")
    result = subprocess.run(
        ["dhall-to-json"], cwd=cwd,
        input=content, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, encoding="utf-8", check=True)
    return json.loads(result.stdout)

# ~\~ begin <<lit/filters.md|bootstrap-card-deck>>[0]
def bootstrap_card_deck(elem: Element, doc: Doc) -> Optional[Element]:
    def outer_container(*elements: Element):
        return Div(Div(*elements, classes=["card-deck"]), classes=["container-fluid", "my-4"])

    def horizontal_card(card_data: JSONType) -> Element:
        assert "title" in card_data and "text" in card_data
        title = card_data["title"]
        text = convert_text(card_data["text"])

        content = []
        body = [
            Header(Str(title), level=3, classes=["card-title"]),
            Div(*text, classes=["card-text"])
        ]

        if "link" in card_data:
            body.append(Plain(Link(Str(card_data["link"]["content"]),
                                   url=card_data["link"]["href"],
                                   classes=["btn", "btn-secondary", "mt-auto", "mx-4"])))

        card_img = Div(Plain(Image(url=card_data["image"], title=title, attributes={"width": "100%"})), classes=["col-4"])
        card_body = Div(Div(*body, classes=["card-body"]), classes=["col-8"])
        if card_data["imageLocation"] == "Left":
            content = [ card_img, card_body ]
        else:
            content = [ card_body, card_img ]
        content = Div(Div(*content, classes=["row", "no-gutters"]), classes=["card", "rounded-lg"])
        return content

    def vertical_card(card_data: JSONType) -> Element:
        assert "title" in card_data and "text" in card_data
        title = card_data["title"]
        text = convert_text(card_data["text"])

        content = []
        if "image" in card_data:
            content.append(Plain(Image(url=card_data["image"], title=title, classes=["card-img-top"])))

        body = [
            Header(Str(title), level=3, classes=["card-title"]),
            Div(*text, classes=["card-text"])
        ]

        if "link" in card_data:
            body.append(Plain(Link(Str(card_data["link"]["content"]),
                                   url=card_data["link"]["href"],
                                   classes=["btn", "btn-secondary", "mt-auto", "mx-4"])))

        content.append(Div(*body, classes=["card-body", "d-flex", "flex-column"]))

        content = Div(Div(*content, classes=["card", "h-100", "rounded-lg"]), classes=["col"])
        return content

    def card(card_data):
        if card_data["imageLocation"] in ["Top", "Bottom"]:
            return vertical_card(card_data)
        else:
            return horizontal_card(card_data)

    if isinstance(elem, CodeBlock) and "bootstrap-card-deck" in elem.classes:
        deck_data = parse_dhall(elem.text, cwd=data_path)
        content = map(card, deck_data)
        return outer_container(*content)

    return None
# ~\~ end
# ~\~ begin <<lit/filters.md|bootstrap-fold-code-block>>[0]
def fix_name(name: str) -> str:
    return name.replace(".", "-dot-").replace("/", "-slash-")


def bootstrap_fold_code(elem: Element, doc: Doc) -> Optional[Element]:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if "bootstrap-fold" in elem.classes and name is not None:
            fixed_name = fix_name(name)
            button_attrs = {
                "class": "btn btn-outline-primary btn-sm fold-toggle",
                "type": "button",
                "data-toggle": "collapse",
                "data-target": "#" + fixed_name + "-container",
                "aria-controls": fixed_name + "-container"
            }
            attr_str = " ".join(f"{k}=\"{v}\"" for k, v in button_attrs.items())
            button = RawBlock(f"<button {attr_str}>&lt;&lt;{name}&gt;&gt;=</button>")
            elem.classes.append("overflow-auto")
            elem.attributes["style"] = "max-height: 50vh"
            return Div(button, Div(elem, classes=["collapse"], identifier=fixed_name + "-container"),
                       classes=["fold-block"])

        else:
            if "annotated" in elem.attributes:
                return None
            return annotate.action(elem, doc)

    return None
# ~\~ end

def prepare(doc: Doc) -> Doc:
    from datetime import date
    from itertools import islice, chain, repeat

    def intersperse(delimiter, seq):
        return islice(chain.from_iterable(zip(repeat(delimiter), seq)), 1, None)

    annotate.prepare(doc)

    if "footer" in doc.metadata:
        content = [[Str(str(date.today()))]]
        try:
            old_footer = list(doc.metadata["footer"].content)
        except AttributeError:
            old_footer = [Str("")]

        try:
            version = doc.metadata["version"].content[0]
            content.append([Str("version:"), Space, version])
        except (AttributeError, KeyError):
            pass

        try:
            license = doc.metadata["license"].content[0]
            content.append([Str("license:"), Space, license])
        except (AttributeError, KeyError):
            pass

        content = sum(intersperse([Space, Str("—"), Space], content), [])
        doc.metadata["footer"] = MetaInlines(
            *old_footer, LineBreak, *content)


def main(doc: Optional[Doc] = None) -> None:
    run_filters([bootstrap_card_deck, bootstrap_fold_code], prepare=prepare, doc=doc)
# ~\~ end
