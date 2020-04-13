card_deck_sample = """
let Card = ./schema/Card.dhall

in [ Card :: { title = "Literate Programming"
             , text =
                 ''
                 Write prose and code intermixed. Not just some choice snippets: **all code is included!**
                 This document is a rendering of a completely **self-contained Markdown** file.
                 ''
             , link = Some { href = "http://entangled.github.io/"
                           , content = "About Entangled" } }

   , Card :: { title = "Dhall Configuration"
             , image = Some "https://dhall-lang.org/img/dhall-large-logo.svg"
             , text =
                 ''
                 The Dhall configuration language is a safe alternative to Yaml. Dhall is a typed
                 language, meaning that schema are tightly integrated.
                 ''
             , link = Some { href = "https://dhall-lang.org/"
                           , content = "About Dhall" } }
   ]
"""


def test_dhall_parser():
    from entangled.bootstrap import parse_dhall, data_path
    x = parse_dhall(card_deck_sample, cwd=data_path)
    assert isinstance(x, list)
    assert all(isinstance(i, dict) for i in x)
    assert x[0]["title"] == "Literate Programming"
    assert x[1]["link"]["href"] == "https://dhall-lang.org/"


def test_bootstrap_filter(tmp_path):
    from subprocess import run
    from shutil import copyfile
    from pathlib import Path

    res = Path.resolve(Path(__file__)).parent
    copyfile(res / "some_blog.md", tmp_path / "some_blog.md")
    run(["pandoc", "-t", "html5", "--filter", "pandoc-bootstrap",
         "./some_blog.md"], cwd=tmp_path, check=True)
