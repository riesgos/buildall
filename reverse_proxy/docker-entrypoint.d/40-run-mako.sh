#!/bin/sh

apk add python3 py3-pip
pip3 install mako

find /templates -type f -exec python3 /run_mako.py {} \;
