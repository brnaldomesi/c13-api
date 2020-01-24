#!/bin/bash
set -e

if [[ "$1" = 'showtime' ]]; then
    exec uwsgi --master --socket :3031 --module cadence13.api.showtime.app --callable app --need-app --py-autoreload 2
elif [[ "$1" = 'showpage' ]]; then
    exec uwsgi --master --socket :3031 --module cadence13.api.showpage.app --callable app --need-app --py-autoreload 2
fi

exec "$@"
