#!/bin/sh

set -eu

WORKDIR=$(dirname "$0")
# shellcheck source=/dev/null
. env.public
# shellcheck source=/dev/null
. env.private

DATABASE_URL="postgresql://$DATABASE_USER:$DATABASE_PASSWORD@$DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME"
if [ "$DATABASE_HOST" = "localhost" ]; then ADD_HOST=host-gateway; else ADD_HOST="$DATABASE_HOST"; fi

docker run -v "$WORKDIR:/workdir" --rm --name kingfisher-collect \
    --add-host=postgres:"$ADD_HOST" \
    kingfisher-collect \
    scrapy crawl $KINGFISHER_COLLECT_SPIDER \
    -a crawl_time=2015-01-01T00:00:00 \
    -s "FILES_STORE=/workdir/data" \
    -s "DATABASE_URL=postgresql://$DATABASE_USER:$DATABASE_PASSWORD@postgres:$DATABASE_PORT/$DATABASE_NAME" \
    --logfile="/workdir/logs/kingfisher_collect-$(date +%F).log"

psql "$DATABASE_URL" -t \
    -c "SELECT data FROM $KINGFISHER_COLLECT_SPIDER" \
    -o "$WORKDIR/scratch/kingfisher_collect.jsonl"

docker run -v "$WORKDIR:/workdir" --rm --name cardinal-rs cardinal-rs \
    prepare \
    -s /workdir/cardinal.ini \
    -o /workdir/scratch/cardinal_prepare.out.jsonl \
    -e /workdir/scratch/cardinal_prepare.err.csv \
    /workdir/scratch/kingfisher_collect.jsonl
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/kingfisher_collect.jsonl"
fi

if [ -s "$WORKDIR/scratch/cardinal_prepare.err.csv" ]; then
    echo "$WORKDIR/scratch/cardinal_prepare.err.csv contains new errors"
    exit 1
fi

docker run -v "$WORKDIR:/workdir" --rm --name cardinal-rs cardinal-rs \
    indicators \
    -s /workdir/cardinal.ini \
    --map \
    /workdir/scratch/cardinal_prepare.out.jsonl \
    > "$WORKDIR/scratch/cardinal_indicators.json"

# This appends to the CSV file, to keep flags consistent over time. Delete it manually if results are incorrect.
docker run -v "$WORKDIR:/workdir" --rm --name kingfisher-collect kingfisher-collect \
    python manage.py json-to-csv \
    -q /workdir/scratch/cardinal_indicators.json \
    /workdir/scratch/cardinal_indicators.csv
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/cardinal_indicators.json"
fi

psql "$DATABASE_URL" -q \
    -c "BEGIN" \
    -c "DROP TABLE IF EXISTS ${KINGFISHER_COLLECT_SPIDER}_clean" \
    -c "CREATE TABLE ${KINGFISHER_COLLECT_SPIDER}_clean (data jsonb)" \
    -c "\copy ${KINGFISHER_COLLECT_SPIDER}_clean (data) from stdin csv quote e'\x01' delimiter e'\x02'" \
    -c "CREATE INDEX idx_${KINGFISHER_COLLECT_SPIDER}_clean ON ${KINGFISHER_COLLECT_SPIDER}_clean (cast(data->>'date' as text))" \
    -c "END" \
    < "$WORKDIR/scratch/cardinal_prepare.out.jsonl"
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/cardinal_prepare.out.jsonl"
fi

psql "$DATABASE_URL" -q \
    -c "BEGIN" \
    -c "DROP TABLE IF EXISTS ${KINGFISHER_COLLECT_SPIDER}_result" \
    -c "CREATE TABLE IF NOT EXISTS ${KINGFISHER_COLLECT_SPIDER}_result (id serial PRIMARY KEY, ocid text, subject text, code text, result numeric, buyer_id text, procuring_entity_id text, tenderer_id text, created_at timestamp without time zone)" \
    -c "\copy ${KINGFISHER_COLLECT_SPIDER}_result (ocid, subject, code, result, buyer_id, procuring_entity_id, tenderer_id, created_at) from stdin csv header" \
    -c "END" \
    < "$WORKDIR/scratch/cardinal_indicators.csv"
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/cardinal_indicators.csv"
fi
