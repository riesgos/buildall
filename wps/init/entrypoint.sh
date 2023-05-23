#!/bin/sh

apk add curl bash
pip install requests
python3 -u /init_wps.py

tail -f /dev/null
