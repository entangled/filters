---
title: Test for doc-testing in Python
author: Johan Hidding
---

# Counting words

``` {.python file=word_count.py}
def word_count(sentence):
    words = sentence.split()
    count = len(words)
    return count
```

## Examples

### Word count

Import the function.

``` {.python #test-word-count}
from word_count import word_count
```

Test the zero-case,

``` {.python .doctest #test-word-count}
word_count("")
---
0
```

And a small sentence.

``` {.python .doctest #test-word-count}
word_count("Hebban olla uogala nestas hagunnan hinase hic anda thu uuat unbidan uue nu")
---
14
```

### Division by zero

This one gives an error.

``` {.python .doctest #test-division}
1/0
---
42
```

So we never get to run this one.

``` {.python .doctest #test-division}
1/1
---
1
```

### Use of noweb references

``` {.python #square}
def square(x):
    return x*x
```

``` {.python .doctest #test-square}
<<square>>
square(10)
---
100
```

### No name no test

```shell
echo "Hello, World!"
```

