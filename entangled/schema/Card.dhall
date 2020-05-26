-- ~\~ language=Dhall filename=entangled/schema/Card.dhall
-- ~\~ begin <<lit/filters.md|entangled/schema/Card.dhall>>[0]
let Link =
    { href : Text
    , content : Text
    }

in let Card =
    { Type =
        { image : Optional Text
        , title : Text
        , text : Text
        , link : Optional Link }
    , default =
        { image = None Text
        , link = None Link }
    }

in Card
-- ~\~ end
