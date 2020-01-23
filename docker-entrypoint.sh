#!/bin/bash
set -e

HOST_DOMAIN="host.docker.internal"
ping -q -c1 $HOST_DOMAIN > /dev/null 2>&1
if [ $? -ne 0 ]; then
  HOST_IP=$(ip route | awk 'NR==1 {print $3}')
  echo -e "$HOST_IP\t$HOST_DOMAIN" >> /etc/hosts
fi

if [[ "$1" = 'showtime' ]]; then
    exec uwsgi --master --socket :3031 --module cadence13.api.showtime.app --callable app --need-app --py-autoreload 2
elif [[ "$1" = 'showpage' ]]; then
    exec uwsgi --master --socket :3031 --module cadence13.api.showpage.app --callable app --need-app --py-autoreload 2
fi

exec "$@"
