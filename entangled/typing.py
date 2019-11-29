## ------ language="Python" file="entangled/typing.py"
from typing import (Union, List, Callable, Any)
from panflute import (Element, Doc)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
JSONType = Any
## ------ end
