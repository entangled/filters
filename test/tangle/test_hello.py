import os
from pathlib import Path
from shutil import copyfile
from subprocess import run

def test_hello(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "hello.md", tmp_path / "hello.md")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "hello.md"],
        cwd=tmp_path, check=True)
    output = open(tmp_path / "hello_world.cc").read()
    expect = open(res / "hello_world.cc").read()
    assert output == expect

