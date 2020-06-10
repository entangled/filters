from pathlib import (Path)
from shutil import (copyfile)
from subprocess import (run)

def test_annotate(tmp_path):
    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "plotly.md", tmp_path / "plotly.md")
    run(["pandoc", "-t", "plain", "--filter", "pandoc-inject", "plotly.md"],
        cwd=tmp_path, check=True)

