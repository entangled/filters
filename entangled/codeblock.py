from __future__ import annotations
from dataclasses import dataclass
from typing import (List, Dict)

@dataclass
class CodeBlock:
    """Mocks the `panflute.CodeBlock` class, and adds some features."""
    text: str
    identifier: str
    classes: List[str]
    attributes: Dict[str, str]

    @staticmethod
    def from_json(value) -> CodeBlock:
        identifier, classes, attributes = value[0]
        return CodeBlock(value[1], identifier, classes, dict(attributes))

    @property
    def name(self) -> str:
        if self.identifier:
            return self.identifier

        if "file" in self.attributes:
            return self.attributes["file"]

        return None

    @property
    def attribute_list(self) -> List[Tuple(str,str)]:
        return list(self.attributes.items())
