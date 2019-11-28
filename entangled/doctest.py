## ------ language="Python" file="entangled/doctest.py"
from panflute import (CodeBlock, run_filter)
from .tangle import get_code, get_name
from . import tangle

## ------ begin <<doctest-session>>[0]
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
## ------ end
## ------ begin <<doctest-finalize>>[0]
import sys
import json

def finalize(doc):
    tests = get_doc_tests(doc.code_map)
    for name, suite in tests.items():
        log = run_suite(doc.config, suite)
        print(name, file=sys.stderr)
        print(log, file=sys.stderr)
    doc.content = []
## ------ end
import subprocess

def prepare(doc=None):
    doc.config = read_config()
    tangle.prepare(doc)

def main(doc=None):
    return run_filter(
        tangle.action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
## ------ end
