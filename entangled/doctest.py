## ------ language="Python" file="entangled/doctest.py"
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

## ------ begin <<read-config>>[0]
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
## ------ end
## ------ begin <<doctest-suite>>[0]
from dataclasses import dataclass
from typing import (Optional, List, Dict)
from enum import Enum

class TestStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    FAIL = 2
    ERROR = 3
    UNKNOWN = 4
## ------ end
## ------ begin <<doctest-suite>>[1]
@dataclass
class Test:
    __test__ = False    # not a pytest class
    code: str
    expect: Optional[str]
    result: Optional[str] = None
    error: Optional[str] = None
    status: TestStatus = TestStatus.PENDING
## ------ end
## ------ begin <<doctest-suite>>[2]
@dataclass
class Suite:
    code_blocks: List[Test]
    language: str
## ------ end
## ------ begin <<get-doc-tests>>[0]
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
## ------ end

## ------ begin <<doctest-run-suite>>[0]
import jupyter_client

def run_suite(config: JSONType, s: Suite) -> None:
    ## ------ begin <<jupyter-get-kernel-name>>[0]
    info = get_language_info(config, s.language)
    kernel_name = info["jupyter"]
    if not kernel_name:
        raise RuntimeError(f"No Jupyter kernel known for the {s.language} language.")
    specs = jupyter_client.kernelspec.find_kernel_specs()
    if kernel_name not in specs:
        raise RuntimeError(f"Jupyter kernel `{kernel_name}` not installed.")
    ## ------ end
    with jupyter_client.run_kernel(kernel_name=kernel_name) as kc:
        print(f"Kernel `{kernel_name}` running ...", file=sys.stderr)
        ## ------ begin <<jupyter-eval-test>>[0]
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
        ## ------ end
        ## ------ begin <<jupyter-eval-test>>[1]
        def handle(test, msg_id, msg):
            from pampy import match, _
            ## ------ begin <<jupyter-handlers>>[0]
            def execute_result_text(data):
                test.result = data
                if (test.expect is None) or test.result.strip() == test.expect.strip():
                    test.status = TestStatus.SUCCESS
                else:
                    test.status = TestStatus.FAIL
                return True
            ## ------ end
            ## ------ begin <<jupyter-handlers>>[1]
            def status_idle(_):
                if test.expect is None:
                    test.status = TestStatus.SUCCESS
                else:
                    test.status = TestStatus.FAIL
                return True
            ## ------ end
            ## ------ begin <<jupyter-handlers>>[2]
            def error_traceback(tb):
                test.error = "\n".join(msg["content"]["traceback"])
                test.status = TestStatus.ERROR 
                return True
            ## ------ end
            return match(msg
                ## ------ begin <<jupyter-match>>[0]
                , { "msg_type": "execute_result"
                  , "parent_header": { "msg_id" : msg_id }
                  , "content": { "data" : { "text/plain": _ } } }
                , execute_result_text
                ## ------ end
                ## ------ begin <<jupyter-match>>[1]
                , { "msg_type": "status"
                  , "parent_header": { "msg_id" : msg_id }
                  , "content": { "execution_state": "idle" } }
                , status_idle
                ## ------ end
                ## ------ begin <<jupyter-match>>[2]
                , { "msg_type": "error"
                  , "parent_header": { "msg_id" : msg_id }
                  , "content": { "traceback": _ } }
                , error_traceback
                ## ------ end
                ## ------ begin <<jupyter-match>>[3]
                , _
                , lambda x: False
                ## ------ end
                )
        ## ------ end

        for test in s.code_blocks:
            jupyter_eval(test)
            if test.status is TestStatus.ERROR:
                break
## ------ end
## ------ begin <<doctest-report>>[0]
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
## ------ end

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
## ------ end
