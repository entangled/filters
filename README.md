[![Test Badge](https://github.com/entangled/filters/workflows/Tests/badge.svg)](https://github.com/entangled/filters/actions?query=workflow%3ATests)
[![codecov](https://codecov.io/gh/entangled/filters/branch/master/graph/badge.svg)](https://codecov.io/gh/entangled/filters)

# Entangled - Pandoc filters

This contains several Pandoc filters and scripts for literate programming in Markdown. These filters are enough to get you going with literate programming.

## Install

```shell
pip install .
```

### Testing

```shell
pip install -e .[test]
pytest
```

## Supported syntax

See the [project homepage](https://entangled.github.io) for more info.

### Named code blocks

~~~markdown
``` {.python #hello}
print("Hello, World!")
```
~~~

### Reference code blocks

~~~markdown
``` {.python #main}
def main():
    <<hello>>
```
~~~

### Define files

~~~markdown
``` {.python file=hello.py}
<<main>>

if __name__ == "__main__":
    main()
```
~~~

### Documentation tests

~~~markdown
``` {.python .doctest #the-question}
6*7
---
42
```
~~~

## `pandoc-tangle`

Extracts code blocks and writes them to files.

```shell
pandoc -t plain --filter pandoc-tangle hello.md
```

## `pandoc-test`

Runs doctests, and include results into output.

```shell
pandoc -t html5 -s --filter pandoc-test hello.md
```

