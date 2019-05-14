#!/bin/bash
set -e

if [[ "$1" = 'dashboard' ]]; then
    exec uwsgi --master --http 0.0.0.0:8080 --module cadence13.api.dashboard.app --callable app --py-autoreload 2]
elif [[ "$1" = 'public' ]]; then
    exec uwsgi --master --http 0.0.0.0:8080 --module cadence13.api.public.app --callable app --py-autoreload 2]
fi

exec "$@"
