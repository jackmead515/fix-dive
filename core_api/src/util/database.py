import psycopg2

import config

def get_connection(db_name) -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dbname=db_name,
    )