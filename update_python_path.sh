#!/bin/bash
sed -i.old '1 s|.*|#!'$(which python3)'|' cgi-bin/submit.py