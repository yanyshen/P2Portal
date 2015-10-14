#!/bin/sh
cd ../update-sites
python -m SimpleHTTPServer &
python ../portal/manage.py runserver 0.0.0.0:8001 &


