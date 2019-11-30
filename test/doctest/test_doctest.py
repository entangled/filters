from entangled.doctest import (Suite, Test, run_suite)
from entangled.config import (read_config)
from entangled import (doctest, tangle)
from panflute import (convert_text, CodeBlock)
from pathlib import (Path)
from shutil import (copyfile)
from subprocess import (run)
from collections import defaultdict
from contextlib import contextmanager

import pytest
import os

def test_suite():
    config = read_config()
    suite = Suite([Test("6*7", "42")], "python")
    run_suite(config, suite)
    assert suite.code_blocks[0].expect == suite.code_blocks[0].result

def count_status_prepare(doc):
    doc.report = defaultdict(lambda: 0)

def count_status_action(elem, doc):
    if isinstance(elem, CodeBlock):
        if "doctest" in elem.classes and "input" in elem.classes:
            assert "status" in elem.attributes
            doc.report[elem.attributes["status"]] += 1

@contextmanager
def pushd(path):
    cwd = Path.cwd()
    os.chdir(path)
    yield
    os.chdir(cwd)

def run_doctest(doc):
    doc.config = read_config()

    tangle.prepare(doc)
    doc = doc.walk(tangle.action)
    
    doctest.prepare(doc)
    doc = doc.walk(doctest.action)

    count_status_prepare(doc)
    doc = doc.walk(count_status_action)

def test_doctest(tmp_path): 
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "doctest-python.md", tmp_path / "doctest-python.md")
    copyfile("entangled.dhall", tmp_path / "entangled.dhall")
    copyfile("entangled.json", tmp_path / "entangled.json")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "doctest-python.md"],
        cwd=tmp_path, check=True)

    with pushd(tmp_path):
        doc = convert_text(Path("doctest-python.md").read_text(), standalone=True)
        run_doctest(doc)

    assert doc.report == {"SUCCESS": 1, "FAIL": 1, "ERROR": 1, "PENDING": 1}

def test_doctest_json(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "doctest-python.md", tmp_path / "doctest-python.md")
    copyfile("entangled.json", tmp_path / "entangled.json")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "doctest-python.md"],
        cwd=tmp_path, check=True)
    run(["pandoc", "-t", "plain", "--filter", "pandoc-test", "doctest-python.md"],
        cwd=tmp_path, check=True)

def test_doctest_main(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "doctest-python.md", tmp_path / "doctest-python.md")
    copyfile("entangled.dhall", tmp_path / "entangled.dhall")
    copyfile("entangled.json", tmp_path / "entangled.json")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "doctest-python.md"],
        cwd=tmp_path, check=True)
    run(["pandoc", "-t", "plain", "--filter", "pandoc-test", "doctest-python.md"],
        cwd=tmp_path, check=True)

def test_doctest_no_lang(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    doc = convert_text(Path(res / "nolang.md").read_text(), standalone=True)
    with pytest.raises(ValueError):
        run_doctest(doc)

def test_doctest_no_sep(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    doc = convert_text(Path(res / "nosep.md").read_text(), standalone=True)
    with pytest.raises(ValueError):
        run_doctest(doc)

