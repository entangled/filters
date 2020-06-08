# MkDocs
Python-markdown powers `MkDocs`. To pass Entangled style code blocks we need to help Python-Markdown along a bit. These routines are designed to be called by `pymdownx.superfences`. To use them, add the following block to `mkdocs.yml` and enable `highlight.js`.

```yaml
markdown_extensions:
        - pymdownx.superfences:
            custom_fences:
               - name: "*"
                 class: "codehilite"
                 format: !!python/name:entangled.pymd.format
                 validator: !!python/name:entangled.pymd.validator
```

TODO:

- [ ] implement validator
- [ ] find a way of testing this code

``` {.python file=entangled/pymd/__init__.py #pymd}
__all__ = ["format", "validator"]
```

## Filter

``` {.python #pymd}
def format(source, language, css_class, options, md, classes=None, id_value='', **kwargs):
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

