import json
import os
import psycopg2.sql
from pymongo import MongoClient

COLLECTIONS_TO_LOAD = ['db_sheet_plan_anual', 'provider_contests', 'provider_data', 'sheet_contests',
                       'sheet_dependencias']

TARGET_TABLE_NAME_PREFIX = 'mexico_nuevo_leon'


class DataLoader:
    def __init__(self, source_database_url, source_database_name, target_database_url):
        self.source_database_url = source_database_url
        self.target_database_url = target_database_url
        self.source_database_name = source_database_name

        self.source_database = None
        self.target_database_connection = None
        self.cursor = None

    def connect(self):
        self.target_database_connection = psycopg2.connect(self.target_database_url)
        self.cursor = self.target_database_connection.cursor()

        self.source_database = MongoClient(self.source_database_url)[self.source_database_name]

    def save_to_target(self, table_name):
        try:
            table_name = f'{TARGET_TABLE_NAME_PREFIX}_{table_name}'
            self.connect()
            self.cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
            self.cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} (data jsonb)')
            for item in self.source_database[table_name].find({}, {'_id': False}):
                self.cursor.execute(
                    f'insert into {table_name} (data) values (%s)', (json.dumps(item, default=str), )
                )
            self.target_database_connection.commit()
        finally:
            self.cursor.close()
            self.target_database_connection.close()


def main():
    dataloader = DataLoader(os.getenv('NUEVO_LEON_SOURCE_DB_URL', 'mongodb://root:example@localhost:27017'),
                            os.getenv('NUEVO_LEON_SOURCE_DB_NAME', 'nuevo_leon'),
                            os.getenv('NUEVO_LEON_TARGET_DB_URL',
                                      'postgresql://postgres:postgres@localhost:5432/postgres'))
    for collection in COLLECTIONS_TO_LOAD:
        dataloader.save_to_target(collection)


if __name__ == '__main__':
    main()
