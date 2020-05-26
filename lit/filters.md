# Config
Configuration of the `entangled` module is done through a file that should sit in the current directory.

As a configuration format we use [**Dhall**](https://dhall-lang.org/), with a fall-back to JSON. The file should be named either `entangled.dhall` or `entangled.json`. For the Dhall based configuration to work, you need to have the `dhall-to-json` executable installed.

``` {.python file=entangled/config.py}
from .typing import (JSONType)
import subprocess
import json
import sys

def read_config() -> JSONType:
    """Reads config from `entangled.dhall` with fall-back to `entangled.json`."""
    try:
        result = subprocess.run(
            ["dhall-to-json", "--file", "entangled.dhall"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error reading `entangled.dhall`:\n" + e.stderr, file=sys.stderr)
    except FileNotFoundError:
        print("Warning: could not find `dhall-to-json`, trying to read JSON instead.",
              file=sys.stderr)
    return json.load(open("entangled.json", "r"))

def get_language_info(config: JSONType, identifier: str) -> JSONType:
    kernels = { k["language"]: k["kernel"] for k in config["jupyter"] }

    try:
        language = next(lang for lang in config["entangled"]["languages"]
                        if identifier in lang["identifiers"])
    except StopIteration:
        raise ValueError(f"Language with identifier `{identifier}` not found in config.")

    return {"jupyter": kernels.get(language["name"]), **language}
```

# Panflute

Panflute reads JSON from standard input, lets you apply filters to an intermediate object based representation and writes back to JSON. The actual filtering is done by a Panflute `Action`. The action takes an `Element` and a `Document` as argument and can return one of three things:

- `None`, leaves the element unchanged
- `Element`, replaces the element
- `List[Element]`, splices the list into list that contained the element

These are some types that we can use for type annotations.

``` {.python file=entangled/typing.py}
from typing import (Union, List, Dict, Callable, Any)
from panflute import (Element, Doc, CodeBlock)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
CodeMap = Dict[str, List[CodeBlock]]
JSONType = Any
```

# Tangle

The global structure of a filter in `panflute` runs `run_filter` from a `main` function. We'll keep a global registry of all code-blocks entered. In `panflute` a global variable is passed on top of the `doc` parameter that is passed to all involved functions.

``` {.python file=entangled/tangle.py}
from panflute import (run_filter, Doc, Element, CodeBlock)
from typing import (Optional, Dict, Callable)
from .typing import (CodeMap)
import sys

<<get-code-block>>

<<tangle-prepare>>
<<tangle-action>>
<<tangle-finalize>>

def main(doc: Optional[Doc] = None) -> None:
    run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)
```

We prepare a global variable `doc.codes` with a `defaultdict` for empty lists.

``` {.python #tangle-prepare}
from collections import defaultdict

def prepare(doc: Doc) -> None:
    doc.code_map = defaultdict(list)
```

In the action, we store whatever code block we can find a name for.

``` {.python #tangle-action}
<<get-name>>

def action(elem: Element, doc: Doc) -> None:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.code_map[name].append(elem)
```

In the finalisation we need to expand code blocks, and run those blocks that are marked as `.doctest`.

### Getting a name

If the code block contains an identifier, that is used as the name. Alternatively, if a the code-block has an attribute `file=...`, the given filename is used as a name.

``` {.python #get-name}
def get_name(elem: Element) -> Optional[str]:
    if elem.identifier:
        return elem.identifier

    if "file" in elem.attributes:
        return elem.attributes["file"]

    return None
```

## Expand code references

To expand code references we match a regular expression with a reference line. Every reference is then replaced with the expanded code block matching it. This is implemented as a doubly recursive function.

``` {.python #get-code-block}
import re

<<replace-expr>>

def get_code(code_map: CodeMap, name: str) -> str:
    <<expand>>
    <<look-up>>
    return look_up(name=name, prefix="")

def expand_code_block(code_map: CodeMap, code_block: CodeBlock) -> str:
    <<expand>>
    <<look-up>>
    return expand(code_block)
```

The `replace_expr` function does one of two things. If the input is not a match, the input is returned unchanged. If it is a match, all named sub-matches are taken out and given as keyword argument to the given `replace` function, the result of which is returned. 

``` {.python #replace-expr}
def replace_expr(expr: str, replace: Callable[..., str], text: str) -> str:
    """Matches (fullmatch) `text` using the expression `expr`. If the expression
    matches, then returns the result of passing named sub-matches as
    keyword arguments to `replace`. Returns `text` otherwise."""
    match = re.fullmatch(expr, text)
    if match:
        return replace(**match.groupdict())
    else:
        return text
```

In our case the `replace` function is called `look_up`; it looks up the given name and indents the result with a given prefix.

``` {.python #look-up}
from textwrap import indent

def look_up(*, name: str, prefix: str) -> str:
    blocks = code_map[name]
    if not blocks:
        raise ValueError(f"No code with name `{name}` found.")
    result = "\n".join(expand(code) for code in blocks)
    return indent(result, prefix)
```

The function `expand` takes a `CodeBlock` object and expands all references using the given regex. Decomposing this particular regex:

- `(?P<prefix>[ \t]*)` matches the indentation, either tabs or spaces.
- `<<(?P<name>[^ >]*)>>` matches the named reference, surrounded by `<<...>>`.
- `\Z` matches the end of input.

``` {.python #expand}
def expand(code: CodeBlock) -> str:
    pattern = "(?P<prefix>[ \t]*)<<(?P<name>[^ >]*)>>\\Z"
    return "\n".join(
        replace_expr(pattern, look_up, line)
        for line in code.text.splitlines())
```

Together, `expand` and `look_up` form a doubly recursive pair of functions, evaluating the contents of any code block found in the input.

## Finalize

To finalize, we write out all files that we can find.

``` {.python #tangle-finalize}
def get_file_map(code_map: CodeMap) -> Dict[str, str]:
    """Extracts all file references from `code_map`."""
    return { code[0].attributes["file"]: codename 
             for codename, code in code_map.items()
             if "file" in code[0].attributes }
```

Only files that are different from those on disk should be overwritten.

``` {.python #tangle-finalize}
def write_file(filename: str, text: str) -> None:
    """Writes `text` to file `filename`, only if `text` is different
    from contents of `filename`."""
    try:
        content = open(filename).read()
        if content == text:
            return
    except FileNotFoundError:
        pass
    print(f"Writing `{filename}`.", file=sys.stderr)
    open(filename, 'w').write(text)

def finalize(doc: Doc) -> None:
    """Writes all file references found in `doc.code_map` to disk.
    This only overwrites a file if the content is different."""
    file_map = get_file_map(doc.code_map)
    for filename, codename in file_map.items():
        write_file(filename, get_code(doc.code_map, codename))
    doc.content = []
```

# Code block annotation
This adds the name of a code block to the output.

``` {.python file=entangled/annotate.py}
from collections import defaultdict
from .tangle import get_name
from panflute import (Span, Str, Para, CodeBlock, Div, Emph, Doc, run_filter)
from typing import (Optional)

def prepare(doc):
    doc.code_count = defaultdict(lambda: 0)

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name is None:
            return
        if doc.code_count[name] == 0:
            label = Span(Emph(Str(f"«{name}»=")))
            doc.code_count[name] += 1
        else:
            label = Span(Emph(Str(f"«{name}»+")))
        return Div(Para(label), elem, classes=["annotated-code"])

def main(doc: Optional[Doc] = None) -> None:
    return run_filter(action, prepare=prepare)
```

# Doctesting
This Pandoc filter runs doc-tests from Python. If a cell is marked with a `.doctest` class, the output is checked against the given output. We use Jupyter kernels to evaluate the input.

``` {.python file=entangled/doctest.py}
from panflute import (Doc, Element, CodeBlock)
from .typing import (ActionReturn, JSONType, CodeMap)
from .tangle import (get_name, expand_code_block)
from .config import get_language_info
from collections import defaultdict

import sys

<<doctest-suite>>
<<get-doc-tests>>
<<doctest-report>>
<<doctest-run-suite>>

def prepare(doc: Doc) -> None:
    assert hasattr(doc, "config"), "Need to read config first."
    assert hasattr(doc, "code_map"), "Need to tangle first."
    doc.suites = get_doc_tests(doc.code_map)
    for name, suite in doc.suites.items():
        run_suite(doc.config, suite)
    doc.code_counter = defaultdict(lambda: 0)

def action(elem: Element, doc: Doc) -> ActionReturn:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if "doctest" in elem.classes or "eval" in elem.classes:
            test = doc.suites[name].code_blocks[doc.code_counter[name]]
            doc.code_counter[name] += 1
            return generate_report(elem, test)

        doc.code_counter[name] += 1
    return None
```

## Get doc tests from code map

``` {.python #get-doc-tests}
def get_language(c: CodeBlock) -> str:
    if not c.classes:
        raise ValueError(f"Code block `{c.name}` has no language specified.")
    return c.classes[0]

def get_doc_tests(code_map: CodeMap) -> Dict[str, Suite]:
    def convert_code_block(c: CodeBlock) -> Test:
        name = get_name(c)
        code = expand_code_block(code_map, c)
        if "doctest" in c.classes:
            s = code.split("\n---\n")
            if len(s) != 2:
                raise ValueError(f"Doc test `{name}` should have single `---` line.")
            return Test(s[0], s[1])
        else:
            return Test(code, None)

    result = {}
    for k, v in code_map.items():
        if any("doctest" in c.classes or "eval" in c.classes for c in v):
            result[k] = Suite(
                code_blocks=[convert_code_block(c) for c in v],
                language=get_language(v[0]))

    return result
```

## Test Suite

Every code block that is part of a `.doctest` suite will be stored in a `Test` object, even if it is not a doc-test block itself. The default `status` of a test is `PENDING`.

A test may succeed, fail, throw an error or return an unknown result (other than `text/plain`).

``` {.python #doctest-suite}
from dataclasses import dataclass
from typing import (Optional, List, Dict)
from enum import Enum

class TestStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    FAIL = 2
    ERROR = 3
    UNKNOWN = 4
```

``` {.python #doctest-suite}
@dataclass
class Test:
    __test__ = False    # not a pytest class
    code: str
    expect: Optional[str]
    result: Optional[str] = None
    error: Optional[str] = None
    status: TestStatus = TestStatus.PENDING
```

A suite is just a list of `Test`s with some meta-data attached.

``` {.python #doctest-suite}
@dataclass
class Suite:
    code_blocks: List[Test]
    language: str
```

## Evaluation

We use `jupyter_client` to communicate with the REPL in question.

``` {.python #doctest-run-suite}
import jupyter_client
import queue

def run_suite(config: JSONType, s: Suite) -> None:
    <<jupyter-get-kernel-name>>
    with jupyter_client.run_kernel(kernel_name=kernel_name) as kc:
        print(f"Kernel `{kernel_name}` running ...", file=sys.stderr)
        <<jupyter-eval-test>>

        for test in s.code_blocks:
            jupyter_eval(test)
            if test.status is TestStatus.ERROR:
                break
```

### Jupyter
The configuration should have a Jupyter kernel name stored for the language.

``` {.python #jupyter-get-kernel-name}
info = get_language_info(config, s.language)
kernel_name = info["jupyter"] if "jupyter" in info else None
if not kernel_name:
    raise RuntimeError(f"No Jupyter kernel known for the {s.language} language.")
specs = jupyter_client.kernelspec.find_kernel_specs()
if kernel_name not in specs:
    raise RuntimeError(f"Jupyter kernel `{kernel_name}` not installed.")
```

After sending the test to the Jupyter kernel, we need to retrieve the result. To match the JSON records, we use `pampy`, making the following code a lot cleaner.

``` {.python #jupyter-eval-test}
def jupyter_eval(test: Test):
    msg_id = kc.execute(test.code)
    while True:
        try:
            msg = kc.get_iopub_msg(timeout=1000)
            if handle(test, msg_id, msg):
               return

        except queue.Empty:
            test.error = "Operation timed out."
            test.status = TestStatus.ERROR
            return
```

The `handle` function is a pattern matcher. Each pattern looks like a dictionary, but may contain one or more `_` symbols. The contents of the matching dictionary at the `_` symbols are passed to the function following the pattern.

``` {.python #jupyter-eval-test}
def handle(test, msg_id, msg):
    from pampy import match, _
    <<jupyter-handlers>>
    return match(msg
        <<jupyter-match>>
        )
```

#### `execute_result`
A result is tested for equality with the expected result.

``` {.python #jupyter-match}
, { "msg_type": "execute_result"
  , "parent_header": { "msg_id" : msg_id }
  , "content": { "data" : { "text/plain": _ } } }
, execute_result_text
```

``` {.python #jupyter-handlers}
def execute_result_text(data):
    test.result = data
    if (test.expect is None) or test.result.strip() == test.expect.strip():
        test.status = TestStatus.SUCCESS
    else:
        test.status = TestStatus.FAIL
    return False
```

#### output to stdout or stderr

``` {.python #jupyter-match}
, { "msg_type": "stream"
  , "parent_header": { "msg_id" : msg_id }
  , "content": { "text": _ } }
, stream_text
```

``` {.python #jupyter-handlers}
def stream_text(data):
    test.result = test.result or ""
    test.result += data
    return False
```

#### `status`
If status `idle` is given, the computation is done, and we don't need to wait for further messages.

``` {.python #jupyter-match}
, { "msg_type": "status"
  , "parent_header": { "msg_id" : msg_id }
  , "content": { "execution_state": "idle" } }
, status_idle
```

``` {.python #jupyter-handlers}
def status_idle(_):
    if test.expect is None:
        test.status = TestStatus.SUCCESS
    elif test.status == TestStatus.PENDING:
        test.status = TestStatus.FAIL
    return True
```

#### `error`
If an error is given, we set the appropriate flags in `test` and stop further testing in this session.

``` {.python #jupyter-match}
, { "msg_type": "error"
  , "parent_header": { "msg_id" : msg_id }
  , "content": { "traceback": _ } }
, error_traceback
```

``` {.python #jupyter-handlers}
def error_traceback(tb):
    test.error = "\n".join(msg["content"]["traceback"])
    test.status = TestStatus.ERROR 
    return True
```

#### otherwise
Any other message we ignore and wait for further messages.

``` {.python #jupyter-match}
, _
, lambda x: False
```

## Generate report
The generic output of a documentation test, in HTML, should look something like:

``` {.html}
<div class="doctest" data-status="STATUS">
    <div class="doctestInput"><...></div>
    <div class="doctestResult"><...></div>
</div>
```

To create the outer `div` we have a helper function.

``` {.python #doctest-content-div}
def content_div(*output):
    status_attr = {"status": t.status.name}
    code = elem.text.split("\n---\n")
    input_code = Div(CodeBlock(
        code[0], identifier=elem.identifier,
        classes=elem.classes), classes=["doctestInput"])
    return Div(input_code, *output, classes=["doctest"], attributes=status_attr)
```

Then the `generate_report` function transforms a `CodeBlock` as follows.

``` {.python #doctest-report}
from panflute import Div

def generate_report(elem: CodeBlock, t: Test) -> ActionReturn:
    lang_class = elem.classes[0]

    <<doctest-content-div>>
    if t.status is TestStatus.ERROR:
        return content_div( Div( CodeBlock(str(t.error))
                               , classes=["doctestError"] ) )
    if t.status is TestStatus.FAIL:
        return content_div( Div( CodeBlock(str(t.result), classes=[lang_class])
                               , classes=["doctestResult"] )
                          , Div( CodeBlock(str(t.expect), classes=[lang_class])
                               , classes=["doctestExpect"] ) )
    if t.status is TestStatus.SUCCESS:
        return content_div( Div( CodeBlock(str(t.result), classes=[lang_class])
                               , classes=["doctestResult"] ) )
    if t.status is TestStatus.PENDING:
        return content_div()
    if t.status is TestStatus.UNKNOWN:
        return content_div( Div( CodeBlock(str(t.result))
                               , classes=["doctestUnknown"] ) )
    return None
```

## Main
This module reuses most of the tangle module.

``` {.python file=entangled/doctest_main.py}
import panflute

from . import tangle
from . import annotate
from . import doctest

from .config import read_config


def main() -> None:
    <<load-document>>
    doc.config = read_config()

    tangle.prepare(doc)
    doc = doc.walk(tangle.action)

    annotate.prepare(doc)
    # doc = doc.walk(annotate.action)

    doctest.prepare(doc)
    doc = doc.walk(doctest.action)

    panflute.dump(doc)
```

## Bug in `panflute` or `jupyter_client`
There is a bug in `jupyter_client` that prevents it from working when either `stdin` or `stdout` is closed. This means that we have to read the input seperately.

``` {.python #load-document}
import io
import sys

json_input = sys.stdin.read()
json_stream = io.StringIO(json_input)
doc = panflute.load(json_stream)
```

# Bootstrap

The `pandoc-bootstrap` filter enables content generation for Bootstrap 4. This has the following features:

- Generate a *card deck* from a Yaml description in a code block.
- Create collapsible code cells to hide boilerplate or othewise boring code.

## Card deck

``` {.dhall file=entangled/schema/Card.dhall}
let Link =
    { href : Text
    , content : Text
    }

in let Card =
    { Type =
        { image : Optional Text
        , title : Text
        , text : Text
        , link : Optional Link }
    , default =
        { image = None Text
        , link = None Link }
    }

in Card
```

``` {.dhall file=test/card-deck-example.dhall}
let Card = ./schema/Card.dhall

in [ Card :: { title = "Literate Programming"
             , text =
                 ''
                 Write prose and code intermixed. Not just some choice snippets: **all code is included!**
                 This document is a rendering of a completely **self-contained Markdown** file.
                 ''
             , link = Some { href = "http://entangled.github.io/"
                           , content = "About Entangled" } } ]
```

Should generate something like:

``` {.html}
<div class="container-fluid"><div class="row">
    <div class="col"><div class="card h-100">
    <div class="card-body">
    <h3 class="card-title">Literate Programming</h3>
    <p class="card-text">Write prose and code intermixed. Not just some choice snippets: **all code is included!**
    This document is a rendering of a completely **self-contained Markdown** file.</p>
    </div>
    <a href="https://entangled.github.io/" class="btn btn-primary mt-auto mx-4">About Entangled</a>
    </div></div>
...
</div></div>
```

``` {.python file=entangled/bootstrap.py}
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

<<bootstrap-card-deck>>
<<bootstrap-fold-code-block>>

def prepare(doc: Doc) -> Doc:
    from datetime import date
    annotate.prepare(doc)

    if "footer" in doc.metadata:
        try:
            old_footer = list(doc.metadata["footer"].content)
        except AttributeError:
            old_footer = [Str("")]

        try:
            version = doc.metadata["version"].content[0]
        except (AttributeError, KeyError):
            version = Str("unknown")
        
        doc.metadata["footer"] = MetaInlines(
            Str(str(date.today())), Space, Str("—"), Space,
            Str("version"), Space, version, LineBreak,
            *old_footer)


def main(doc: Optional[Doc] = None) -> None:
    run_filters([bootstrap_card_deck, bootstrap_fold_code], prepare=prepare, doc=doc)
```

``` {.python #bootstrap-card-deck}
def bootstrap_card_deck(elem: Element, doc: Doc) -> Optional[Element]:
    def outer_container(*elements: Element):
        return Div(Div(*elements, classes=["card-deck"]), classes=["container-fluid", "my-4"])

    def card(card_data: JSONType) -> Element:
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

    if isinstance(elem, CodeBlock) and "bootstrap-card-deck" in elem.classes:
        content = map(card, parse_dhall(elem.text, cwd=data_path))
        return outer_container(*content)

    return None
```

## Foldable code blocks

``` {.python #bootstrap-fold-code-block}
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
            return annotate.action(elem, doc)

    return None
```

