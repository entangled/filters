---
title: Testing Bootstrap Functionality
author: Johan Hidding
---

``` {.dhall .bootstrap-card-deck}
let Card = ./schema/Card.dhall

in [ Card :: { title = "Literate Programming"
             , text =
                 ''
                 Write prose and code intermixed. Not just some choice snippets: **all code is included!**
                 This document is a rendering of a completely **self-contained Markdown** file.
                 ''
             , link = Some { href = "http://entangled.github.io/"
                           , content = "About Entangled" } }

   , Card :: { title = "Dhall Configuration"
             , image = Some "https://dhall-lang.org/img/dhall-large-logo.svg"
             , text =
                 ''
                 The Dhall configuration language is a safe alternative to Yaml. Dhall is a typed
                 language, meaning that schema are tightly integrated.
                 ''
             , link = Some { href = "https://dhall-lang.org/"
                           , content = "About Dhall" } }
   ]
```


``` {.python .bootstrap-fold #folded}
"This code ends up being folded away under a button."
```

``` {.python #not-folded}
"While this code is just annotated as normal."
```

