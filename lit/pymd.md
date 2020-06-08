# Python-markdown
Python-markdown powers `MkDocs`. To pass Entangled style code blocks we need to help Python-Markdown along a bit.

``` {.python file=entangled/pymd/__init__.py #pymd}
__all__ = ["format", "validator"]
```

## Filter

``` {.python #pymd}
def format(source, language, css_class, options, md, classes=None, id_value='', **kwargs):
    import sys
    print("{} {} {} {}".format(language, css_class, options, md), file=sys.stderr)
    code_block = "<pre><code class={}>{}</code></pre>".format(language, source)
    ann = "<div class=\"lp-fragment\"><div class=\"lp-ref\">{}</div>{}</div>"
    if "file" in options:
        name = "«file://{}»".format(options["file"])
        return ann.format(name, code_block)
    elif "id" in options:
        name = "«{}»".format(options["id"])
        return ann.format(name, code_block)
    return code_block
```

## Validate

``` {.python #pymd}
def validator(language, options):
    return True
```

