[![Test Badge](https://github.com/entangled/filters/workflows/Tests/badge.svg)](https://github.com/entangled/filters/actions?query=workflow%3ATests)
[![codecov](https://codecov.io/gh/entangled/filters/branch/master/graph/badge.svg)](https://codecov.io/gh/entangled/filters)

# Entangled - Pandoc filters

This contains several Pandoc filters and scripts for literate programming in Markdown. These filters are enough to get you going with literate programming.

## Install

```shell
pip install entangled-filters
```

## For development

To run tests

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

## Docker

The Entangled pandoc filters is available as a [Docker image](https://hub.docker.com/repository/docker/nlesc/pandoc-tangle).

### Run

In your current working directory with a README.md file run.

```shell
docker run --rm -ti --user $UID -v $PWD:/data nlesc/pandoc-tangle README.md
```

This will extracts code blocks and writes them to files.

### Build

```shell
docker build -t nlesc/pandoc-tangle .
```
