#!/usr/bin/env python

import pandocfilters as pf
import sys

def action(key, value, fmt, meta):
    print(key, value, fmt, meta, file=sys.stderr)

if __name__ == "__main__":
    pf.toJSONFilter(action)

