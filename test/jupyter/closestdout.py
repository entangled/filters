#!/usr/bin/env python

import jupyter_client
import sys

def main():
    sys.stdout.close()
    with jupyter_client.run_kernel(kernel_name="python3") as kc:
        print(kc.is_alive(), file=sys.stderr)

if __name__ == "__main__":
    main()

