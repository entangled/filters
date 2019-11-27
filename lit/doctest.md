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
    result = subprocess.run(
        ["dhall-to-json", "--file", "entangled.dhall"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
    return json.loads(result.stdout)

def get_language_info(config, identifier):
    return next(lang for lang in config["languages"]
                if identifier in lang["identifiers"])
```

## Finalize

``` {.python #get-doc-tests}
def get_language(c: CodeBlock) -> str:
    if not c.classes:
        name = get_name(c)
        raise ValueError(f"Code block `{name}` has no language specified.")
    return c.classes[0]

def get_doc_tests(code_map: Dict[str, List[CodeBlock]]) -> Dict[str, Suite]:
    def convert_code_block(c: CodeBlock) -> Test:
        if "doctest" in c.classes:
            s = c.text.split("\n---\n")
            name = get_name(c)
            if len(s) != 2:
                raise ValueError(f"Doc test `{name}` should have single `---` line.")
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
@dataclass
class Test:
    __test__ = False
    code: str
    expect: Optional[str]

@dataclass
class Suite:
    code_blocks: List[Test]
    language: str

@dataclass
class ReplLog:
    code_input: str
    repl_output: str
    expected: Optional[str]

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
        def read_output(msg_id):
            while True:
                try:
                    msg = kc.get_iopub_msg(timeout=1)
                    if msg["msg_type"] == "execute_result" and \
                            msg["parent_header"]["msg_id"] ==  msg_id:
                        data = msg["content"]["data"]
                        if "text/plain" in data:
                            return data["text/plain"]
                        else:
                            raise ValueError(f"Unknown return value: `{data}`")
                    if msg["msg_type"] == "status" and \
                            msg["parent_header"]["msg_id"] == msg_id and \
                            msg["content"]["execution_state"] == "idle":
                        return
                    if msg["msg_type"] == "error":
                        print("\n".join(msg["content"]["traceback"]), file=sys.stderr)
                        raise RuntimeError("Error")

                except:
                    raise TimeoutError("Operation timed-out.");

        for c in s.code_blocks:
            msg_id = kc.execute(c.code)
            result = read_output(msg_id)
            repl_log.append(ReplLog(c.code, result, c.expect))

    return repl_log
```

## Bug in `panflute` or `jupyter_client`

There is something in `panflute` that prevents `jupyter_client` from working properly. We're down to using the `pandocfilters` interface. We can reuse much of what we did before.

``` {.python file=entangled/doctest2.py}
from pandocfilters import (applyJSONFilters)
from collections import defaultdict
from typing import (List, Dict, Union, Optional)
from dataclasses import dataclass
from .tangle import (get_code, get_name)
import sys

@dataclass
class CodeBlock:
    """Mocks the `panflute.CodeBlock` class."""
    text: str
    identifier: str
    classes: List[str]
    attributes: Dict[str, str]

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
            identifier, classes, attributes = value[0]
            c = CodeBlock(value[1], identifier, classes, dict(attributes))
            name = get_name(c)
            code_map[name].append(c)
        return []
    return action

def main():
    config = read_config()
    code_map = defaultdict(list)
    json_data = sys.stdin.read()
    output_json = applyJSONFilters([tangle_action(code_map)], json_data)
    suites = get_doc_tests(code_map)
    for name, s in suites.items():
        log = run_suite(config, s)
        print(log, file=sys.stderr)
    sys.stdout.write(output_json)
```
