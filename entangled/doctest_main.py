## ------ language="Python" file="entangled/doctest_main.py" project://lit/entangled-python.md#587
import panflute

from . import tangle
from . import annotate
from . import doctest

from .config import read_config


def main() -> None:
    ## ------ begin <<load-document>>[0] project://lit/entangled-python.md#617
    import io
    import sys
    
    json_input = sys.stdin.read()
    json_stream = io.StringIO(json_input)
    doc = panflute.load(json_stream)
    ## ------ end
    doc.config = read_config()

    tangle.prepare(doc)
    doc = doc.walk(tangle.action)

    annotate.prepare(doc)
    doc = doc.walk(annotate.action)

    doctest.prepare(doc)
    doc = doc.walk(doctest.action)

    panflute.dump(doc)
## ------ end
