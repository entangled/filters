#!/usr/bin/env python3.7

import panflute
import jupyter_client
import sys

def action(elem, doc):
    pass

def finalize(doc):
    with jupyter_client.run_kernel(kernel_name="python3") as kc:
        print(kc.is_alive(), file=sys.stderr)

def main(doc=None):
    return panflute.run_filter(action, finalize=finalize)

if __name__ == "__main__":
    main()

