# Arguments to Pandoc; these are reasonable defaults
pandoc_args += --template bootstrap/template.html
pandoc_args += --css css/mods.css
pandoc_args += -t html5 -s --mathjax --toc
pandoc_args += --toc-depth 1
pandoc_args += --filter pandoc-bootstrap
pandoc_args += --filter pandoc-doctest
pandoc_args += -f markdown+multiline_tables+simple_tables

# Load syntax definitions for languages that are not supported
# by default. These XML files are in the format of the Kate editor.
pandoc_args += --syntax-definition bootstrap/elm.xml
pandoc_args += --syntax-definition bootstrap/pure.xml
pandoc_args += --syntax-definition bootstrap/dhall.xml
pandoc_args += --highlight-style tango

# Any file in the `lit` directory that is not a Markdown source 
# is to be copied to the `docs` directory
static_files := $(shell find -L lit -type f -not -name '*.md')
static_targets := $(static_files:lit/%=docs/%)

input_files := lit/entangled-python.md README.md lit/filters.md lit/pymd.md lit/inject.md

.PHONY: site clean watch watch-pandoc watch-browser-sync

# This should build everything needed to generate your web site. That includes
# possible Javascript targets that may need compiling.
site: docs/index.html docs/css/mods.css $(static_targets)

clean:
	rm -rf docs

# Starts a tmux with Entangled, Browser-sync and an Inotify loop for running
# Pandoc.
watch:
	@tmux new-session make --no-print-directory watch-pandoc \; \
		split-window -v make --no-print-directory watch-browser-sync \; \
		split-window -v entangled daemon \; \
		select-layout even-vertical \;

watch-pandoc:
	@while true; do \
		inotifywait -e close_write bootstrap lit Makefile README.md; \
		make site; \
	done

watch-browser-sync:
	browser-sync start -w -s docs

docs/index.html: $(input_files) Makefile
	@mkdir -p docs
	pandoc $(pandoc_args) $(input_files) -o $@

docs/css/mods.css: bootstrap/mods.css
	@mkdir -p docs/css
	cp $< $@

$(static_targets): docs/%: lit/%
	@mkdir -p $(dir $@)
	cp $< $@

