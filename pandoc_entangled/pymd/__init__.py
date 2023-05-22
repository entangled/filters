# ~\~ language=Python filename=entangled/pymd/__init__.py
# ~\~ begin <<lit/pymd.md|pymd>>[0]
__all__ = ["format", "validator"]
# ~\~ end
# ~\~ begin <<lit/pymd.md|pymd>>[1]
def format(source, language, css_class, options, md, classes=None, id_value='', **kwargs):
    patched_source = source \
        .replace("<", "&lt;") \
        .replace(">", "&gt;")
    code_block = "<pre><code class={}>{}</code></pre>".format(language, patched_source)
    ann = "<div class=\"lp-fragment\"><div class=\"lp-ref\">{}</div>{}</div>"
    if "file" in options:
        name = "«file://{}»".format(options["file"])
        return ann.format(name, code_block)
    elif "id" in options:
        name = "«{}»".format(options["id"])
        return ann.format(name, code_block)
    return code_block
# ~\~ end
# ~\~ begin <<lit/pymd.md|pymd>>[2]
def validator(language, options):
    return True
# ~\~ end
