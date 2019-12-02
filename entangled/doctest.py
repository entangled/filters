## ------ language="Python" file="entangled/doctest.py"
from panflute import (Doc, Element, CodeBlock)
from .typing import (ActionReturn, JSONType, CodeMap)
from .tangle import (get_name, expand_code_block)
from .config import get_language_info
from collections import defaultdict

import sys

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

def get_doc_tests(code_map: CodeMap) -> Dict[str, Suite]:
    def convert_code_block(c: CodeBlock) -> Test:
        name = get_name(c)
        code = expand_code_block(code_map, c)
        if "doctest" in c.classes:
            s = code.split("\n---\n")
            if len(s) != 2:
                raise ValueError(f"Doc test `{name}` should have single `---` line.")
            return Test(*s)
        else:
            return Test(code, None)

    result = {}
    for k, v in code_map.items():
        if any("doctest" in c.classes for c in v):
            result[k] = Suite(
                code_blocks=[convert_code_block(c) for c in v],
                language=get_language(v[0]))

    return result
## ------ end
## ------ begin <<doctest-report>>[0]
from panflute import Div

def generate_report(elem: CodeBlock, t: Test) -> ActionReturn:
    lang_class = elem.classes[0]

    ## ------ begin <<doctest-content-div>>[0]
    def content_div(*output):
        status_attr = {"status": t.status.name}
        input_code = Div(CodeBlock(
            t.code, identifier=elem.identifier,
            classes=elem.classes), classes=["doctestInput"])
        return Div(input_code, *output, classes=["doctest"], attributes=status_attr)
    ## ------ end
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
## ------ end
## ------ begin <<doctest-run-suite>>[0]
import jupyter_client
import queue

def run_suite(config: JSONType, s: Suite) -> None:
    ## ------ begin <<jupyter-get-kernel-name>>[0]
    info = get_language_info(config, s.language)
    kernel_name = info["jupyter"] if "jupyter" in info else None
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
    return None
## ------ end
