import os
import psycopg2

DATABASE_URL = os.getenv("postgresql://postgres:FMGmkhnZAhcDMkFfLYVBwsGBcrLGEffF@postgres.railway.internal:5432/railway")

def get_conn():
    return psycopg2.connect(DATABASE_URL)
