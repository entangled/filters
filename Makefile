#| Makefile
#| ========
#|
#| Write your presentation in Markdown. This `Makefile` lets you watch the sources
#| and preview the presentation, live in your browser.
#|
#| Usage
#| -----
#|
#|     make [help|clean|watch|pages]
#|
#| Prerequisites
#| -------------
#|
#| * Pandoc
#| * Node (stable)
#| * inotify-tools
#|

build_dir := docs
src_dir := docsrc
source := $(src_dir)/index.md lit/entangled-python.md
style := dark.css
images := $(shell find $(src_dir)/img/*)
image_tgts := $(images:$(src_dir)/%=$(build_dir)/%)

pandoc_args := -s -t html5
pandoc_args += --highlight-style $(src_dir)/style/syntax.theme
pandoc_args += --filter pandoc-citeproc --mathjax
pandoc_args += --filter pandoc-test
pandoc_args += --css dark.css
pandoc_args += --template=$(src_dir)/template.html

#|
#| Targets
#| -------

#| * `help`: print this help
help:
	@ grep -e '^#|' Makefile \
	| sed -e 's/^#| \?\(.*\)/\1/' \
	| pandoc -f markdown -t filters/terminal.lua \
	| fold -s -w 80

#| * `watch`: reload browser upon changes
watch: $(build_dir)/source.html $(build_dir)/index.html $(build_dir)/img $(build_dir)/$(style)
	@tmux new-session make --no-print-directory watch-pandoc \; \
		split-window -v make --no-print-directory watch-browser \; \
		select-layout even-vertical \;

watch-pandoc:
	@while true; do \
		inotifywait -e close_write $(source) $(src_dir)/style/* Makefile $(src_dir)/img/*; \
		make build; \
	done

watch-browser:
	browser-sync start -s $(build_dir) -f $(build_dir) --no-notify

#| * `clean`: clean reveal.js and docs
clean:
	rm -rf $(build_dir)

build: $(build_dir)/index.html $(build_dir)/source.html \
       $(build_dir)/$(style) $(image_tgts) $(build_dir)/fonts

# Rules ============================================

$(build_dir)/%.html: $(src_dir)/%.md $(src_dir)/style/syntax.theme $(src_dir)/template.html Makefile
	@mkdir -p $(build_dir)
	pandoc $(pandoc_args) -o $@ $<

$(build_dir)/source.html: lit/entangled-python.md $(src_dir)/style/syntax.theme $(src_dir)/template.html Makefile
	@mkdir -p $(build_dir)
	pandoc --toc $(pandoc_args) -o $@ $<	

$(build_dir)/img/%: $(src_dir)/img/%
	@mkdir -p $(build_dir)/img
	cp -r $(src_dir)/img/* $(build_dir)/img

$(build_dir)/%.css: $(src_dir)/style/%.css
	@mkdir -p $(build_dir)
	cp $< $@

$(build_dir)/fonts: $(src_dir)/fonts
	@mkdir -p $(build_dir)
	cp -r $< $@

.PHONY: all clean build watch watch-pandoc watch-browser


