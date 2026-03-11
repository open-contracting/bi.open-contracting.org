#!/bin/sh

set -eu

WORKDIR=$(dirname "$0")
# shellcheck source=/dev/null
. env.public
# shellcheck source=/dev/null
. env.private

DATABASE_URL="postgresql://$DATABASE_USER:$DATABASE_PASSWORD@$DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME"
if [ "$DATABASE_HOST" = "localhost" ]; then ADD_HOST=host-gateway; else ADD_HOST="$DATABASE_HOST"; fi

# shellcheck disable=SC2086
docker run -v "$WORKDIR:/workdir" --rm --name kingfisher-collect \
    --add-host=postgres:"$ADD_HOST" \
    kingfisher-collect \
    scrapy crawl "$KINGFISHER_COLLECT_SPIDER" \
    -a crawl_time=2015-01-01T00:00:00 $KINGFISHER_COLLECT_SPIDER_ARGUMENTS \
    -s "FILES_STORE=/workdir/data" \
    -s "DATABASE_URL=postgresql://$DATABASE_USER:$DATABASE_PASSWORD@postgres:$DATABASE_PORT/$DATABASE_NAME" \
    --logfile="/workdir/logs/kingfisher_collect-$(date +%F).log"
