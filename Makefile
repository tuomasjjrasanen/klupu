.PHONY: all
all: README.html

README.html: README
	rst2html $< $@

.PHONY: clean
clean:
