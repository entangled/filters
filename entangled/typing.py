# ~\~ language=Python filename=entangled/typing.py
# ~\~ begin <<lit/filters.md|entangled/typing.py>>[0]
from typing import (Union, List, Dict, Callable, Any)
from panflute import (Element, Doc, CodeBlock)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
CodeMap = Dict[str, List[CodeBlock]]
JSONType = Any
# ~\~ end
