import json
import os

import psycopg2.extras
import psycopg2.sql
from pymongo import MongoClient

TARGET_TABLE_NAME_PREFIX = "mexico_nuevo_leon"


class Json(psycopg2.extras.Json):
    def dumps(self, obj):
        return json.dumps(obj, default=str)


class DataLoader:
    def __init__(self, *, source_database_url, source_database_name, target_database_url):
        self.source_database_url = source_database_url
        self.target_database_url = target_database_url
        self.source_database_name = source_database_name

        self.source_database = None
        self.target_database_connection = None

    def connect(self):
        self.source_database = MongoClient(self.source_database_url)[self.source_database_name]
        self.target_database_connection = psycopg2.connect(self.target_database_url)

    def save_to_target(self, collection_name):
        table_name = f"{TARGET_TABLE_NAME_PREFIX}_{collection_name}"

        try:
            self.connect()
            with self.target_database_connection, self.target_database_connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (data jsonb)")
                psycopg2.extras.execute_values(
                    cursor,
                    f"INSERT INTO {table_name} (data) VALUES %s",
                    [
                        (Json(item),)
                        for item in self.source_database[collection_name].find({}, {"_id": False})
                    ],
                )
        finally:
            self.source_database.close()
            self.target_database_connection.close()


def main():
    dataloader = DataLoader(
        source_database_url=os.getenv("NUEVO_LEON_SOURCE_DB_URL", "mongodb://root:example@localhost:27017"),
        source_database_name=os.getenv("NUEVO_LEON_SOURCE_DB_NAME", "nuevo_leon"),
        target_database_url=os.getenv(
            "NUEVO_LEON_TARGET_DB_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        ),
    )
    for collection in (
        "contests",
        "db_sheet_plan_anual",
        "provider_contests",
        "provider_data",
        "sheet_contests",
        "sheet_dependencias",
    ):
        dataloader.save_to_target(collection)


if __name__ == "__main__":
    main()
