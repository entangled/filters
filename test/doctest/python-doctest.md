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
13
```
