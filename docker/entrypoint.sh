#!/bin/sh
set -eu

python -m app migrate
python -m app seed --bookings "${SEED_BOOKINGS:-100000}"
exec python -m app serve --host 0.0.0.0 --port "${PORT:-8000}"
