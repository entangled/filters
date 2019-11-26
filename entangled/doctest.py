## ------ language="Python" file="entangled/doctest.py"
import panflute as pf
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
    spces = jupyter_client.kernelspec.find_kernel_specs()
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

def get_language(c: pf.CodeBlock) -> str:
    if not c.classes:
        name = get_name(c)
        raise ValueError(f"Code block `{name}` has no language specified.")
    return c.classes[0]

def get_doc_tests(code_map: Dict[str, List[pf.CodeBlock]]) -> Dict[str, Suite]:
    def convert_code_block(c: pf.CodeBlock) -> Test:
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

def finalize(doc):
    tests = get_doc_tests(doc.code_map)
    for name, suite in tests.items():
        log = run_suite(doc.config, suite)
        print(name, file=sys.stderr)
        print(log, file=sys.stderr)
    doc.content = []
## ------ end
import subprocess

def read_config():
    result = subprocess.run(
        ["dhall-to-json", "--file", "entangled.dhall"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
    return json.loads(result.stdout)

def get_language_info(config, identifier):
    return next(lang for lang in config["languages"]
                if identifier in lang["identifiers"])

def prepare(doc=None):
    doc.config = read_config()
    tangle.prepare(doc)

def main(doc=None):
    return pf.run_filter(
        tangle.action, prepare=prepare, finalize=finalize, doc=doc)

if __name__ == "__main__":
    main()
## ------ end