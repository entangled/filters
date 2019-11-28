## ------ language="Python" file="entangled/doctest2.py"
from pandocfilters import (applyJSONFilters)
from collections import defaultdict
from typing import (List, Dict, Union, Optional)
from dataclasses import dataclass
from .tangle import (get_code)
from .weave import annotate_action
import sys
import queue
from enum import Enum

@dataclass
class CodeBlock:
    """Mocks the `panflute.CodeBlock` class, and adds some features."""
    text: str
    identifier: str
    classes: List[str]
    attributes: Dict[str, str]

    @staticmethod
    def from_json(value):
        identifier, classes, attributes = value[0]
        return CodeBlock(value[1], identifier, classes, dict(attributes))

    @property
    def name(self):
        if self.identifier:
            return self.identifier

        if "file" in self.attributes:
            return self.attributes["file"]

        return None

    @property
    def attribute_list(self):
        return list(self.attributes.items())
## ------ begin <<read-config>>[0]
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
## ------ end
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
## ------ begin <<get-doc-tests>>[0]
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
## ------ end
## ------ begin <<doctest2-action>>[0]
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
            c.from_json(value)

            if "doctest" in classes:
                suite = suites[c.name].code_blocks[code_counter[c.name]]
                code_counter[c.name] += 1
                return generate_report(c, suite)
            code_counter[c.name] += 1
        return None
    return action
 
def main():
    config = read_config()
    code_map = defaultdict(list)
    json_data = sys.stdin.read()
    applyJSONFilters([tangle_action(code_map)], json_data)
    json_data = applyJSONFilters([annotate_action()], json_data)
    suites = get_doc_tests(code_map)
    for name, s in suites.items():
        run_suite(config, s)
    output_json = applyJSONFilters([doctest_action(suites)], json_data)
    sys.stdout.write(output_json)
## ------ end
## ------ end
