-- ~\~ language=Dhall filename=pandoc_entangled/schema/Card.dhall
-- ~\~ begin <<lit/filters.md|pandoc_entangled/schema/Card.dhall>>[init]
let Link =
    { href : Text
    , content : Text
    }

let Location = < Top | Right | Bottom | Left >

in let Card =
    { Type =
        { image : Optional Text
        , title : Text
        , text : Text
        , link : Optional Link
        , imageLocation : Location }
    , default =
        { image = None Text
        , link = None Link
        , imageLocation = Location.Top }
    }

in Card
-- ~\~ end
