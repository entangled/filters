## ------ language="Python" file="entangled/doctest.py"
from panflute import (CodeBlock, run_filter)
from .tangle import get_code, get_name
from . import tangle

## ------ begin <<doctest-session>>[0]
from typing import (List, Dict, Union, Optional)
from dataclasses import dataclass

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
    with jupyter_client.run_kernel(kernel_name=info["jupyter"]) as kc:
        print("Kernel running ...", file=sys.stderr)
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
                except:
                    raise TimeoutError("Operation timed-out.");

        for c in s.code_blocks:
            msg_id = kc.execute(c.code)
            result = read_output(msg_id)
            repl_log.append(ReplLog(c.code, result, c.expect))

    return repl_log
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
