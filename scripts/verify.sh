#!/bin/sh
set -eu
docker compose config --quiet
docker compose exec app python manage.py check
docker compose exec app python manage.py test sketches catalog
