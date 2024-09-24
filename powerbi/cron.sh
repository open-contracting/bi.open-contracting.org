#!/bin/sh

set -eu

WORKDIR=$(dirname "$0")
# shellcheck source=/dev/null
. config.mk
# shellcheck source=/dev/null
. env.list

DATABASE_URL="postgresql://$DATABASE_USER:$DATABASE_PASSWORD@$DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME"
if [ "$DATABASE_HOST" = "localhost" ]; then ADD_HOST=host-gateway; else ADD_HOST="$DATABASE_HOST"; fi

docker run -v "$WORKDIR:/workdir" --rm --name kingfisher-collect \
    --add-host=postgres:"$ADD_HOST" \
    kingfisher-collect \
    scrapy crawl ecuador_sercop_bulk \
    -a crawl_time=2015-01-01T00:00:00 \
    -s "FILES_STORE=/workdir/data" \
    -s "DATABASE_URL=postgresql://$DATABASE_USER:$DATABASE_PASSWORD@postgres:$DATABASE_PORT/$DATABASE_NAME" \
    --logfile="/workdir/logs/ecuador_sercop_bulk-$(date +%F).log"

psql "$DATABASE_URL" -t \
    -c 'SELECT data FROM ecuador_sercop_bulk' \
    -o "$WORKDIR/scratch/ecuador_sercop_bulk.jsonl"

docker run -v "$WORKDIR:/workdir" --rm --name cardinal-rs cardinal-rs \
    prepare \
    -s /workdir/ecuador_sercop_bulk.ini \
    -o /workdir/scratch/ecuador_sercop_bulk.out.jsonl \
    -e /workdir/scratch/ecuador_sercop_bulk.err.csv \
    /workdir/scratch/ecuador_sercop_bulk.jsonl
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/ecuador_sercop_bulk.jsonl"
fi

if [ -s "$WORKDIR/scratch/ecuador_sercop_bulk.err.csv" ]; then
    echo "$WORKDIR/scratch/ecuador_sercop_bulk.err.csv contains new errors"
    exit 1
fi

docker run -v "$WORKDIR:/workdir" --rm --name cardinal-rs cardinal-rs \
    indicators \
    -s /workdir/ecuador_sercop_bulk.ini \
    --map \
    /workdir/scratch/ecuador_sercop_bulk.out.jsonl \
    > "$WORKDIR/scratch/ecuador_sercop_bulk.json"

# This appends to the CSV file, to keep flags consistent over time. Delete it manually if results are incorrect.
docker run -v "$WORKDIR:/workdir" --rm --name kingfisher-collect kingfisher-collect \
    python manage.py json-to-csv \
    -q /workdir/scratch/ecuador_sercop_bulk.json \
    /workdir/scratch/ecuador_sercop_bulk.csv
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/ecuador_sercop_bulk.json"
fi

psql "$DATABASE_URL" -q \
    -c "BEGIN" \
    -c "DROP TABLE IF EXISTS ecuador_sercop_bulk_clean" \
    -c "CREATE TABLE ecuador_sercop_bulk_clean (data jsonb)" \
    -c "\copy ecuador_sercop_bulk_clean (data) from stdin csv quote e'\x01' delimiter e'\x02'" \
    -c "CREATE INDEX idx_ecuador_sercop_bulk_clean ON ecuador_sercop_bulk_clean (cast(data->>'date' as text))" \
    -c "END" \
    < "$WORKDIR/scratch/ecuador_sercop_bulk.out.jsonl"
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/ecuador_sercop_bulk.out.jsonl"
fi

psql "$DATABASE_URL" -q \
    -c "BEGIN" \
    -c "DROP TABLE IF EXISTS ecuador_sercop_bulk_result" \
    -c "CREATE TABLE IF NOT EXISTS ecuador_sercop_bulk_result (id serial PRIMARY KEY, ocid text, subject text, code text, result numeric, buyer_id text, procuring_entity_id text, tenderer_id text, created_at timestamp without time zone)" \
    -c "\copy ecuador_sercop_bulk_result (ocid, subject, code, result, buyer_id, procuring_entity_id, tenderer_id, created_at) from stdin csv header" \
    -c "END" \
    < "$WORKDIR/scratch/ecuador_sercop_bulk.csv"
if [ -z "$CARDINAL_DEBUG" ]; then
    rm -f "$WORKDIR/scratch/ecuador_sercop_bulk.csv"
fi
