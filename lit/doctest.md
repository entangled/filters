# Panflute

``` {.python file=entangled/typing.py}
from typing import (Union, List, Callable, Any)
from panflute import (Element, Doc)

ActionReturn = Union[Element, List[Element], None]
Action = Callable[[Element, Doc], ActionReturn]
JSONType = Any
```

# Doc-testing

This Pandoc filter runs doc-tests from Python. All this requires is a REPL to be available: a REPL reads commands from standard input and gives output on standard output. Cells with the same identifier are passed through a REPL in a single session. If a cell is marked with a `.doctest` class, the output is checked against the given output.

This module reuses most of the tangle module.

``` {.python file=entangled/doctest.py}
import panflute
from panflute import (CodeBlock, Element, Doc)

from . import tangle
from . import annotate
from .tangle import get_code, get_name

from typing import (Dict, List)
from .typing import (ActionReturn, JSONType)

import io
import sys
import queue
from collections import defaultdict

<<read-config>>
<<doctest-suite>>
<<get-doc-tests>>

<<doctest-run-suite>>
<<doctest-report>>

def prepare_report(doc: Doc) -> None:
    doc.code_counter = defaultdict(lambda: 0)

def action_report(elem: Element, doc: Doc) -> ActionReturn:
    if isinstance(elem, CodeBlock):
        name = get_name(elem)
        if "doctest" in elem.classes:
            suite = doc.suites[name].code_blocks[doc.code_counter[name]]
            doc.code_counter[name] += 1
            return generate_report(elem, suite)
        doc.code_counter[name] += 1

def prepare(doc: Doc) -> None:
    doc.config = read_config()
    tangle.prepare(doc)

def main() -> None:
    json_input = sys.stdin.read()
    json_stream = io.StringIO(json_input)
    doc = panflute.load(json_stream)

    prepare(doc)
    tangle.prepare(doc)
    annotate.prepare(doc)
    doc = doc.walk(tangle.action).walk(annotate.action)

    doc.suites = get_doc_tests(doc.code_map)
    for name, suite in doc.suites.items():
        run_suite(doc.config, suite)

    prepare_report(doc)
    doc = doc.walk(action_report)
    panflute.dump(doc)

if __name__ == "__main__":
    main()
```

## Config

``` {.python #read-config}
import subprocess
import json

def read_config() -> JSONType:
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

## Finalize

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

### Evaluation

We use `jupyter_client` to communicate with the REPL in question.

``` {.python #doctest-run-suite}
import jupyter_client

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

### Generate report

``` {.python #doctest-report}
def generate_report(elem: CodeBlock, t: Test) -> ActionReturn:
    status_attr = {"status": t.status.name}
    elem.attributes.update(status_attr)
    lang_class = elem.classes[0]
    if t.status is TestStatus.ERROR:
        return [ elem
               , CodeBlock( str(t.error), classes=["error"], attributes=status_attr ) ]
    if t.status is TestStatus.FAIL:
        return [ elem
               , CodeBlock( str(t.result), classes=[lang_class, "doctest", "result"]
                          , attributes=status_attr )
               , CodeBlock( str(t.expect), classes=[lang_class, "doctest", "expect"]
                          , attributes=status_attr ) ]
    if t.status is TestStatus.SUCCESS:
        return [ elem
               , CodeBlock( str(t.result), classes=[lang_class, "doctest", "result"]
                          , attributes=status_attr ) ]
    if t.status is TestStatus.PENDING:
        return [ elem ]
    if t.status is TestStatus.UNKNOWN:
        return [ elem
               , CodeBlock( str(t.result), classes=["doctest", "unknown"]
                          , attributes=status_attr ) ]
    return None
```

## Bug in `panflute` or `jupyter_client`

There is something in `panflute` that prevents `jupyter_client` from working properly. We're down to using the `pandocfilters` interface. We can reuse much of what we did before.

