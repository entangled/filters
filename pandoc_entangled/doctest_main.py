# ~\~ language=Python filename=entangled/doctest_main.py
# ~\~ begin <<lit/filters.md|entangled/doctest_main.py>>[0]
import panflute

from . import tangle
from . import annotate
from . import doctest

from .config import read_config


def main() -> None:
    # ~\~ begin <<lit/filters.md|load-document>>[0]
    import io
    import sys

    json_input = sys.stdin.read()
    json_stream = io.StringIO(json_input)
    doc = panflute.load(json_stream)
    # ~\~ end
    doc.config = read_config()

    tangle.prepare(doc)
    doc = doc.walk(tangle.action)

    annotate.prepare(doc)
    # doc = doc.walk(annotate.action)

    doctest.prepare(doc)
    doc = doc.walk(doctest.action)

    panflute.dump(doc)
# ~\~ end
