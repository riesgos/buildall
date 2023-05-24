#!/usr/bin/env python3

import sys
from mako.template import Template

def main():
    filename = sys.argv[1]
    result = Template(open(filename).read()).render()
    resulting_filename = filename.replace("/templates", "")
    open(resulting_filename, "w").write(result)

if __name__ == "__main__":
    main()
