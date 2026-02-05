import psycopg
from settings import settings

def get_conn():
    return psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        autocommit=True,
    )
