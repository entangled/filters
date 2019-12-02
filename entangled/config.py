## ------ language="Python" file="entangled/config.py"
from .typing import (JSONType)
import subprocess
import json
import sys

def read_config() -> JSONType:
    """Reads config from `entangled.dhall` with fall-back to `entangled.json`."""
    try:
        result = subprocess.run(
            ["dhall-to-json", "--file", "entangled.dhall"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error reading `entangled.dhall`:\n" + e.stderr, file=sys.stderr)
    except FileNotFoundError:
        print("Warning: could not find `dhall-to-json`, trying to read JSON instead.",
              file=sys.stderr)
    return json.load(open("entangled.json", "r"))

def get_language_info(config: JSONType, identifier: str) -> JSONType:
    try:
        return next(lang for lang in config["languages"]
                    if identifier in lang["identifiers"])
    except StopIteration:
        raise ValueError(f"Language with identifier `{identifier}` not found in config.")
## ------ end
