-- ------ language="Dhall" file="entangled/schema/Card.dhall" project://lit/entangled-python.md#635
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
-- ------ end
