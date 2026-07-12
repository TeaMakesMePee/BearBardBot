import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import (
    POSTGRES_HOST, POSTGRES_DB,
    POSTGRES_USER, POSTGRES_PASSWORD
)

def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        cursor_factory=RealDictCursor
    )

def init_db():
    with open("init.sql", "r") as f:
        sql = f.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()
