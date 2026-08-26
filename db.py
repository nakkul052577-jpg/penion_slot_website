import sqlite3

DB_NAME = "slot_data.db"

def init_db():
    """データベースとテーブルの作成"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slot_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,          -- 'suropachi_web' または 'x_twitter'
            date TEXT,            -- 日付
            hall_name TEXT,       -- 店舗名
            machine_name TEXT,    -- 機種名
            machine_number TEXT,  -- 台番号
            diff_medals INTEGER,  -- 差枚数
            games INTEGER,        -- ゲーム数
            raw_text TEXT,        -- ポスト本文など（X用）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, date, hall_name, machine_number) -- 重複防止
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(data_list):
    """データの一括保存"""
    if not data_list:
        return 0
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.executemany('''
        INSERT OR IGNORE INTO slot_results 
        (source, date, hall_name, machine_name, machine_number, diff_medals, games, raw_text)
        VALUES (:source, :date, :hall_name, :machine_name, :machine_number, :diff_medals, :games, :raw_text)
    ''', data_list)
    
    conn.commit()
    inserted_count = cursor.rowcount
    conn.close()
    return inserted_count