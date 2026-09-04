import os
import sqlite3
import pandas as pd
from config import BASE_DIR, STORE_CONFIG

def resolve_db_path(filename):
    candidates = [os.path.join(BASE_DIR, filename), os.path.abspath(filename)]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[0]

def quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'

def init_db():
    return

def load_data(store_name):
    config = STORE_CONFIG[store_name]
    db_path = resolve_db_path(config["db_path"])
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"DBファイルが見つかりません: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        existing_tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        slopachi_name = config["slopachi_table"]
        if slopachi_name not in existing_tables:
            raise RuntimeError(
                f"テーブルが見つかりません: {slopachi_name} / DB: {db_path} / "
                f"存在するテーブル: {', '.join(sorted(existing_tables))}")
        df_sp = pd.read_sql_query(
            f"SELECT * FROM {quote_identifier(slopachi_name)} ORDER BY 日付 DESC", conn)
        matomaru_table = config.get("matomaru_table")
        if matomaru_table and matomaru_table in existing_tables:
            df_mt = pd.read_sql_query(
                f"SELECT * FROM {quote_identifier(matomaru_table)} ORDER BY 日付 DESC", conn)
        else:
            df_mt = pd.DataFrame()
    finally:
        conn.close()
    return df_sp, df_mt
