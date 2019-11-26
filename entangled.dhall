let Comment : Type = { start : Text, end : Optional Text }
let Language : Type = { name : Text, identifiers : List Text, comment : Comment, jupyter : Optional Text }

let hashComment         : Comment = { start = "#", end = None Text }
let lispStyleComment    : Comment = { start = ";", end = None Text }
let cStyleComment       : Comment = { start = "/*", end = Some "*/" }
let haskellStyleComment : Comment = { start = "--", end = None Text }
let mlStyleComment      : Comment = { start = "(*", end = Some "*)" }
let xmlStyleComment     : Comment = { start = "<!--", end = Some "-->" }

in { languages =
    [ { name = "Python"
      , identifiers = ["py", "python", "python3"]
      , comment = hashComment
      , jupyter = Some "python3" }

    , { name = "Scheme"
      , identifiers = ["scheme", "r6rs", "r7rs"]
      , comment = lispStyleComment
      , jupyter = Some "guile" } ]
   }
