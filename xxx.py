#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# 設定
# ============================================================

# xxx.py と同じフォルダに p_ark_database.db を置いてください
DB_PATH = Path(__file__).resolve().parent / "p_ark_database.db"

# 使用するテーブル
TABLE_NAME = "ピーアーク相模大野_スロパチ"


# ============================================================
# 入力
# ============================================================

def get_year_month():
    while True:
        year_text = input("対象年を入力してください（例: 2026）: ").strip()
        month_text = input("対象月を入力してください（例: 8）: ").strip()

        try:
            year = int(year_text)
            month = int(month_text)

            # 実在する年月か確認
            datetime(year, month, 1)

            return year, month

        except ValueError:
            print("入力が正しくありません。年・月を数字で入力してください。\n")


def get_machine_name():
    return input(
        "機種名を入力してください（空欄で全機種）: "
    ).strip()


# ============================================================
# 次の月
# ============================================================

def get_next_month(year, month):
    if month == 12:
        return year + 1, 1

    return year, month + 1


# ============================================================
# ランキング取得
# ============================================================

def get_ranking(year, month, machine_name):
    start_date = f"{year:04d}/{month:02d}/01"

    next_year, next_month = get_next_month(year, month)
    end_date = f"{next_year:04d}/{next_month:02d}/01"

    # まず対象期間のデータを絞り込み、
    # 台番号ごとの回数を集計します。
    #
    # 機種名は、同じ台番号で期間中に機種変更があった場合でも
    # 「その台番号の期間内で一番新しいデータの機種名」を表示します。
    query = f"""
        WITH filtered AS (
            SELECT
                項番,
                日付,
                機種名,
                台番号
            FROM "{TABLE_NAME}"
            WHERE 日付 >= ?
              AND 日付 < ?
    """

    params = [start_date, end_date]

    # 機種名を指定した場合だけ絞り込み
    if machine_name:
        query += """
            AND 機種名 = ?
        """
        params.append(machine_name)

    query += f"""
        )
        SELECT
            f.台番号,
            (
                SELECT f2.機種名
                FROM filtered f2
                WHERE f2.台番号 = f.台番号
                ORDER BY f2.日付 DESC, f2.項番 DESC
                LIMIT 1
            ) AS 機種名,
            COUNT(*) AS 回数
        FROM filtered f
        GROUP BY f.台番号
        ORDER BY 回数 DESC, CAST(f.台番号 AS INTEGER) ASC
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


# ============================================================
# ランキング表示
# ============================================================

def print_ranking(year, month, machine_name, rows):
    print()
    print("=" * 60)
    print(f"{year}年{month}月 台番号ランキング")

    if machine_name:
        print(f"機種名：{machine_name}")
    else:
        print("機種名：全機種")

    print("=" * 60)

    if not rows:
        print("条件に一致するデータがありません。")
        print("=" * 60)
        return

    print(f"{'順位':<6}{'台番号':<10}{'機種名':<25}{'回数':>8}")
    print("-" * 60)

    # Dense Rank
    #
    # 例：
    # 5回 → 1位
    # 5回 → 1位
    # 4回 → 2位
    # 4回 → 2位
    # 3回 → 3位
    #
    # ユーザー指定の「同じ回数は同じ順位」に合わせています。
    current_rank = 0
    previous_count = None

    for number, machine, count in rows:
        if count != previous_count:
            current_rank += 1
            previous_count = count

        print(
            f"{str(current_rank) + '位':<6}"
            f"{str(number):<10}"
            f"{str(machine):<25}"
            f"{str(count):>8}"
        )

    print("=" * 60)
    print(f"該当台数：{len(rows)}台")


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 60)
    print("台番号重複ランキング")
    print("=" * 60)

    if not DB_PATH.exists():
        print()
        print("DBファイルが見つかりません。")
        print(f"必要なファイル：{DB_PATH.name}")
        print()
        print("xxx.py と同じフォルダに p_ark_database.db を置いてください。")
        return

    year, month = get_year_month()
    machine_name = get_machine_name()

    print()
    print(f"{year}年{month}月のデータを検索しています...")

    if machine_name:
        print(f"機種名：{machine_name}")
    else:
        print("機種名：全機種")

    try:
        rows = get_ranking(year, month, machine_name)

        print_ranking(
            year,
            month,
            machine_name,
            rows
        )

    except sqlite3.Error as e:
        print()
        print("DBの読み込み中にエラーが発生しました。")
        print(f"エラー内容：{e}")


if __name__ == "__main__":
    main()
