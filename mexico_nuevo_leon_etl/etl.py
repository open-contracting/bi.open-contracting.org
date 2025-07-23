import json
import os
from functools import partial
from pathlib import Path

import ijson
import psycopg2
import requests
from ocdskit.combine import merge
from psycopg2 import extras, sql
from pymongo import MongoClient

TARGET_TABLE_NAME_PREFIX = "mexico_nuevo_leon"


class Json(extras.Json):
    def dumps(self, obj):
        # The original datasets contains dates
        return json.dumps(obj, default=str)


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


def main():
    try:
        source_database_connection = MongoClient(
            os.getenv("NUEVO_LEON_SOURCE_DB_URL", "mongodb://root:example@localhost:27017")
        )
        target_database_connection = psycopg2.connect(
            os.getenv("NUEVO_LEON_TARGET_DB_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
        )
        source_database = source_database_connection[os.getenv("NUEVO_LEON_SOURCE_DB_NAME", "nuevo_leon")]
        files_store_path = Path(os.getenv("NUEVO_LEON_FILES_STORE_PATH", "data"))

        update = partial(update_target_database, target_database_connection)

        try:
            for collection in (
                "db_sheet_plan_anual",
                "db_provider_data",
                "sheet_contests",
                "sheet_dependencias",
            ):
                update(collection, source_database[collection].find({}, {"_id": False}))

            # Compile the internal OCDS data, and update the target database.
            update(
                "ocds_internal",
                merge(
                    json.loads(Json(item).dumps(item))  # MongoDB decodes to native datetimes
                    for item in source_database["db_release_ocds_detalle"].find({}, {"_id": False})
                ),
            )

            # Compile the external OCDS data, and update the target database.
            response = requests.get(
                "https://catalogodatos.nl.gob.mx/api/3/action/package_show?id=contrataciones-abiertas-direccion-general-de-adquisiciones-y-servicios",
                verify=False,  # noqa: S501
                timeout=10,
            )
            response.raise_for_status()

            files_store_path.mkdir(parents=True, exist_ok=True)
            existing = {file.name for file in files_store_path.iterdir() if file.name.endswith(".json")}

            for resource in response.json()["result"]["resources"]:
                filename = f"{resource['name']}.json"
                if (
                    filename.upper().startswith("JSON-OCDS") and filename not in existing
                ):  # Note: Delete old files if the publisher changes any
                    response = requests.get(resource["url"], verify=False, timeout=180)  # noqa: S501
                    response.raise_for_status()
                    (files_store_path / filename).write_bytes(response.content)

            update("ocds_external", merge(yield_items_from_directory(files_store_path)))
        finally:
            del update  # prevent use of stale connections, in case this code is modified
    finally:
        source_database_connection.close()
        target_database_connection.close()


if __name__ == "__main__":
    main()
