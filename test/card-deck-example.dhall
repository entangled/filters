-- ~\~ language=Dhall filename=test/card-deck-example.dhall
-- ~\~ begin <<lit/filters.md|test/card-deck-example.dhall>>[0]
let Card = ./schema/Card.dhall

in [ Card :: { title = "Literate Programming"
             , text =
                 ''
                 Write prose and code intermixed. Not just some choice snippets: **all code is included!**
                 This document is a rendering of a completely **self-contained Markdown** file.
                 ''
             , link = Some { href = "http://entangled.github.io/"
                           , content = "About Entangled" } } ]
-- ~\~ end
