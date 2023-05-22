# ~\~ language=Python filename=pandoc_entangled/typing.py
# ~\~ begin <<lit/filters.md|pandoc_entangled/typing.py>>[init]
from typing import (Union, List, Dict, Callable, Any)
from panflute import (Element, Doc, CodeBlock)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
CodeMap = Dict[str, List[CodeBlock]]
JSONType = Any
# ~\~ end
