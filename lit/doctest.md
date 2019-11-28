# Doc-testing

This Pandoc filter runs doc-tests from Python. All this requires is a REPL to be available: a REPL reads commands from standard input and gives output on standard output. Cells with the same identifier are passed through a REPL in a single session. If a cell is marked with a `.doctest` class, the output is checked against the given output.

This module reuses most of the tangle module.

``` {.python file=entangled/doctest.py}
from panflute import (CodeBlock, run_filter)
from .tangle import get_code, get_name
from . import tangle

<<doctest-session>>
<<doctest-finalize>>
import subprocess

def prepare(doc=None):
    doc.config = read_config()
    tangle.prepare(doc)

def main(doc=None):
    return run_filter(
        tangle.action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
```

## Config

``` {.python #read-config}
import subprocess
import json

def read_config():
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

def get_language_info(config, identifier):
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

``` {.python #doctest-finalize}
import sys
import json

def finalize(doc):
    tests = get_doc_tests(doc.code_map)
    for name, suite in tests.items():
        log = run_suite(doc.config, suite)
        print(name, file=sys.stderr)
        print(log, file=sys.stderr)
    doc.content = []
```

## Sessions

A session has a list of input blocks, a line to the REPL, and a method to add new code. Code is only passed to the actual REPL at the time a `.doctest` class code block is pushed.

``` {.python #doctest-session}
class TestStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    FAIL = 2
    ERROR = 3
    UNKNOWN = 4

@dataclass
class Test:
    __test__ = False    # not a pytest class
    code: str
    expect: Optional[str]
    result: Optional[str] = None
    error: Optional[str] = None
    status: TestStatus = TestStatus.PENDING

@dataclass
class Suite:
    code_blocks: List[Test]
    language: str

import jupyter_client

def run_suite(config, s: Suite):
    info = get_language_info(config, s.language)
    kernel_name = info["jupyter"]
    if not kernel_name:
        raise RuntimeError(f"No Jupyter kernel known for the {s.language} language.")
    specs = jupyter_client.kernelspec.find_kernel_specs()
    if kernel_name not in specs:
        raise RuntimeError(f"Jupyter kernel `{kernel_name}` not installed.")

    repl_log = []
    with jupyter_client.run_kernel(kernel_name=kernel_name) as kc:
        print(f"Kernel `{kernel_name}` running ...", file=sys.stderr)
        def jeval(test: Test):
            msg_id = kc.execute(test.code)
            while True:
                try:
                    msg = kc.get_iopub_msg(timeout=1000)
                    if msg["msg_type"] == "execute_result" and \
                            msg["parent_header"]["msg_id"] ==  msg_id:
                        data = msg["content"]["data"]
                        if "text/plain" in data:
                            test.result = data["text/plain"]
                            if (test.expect is None) or test.result.strip() == test.expect.strip():
                                test.status = TestStatus.SUCCESS
                            else:
                                test.status = TestStatus.FAIL
                            return
                        else:
                            test.status = TestStatus.UNKNOWN
                            test.result = str(data)
                            return
                    if msg["msg_type"] == "status" and \
                            msg["parent_header"]["msg_id"] == msg_id and \
                            msg["content"]["execution_state"] == "idle":
                        if test.expect is None:
                            test.status = TestStatus.SUCCESS
                        else:
                            test.status = TestStatus.FAIL
                        return
                    if msg["msg_type"] == "error":
                        test.error = "\n".join(msg["content"]["traceback"])
                        test.status = TestStatus.ERROR 
                        return
                except queue.Empty:
                    test.error = "Operation timed out."
                    test.status = TestStatus.ERROR
                    return

        for test in s.code_blocks:
            jeval(test)
            if test.status is TestStatus.ERROR:
                break

    return s

import pandocfilters as pandoc

def generate_report(c: CodeBlock, t: Test) -> List [pandoc.CodeBlock]:
    status_attr = [("status", t.status.name)]
    input_code = pandoc.CodeBlock(
        [c.identifier, c.classes, c.attribute_list + status_attr], t.code)
    lang_class = c.classes[0]

    if t.status is TestStatus.ERROR:
        return [input_code, pandoc.CodeBlock(["", ["error"], status_attr], str(t.error))]
    if t.status is TestStatus.FAIL:
        return [ input_code
               , pandoc.CodeBlock(["", [lang_class, "doctest", "result"], status_attr], str(t.result))
               , pandoc.CodeBlock(["", [lang_class, "doctest", "expect"], status_attr], str(t.expect)) ]
    if t.status is TestStatus.SUCCESS:
        return [ input_code
               , pandoc.CodeBlock(["", [lang_class, "doctest", "result"], status_attr], str(t.result)) ]
    if t.status is TestStatus.PENDING:
        return [ input_code ]
    if t.status is TestStatus.UNKNOWN:
        return [ input_code
               , pandoc.CodeBlock(["", ["doctest", "unknown"], status_attr], str(t.result)) ]

    return None
```

## Bug in `panflute` or `jupyter_client`

There is something in `panflute` that prevents `jupyter_client` from working properly. We're down to using the `pandocfilters` interface. We can reuse much of what we did before.

``` {.python file=entangled/doctest2.py}
from pandocfilters import (applyJSONFilters)
from collections import defaultdict
from typing import (List, Dict, Union, Optional)
from dataclasses import dataclass
from .tangle import (get_code)
from .weave import annotate_action
import sys
import queue
from enum import Enum
from .codeblock import CodeBlock

<<read-config>>
<<doctest-session>>
<<get-doc-tests>>
<<doctest2-action>>
```

### Action

`pandocfilters` is a bit more spartan interface. It uses functions `action(key, value, format, meta)`.

``` {.python #doctest2-action}
def tangle_action(code_map):
    def action(key, value, fmt, meta):
        if key == "CodeBlock":
            c = CodeBlock.from_json(value)
            code_map[c.name].append(c)
    return action

def doctest_action(suites):
    code_counter = defaultdict(lambda: 0)
    def action(key, value, fmt, meta):
        if key == "CodeBlock":
            c = CodeBlock.from_json(value)

            if "doctest" in c.classes:
                suite = suites[c.name].code_blocks[code_counter[c.name]]
                code_counter[c.name] += 1
                return generate_report(c, suite)
            code_counter[c.name] += 1
        return None
    return action

from pprint import pprint

def main():
    config = read_config()
    code_map = defaultdict(list)
    json_data = sys.stdin.read()
    print("tangling ...", file=sys.stderr)
    applyJSONFilters([tangle_action(code_map)], json_data)
    print("annotating ...", file=sys.stderr)
    json_data = applyJSONFilters([annotate_action()], json_data)
    suites = get_doc_tests(code_map)
    for name, s in suites.items():
        run_suite(config, s)
    print("inserting doctest report ...", file=sys.stderr)
    json_data = applyJSONFilters([doctest_action(suites)], json_data)
    # pprint(json.loads(json_data)['blocks'][1]['c'][1][0]['c'], stream=sys.stderr)
    sys.stdout.write(json_data)
```
