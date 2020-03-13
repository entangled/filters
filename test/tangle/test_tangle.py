from pathlib import Path
from shutil import copyfile
from subprocess import run, CalledProcessError
import pytest
import time

def test_hello(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "hello.md", tmp_path / "hello.md")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "hello.md"],
        cwd=tmp_path, check=True)
    output = open(tmp_path / "hello_world.cc").read()
    expect = open(res / "hello_world.cc").read()
    assert output == expect

def test_write_unchanged(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "hello.md", tmp_path / "hello.md")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "hello.md"],
        cwd=tmp_path, check=True)
    t1 = (tmp_path / "hello_world.cc").stat().st_mtime
    time.sleep(0.01)
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "hello.md"],
        cwd=tmp_path, check=True)
    t2 = (tmp_path / "hello_world.cc").stat().st_mtime
    assert t1 == t2, "file should not be modified"

def test_missing(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "missing_ref.md", tmp_path / "missing_ref.md")
    with pytest.raises(CalledProcessError):
        run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "missing_ref.md"],
            cwd=tmp_path, check=True)


def test_makefile(tmp_path):
    md = tmp_path / "makefile.md"
    md.write_text("```{.makefile file=Makefile}\nall:\n\techo 1\n```\n")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-tangle", "makefile.md"],
        cwd=str(tmp_path), check=True)
    result = tmp_path / "Makefile"
    expected = "all:\n\techo 1\n"
    assert repr(result.read_text()) == repr(expected)
