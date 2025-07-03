import json
import os

import psycopg2
from psycopg2 import extras, sql
from pymongo import MongoClient

TARGET_TABLE_NAME_PREFIX = "mexico_nuevo_leon"


class Json(extras.Json):
    def dumps(self, obj):
        return json.dumps(obj, default=str)


class DataLoader:
    def __init__(self, *, source_database_url, source_database_name, target_database_url):
        self.source_database_url = source_database_url
        self.target_database_url = target_database_url
        self.source_database_name = source_database_name

        self.source_database = None
        self.source_database_client = None
        self.target_database_connection = None

    def connect(self):
        self.source_database_client = MongoClient(self.source_database_url)
        self.source_database = self.source_database_client[self.source_database_name]
        self.target_database_connection = psycopg2.connect(self.target_database_url)

    def save_to_target(self, collection):
        table = f"{TARGET_TABLE_NAME_PREFIX}_{collection}"

        try:
            self.connect()
            with self.target_database_connection, self.target_database_connection.cursor() as cursor:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {table}").format(table=sql.Identifier(table)))
                cursor.execute(
                    sql.SQL("CREATE TABLE IF NOT EXISTS {table} (data jsonb)").format(table=sql.Identifier(table))
                )
                statement = sql.SQL("INSERT INTO {table} (data) VALUES %s").format(table=sql.Identifier(table))
                extras.execute_values(
                    cursor,
                    statement.as_string(cursor),
                    [(Json(item),) for item in self.source_database[collection].find({}, {"_id": False})],
                )
        finally:
            self.source_database_client.close()
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
        "db_sheet_plan_anual",
        "db_provider_data",
        "sheet_contests",
        "sheet_dependencias",
    ):
        dataloader.save_to_target(collection)


if __name__ == "__main__":
    main()
