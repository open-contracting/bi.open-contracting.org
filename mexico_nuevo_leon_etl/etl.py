import json
import os
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


class DataLoader:
    def __init__(self, *, source_database_url, source_database_name, target_database_url, files_store_path):
        self.source_database_url = source_database_url
        self.target_database_url = target_database_url
        self.source_database_name = source_database_name

        self.source_database = None
        self.source_database_client = None
        self.target_database_connection = None

        self.files_store_path = Path(files_store_path)
        self.files_store_path.mkdir(parents=True, exist_ok=True)

    def connect(self):
        self.source_database_client = MongoClient(self.source_database_url)
        self.source_database = self.source_database_client[self.source_database_name]
        self.target_database_connection = psycopg2.connect(self.target_database_url)

    def get_list_of_existing_ocds_files(self):
        return [file for file in Path.iterdir(self.files_store_path) if file.name.endswith(".json")]

    def get_compiled_public_ocds_data(self):
        existing_files = self.get_list_of_existing_ocds_files()
        response = requests.get(
            "https://catalogodatos.nl.gob.mx/api/3/action/package_show?id=contrataciones-abiertas"
            "-direccion-general-de-adquisiciones-y-servicios",
            verify=False,  # noqa: S501
            timeout=10,
        )
        for resource in response.json()["result"]["resources"]:
            resource_file_name = f"{resource['name']}.json"
            if resource_file_name.upper().startswith("JSON-OCDS") and resource_file_name not in existing_files:
                file_name = self.files_store_path / resource_file_name
                json_data = requests.get(resource["url"], verify=False, timeout=180).json()  # noqa: S501
                with Path.open(file_name, "w") as f:
                    json.dump(json_data, f)
        return merge(self.yield_items_from_directory(self.files_store_path))

    def yield_items_from_directory(self, crawl_directory):
        for root, _, files in os.walk(crawl_directory):
            for name in files:
                if name.endswith(".json"):
                    with Path.open(Path(root) / name, "rb") as f:
                        yield from ijson.items(f, "releases.item")

    def save_to_target(self, collection, data=None):
        table = f"{TARGET_TABLE_NAME_PREFIX}_{collection}"

        try:
            self.connect()
            data_to_save = data if data else self.source_database[collection].find({}, {"_id": False})
            with self.target_database_connection, self.target_database_connection.cursor() as cursor:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {table}").format(table=sql.Identifier(table)))
                cursor.execute(
                    sql.SQL("CREATE TABLE IF NOT EXISTS {table} (data jsonb)").format(table=sql.Identifier(table))
                )
                statement = sql.SQL("INSERT INTO {table} (data) VALUES %s").format(table=sql.Identifier(table))
                extras.execute_values(
                    cursor,
                    statement.as_string(cursor),
                    [(Json(item),) for item in data_to_save],
                )
        finally:
            self.source_database = None
            self.source_database_client.close()
            self.target_database_connection.close()


def main():
    dataloader = DataLoader(
        source_database_url=os.getenv("NUEVO_LEON_SOURCE_DB_URL", "mongodb://root:example@localhost:27017"),
        source_database_name=os.getenv("NUEVO_LEON_SOURCE_DB_NAME", "nuevo_leon"),
        target_database_url=os.getenv(
            "NUEVO_LEON_TARGET_DB_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        ),
        files_store_path=os.getenv("NUEVO_LEON_FILES_STORE_PATH", "data"),
    )
    for collection in (
        "db_sheet_plan_anual",
        "db_provider_data",
        "sheet_contests",
        "sheet_dependencias",
    ):
        dataloader.save_to_target(collection)

    dataloader.save_to_target("ocds_public", dataloader.get_compiled_public_ocds_data())


if __name__ == "__main__":
    main()
