#!/usr/bin/env python
import json
import os
from functools import partial
from pathlib import Path

import click
import ijson
import psycopg2
import requests
from ocdskit.combine import merge
from psycopg2 import extras, sql
from pymongo import MongoClient

TARGET_TABLE_NAME_PREFIX = "mexico_nuevo_leon"
COLLECTIONS = [
    "db_sheet_plan_anual",
    "db_provider_data",
    "sheet_contests",
    "sheet_dependencias",
    "ocds_internal",
    "ocds_external",
]


class Json(extras.Json):
    def dumps(self, obj):
        return json.dumps(obj, default=str)  # pymongo decodes to native datetimes


# Adapted from kingfisher-collect/kingfisher_scrapy/extensions/database_store.py
def yield_items_from_directory(crawl_directory):
    for root, _, files in os.walk(crawl_directory):
        root_path = Path(root)
        for name in files:
            if name.endswith(".json"):
                with (root_path / name).open("rb") as f:
                    yield from ijson.items(f, "releases.item")


def update_target_database(connection, collection, data):
    table = f"{TARGET_TABLE_NAME_PREFIX}_{collection}"
    with connection, connection.cursor() as cursor:
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {table}").format(table=sql.Identifier(table)))
        cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {table} (data jsonb)").format(table=sql.Identifier(table)))
        statement = sql.SQL("INSERT INTO {table} (data) VALUES %s").format(table=sql.Identifier(table))
        extras.execute_values(cursor, statement.as_string(cursor), [(Json(item),) for item in data])


@click.command(context_settings={"show_default": True})
@click.argument("collections", nargs=-1, required=False, type=click.Choice(COLLECTIONS))
@click.option(
    "--source-db-url",
    envvar="BI_SOURCE_DB_URL",
    default="localhost",
    help="MongoDB source database URL",
)
@click.option(
    "--source-db-name",
    envvar="BI_SOURCE_DB_NAME",
    default="nuevo_leon",
    help="MongoDB source database name",
)
@click.option(
    "--target-db-url",
    envvar="BI_TARGET_DB_URL",
    default="postgresql:///kingfisher_collect?application_name=bi.open-contracting.org",
    help="PostgreSQL target database URL",
)
@click.option(
    "--files-store-path",
    envvar="BI_FILES_STORE_PATH",
    default="data",
    help="Path to store OCDS files",
)
@click.option(
    "--ocds-external-collection-name",
    help="Source collection name to consume the external OCDS data, instead of using CKAN",
)
def main(collections, source_db_url, source_db_name, target_db_url, files_store_path, ocds_external_collection_name):
    if not collections:
        collections = COLLECTIONS

    source_database_connection = MongoClient(source_db_url)
    target_database_connection = psycopg2.connect(target_db_url)

    update = partial(update_target_database, target_database_connection)

    try:
        source_database = source_database_connection[source_db_name]

        for collection in (
            "db_sheet_plan_anual",
            "db_provider_data",
            "sheet_contests",
            "sheet_dependencias",
        ):
            if collection in collections:
                update(collection, source_database[collection].find({}, {"_id": False}))

        if "ocds_internal" in collections:
            update(
                "ocds_internal",
                merge(
                    json.loads(json.dumps(item, default=str))  # pymongo decodes to native datetimes
                    for item in source_database["db_release_ocds_detalle"].find({}, {"_id": False})
                ),
            )

        if "ocds_external" in collections:
            if ocds_external_collection_name:
                update(
                    "ocds_external",
                    merge(
                        json.loads(json.dumps(item, default=str))  # pymongo decodes to native datetimes
                        for item in source_database[ocds_external_collection_name].find({}, {"_id": False})
                    ),
                )
            else:
                response = requests.get(
                    "https://catalogodatos.nl.gob.mx/api/3/action/package_show?id=contrataciones-abiertas-direccion"
                    "-general-de-adquisiciones-y-servicios",
                    verify=False,  # noqa: S501
                    timeout=10,
                )
                response.raise_for_status()

                files_store_path = Path(files_store_path)
                files_store_path.mkdir(parents=True, exist_ok=True)
                existing = {file.name for file in files_store_path.iterdir()}

                for resource in response.json()["result"]["resources"]:
                    filename = f"{resource['name']}.json"
                    # Note: We would need to delete old files if the publisher changes any.
                    if filename.upper().startswith("JSON-OCDS") and filename not in existing:
                        response = requests.get(resource["url"], verify=False, timeout=180)  # noqa: S501
                        response.raise_for_status()
                        (files_store_path / filename).write_bytes(response.content)

                update("ocds_external", merge(yield_items_from_directory(files_store_path)))
    finally:
        source_database_connection.close()
        target_database_connection.close()
        del update  # prevent use of stale connections, in case this code is modified


if __name__ == "__main__":
    main()
