---
title: Entangled Python module
author: Johan Hidding
---

This is a set of Pandoc filters for literate programming written in Python. These filters are part of Entangled. They constitute a complete workflow for literate programming on them selves, but it is advised to use them in conjunction with Entangled. 

In particular, while you can tangle source files with the `entangled.tangle` Python module, it is much more convenient to use the `entangled` executable, which automatically tangles files upon saving the Markdown files, and more importantly, also does the reverse, keeping your files continuously in sync.

This module also acts as a test-bed and environment for rapid prototyping of features that may end up in the main (Haskell based part of) Entangled distribution. Currently we have:

- `tangle`, extract source files from embedded code blocks in Markdown.
- `annotate`, add name tags to code blocks.
- `doctest`, run documentation tests through Jupyter.

``` {.python file=entangled/__init__.py}
__version__ = "0.4.0"
```

# Config

Configuration of the `entangled` module is done through a file that should sit in the current directory.

::: {.future}
As a planned feature. Config files may sit in several places.

- `${ENTANGLED_PREFIX}/share/entangled`
- `${XDG_CONFIG_HOME}/entangled`
- Find first parent of current working directory
:::

As a configuration format we use [**Dhall**](https://dhall-lang.org/), with a fall-back to JSON. The file should be named either `entangled.dhall` or `entangled.json`. For the Dhall based configuration to work, you need to have the `dhall-to-json` executable installed.

The schema is as follows:

``` {.dhall #dhall-config-schema}
let Comment : Type =
    { start : Text
    , end : Optional Text }

let Language : Type =
    { name : Text
    , identifiers : List Text
    , comment : Comment
    , jupyter : Optional Text }

let Config : Type =
    { languages : List Language }
```

A number of comment styles can be defined.

``` {.dhall #config-comment-styles}
let hashComment         : Comment = { start = "#", end = None Text }
let lispStyleComment    : Comment = { start = ";", end = None Text }
let cStyleComment       : Comment = { start = "/*", end = Some "*/" }
let cppStyleComment     : Comment = { start = "//", end = None Text }
let haskellStyleComment : Comment = { start = "--", end = None Text }
let mlStyleComment      : Comment = { start = "(*", end = Some "*)" }
let xmlStyleComment     : Comment = { start = "<!--", end = Some "-->" }
```

``` {.python file=entangled/config.py}
from .typing import (JSONType)
import subprocess
import json

def read_config() -> JSONType:
    """Reads config from `entangled.dhall` with fall-back to `entangled.json`."""
    try:
        result = subprocess.run(
            ["dhall-to-json", "--file", "entangled.dhall"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
    except subprocess.CalledProcessError as e:
        print("Error reading `entangled.dhall`:\n" + e.stderr, file=sys.stderr)
    except FileNotFoundError as e:
        print("Warning: could not find `dhall-to-json`, trying to read JSON instead.",
              file=sys.stderr)
        return json.load("entangled.json")
    return json.loads(result.stdout)

def get_language_info(config: JSONType, identifier: str) -> JSONType:
    return next(lang for lang in config["languages"]
                if identifier in lang["identifiers"])
```

# Panflute

Panflute reads JSON from standard input, lets you apply filters to an intermediate object based representation and writes back to JSON. The actual filtering is done by a Panflute `Action`. The action takes an `Element` and a `Document` as argument and can return one of three things:

- `None`, leaves the element unchanged
- `Element`, replaces the element
- `List[Element]`, splices the list into list that contained the element

These are some types that we can use for type annotations.

``` {.python file=entangled/typing.py}
from typing import (Union, List, Callable, Any)
from panflute import (Element, Doc)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
JSONType = Any
```

# Doc-testing

This Pandoc filter runs doc-tests from Python. If a cell is marked with a `.doctest` class, the output is checked against the given output. We use Jupyter kernels to evaluate the input.

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
    doc = doc.walk(annotate.action)

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

# Tangle

The global structure of a filter in `panflute` runs `run_filter` from a `main` function. We'll keep a global registry of all code-blocks entered. In `panflute` a global variable is passed on top of the `doc` parameter that is passed to all involved functions.

``` {.python file=entangled/tangle.py}
from panflute import *

<<get-code-block>>

<<tangle-prepare>>
<<tangle-action>>
<<tangle-finalize>>

def main(doc=None):
    return run_filter(
        action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
```

We prepare a global variable `doc.codes` with a `defaultdict` for empty lists.

``` {.python #tangle-prepare}
from collections import defaultdict

def prepare(doc):
    doc.code_map = defaultdict(list)
```

In the action, we store whatever code block we can find a name for.

``` {.python #tangle-action}
<<get-name>>

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if name:
            doc.code_map[name].append(elem)
```

In the finalisation we need to expand code blocks, and run those blocks that are marked as `.doctest`.

### Getting a name

If the code block contains an identifier, that is used as the name. Alternatively, if a the code-block has an attribute `file=...`, the given filename is used as a name.

``` {.python #get-name}
def get_name(elem):
    if elem.identifier:
        return elem.identifier

    if "file" in elem.attributes:
        return elem.attributes["file"]

    return None
```

## Expand code references

To expand code references we match a regular expression with a reference line. Every reference is then replaced with the expanded code block matching it. This is implemented as a doubly recursive function.

``` {.python #get-code-block}
from typing import (Dict, List)
import re

<<replace-expr>>

def get_code(code_map: Dict[str, List[CodeBlock]], name: str) -> str:
    <<expand>>
    <<look-up>>
    return look_up(name=name, prefix="")
```

The `replace_expr` function does one of two things. If the input is not a match, the input is returned unchanged. If it is a match, all named sub-matches are taken out and given as keyword argument to the given `replace` function, the result of which is returned. 

``` {.python #replace-expr}
def replace_expr(expr, replace, text):
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

``` {.python #get-file-map}
def get_file_map(code_map: Dict[str, List[CodeBlock]]) -> Dict[str, str]:
    result = {}
    for k, v in code_map.items():
        if "file" in v.attributes:
            result[v.attributes["file"]] = k

    return result
```

Only files that are different from those on disk should be overwritten.

::: {.TODO}
Complete this script.
:::

``` {.python #tangle-finalize}
import sys

def finalize(doc):
    for k in doc.code_map:
        print(k, ':\n', get_code(doc.code_map, k), file=sys.stderr)
    doc.content = []
```

# Code block annotation

``` {.python file=entangled/annotate.py}
from collections import defaultdict
from .tangle import get_name
from .codeblock import CodeBlock
from panflute import (Span, Str, Para, CodeBlock, Div)

def prepare(doc):
    doc.code_count = defaultdict(lambda: 0)

def action(elem, doc):
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if doc.code_count[name] == 0:
            label = Span(Str(f"«{name}»="))
            doc.code_count[name] += 1
        else:
            label = Span(Str(f"«{name}»+"))
        return Div(Para(label), elem, classes=["annotated-code"])
```

# Doctesting

``` {.python file=entangled/doctest.py}
from panflute import (Doc, Element, CodeBlock)
from .typing import (ActionReturn, JSONType)
from .tangle import (get_name)
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
        if "doctest" in elem.classes:
            suite = doc.suites[name].code_blocks[doc.code_counter[name]]
            doc.code_counter[name] += 1
            return generate_report(elem, suite)
        doc.code_counter[name] += 1
```

## Get doc tests from code map

``` {.python #get-doc-tests}
def get_language(c: CodeBlock) -> str:
    if not c.classes:
        raise ValueError(f"Code block `{c.name}` has no language specified.")
    return c.classes[0]

def get_doc_tests(code_map: Dict[str, List[CodeBlock]]) -> Dict[str, Suite]:
    def convert_code_block(c: CodeBlock) -> Test:
        if "doctest" in c.classes:
            s = c.text.split("\n---\n")
            if len(s) != 2:
                raise ValueError(f"Doc test `{c.name}` should have single `---` line.")
            return Test(*s)
        else:
            return Test(c.text, None)

    result = {}
    for k, v in code_map.items():
        if any("doctest" in c.classes for c in v):
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
kernel_name = info["jupyter"]
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
    return True
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
    else:
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

``` {.python #doctest-report}
def generate_report(elem: CodeBlock, t: Test) -> ActionReturn:
    status_attr = {"status": t.status.name}
    input_code = CodeBlock(
        t.code, identifier=elem.identifier,
        classes=elem.classes, attributes=elem.attributes)
    input_code.attributes.update(status_attr)
    lang_class = elem.classes[0]
    if t.status is TestStatus.ERROR:
        return [ input_code
               , CodeBlock( str(t.error), classes=["error"], attributes=status_attr ) ]
    if t.status is TestStatus.FAIL:
        return [ input_code
               , CodeBlock( str(t.result), classes=[lang_class, "doctest", "result"]
                          , attributes=status_attr )
               , CodeBlock( str(t.expect), classes=[lang_class, "doctest", "expect"]
                          , attributes=status_attr ) ]
    if t.status is TestStatus.SUCCESS:
        return [ input_code
               , CodeBlock( str(t.result), classes=[lang_class, "doctest", "result"]
                          , attributes=status_attr ) ]
    if t.status is TestStatus.PENDING:
        return [ input_code ]
    if t.status is TestStatus.UNKNOWN:
        return [ input_code
               , CodeBlock( str(t.result), classes=["doctest", "unknown"]
                          , attributes=status_attr ) ]
    return None
```

