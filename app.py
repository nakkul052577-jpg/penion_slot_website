import os
import time
import sqlite3
import base64
import calendar
import re
import random
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. ページ基本設定・認証設定
# ==========================================

st.set_page_config(
    page_title="PENION ANALYTICS",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

AUTH_PASSWORD = "complete777"

# DBは「実行したターミナルのカレントフォルダ」ではなく、
# このPythonファイルが置かれているフォルダを基準に読み込む。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resolve_db_path(filename):
    """
    DBの実体を確実に探す。
    1. このPythonファイルと同じフォルダ
    2. Streamlitを実行した現在のフォルダ
    の順に確認する。
    """
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.abspath(filename),
    ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    # 見つからない場合も、最も自然な配置場所を返す。
    # load_data()側で存在チェックを行い、SQLiteが空DBを新規作成するのを防ぐ。
    return candidates[0]

# 日本語カレンダーは外部パッケージを使わず、このファイル内で実装しています。



# ==========================================
# ミニゲーム用画像
# このPythonファイルと同じフォルダに配置
# ==========================================
LOTTERY_RED_IMAGE = os.path.join(BASE_DIR, "lottery_red.png")
LOTTERY_GOLD_IMAGE = os.path.join(BASE_DIR, "lottery_gold.png")
LOTTERY_RAINBOW_IMAGE = os.path.join(BASE_DIR, "lottery_rainbow.png")

# ==========================================
# 2. データベース初期化＆ロード処理
# ==========================================

STORE_CONFIG = {
    "ピーアーク相模大野": {
        "db_path": "database.db",
        "slopachi_table": "ピーアーク相模大野_スロパチ",
        "matomaru_table": "ピーアーク相模大野_まとまる君",
        "map": "p_ark",
    },
    "メガフェイス1180座間店": {
        "db_path": "database.db",
        "slopachi_table": "メガフェイス1180座間店_スロパチ",
        "matomaru_table": None,
        "map": "megaface_zama",
    },
}


def quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


def init_db():
    """
    既存DBは一切変更しない。
    以前の実装ではDBが見つからない場合でもSQLiteが空のDBを作成し、
    「データがありません」という分かりにくい状態になっていたため、
    ここではDBやテーブルを自動作成しない。
    """
    return


def load_data(store_name):
    """選択した店舗の既存DB・既存テーブルだけを安全に読み込む。"""
    config = STORE_CONFIG[store_name]
    db_path = resolve_db_path(config["db_path"])

    # sqlite3.connect() は存在しないパスでも空DBを作ってしまうため、
    # 必ず先に存在確認を行う。
    if not os.path.isfile(db_path):
        raise FileNotFoundError(
            f"DBファイルが見つかりません: {db_path}"
        )

    conn = sqlite3.connect(db_path)

    try:
        existing_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        slopachi_name = config["slopachi_table"]
        if slopachi_name not in existing_tables:
            raise RuntimeError(
                f"テーブルが見つかりません: {slopachi_name} / "
                f"DB: {db_path} / 存在するテーブル: {', '.join(sorted(existing_tables))}"
            )

        table_sp = quote_identifier(slopachi_name)
        df_sp = pd.read_sql_query(
            f"SELECT * FROM {table_sp} ORDER BY 日付 DESC",
            conn,
        )

        matomaru_table = config.get("matomaru_table")
        if matomaru_table and matomaru_table in existing_tables:
            table_mt = quote_identifier(matomaru_table)
            df_mt = pd.read_sql_query(
                f"SELECT * FROM {table_mt} ORDER BY 日付 DESC",
                conn,
            )
        else:
            df_mt = pd.DataFrame()

    finally:
        conn.close()

    return df_sp, df_mt

# ==========================================
# 島図表示（ランキング完全連動・HTML/SVG描画）
# ==========================================
# 以前の版は元の島図画像の上に色を重ねていました。
# 元画像そのものに色付きセルが含まれていたため、日付を変更しても
# 元画像の色が残ってしまう問題がありました。
# 今回は画像を一切使わず、台番号・配置・枠・色を画面上で直接描画します。

import hashlib
import html as html_lib
import json

ISLAND_CANVAS_SIZE = (2050, 700)
ISLAND_CELL_W = 37
ISLAND_CELL_H = 19

ISLAND_RANK_COLORS = {
    1: "#ff1b1b",
    2: "#a900d6",
    3: "#df4be8",
    4: "#13a84a",
    5: "#ffb300",
    6: "#ffe000",
    7: "#087bb9",
    8: "#00a9d8",
    9: "#a9a9a9",
}
ISLAND_DEFAULT_COLOR = "#f7f7f7"
ISLAND_BORDER_COLOR = "#7b7b7b"
ISLAND_TEXT_COLOR = "#4a4a4a"


def _add_island_row(position_map, numbers, y, xs=None, x0=180, step=42):
    numbers = list(numbers)
    if xs is None:
        xs = [x0 + i * step for i in range(len(numbers))]

    # 2枚目の島図に合わせた座標変換
    # 元の x=180 を画面上 x=166 に合わせ、
    # 全体を 0.883 倍に縮小して横方向の間隔を一致させる。
    # y も同じ比率で縮小し、上端を y=34 に合わせる。
    X_SCALE = 0.883
    Y_SCALE = 0.883
    X_OFFSET = 166
    Y_OFFSET = 34

    for number, x in zip(numbers, xs):
        mapped_x = round(X_OFFSET + (x - 180) * X_SCALE)
        mapped_y = round(Y_OFFSET + (y - 46) * Y_SCALE)
        position_map.setdefault(str(number), []).append((mapped_x, mapped_y))


def build_p_ark_island_positions():
    m = {}

    _add_island_row(m, range(2245, 2264), 46)
    _add_island_row(m, range(2282, 2301), 109)
    _add_island_row(m, range(2283, 2301), 130)

    _add_island_row(m, range(2313, 2301, -1), 193)
    _add_island_row(m, range(2314, 2326), 214)

    _add_island_row(m, range(2335, 2330, -1), 277,
                    xs=[180, 222, 264, 306, 348])
    _add_island_row(m, range(2330, 2325, -1), 277,
                    xs=[474, 516, 558, 600, 642])
    _add_island_row(m, range(2336, 2348), 298)

    _add_island_row(m, range(2362, 2347, -1), 361)
    _add_island_row(m, range(2363, 2378), 382)

    _add_island_row(m, range(2390, 2385, -1), 445,
                    xs=[180, 222, 264, 306, 348])
    _add_island_row(m, range(2385, 2377, -1), 445,
                    xs=[432, 474, 516, 558, 600, 642, 684, 726])
    _add_island_row(m, range(2391, 2405), 466)

    _add_island_row(m, range(2416, 2404, -1), 529)
    _add_island_row(m, range(2417, 2429), 550)

    _add_island_row(m, range(2440, 2428, -1), 613)
    _add_island_row(m, range(2441, 2453), 634)

    for i, number in enumerate(range(2481, 2471, -1)):
        _add_island_row(m, [number], 676 + i * 21, xs=[106])

    _add_island_row(m, [2482], 739, xs=[306])
    _add_island_row(m, [2483], 760, xs=[306])
    _add_island_row(m, [2484, 2485, 2486], 781,
                    xs=[348, 390, 432])
    _add_island_row(m, [2488], 739, xs=[474])
    _add_island_row(m, [2487], 760, xs=[474])
    _add_island_row(m, range(2471, 2462, -1), 865,
                    xs=[264, 306, 348, 390, 432, 474, 516, 558, 600])

    for i, number in enumerate(range(2453, 2463)):
        _add_island_row(m, [number], 676 + i * 21, xs=[726])

    _add_island_row(m, range(2013, 2031), 46, x0=1230)
    _add_island_row(m, range(2039, 2030, -1), 151, x0=1398)
    _add_island_row(m, range(2040, 2049), 172, x0=1398)

    _add_island_row(m, [2002, 2003], 193, xs=[936, 978])
    for i, number in enumerate([2001, 2012, 2011, 2010]):
        _add_island_row(m, [number], 214 + i * 21, xs=[894])
    for i, number in enumerate([2004, 2005, 2006, 2007]):
        _add_island_row(m, [number], 214 + i * 21, xs=[1020])
    _add_island_row(m, [2009, 2008], 298, xs=[936, 978])

    _add_island_row(m, range(2062, 2048, -1), 235, x0=1230)
    _add_island_row(m, range(2063, 2077), 256, x0=1230)

    _add_island_row(m, range(2089, 2074, -1), 319, x0=1188)
    _add_island_row(m, range(2090, 2105), 340, x0=1188)

    _add_island_row(m, range(2121, 2104, -1), 403, x0=1104)
    _add_island_row(m, range(2122, 2141), 424, x0=1020)

    _add_island_row(m, range(2146, 2151), 529, x0=936)
    _add_island_row(m, range(2145, 2140, -1), 550, x0=936)

    _add_island_row(m, range(2151, 2159), 613, x0=936)
    _add_island_row(m, range(2186, 2178, -1), 634, x0=936)
    _add_island_row(m, range(2159, 2169), 613, x0=1398)
    _add_island_row(m, range(2178, 2168, -1), 634, x0=1398)

    # 2187～2204
    # 2185・2186 の重複ブロックは島図には存在しないため描画しない
    _add_island_row(m, range(2187, 2205), 718, x0=936)

    # 2222～2205
    # 2222 の重複・2223 の混入を修正
    _add_island_row(
        m,
        range(2222, 2204, -1),
        739,
        x0=936,
    )

    _add_island_row(m, range(2223, 2245), 823, x0=936)

    for i, number in enumerate(range(2519, 2509, -1)):
        _add_island_row(m, [number], 151 + i * 21, xs=[1944])
    for i, number in enumerate(range(2509, 2499, -1)):
        _add_island_row(m, [number], 508 + i * 21, xs=[1944])

    # 2531 と 2532 の間に実際の島図どおりの空白を入れる
    _add_island_row(
        m,
        list(range(2520, 2532)),
        844,
        x0=936,
    )
    _add_island_row(
        m,
        list(range(2532, 2541)),
        844,
        x0=936 + 42 * 13,
    )

    for i, number in enumerate(range(2541, 2547)):
        _add_island_row(m, [number], 781 + i * 21, xs=[1944])

    _add_island_row(m, range(2568, 2546, -1), 907, x0=936)

    return m


P_ARK_ISLAND_POSITIONS = build_p_ark_island_positions()



# ==========================================
# メガフェイス1180座間店 島図
# ユーザー提供の島図画像に合わせた台番号配置
# ==========================================

def _add_raw_row(position_map, numbers, y, x0, step=40):
    for i, number in enumerate(numbers):
        position_map.setdefault(str(number), []).append((x0 + i * step, y))


def build_megaface_zama_positions():
    """
    メガフェイス1180座間店の島図。
    ユーザー提供の基準画像（2048×698）に合わせて座標を作り直した版。
    1つの台番号につき1つの座標だけを登録し、重なりを発生させない。
    """
    m = {}

    # 同じ台番号が島図内の複数箇所に表示されるケースがあるため、
    # 代入で上書きせず、座標を追加する。
    def add(number, x, y):
        key = str(number)
        m.setdefault(key, []).append((x, y))

    def row(numbers, y, x0, step=40):
        for i, number in enumerate(numbers):
            add(number, x0 + i * step, y)

    def col(numbers, x, y0, step=20):
        for i, number in enumerate(numbers):
            add(number, x, y0 + i * step)

    # ===== 左上ブロック =====
    row(range(870, 884), 45, 315)
    row(range(869, 856, -1), 65, 355)
    row(range(843, 857), 105, 315)
    row(range(842, 828, -1), 125, 315)
    row(range(812, 829), 175, 205)
    row(range(811, 796, -1), 195, 225)

    # ===== 左中央・折れ島 =====
    col([735, 734, 733, 732, 731, 730, 729, 728, 727], 115, 285)
    col([739, 740, 741, 742], 155, 325)
    row([743], 385, 195)
    row([744], 425, 155)
    row([726, 725, 724], 445, 150)
    row([723], 425, 280)

    # 左中央横島
    row(range(769, 782), 325, 355)
    row(range(768, 781, -1), 345, 315)
    row(range(765, 755, -1), 385, 390)
    row(range(744, 755), 425, 420)
    row(range(720, 710, -1), 445, 420)
    row([721], 405, 315)
    row([722], 425, 315)

    # ===== 左下 =====
    row(range(692, 710), 520, 165)
    row(range(691, 676, -1), 540, 315)
    row(range(656, 677), 590, 60)
    row(range(655, 634, -1), 610, 60)
    row(range(614, 635), 665, 60)

    # ===== 中央上 789番台 =====
    row(range(789, 796), 245, 565)
    row(range(788, 781, -1), 265, 565)

    # ===== 中央上・1100番台の折れ島 =====
    row([1105, 1106, 1107], 80, 1040)
    row([1104], 100, 1000)
    row([1108], 100, 1160)
    row([1103, 1102], 120, 1040)
    col([1101, 1100], 1115, 140)
    col([1109, 1110, 1111, 1112], 1200, 140)
    row([1098, 1099], 180, 1040)
    row([1117], 200, 1000)
    row([1116, 1115, 1114], 220, 1040)
    row([1113], 200, 1160)

    # ===== 中央 1050・1040番台 =====
    # ここは以前 step=0 で重なっていたため、縦配置に修正
    col([1045, 1046, 1047, 1048, 1049, 1050], 1220, 245)
    col([1059, 1058, 1057], 970, 305)
    row([1056], 385, 1000)
    row([1055, 1054, 1053, 1052], 405, 1040)
    row([1051], 385, 1200)

    # ===== 中央横長 900番台 =====
    row(range(925, 941), 445, 965)
    row(range(364, 349, -1), 465, 1040)

    # ===== 330番台 =====
    row(range(331, 351), 520, 965)
    row(range(330, 315, -1), 540, 1080)

    # ===== 290番台 =====
    row(range(295, 314), 590, 1040)
    row(range(294, 272, -1), 610, 965)

    # ===== 250番台 =====
    row(range(253, 275), 665, 965)

    # ===== 右上長島 =====
    row(range(1151, 1134, -1), 180, 1340)
    row(range(1118, 1135), 230, 1335)
    row(range(1117, 1133, -1), 250, 1335)

    # ===== 右中央 1000番台 =====
    row(range(1067, 1081), 305, 1335)
    row(range(1011, 996, -1), 325, 1335)

    # ===== 右中央の折れ島 =====
    # Excel画像の形に合わせて、上段・下段・縦列を個別配置。
    row([956, 957, 958, 959, 960, 961], 375, 1340)
    row([979, 978, 977, 976, 975, 974], 395, 1340)

    # 左側の縦列
    col([973, 972, 971, 970, 969], 1620, 375)

    # 上側の折れ部分
    row([995, 994, 993], 395, 1660)
    row([992], 435, 1660)
    row([991, 990], 455, 1700)
    row([989], 435, 1780)
    row([988, 987, 986], 395, 1780)

    # 下側の折れ部分
    row([968], 475, 1660)
    row([967, 966], 495, 1700)
    row([965], 475, 1780)
    row([964], 455, 1860)

    # Excelでは 961〜963 が右側に縦配置されているため、
    # 上段の961を残したまま別座標を追加する。
    col([961, 962, 963], 1860, 415)

    # ===== 右端縦列 =====
    col([960, 959, 958, 957], 1980, 180)
    col([955, 953, 952, 951, 950, 949, 948], 1980, 285)
    col([946, 945, 944, 943, 941], 1980, 445)

    return m

MEGAFACE_ZAMA_ISLAND_POSITIONS = build_megaface_zama_positions()


def get_island_positions(store_name):
    if STORE_CONFIG.get(store_name, {}).get("map") == "megaface_zama":
        return MEGAFACE_ZAMA_ISLAND_POSITIONS
    return P_ARK_ISLAND_POSITIONS

def _normalise_ranking_for_map(ranking_df):
    rank_map = {}
    if ranking_df is None or ranking_df.empty:
        return rank_map
    if not {"順位", "台番号"}.issubset(ranking_df.columns):
        return rank_map

    for _, row_data in ranking_df.iterrows():
        machine_number = str(row_data.get("台番号", "")).strip()
        if not machine_number:
            continue
        try:
            rank = int(row_data.get("順位", 0))
        except (TypeError, ValueError):
            continue
        try:
            count = int(row_data.get("回数", 0))
        except (TypeError, ValueError):
            count = 0
        rank_map[machine_number] = {
            "rank": rank,
            "count": count,
            "machine": str(row_data.get("機種名", "")),
        }
    return rank_map


def _island_rank_signature(rank_map):
    payload = json.dumps(
        rank_map,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _svg_escape(value):
    return html_lib.escape(str(value), quote=True)


def render_island_map(ranking_df, store_name):
    """画像を使わずSVGで島図を描画し、ランキング変更に完全連動させる。"""
    rank_map = _normalise_ranking_for_map(ranking_df)
    island_positions = get_island_positions(store_name)
    signature = _island_rank_signature(rank_map)

    cells = []
    seen = set()

    for machine_number, positions in island_positions.items():
        for x, y in positions:
            coord_key = (machine_number, x, y)
            if coord_key in seen:
                continue
            seen.add(coord_key)

            info = rank_map.get(machine_number)
            if info is None:
                fill = ISLAND_DEFAULT_COLOR
                text_color = ISLAND_TEXT_COLOR
                stroke = ISLAND_BORDER_COLOR
                rank_text = ""
                tooltip = f"台番号 {machine_number}"
            else:
                rank = info["rank"]
                fill = ISLAND_RANK_COLORS.get(rank, ISLAND_RANK_COLORS[9])
                text_color = "#111111" if rank in (5, 6, 8, 9) else "#ffffff"
                stroke = "#333333"
                rank_text = f"{rank}位"
                tooltip = (
                    f"{rank}位 / 台番号 {machine_number} / "
                    f"{info['machine']} / {info['count']}回"
                )

            rank_badge = ""
            if rank_text:
                rank_badge = (
                    f'<text x="{x + ISLAND_CELL_W - 2}" y="{y + 7}" '
                    f'text-anchor="end" font-size="6.5" font-weight="800" '
                    f'fill="{text_color}">{_svg_escape(rank_text)}</text>'
                )

            cells.append(
                f'<g class="island-machine" data-machine="{_svg_escape(machine_number)}" '
                f'data-signature="{signature}">'
                f'<title>{_svg_escape(tooltip)}</title>'
                f'<rect x="{x}" y="{y}" width="{ISLAND_CELL_W}" height="{ISLAND_CELL_H}" '
                f'rx="1.5" ry="1.5" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
                f'<text x="{x + ISLAND_CELL_W / 2}" y="{y + 15}" text-anchor="middle" '
                f'font-size="12" font-family="Arial, Noto Sans JP, sans-serif" font-weight="500" '
                f'fill="{text_color}">{_svg_escape(machine_number)}</text>'
                f'{rank_badge}</g>'
            )

    legend = [
        '<rect x="20" y="20" width="70" height="205" rx="3" fill="#ffffff" stroke="#777777" stroke-width="1"/>',
        '<text x="55" y="35" text-anchor="middle" font-size="12" font-weight="700" font-family="Arial, sans-serif" fill="#444444">順位</text>',
    ]
    for rank in range(1, 10):
        y = 42 + (rank - 1) * 20
        color = ISLAND_RANK_COLORS[rank]
        legend.append(
            f'<rect x="25" y="{y}" width="60" height="18" fill="{color}" stroke="#555555" stroke-width=".7"/>'
        )
        label_color = "#111111" if rank in (5, 6, 8, 9) else "#ffffff"
        legend.append(
            f'<text x="55" y="{y + 13}" text-anchor="middle" font-size="11" font-weight="700" '
            f'font-family="Arial, sans-serif" fill="{label_color}">{rank}</text>'
        )


    svg = (
        f'<svg class="island-svg" viewBox="0 0 {ISLAND_CANVAS_SIZE[0]} {ISLAND_CANVAS_SIZE[1]}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="台番号島図">'
        f'<rect x="0" y="0" width="{ISLAND_CANVAS_SIZE[0]}" height="{ISLAND_CANVAS_SIZE[1]}" fill="#fafafa"/>'
        f'{"".join(legend)}'
        f'{"".join(cells)}'
        f'<text x="{ISLAND_CANVAS_SIZE[0] / 2}" y="28" text-anchor="middle" font-size="14" font-weight="800" '
        f'font-family="Arial, Noto Sans JP, sans-serif" fill="#555555">{_svg_escape(store_name)} / 台番号ランキング</text>'
        f'</svg>'
    )

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:#070912; }}
body {{ font-family:Arial,"Noto Sans JP",sans-serif; }}
.map-card {{ width:100%; background:#fff; border:1px solid rgba(255,255,255,.12); border-radius:14px; overflow:hidden; }}
.toolbar {{ height:46px; display:flex; align-items:center; justify-content:space-between; padding:0 12px; background:#111522; color:#f5f7ff; font-size:13px; font-weight:700; }}
.toolbar button {{ border:1px solid rgba(255,255,255,.2); background:#1b2131; color:#fff; border-radius:7px; padding:5px 10px; cursor:pointer; font-weight:700; }}
.toolbar button:hover {{ background:#2a3247; }}
.map-scroll {{ width:100%; overflow:auto; -webkit-overflow-scrolling:touch; background:#fafafa; padding:8px; }}
.map-stage {{ position:relative; width:2050px; height:700px; transform-origin:top left; }}
.island-svg {{ display:block; width:2050px; height:700px; user-select:none; }}
.island-machine {{ cursor:default; }}
.island-machine rect {{ transition:filter .12s, stroke-width .12s; }}
.island-machine:hover rect {{ filter:brightness(1.06) drop-shadow(0 1px 2px rgba(0,0,0,.25)); stroke-width:2; }}
.zoom-label {{ min-width:45px; text-align:center; }}
.hint {{ padding:8px 12px; background:#fafafa; color:#777; font-size:11px; text-align:center; border-top:1px solid #ddd; }}

/* ===== スマホ対応：ダッシュボード上部 ===== */
.dashboard-header {{ width:100%; min-width:0; box-sizing:border-box; }}
.dashboard-kicker {{ font-family:Orbitron,sans-serif; font-size:11px; letter-spacing:2px; color:#8e98b0; margin-bottom:3px; }}
.dashboard-main-title {{ width:100%; color:#f8f9ff; font-size:42px; line-height:1.18; font-weight:850; letter-spacing:-1.2px; white-space:normal; word-break:keep-all; overflow-wrap:normal; margin:0; }}
@media (max-width:768px) {{
  .dashboard-kicker {{ font-size:10px !important; }}
  .dashboard-main-title {{ font-size:28px !important; line-height:1.3 !important; letter-spacing:-.6px !important; }}
}}

/* ===== スマホ対応：カレンダー ===== */
div[data-testid="stPopoverBody"] {{
  width: min(360px, calc(100vw - 24px)) !important;
  max-width: min(360px, calc(100vw - 24px)) !important;
  min-width: 0 !important;
  box-sizing:border-box !important;
  overflow-x:hidden !important;
  padding:10px !important;
}}
div[data-testid="stPopoverBody"] > div,
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"],
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlockBorderWrapper"] {{
  width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important;
}}
/* 日付グリッド用の目印。曜日はHTML、日付は7列columnsだが列幅を強制する。 */
div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] {{
  width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important;
  gap:3px !important; flex-wrap:nowrap !important;
}}
div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
  min-width:0 !important; width:0 !important; max-width:none !important; flex:1 1 0 !important; box-sizing:border-box !important;
}}
div[data-testid="stPopoverBody"] div.stButton,
div[data-testid="stPopoverBody"] div.stButton > button {{
  width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important;
}}
div[data-testid="stPopoverBody"] div.stButton > button {{
  min-height:36px !important; padding:3px 1px !important; font-size:13px !important; white-space:nowrap !important;
}}
.jp-calendar-weekdays {{ display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:3px; width:100%; box-sizing:border-box; }}
.jp-calendar-weekday {{ min-width:0; text-align:center; overflow:hidden; }}
.jp-calendar-empty {{ height:36px; width:100%; }}
@media (max-width:768px) {{
  div[data-testid="stPopoverBody"] {{ width:calc(100vw - 24px) !important; max-width:calc(100vw - 24px) !important; }}
}}
</style>
</head>
<body data-ranking-signature="{signature}">
<div class="map-card">
<div class="toolbar">

<div style="display:flex;align-items:center;gap:5px;">
<button onclick="zoom(-0.1)">−</button><span class="zoom-label" id="zoomLabel">100%</span><button onclick="zoom(0.1)">＋</button>
</div>
</div>
<div class="map-scroll"><div class="map-stage" id="mapStage">{svg}</div></div>
</div>
<script>
(function() {{
const stage=document.getElementById('mapStage'); const label=document.getElementById('zoomLabel'); let scale=1;
window.zoom=function(delta) {{ scale=Math.max(.5,Math.min(1.6,scale+delta)); stage.style.transform=`scale(${{scale}})`; stage.style.marginBottom=`${{700*(scale-1)}}px`; label.textContent=Math.round(scale*100)+'%'; }};
window.resetZoom=function() {{ scale=1; stage.style.transform='scale(1)'; stage.style.marginBottom='0px'; label.textContent='100%'; }};
}})();
</script>
</body>
</html>'''

    components.html(html, height=790, scrolling=False)


# ==========================================
# 日本語カレンダー（外部パッケージ不要）
# ==========================================

JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

def japanese_calendar(label, state_key, default_date=None):
    """スマホ対応の日付選択。年月日を個別のプルダウンで選択する。"""
    if default_date is None:
        default_date = date.today()

    # 保存値を date 型へ統一
    selected_date = st.session_state.get(state_key, default_date)
    if isinstance(selected_date, pd.Timestamp):
        selected_date = selected_date.date()
    elif isinstance(selected_date, str):
        selected_date = pd.to_datetime(selected_date).date()
    if not isinstance(selected_date, date):
        selected_date = default_date

    # 年の選択範囲。データの年に依存せず、スマホでも十分選べる範囲にする。
    current_year = date.today().year
    min_year = min(2020, selected_date.year - 5)
    max_year = max(2035, selected_date.year + 5)
    years = list(range(min_year, max_year + 1))
    months = list(range(1, 13))

    st.markdown(
        f"<div class='date-picker-label'>{label}</div>",
        unsafe_allow_html=True,
    )

    # 年・月・日を独立したプルダウンにする。
    # st.popover / st.columns(7) を使わないため、スマホで横幅が膨らまない。
    year_key = f"{state_key}_year"
    month_key = f"{state_key}_month"
    day_key = f"{state_key}_day"

    if year_key not in st.session_state:
        st.session_state[year_key] = selected_date.year
    if month_key not in st.session_state:
        st.session_state[month_key] = selected_date.month
    if day_key not in st.session_state:
        st.session_state[day_key] = selected_date.day

    # 既存の値が範囲外になっている場合に補正
    if st.session_state[year_key] not in years:
        st.session_state[year_key] = selected_date.year
    if st.session_state[month_key] not in months:
        st.session_state[month_key] = selected_date.month

    selected_year = st.selectbox(
        "年",
        years,
        format_func=lambda y: f"{y}年",
        key=year_key,
        label_visibility="collapsed",
    )

    selected_month = st.selectbox(
        "月",
        months,
        format_func=lambda m: f"{m}月",
        key=month_key,
        label_visibility="collapsed",
    )

    # 月・年に応じて日数を決定（うるう年にも対応）
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    days = list(range(1, days_in_month + 1))

    # 31日→30日など月を変更した際に存在しない日にならないよう補正
    if st.session_state[day_key] not in days:
        st.session_state[day_key] = days[-1]

    selected_day = st.selectbox(
        "日",
        days,
        format_func=lambda d: f"{d}日",
        key=day_key,
        label_visibility="collapsed",
    )

    selected_date = date(selected_year, selected_month, selected_day)
    st.session_state[state_key] = selected_date

    return selected_date


# ==========================================
# 3. セッション状態
# ==========================================
# 機種フィルタは日付変更によるStreamlit rerun後も保持します。

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None


# ==========================================
# 4. 全体デザイン (CSS)
# ==========================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');

/* 基本設定 */
html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

.stApp {
    background: #070912;
    color: #f5f7ff;
}


/* =========================================================
   Streamlit Community Cloud の外側UIを非表示
   ・GitHub / Fork
   ・右上の三点メニュー
   ・StreamlitのDeploy/管理UI
   ・右下の赤いステータス/管理ボタン
   ・上部ヘッダーの余白
   ※アプリ本体のUIには影響させない
   ========================================================= */

/* 上部ヘッダー全体 */
header,
header[data-testid="stHeader"],
div[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* GitHub / Fork / 三点メニュー等を含むStreamlit Toolbar */
[data-testid="stToolbar"],
div[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
div[data-testid="stToolbarActions"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Streamlit の上部・下部にある管理用UI */
.stDeployButton,
div[data-testid="stAppDeployButton"],
button[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
div[data-testid="stStatusWidget"],
[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* 旧バージョンのStreamlitで使われる管理UI */
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ヘッダーを消した分、アプリを最上部から開始 */
[data-testid="stAppViewContainer"],
.stAppViewContainer,
.main {
    padding-top: 0 !important;
}

section.main {
    padding-top: 0 !important;
}

/* モバイルSafari等で残るヘッダー用スペースを除去 */
[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
}

/* Streamlitがheader用に確保する上部余白を除去 */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1rem !important;
}

/* 念のため、ヘッダー内のGitHub/Fork等のボタンも対象 */
header button,
header a,
header [role="button"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* ブラウザ／パスワードマネージャーの鍵アイコンのみを非表示 */
input::-webkit-credentials-auto-fill-button,
input::-webkit-contacts-auto-fill-button,
input::-ms-reveal,
input::-ms-clear,
com-1password-button,
[data-1password-overlay] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}


/* ==========================================
   ボタンの文字色・背景色を明示指定
   初期表示でも文字が見えるようにする
   ========================================== */
div.stButton > button {
    background: #111522 !important;
    color: #f5f7ff !important;
    border: 1px solid rgba(255,255,255,.24) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    opacity: 1 !important;
    box-shadow: none !important;
}

div.stButton > button:hover {
    background: #252b3d !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,.42) !important;
}

div.stButton > button:focus,
div.stButton > button:active {
    background: #1c2232 !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,.38) !important;
}

div.stButton > button p,
div.stButton > button span,
div.stButton > button div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}

/* ==========================================
   画面幅を広げすぎず、スマホでも収まるようにする
   ========================================== */
.block-container {
    width: min(650px, calc(100vw - 28px)) !important;
    max-width: 650px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

/* 店舗選択画面・分析画面もログイン画面と同じ最大幅 */
section.main > div.block-container {
    width: min(650px, calc(100vw - 28px)) !important;
    max-width: 650px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}

/* ダッシュボード上部の3列も横幅を使いすぎない */
.dashboard-main-title {
    max-width: 100% !important;
}

@media (max-width: 768px) {
    .date-range-wave {
        font-size: 20px;
        margin-top: 31px;
    }

    .custom-date-field {
        font-size: 16px;
        padding: 0 10px;
    }

    .block-container,
    section.main > div.block-container {
        width: calc(100vw - 28px) !important;
        max-width: 650px !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 1.25rem !important;
        padding-bottom: 1.5rem !important;
        box-sizing: border-box !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* タイトルをスマホ用に縮小 */
    .dashboard-main-title {
        font-size: 28px !important;
        line-height: 1.3 !important;
        letter-spacing: -0.6px !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
    }

    /* タブ文字をスマホでも読みやすく */
    [data-baseweb="tab-list"] {
        gap: 5px !important;
        width: 100% !important;
        overflow-x: auto !important;
        scrollbar-width: none !important;
    }

    [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none !important;
    }

    button[data-baseweb="tab"] {
        flex: 0 0 auto !important;
        padding: 8px 10px !important;
    }

    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] div {
        font-size: 13px !important;
        line-height: 1.3 !important;
    }

    /* ダッシュボード上部の「タイトル・更新・戻る」はスマホでも横並び */
    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-start !important;
        width: 100% !important;
        max-width: 100% !important;
        gap: 8px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) > [data-testid="column"] {
        min-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) > [data-testid="column"]:nth-child(1) {
        flex: 8 1 0 !important;
        width: auto !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) > [data-testid="column"]:nth-child(2),
    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) > [data-testid="column"]:nth-child(3) {
        flex: 1.5 1 0 !important;
        width: auto !important;
    }

    /* 更新・戻るボタンは各列の中で横幅いっぱいにする */
    div[data-testid="stHorizontalBlock"]:has(.dashboard-main-title) div.stButton > button {
        width: 100% !important;
        min-width: 0 !important;
        white-space: nowrap !important;
        padding-left: 8px !important;
        padding-right: 8px !important;
    }

    /* 店舗選択・ログインのボタンを画面幅に合わせる */
    div.stButton > button {
        max-width: 100% !important;
        min-height: 42px !important;
    }

    /* データテーブルなどの横スクロールを許容 */
    div[data-testid="stDataFrame"] {
        max-width: 100% !important;
        overflow-x: auto !important;
    }
}

/* ラベル・入力項目の文字色調整 */
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.20) !important;
    border-radius: 12px !important;
}

div[data-baseweb="input"] input {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* ログイン画面のパスワード入力欄を右端まで白背景にする */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="input"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"] input {
    background: #ffffff !important;
}

/* パスワードの「・」を少し大きくする */
div[data-testid="stTextInput"] input[type="password"] {
    font-size: 15px !important;
    letter-spacing: 2px !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* 「Press Enter to apply」を完全に非表示 */
div[data-testid="InputInstructions"],
div[data-testid="InputInstructions"] > span {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
}

/* Streamlitのパスワード表示／非表示の目アイコンを表示 */
div[data-testid="stTextInput"] button[aria-label="Show password"],
div[data-testid="stTextInput"] button[aria-label="Hide password"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #ffffff !important;
    color: #333333 !important;
    pointer-events: auto !important;
}

div[data-testid="stTextInput"] button[aria-label="Show password"] svg,
div[data-testid="stTextInput"] button[aria-label="Hide password"] svg {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #333333 !important;
    fill: currentColor !important;
}

/* セレクトボックスの指定 */
div[data-baseweb="select"] > div {
    background: #171d2d !important;
    border: 1px solid #454b5a !important;
    border-radius: 12px !important;
    color: #ffffff !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

div[data-baseweb="select"] svg {
    fill: #ffffff !important;
}

/* タブ（st.tabs）の文字色・スタイルの適用 */
button[data-baseweb="tab"] {
    border-radius: 10px 10px 0 0 !important;
}

button[data-baseweb="tab"] p,
button[data-baseweb="tab"] div {
    color: #929bb2 !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}

button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] div {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* ==========================================
   タブを1個ずつ枠で囲んで境界を明確化
   ========================================== */
[data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: none !important;
}

button[data-baseweb="tab"] {
    border: 1px solid rgba(255,255,255,.18) !important;
    border-radius: 9px 9px 0 0 !important;
    background: rgba(255,255,255,.035) !important;
    padding: 10px 16px !important;
    margin: 0 !important;
}

button[data-baseweb="tab"]:hover {
    border-color: rgba(255,255,255,.35) !important;
    background: rgba(255,255,255,.07) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    border-color: #ff5a60 !important;
    background: rgba(255,255,255,.06) !important;
}

/* ==========================================
   ダークテーマのランキング表
   ========================================== */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,.10) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

/* ==========================================
   ダッシュボードタイトル
   変な位置で折り返さず、使用可能幅いっぱいを使う
   ========================================== */
.dashboard-main-title {
    width: 100% !important;
    color: #f8f9ff !important;
    font-size: 42px !important;
    line-height: 1.18 !important;
    font-weight: 850 !important;
    letter-spacing: -1.2px !important;
    white-space: normal !important;
    word-break: keep-all !important;
    overflow-wrap: normal !important;
    margin: 0 !important;
}


/* 日付選択 */
.date-picker-label {
    font-size: 18px;
    font-weight: 800;
    color: #aeb8cc;
    margin-bottom: 7px;
}

/* =====================================================
   日付選択欄
   ・機種選択欄と完全に同系統のダーク背景
   ・日付文字を白で明示
   ・カレンダーアイコンは枠の右端に固定
   ・枠全体をクリックしてカレンダーを開く
   ===================================================== */
div[data-testid="stPopover"] {
    width: 100% !important;
}

/* Streamlit のバージョン差でボタンの直下構造が変わっても効くように両方指定 */
div[data-testid="stPopover"] > button,
div[data-testid="stPopover"] > div > button {
    position: relative !important;
    width: 100% !important;
    min-height: 50px !important;
    box-sizing: border-box !important;
    padding: 0 52px 0 16px !important;
    background: #171d2d !important;
    background-color: #171d2d !important;
    color: #f5f7ff !important;
    border: 1px solid #454b5a !important;
    border-radius: 12px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    justify-content: flex-start !important;
    align-items: center !important;
    opacity: 1 !important;
    box-shadow: none !important;
    -webkit-text-fill-color: #f5f7ff !important;
}

/* カレンダーアイコンを入力枠の右端に固定 */
div[data-testid="stPopover"] > button::after,
div[data-testid="stPopover"] > div > button::after {
    content: "🗓️" !important;
    position: absolute !important;
    right: 16px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 22px !important;
    line-height: 1 !important;
    pointer-events: none !important;
}

div[data-testid="stPopover"] > button:hover,
div[data-testid="stPopover"] > div > button:hover {
    background: #252b3d !important;
    background-color: #252b3d !important;
    border-color: rgba(255,255,255,.42) !important;
}

div[data-testid="stPopover"] > button:focus,
div[data-testid="stPopover"] > div > button:focus,
div[data-testid="stPopover"] > button:active,
div[data-testid="stPopover"] > div > button:active {
    background: #1f2638 !important;
    background-color: #1f2638 !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,.42) !important;
}

/* 日付選択欄のプルダウン矢印（^）を非表示 */
div[data-testid="stPopover"] > button svg,
div[data-testid="stPopover"] > div > button svg {
    display: none !important;
    visibility: hidden !important;
}

div[data-testid="stPopover"] > button p,
div[data-testid="stPopover"] > button span,
div[data-testid="stPopover"] > button div,
div[data-testid="stPopover"] > div > button p,
div[data-testid="stPopover"] > div > button span,
div[data-testid="stPopover"] > div > button div {
    color: #f5f7ff !important;
    -webkit-text-fill-color: #f5f7ff !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* 「〜」を日付入力枠の高さ中央に配置 */
.date-range-wave {
    min-height: 50px;
    margin-top: 31px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #f5f7ff;
    font-size: 24px;
    font-weight: 800;
}

/* ==========================================
   カレンダーポップオーバー
   ダーク背景＋白文字
   ========================================== */

/* =========================================================
   カレンダーポップオーバー
   スマホでは「ポップオーバー本体」を画面幅に合わせる。
   StreamlitのバージョンによってDOMが異なるため、複数の
   セレクタを同時に指定する。
   ========================================================= */
@media (max-width: 768px) {
  div[data-testid="stPopoverBody"],
  div[data-baseweb="popover"],
  div[role="dialog"] {
    width: calc(100vw - 24px) !important;
    max-width: 360px !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
  }

  div[data-testid="stPopoverBody"] > div,
  div[data-baseweb="popover"] > div,
  div[role="dialog"] > div,
  div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"],
  div[data-baseweb="popover"] [data-testid="stVerticalBlock"],
  div[role="dialog"] [data-testid="stVerticalBlock"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
  }

  /* 日付行の7列を必ず横一列にする */
  div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"],
  div[data-baseweb="popover"] [data-testid="stHorizontalBlock"],
  div[role="dialog"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    gap: 3px !important;
  }

  div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] > [data-testid="column"],
  div[data-baseweb="popover"] [data-testid="stHorizontalBlock"] > [data-testid="column"],
  div[role="dialog"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    width: 0 !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: 1 1 0 !important;
    box-sizing: border-box !important;
  }

  /* ボタンが列幅を押し広げないようにする */
  div[data-testid="stPopoverBody"] div.stButton,
  div[data-testid="stPopoverBody"] div.stButton > button,
  div[data-baseweb="popover"] div.stButton,
  div[data-baseweb="popover"] div.stButton > button,
  div[role="dialog"] div.stButton,
  div[role="dialog"] div.stButton > button {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
  }

  div[data-testid="stPopoverBody"] div.stButton > button,
  div[data-baseweb="popover"] div.stButton > button,
  div[role="dialog"] div.stButton > button {
    min-height: 36px !important;
    padding: 3px 1px !important;
    font-size: 13px !important;
    white-space: nowrap !important;
  }
}

/* 曜日はStreamlit columnsではなくHTMLの7列グリッド */
.jp-calendar-weekdays {
  display: grid !important;
  grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
  gap: 3px !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
}

.jp-calendar-weekday {
  min-width: 0 !important;
  width: auto !important;
  text-align: center !important;
  overflow: hidden !important;
  white-space: nowrap !important;
}

.jp-calendar-empty {
  height: 36px !important;
  width: 100% !important;
  min-width: 0 !important;
}

@media (max-width: 768px) {
  div[data-testid="stPopoverBody"],
  div[data-baseweb="popover"],
  div[role="dialog"] {
    width: calc(100vw - 24px) !important;
    max-width: 360px !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
  }
}

div[data-testid="stPopoverBody"] {
    background: #0f1422 !important;
    background-color: #0f1422 !important;
    border: 1px solid rgba(255,255,255,.16) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    box-shadow: 0 16px 40px rgba(0,0,0,.45) !important;
}

/* カレンダー内部のコンテナもダークにする */
div[data-testid="stPopoverBody"] > div,
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"],
div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] {
    background: transparent !important;
    color: #ffffff !important;
}

/* 年月タイトル */
div[data-testid="stPopoverBody"] .jp-calendar-title {
    color: #ffffff !important;
}

/* 曜日 */
div[data-testid="stPopoverBody"] .jp-calendar-weekday {
    color: #aeb8cc !important;
}

/* カレンダーの日付ボタン */
div[data-testid="stPopoverBody"] div.stButton > button {
    min-height: 38px !important;
    padding: 4px 2px !important;
    font-size: 14px !important;
    background: #111522 !important;
    background-color: #111522 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,.20) !important;
    border-radius: 9px !important;
}

/* 日付ボタンの文字 */
div[data-testid="stPopoverBody"] div.stButton > button p,
div[data-testid="stPopoverBody"] div.stButton > button span,
div[data-testid="stPopoverBody"] div.stButton > button div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* 日付ボタン hover */
div[data-testid="stPopoverBody"] div.stButton > button:hover {
    background: #252b3d !important;
    background-color: #252b3d !important;
    border-color: rgba(255,255,255,.42) !important;
}

/* 前月・次月ボタン */
div[data-testid="stPopoverBody"] div.stButton > button {
    color: #ffffff !important;
}

/* 選択日表示 */
div[data-testid="stPopoverBody"] .jp-calendar-selected {
    background: #111522 !important;
    background-color: #111522 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,.16) !important;
}

/* 空白部分 */
div[data-testid="stPopoverBody"] .jp-calendar-empty {
    background: transparent !important;
}

/* カレンダー内の日付ボタンもダークテーマに統一 */
div[data-testid="stPopoverBody"] div.stButton > button {
    min-height: 38px !important;
    padding: 4px 2px !important;
    font-size: 14px !important;
    background: #111522 !important;
    color: #f5f7ff !important;
    border: 1px solid rgba(255,255,255,.20) !important;
    border-radius: 9px !important;
}

div[data-testid="stPopoverBody"] div.stButton > button:hover {
    background: #252b3d !important;
    border-color: rgba(255,255,255,.42) !important;
}

/* カレンダー内の前月・次月ボタン */
div[data-testid="stPopoverBody"] div.stButton > button p,
div[data-testid="stPopoverBody"] div.stButton > button span,
div[data-testid="stPopoverBody"] div.stButton > button div {
    color: #f5f7ff !important;
    -webkit-text-fill-color: #f5f7ff !important;
}

/* 日本語カレンダー */
.jp-calendar-title {
    text-align: center;
    font-size: 18px;
    font-weight: 800;
    color: #f5f7ff;
    padding: 8px 0 10px;
}
.jp-calendar-weekday {
    text-align: center;
    color: #aeb8cc;
    font-weight: 700;
    font-size: 12px;
    padding: 4px 0;
}
.jp-calendar-empty {
    height: 38px;
}
.jp-calendar-selected {
    margin-top: 8px;
    padding: 8px 10px;
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 8px;
    background: #111522;
    color: #dce3f3;
    text-align: center;
    font-size: 12px;
}


/* 日付選択欄：機種選択欄と同じダーク系背景に統一 */
div[data-testid="stDateInput"] > div {
    background: transparent !important;
}
div[data-testid="stDateInput"] input {
    background-color: #171d2d !important;
    color: #f5f7ff !important;
    -webkit-text-fill-color: #f5f7ff !important;
    border: 1px solid #454b5a !important;
    border-radius: 12px !important;
}
div[data-testid="stDateInput"] input::placeholder {
    color: #aeb8cc !important;
    -webkit-text-fill-color: #aeb8cc !important;
}
div[data-testid="stDateInput"] button {
    background-color: #171d2d !important;
    color: #f5f7ff !important;
    border: 1px solid #454b5a !important;
    border-radius: 12px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 5. ログイン画面
# ==========================================

if not st.session_state["authenticated"]:

    # ログイン画面専用CSSを追加適用
    st.markdown(
        """
        <style>


        /* Streamlitの外側UIは全画面共通CSSで非表示にしています。 */
        
        .block-container {
            width: min(650px, calc(100vw - 28px)) !important;
            max-width: 650px !important;
            margin: 0 auto !important;
            padding: 3rem 20px 2rem !important;
            box-sizing: border-box !important;
        }

        @media (max-width: 768px) {
            .block-container {
                width: calc(100vw - 28px) !important;
                max-width: 650px !important;
                padding: 1.5rem 14px 1.25rem !important;
                box-sizing: border-box !important;
            }

            .login-title {
                font-size: 32px !important;
            }

            .login-description {
                font-size: 12px !important;
                line-height: 1.8 !important;
            }

            .character-center img {
                width: min(220px, 65vw) !important;
            }
        }
        
        .login-brand {
            text-align: center;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            letter-spacing: 3px !important;
            color: #b9c2d9 !important;
            margin: 0 0 12px !important;
        }
        
        .login-brand span { color: #a78bfa !important; }
        
        .character-center {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0 auto 8px !important;
        }
        
        .character-center img {
            width: 260px !important;
            max-width: 70vw !important;
            height: auto !important;
        }
        
        .login-kicker {
            text-align: center;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            color: #818ba4 !important;
            margin: 6px 0 5px !important;
        }
        
        .login-title {
            text-align: center;
            font-size: 38px !important;
            font-weight: 850 !important;
            color: #f8f9ff !important;
            margin: 0 !important;
        }
        
        .login-description {
            text-align: center;
            color: #8d97ad !important;
            font-size: 12px !important;
            margin: 10px 0 23px !important;
        }
        
        .login-security, .login-footer {
            text-align: center;
            color: #68738a !important;
            font-size: 10px !important;
            margin-top: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    character_path = os.path.join(base_dir, "assets", "penion_character_hd.png")
    if not os.path.exists(character_path):
        character_path = os.path.join(base_dir, "assets", "penion_character.png")

    character_base64 = None
    if os.path.exists(character_path):
        try:
            with open(character_path, "rb") as image_file:
                character_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception:
            character_base64 = None

    with st.container(border=True):

        st.markdown(
            '<div class="login-brand">PENION <span>ANALYTICS</span></div>',
            unsafe_allow_html=True,
        )

        if character_base64:
            st.markdown(
                f"""
                <div class="character-center">
                    <img src="data:image/png;base64,{character_base64}" alt="PENION CHARACTER">
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="login-kicker">SECURE ACCESS</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">ログイン</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-description">
                僕はペニオン君ぺに。<br>
                パスワードを入力して僕の分析ページに進むぺに！
            </div>
            """,
            unsafe_allow_html=True,
        )

        pwd_input = st.text_input(
            "パスワード",
            type="password",
            placeholder="パスワードを入力してください",
            key="login_password",
        )

        login_clicked = st.button("ログイン", use_container_width=True, key="login_button")

        if login_clicked:
            if pwd_input == AUTH_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("パスワードが一致しません。")

        st.markdown('<div class="login-security">🔒 認証されたユーザーのみアクセスできます。</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-footer">PENION ANALYTICS · PACHISLOT DATA SYSTEM</div>', unsafe_allow_html=True)

    st.stop()


# ==========================================
# 6. メニュー画面 / 店舗分析 / ミニゲーム
# ==========================================

if "app_page" not in st.session_state:
    st.session_state["app_page"] = "menu"

if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None


def show_top_menu():
    st.markdown(
        """
        <div style="padding: 20px 0 8px; font-family: Orbitron, sans-serif;
                    color: #9fa8bf; font-size: 11px; letter-spacing: 2px;">
            PENION ANALYTICS / MENU
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title("PENION MENU")
    st.caption("利用するコンテンツを選択してください。")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("店舗分析")
            st.caption("店舗ごとのスロパチデータを分析します。")

            if st.button(
                "店舗分析を開く",
                use_container_width=True,
                key="open_store_analysis",
            ):
                st.session_state["app_page"] = "store_select"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("ミニゲーム")
            st.caption("ちょっと遊べるPENIONミニゲーム。")

            if st.button(
                "ミニゲームを開く",
                use_container_width=True,
                key="open_minigame",
            ):
                st.session_state["app_page"] = "minigame"
                st.rerun()


def show_store_select():
    st.markdown(
        """
        <div style="padding: 20px 0 8px; font-family: Orbitron, sans-serif;
                    color: #9fa8bf; font-size: 11px; letter-spacing: 2px;">
            PENION ANALYTICS / STORE SELECT
        </div>
        """,
        unsafe_allow_html=True,
    )

    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("メニュー", key="back_to_menu_from_store"):
            st.session_state["app_page"] = "menu"
            st.session_state["selected_store"] = None
            st.rerun()

    st.title("店舗選択")
    st.caption("分析対象の店舗を選択してください。")

    store_options = [
        "店舗を選択して下さい",
        "ピーアーク相模大野",
        "メガフェイス1180座間店",
    ]

    current_store = st.session_state.get("selected_store")
    default_index = (
        store_options.index(current_store)
        if current_store in store_options
        else 0
    )

    store_name = st.selectbox(
        "店舗",
        store_options,
        index=default_index,
        label_visibility="collapsed",
        key="store_select_menu",
    )

    if st.button(
        "分析を開始",
        use_container_width=False,
        key="start_analysis_button",
    ):
        if store_name == "店舗を選択して下さい":
            st.warning("店舗を選択して下さい。")
        else:
            st.session_state["selected_store"] = store_name
            st.session_state["app_page"] = "analysis"
            st.rerun()


def show_minigame():
    st.markdown(
        """
        <div style="padding:20px 0 8px;font-family:Orbitron,sans-serif;color:#9fa8bf;font-size:11px;letter-spacing:2px;">
            PENION ANALYTICS / MINI GAME
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("メニューに戻る", key="back_to_menu_from_minigame"):
        st.session_state["app_page"] = "menu"
        st.rerun()

    st.title("ゲーム選択")
    st.caption("プレイするゲームを選択してください。")

    game_name = st.selectbox(
        "ゲームを選択",
        ["抽選", "IFのパチンコ"],
        key="selected_minigame",
    )

    st.markdown("---")

    if game_name == "抽選":
        st.subheader("抽選")
        st.caption("抽選人数を選択し、ランダムで1人を決定します。")

        # 抽選人数欄をゲーム選択欄と同じダーク系にする
        st.markdown(
            """
            <style>
            div[data-testid="stNumberInput"] {
                width: 100% !important;
            }
            div[data-testid="stNumberInput"] > div {
                width: 100% !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            div[data-testid="stNumberInput"] div[data-baseweb="input"] {
                width: 100% !important;
                min-height: 50px !important;
                background: #171d2d !important;
                background-color: #171d2d !important;
                border: 1px solid #454b5a !important;
                border-radius: 12px !important;
                box-shadow: none !important;
                outline: none !important;
                box-sizing: border-box !important;
            }
            div[data-testid="stNumberInput"] div[data-baseweb="input"] > div {
                background: #171d2d !important;
                background-color: #171d2d !important;
                border: none !important;
                box-shadow: none !important;
            }
            div[data-testid="stNumberInput"] input {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                background: transparent !important;
                font-size: 18px !important;
                font-weight: 700 !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }
            div[data-testid="stNumberInput"] button {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
                max-width: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                border: none !important;
            }
            div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
            div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within {
                background: #171d2d !important;
                background-color: #171d2d !important;
                border-color: #454b5a !important;
                box-shadow: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        lottery_people = st.number_input(
            "抽選人数",
            min_value=1,
            max_value=10000,
            value=100,
            step=1,
            key="lottery_people",
        )

        # カットイン用CSS
        st.markdown(
            """
            <style>
            .lottery-cutin-image {
                width: 100%;
                height: 100%;
                object-fit: cover;
                object-position: center;
                display: block;
            }
            .lottery-loading-area {
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: #ffffff;
                background: radial-gradient(
                    circle at center,
                    rgba(40,45,65,0.95),
                    rgba(5,7,15,1)
                );
                box-sizing: border-box;
            }
            .lottery-loading-title {
                font-size: 52px;
                font-weight: 900;
                letter-spacing: 4px;
                margin-bottom: 24px;
            }
            .lottery-spinner {
                width: 68px;
                height: 68px;
                border-radius: 50%;
                border: 6px solid rgba(255,255,255,0.18);
                border-top-color: #ffffff;
                animation: lottery-spin 0.8s linear infinite;
                margin-bottom: 22px;
                box-sizing: border-box;
            }
            .lottery-loading-text {
                color: rgba(255,255,255,0.72);
                font-size: 15px;
                letter-spacing: 3px;
            }
            @keyframes lottery-spin {
                to { transform: rotate(360deg); }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "抽選する 🎰",
            use_container_width=True,
            key="run_lottery",
        ):
            result = random.randint(1, int(lottery_people))
            max_people = int(lottery_people)

            if result <= 1:
                with open(LOTTERY_RAINBOW_IMAGE, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                animation_html = f"""
                <img
                    class="lottery-cutin-image"
                    src="data:image/png;base64,{b64}"
                    alt=""
                >
                """

            elif result <= 10:
                with open(LOTTERY_GOLD_IMAGE, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                animation_html = f"""
                <img
                    class="lottery-cutin-image"
                    src="data:image/png;base64,{b64}"
                    alt=""
                >
                """

            elif result <= 100:
                with open(LOTTERY_RED_IMAGE, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                animation_html = f"""
                <img
                    class="lottery-cutin-image"
                    src="data:image/png;base64,{b64}"
                    alt=""
                >
                """

            else:
                animation_html = """
                <div class="lottery-loading-area">
                    <div class="lottery-loading-title">抽選中...</div>
                    <div class="lottery-spinner"></div>
                    <div class="lottery-loading-text">RESULT CHECKING</div>
                </div>
                """

            # 重要：st.markdownではなくcomponents.htmlでiframe内に描画する。
            # これにより画像のBase64データを確実にブラウザへ渡す。
            components.html(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        * {{ box-sizing: border-box; }}
                        html, body {{
                            margin: 0;
                            padding: 0;
                            width: 100%;
                            height: 100%;
                            overflow: hidden;
                            background: transparent;
                        }}
                        .lottery-overlay {{
                            position: fixed;
                            inset: 0;
                            width: 100%;
                            height: 100%;
                            background: rgba(0,0,0,0.84);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: 20px;
                        }}
                        .lottery-window {{
                            width: min(650px, calc(100vw - 40px));
                            height: 300px;
                            position: relative;
                            overflow: hidden;
                            border-radius: 16px;
                            border: 1px solid rgba(255,255,255,0.25);
                            background: #070912;
                            box-shadow: 0 0 50px rgba(0,0,0,0.90), 0 0 100px rgba(255,255,255,0.08);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                        .lottery-cutin-image {{
                            display: block;
                            width: auto !important;
                            height: auto !important;
                            max-width: 100% !important;
                            max-height: 100% !important;
                            object-fit: contain !important;
                            object-position: center center !important;
                            margin: 0 auto;
                        }}
                        .lottery-loading-area {{
                            position: absolute;
                            inset: 0;
                            width: 100%;
                            height: 100%;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            color: #ffffff;
                            background: radial-gradient(circle at center, rgba(40,45,65,0.95), rgba(5,7,15,1));
                        }}
                        .lottery-loading-title {{
                            font-size: 52px;
                            font-weight: 900;
                            letter-spacing: 4px;
                            margin-bottom: 24px;
                            color: #ffffff;
                        }}
                        .lottery-spinner {{
                            width: 68px;
                            height: 68px;
                            flex: 0 0 68px;
                            border-radius: 50%;
                            border: 6px solid rgba(255,255,255,0.18);
                            border-top-color: #ffffff;
                            animation: lottery-spin 0.8s linear infinite;
                            margin-bottom: 22px;
                        }}
                        .lottery-loading-text {{
                            color: rgba(255,255,255,0.72);
                            font-size: 15px;
                            letter-spacing: 3px;
                        }}
                        @keyframes lottery-spin {{
                            to {{ transform: rotate(360deg); }}
                        }}
                        @media (max-width: 700px) {{
                            .lottery-window {{
                                width: 92vw;
                                height: min(300px, 55vw);
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="lottery-overlay">
                        <div class="lottery-window">
                            {animation_html}
                        </div>
                    </div>
                </body>
                </html>
                """,
                height=420,
                scrolling=False,
            )

            # 結果は保存するが、現在の実行では表示しない。
            # 3秒間のカットインを確実に見せるため、次回rerunで結果を表示する。
            st.session_state["lottery_result"] = result
            st.session_state["lottery_max_people"] = max_people

            # 3秒後にブラウザ側ではなくPython側で結果へ切り替える。
            # components.htmlが表示されるまでsleepしてからrerunする。
            time.sleep(3)
            st.rerun()

        # 抽選ボタンを押した直後のrerunでは結果を表示する。
        if "lottery_result" in st.session_state:
            result = st.session_state["lottery_result"]
            max_people = st.session_state.get(
                "lottery_max_people",
                int(lottery_people),
            )

            st.html(
                f"""
                <div style="
                    margin:24px 0 12px;
                    padding:24px 16px;
                    border-radius:16px;
                    border:1px solid rgba(255,255,255,.18);
                    background:rgba(255,255,255,.04);
                    text-align:center;
                    height:300px;
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                    align-items:center;
                    box-sizing:border-box;
                ">
                    <div style="
                        color:#9fa8bf;
                        font-size:15px;
                        letter-spacing:1px;
                        margin-bottom:8px;
                    ">抽選結果</div>
                    <div style="
                        color:#fff;
                        font-size:64px;
                        font-weight:900;
                        line-height:1.1;
                    ">{result}</div>
                    <div style="
                        color:#9fa8bf;
                        font-size:14px;
                        margin-top:10px;
                    ">1 〜 {max_people} の中から抽選</div>
                </div>
                """
            )

    elif game_name == "IFのパチンコ":
        st.markdown(
            """
            <style>
            div[data-testid="stNumberInput"] label,
            div[data-testid="stNumberInput"] p {
                color: #d8dee9 !important;
                font-weight: 600 !important;
            }

            /* 数値入力欄：ゲーム選択と同じ暗い背景・グレー系の枠 */
            div[data-testid="stNumberInput"] {
                background: transparent !important;
            }

            div[data-testid="stNumberInput"] [data-baseweb="input"],
            div[data-testid="stNumberInput"] [data-baseweb="base-input"],
            div[data-testid="stNumberInput"] [data-baseweb="input"] > div {
                background-color: #1d2635 !important;
                border-color: #465267 !important;
                box-shadow: none !important;
            }

            div[data-testid="stNumberInput"] [data-baseweb="input"] {
                border: 1px solid #465267 !important;
                border-radius: 14px !important;
                overflow: hidden !important;
            }

            div[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within {
                background-color: #1d2635 !important;
                border-color: #64748b !important;
                box-shadow: none !important;
            }

            div[data-testid="stNumberInput"] input,
            div[data-testid="stNumberInput"] input[type="number"] {
                color: #e5e7eb !important;
                background-color: #1d2635 !important;
                -webkit-text-fill-color: #e5e7eb !important;
                border: none !important;
                box-shadow: none !important;
                opacity: 1 !important;
            }

            div[data-testid="stNumberInput"] input::placeholder {
                color: #9ca3af !important;
                -webkit-text-fill-color: #9ca3af !important;
            }

            /* number_input標準の－／＋ボタンは非表示 */
            div[data-testid="stNumberInput"] button {
                display: none !important;
            }

            div[data-testid="stCaptionContainer"] {
                color: #aab4c5 !important;
            }

            /* IFのパチンコ内の条件入力枠 */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid #3f4a5c !important;
                background: #171d29 !important;
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                border-color: transparent !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("IFのパチンコ")
        st.caption("入力した条件をもとに、通常時・初当たり・RUSHを完全確率でシミュレーションします。")

        # ==========================================
        # IFのパチンコ：振り分け行数の管理
        # ==========================================
        if "pachinko_distribution_count" not in st.session_state:
            st.session_state["pachinko_distribution_count"] = 2

        if "pachinko_result" not in st.session_state:
            st.session_state["pachinko_result"] = None

        def _pachinko_number(value, digits=0):
            """表示用の数値整形"""
            if digits == 0:
                return f"{int(round(value)):,}"
            return f"{value:,.{digits}f}"


        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, rgba(31,41,55,.98), rgba(17,24,39,.98));
                border: 1px solid #3f4a5c;
                border-radius: 14px;
                padding: 18px 20px 8px;
                margin-bottom: 12px;
                color: #e5e7eb;
            ">
                <div style="
                    font-size: 24px;
                    font-weight: 800;
                    color: #f3f4f6;
                    letter-spacing: .5px;
                ">条件</div>
                <div style="
                    margin-top: 5px;
                    color: #aab4c5;
                    font-size: 13px;
                ">シミュレーションに使用する条件を入力してください</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):

            jackpot_probability = st.number_input(
                "1. 大当たり確率（1 / ○○○）",
                min_value=1.0,
                value=float(st.session_state.get("pachinko_jackpot_probability", 319.0)),
                step=1.0,
                key="pachinko_jackpot_probability",
            )

            rush_entry_rate = st.number_input(
                "2. ラッシュ突入確率（%）",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("pachinko_rush_entry_rate", 60.0)),
                step=1.0,
                key="pachinko_rush_entry_rate",
            )

            initial_payout = st.number_input(
                "3. 初当たり時の出球（玉）",
                min_value=0,
                value=int(st.session_state.get("pachinko_initial_payout", 1500)),
                step=100,
                key="pachinko_initial_payout",
            )

            rush_continue_rate = st.number_input(
                "4. ラッシュ継続率（%）",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("pachinko_rush_continue_rate", 81.0)),
                step=1.0,
                key="pachinko_rush_continue_rate",
            )

            st.markdown("**ラッシュの出玉振り分け**")
            st.caption("左に確率（%）、右に出球（玉）を入力してください。")

            distribution = []
            for i in range(st.session_state["pachinko_distribution_count"]):
                left, right = st.columns(2)

                default_rate = 50.0 if i < 2 else 0.0
                default_payout = 1500 if i == 0 else (3000 if i == 1 else 1500)

                with left:
                    rate = st.number_input(
                        f"確率 {i + 1}（%）",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(st.session_state.get(f"pachinko_distribution_rate_{i}", default_rate)),
                        step=1.0,
                        key=f"pachinko_distribution_rate_{i}",
                    )
                with right:
                    payout = st.number_input(
                        f"出球 {i + 1}（玉）",
                        min_value=0,
                        value=int(st.session_state.get(f"pachinko_distribution_payout_{i}", default_payout)),
                        step=100,
                        key=f"pachinko_distribution_payout_{i}",
                    )

                distribution.append({
                    "rate": float(rate),
                    "payout": int(payout),
                })

            # 振り分け入力欄の下に追加・削除ボタンを配置
            add_col, remove_col, _ = st.columns([1, 1, 4])

            with add_col:
                add_distribution_clicked = st.button(
                    "追加",
                    key="pachinko_add_distribution",
                    use_container_width=True,
                )

            with remove_col:
                remove_distribution_clicked = (
                    st.session_state["pachinko_distribution_count"] > 1
                    and st.button(
                        "削除",
                        key="pachinko_remove_distribution",
                        use_container_width=True,
                    )
                )

            if add_distribution_clicked:
                st.session_state["pachinko_distribution_count"] += 1
                st.rerun()

            if remove_distribution_clicked:
                last_index = st.session_state["pachinko_distribution_count"] - 1
                st.session_state["pachinko_distribution_count"] -= 1
                st.session_state.pop(f"pachinko_distribution_rate_{last_index}", None)
                st.session_state.pop(f"pachinko_distribution_payout_{last_index}", None)
                st.rerun()

            rotation_rate = st.number_input(
                "6. 回転率（250玉あたりの回転数）",
                min_value=0.1,
                value=float(st.session_state.get("pachinko_rotation_rate", 18.0)),
                step=0.1,
                key="pachinko_rotation_rate",
            )

            spins_per_hour = st.number_input(
                "7. 1時間あたりの回転数（エヴァ15の場合200回転）",
                min_value=0.1,
                value=float(st.session_state.get("pachinko_spins_per_hour", 200.0)),
                step=1.0,
                key="pachinko_spins_per_hour",
            )
            st.caption(
                f"1回転あたり：約 {3600 / float(spins_per_hour):.2f} 秒"
            )

            operation_hours = st.number_input(
                "8. 稼働時間（時間）",
                min_value=0.01,
                value=float(st.session_state.get("pachinko_operation_hours", 8.0)),
                step=0.5,
                key="pachinko_operation_hours",
            )

        distribution_total = sum(item["rate"] for item in distribution)

        if abs(distribution_total - 100.0) > 0.000001:
            st.warning(
                f"ラッシュ出玉振り分けの合計は現在 {_pachinko_number(distribution_total, 1)}% です。"
                "結果を実行するには100%にしてください。"
            )

        if st.button(
            "結果を見る 🎰",
            use_container_width=True,
            key="run_if_pachinko",
        ):
            if abs(distribution_total - 100.0) > 0.000001:
                st.error("ラッシュの出玉振り分けの確率合計を100%にしてください。")
            elif (
                jackpot_probability <= 0
                or rotation_rate <= 0
                or spins_per_hour <= 0
                or operation_hours <= 0
            ):
                st.error(
                    "大当たり確率・回転率・1時間あたりの回転数・稼働時間は0より大きい値を入力してください。"
                )
            else:
                # ------------------------------------------
                # シミュレーション開始
                # ------------------------------------------
                remaining_time = float(operation_hours) * 3600.0
                balance = 0.0
                total_spins = 0
                history = []

                # 1時間あたりの回転数から、1回転あたりの時間を計算
                seconds_per_spin = 3600.0 / float(spins_per_hour)

                # 250玉あたりの回転率から、1回転あたりの消費玉数を計算
                balls_per_spin = 250.0 / float(rotation_rate)


                while remaining_time >= seconds_per_spin:
                    spins_since_last_hit = 0
                    hit = False

                    # ===== 通常時：時間が足りる間だけ回転 =====
                    while remaining_time >= seconds_per_spin:
                        remaining_time -= seconds_per_spin
                        balance -= balls_per_spin
                        total_spins += 1
                        spins_since_last_hit += 1

                        # 大当たり抽選
                        if random.random() < (1.0 / float(jackpot_probability)):
                            hit = True
                            break

                    # 当たらず時間切れ
                    if not hit:
                        # 最後に当たらず終了した回転数も履歴に残す
                        if spins_since_last_hit > 0:
                            history.append({
                                "回転数": spins_since_last_hit,
                                "出玉": 0,
                                "振り分け履歴": "時間切れ",
                                "RUSH突入": "－",
                                "収支": balance,
                            })
                        break

                    # ここから大当たり後の処理
                    hit_payout = 0
                    distribution_counts = {}
                    entered_rush = random.random() < (float(rush_entry_rate) / 100.0)

                    if entered_rush:
                        # 初当たり時の出球
                        hit_payout += int(initial_payout)
                        balance += int(initial_payout)

                        # RUSH中は、時間が0以下になってもRUSH終了まで継続
                        while random.random() < (float(rush_continue_rate) / 100.0):
                            # 振り分け抽選
                            roll = random.random() * 100.0
                            cumulative = 0.0
                            selected = distribution[-1]

                            for item in distribution:
                                cumulative += item["rate"]
                                if roll < cumulative:
                                    selected = item
                                    break

                            selected_payout = int(selected["payout"])
                            hit_payout += selected_payout
                            balance += selected_payout
                            distribution_counts[selected_payout] = (
                                distribution_counts.get(selected_payout, 0) + 1
                            )

                            # RUSH1回継続ごとに500秒消費
                            remaining_time -= 500.0

                        if distribution_counts:
                            rush_distribution_text = "、".join(
                                f"RUSH {_pachinko_number(payout)}玉 × {count}回"
                                for payout, count in sorted(distribution_counts.items())
                            )
                            distribution_text = (
                                f"初当たり {_pachinko_number(initial_payout)}玉、"
                                f"{rush_distribution_text}"
                            )
                        else:
                            distribution_text = (
                                f"初当たり {_pachinko_number(initial_payout)}玉、"
                                "RUSH継続なし"
                            )
                    else:
                        distribution_text = "RUSHなし"

                    # 当たり終了時点、またはRUSH終了時点の累計収支を保存
                    history.append({
                        "回転数": spins_since_last_hit,
                        "出玉": hit_payout,
                        "振り分け履歴": distribution_text,
                        "RUSH突入": "突入" if entered_rush else "非突入",
                        "収支": balance,
                    })

                    # RUSH終了時点で時間が0以下なら即終了
                    if remaining_time <= 0:
                        break

                    # 通常時へ戻る
                    continue

                # 結果をsession_stateに保存
                st.session_state["pachinko_result"] = {
                    "balance": balance,
                    "total_spins": total_spins,
                    "remaining_time": remaining_time,
                    "history": history,
                    "balls_per_spin": balls_per_spin,
                    "operation_seconds": float(operation_hours) * 3600.0,
                    "seconds_per_spin": seconds_per_spin,
                    "spins_per_hour": float(spins_per_hour),
                }
                st.rerun()

        # ==========================================
        # 結果表示
        # ==========================================
        pachinko_result = st.session_state.get("pachinko_result")

        if pachinko_result is not None:
            balance = pachinko_result["balance"]
            history = pachinko_result["history"]
            sign = "+" if balance >= 0 else "－"

            st.markdown("---")
            st.markdown("### シミュレーション結果")

            st.html(
                f"""
                <div style="
                    margin:12px 0 18px;
                    padding:26px 18px;
                    border-radius:16px;
                    border:1px solid rgba(255,255,255,.18);
                    background:rgba(255,255,255,.04);
                    text-align:center;
                ">
                    <div style="
                        color:#9fa8bf;
                        font-size:14px;
                        letter-spacing:1px;
                        margin-bottom:8px;
                    ">最終収支</div>
                    <div style="
                        color:#ffffff;
                        font-size:48px;
                        font-weight:900;
                        line-height:1.1;
                    ">{sign}{_pachinko_number(abs(balance))} 玉</div>
                    <div style="
                        color:#9fa8bf;
                        font-size:13px;
                        margin-top:12px;
                    ">総回転数：{_pachinko_number(pachinko_result["total_spins"])} 回転</div>
                </div>
                """
            )

            st.subheader("📜 履歴")

            if history:
                history_df = pd.DataFrame(history)

                # 履歴の収支を「＋ / － ○○玉」で表示
                def _format_history_balance(value):
                    value = float(value)
                    sign = "+" if value >= 0 else "－"
                    return f"{sign}{_pachinko_number(abs(value))}玉"

                history_df["収支"] = history_df["収支"].apply(
                    _format_history_balance
                )

                history_df.index = range(1, len(history_df) + 1)
                history_df.index.name = "No."
                st.dataframe(
                    history_df,
                    use_container_width=True,
                )
            else:
                st.info("大当たり履歴はありません。")

            if st.button(
                "結果をリセット",
                use_container_width=True,
                key="reset_if_pachinko_result",
            ):
                st.session_state["pachinko_result"] = None
                st.rerun()


# 最初はメニュー画面を表示
if st.session_state["app_page"] == "menu":
    show_top_menu()
    st.stop()

# 店舗分析を選択した場合だけ、従来の店舗選択を表示
if st.session_state["app_page"] == "store_select":
    show_store_select()
    st.stop()

# ミニゲームを選択
if st.session_state["app_page"] == "minigame":
    show_minigame()
    st.stop()

# ==========================================
# 7. 分析メイン画面
# ==========================================

store = st.session_state["selected_store"]

top_col1, top_col2 = st.columns([1, 5])
with top_col1:
    if st.button("メニュー", key="back_to_main_menu_from_analysis"):
        st.session_state["app_page"] = "menu"
        st.session_state["selected_store"] = None
        st.rerun()

st.markdown(
    """
    <div class="dashboard-header">
        <div class="dashboard-kicker">PENION ANALYTICS / DASHBOARD</div>
        <div class="dashboard-main-title">分析ダッシュボード</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# ==========================================
# DBから最新データ取得＆タブ描画
# ==========================================

try:
    df_slopachi, df_matomaru = load_data(store)
except Exception as e:
    st.error("データベースの読み込みに失敗しました。")
    st.code(str(e))
    st.info(
        "相模大野の場合は、このPythonファイルと同じフォルダに "
        "p_ark_database.db があるか確認してください。"
    )
    st.stop()

# タブの作成
tab1, tab2 = st.tabs(
    [
        "1. スロパチ分析",
        "2. まとまる君",
    ]
)

# ------------------------------------------
# タブ1：スロパチ分析
# ------------------------------------------
with tab1:

    st.subheader("スロパチ分析")

    df_filter = df_slopachi.copy()

    # ==========================================
    # 日付データをdate型に変換
    # ==========================================

    if not df_filter.empty:
        df_filter["_日付_dt"] = pd.to_datetime(
            df_filter["日付"],
            errors="coerce"
        ).dt.date

        valid_dates = df_filter["_日付_dt"].dropna()

    else:
        valid_dates = pd.Series(dtype="object")

    # ==========================================
    # 条件
    # ==========================================

    st.markdown(
        "<div style='font-size: 22px; font-weight: 800; "
        "color: #ffffff; margin-top: 10px; "
        "margin-bottom: 12px; letter-spacing: 1px;'>条件</div>",
        unsafe_allow_html=True,
    )

    # ==========================================
    # 1段目：開始日 ～ 終了日
    # ==========================================

    if len(valid_dates) > 0:
        default_start_date = min(valid_dates)
        default_end_date = max(valid_dates)
    else:
        default_start_date = date.today()
        default_end_date = date.today()

    # 店舗ごとに日付選択状態を分離する。
    # 以前に別の期間を選択した状態が残っていても、現在のDBに存在する
    # 最小日付〜最大日付の外側であれば自動的に補正する。
    # これにより「DBにはデータがあるのに、古い日付選択だけが残って0件」
    # になる問題を防ぐ。
    # これにより、メガフェイスで選択した日付が
    # ピーアーク相模大野にそのまま残る問題を防ぐ。
    # 店舗名をそのままstate keyに使うと、日本語名を記号に置換した際に
    # 別店舗同士で似たキーになる可能性があるため、UTF-8の16進数で完全分離する。
    store_state_key = str(store).encode("utf-8").hex()

    start_state_key = f"analysis_start_date_{store_state_key}"
    end_state_key = f"analysis_end_date_{store_state_key}"

    # 初回だけDBの最小日付・最大日付を設定する。
    # 以前の実装は毎回ここで年月日のselectbox stateまで上書きしていたため、
    # ユーザーが変更しても次の再実行時に初期日付へ戻っていました。
    def _initialize_date_state(state_key, initial_date):
        if state_key not in st.session_state:
            st.session_state[state_key] = initial_date
            st.session_state[f"{state_key}_year"] = initial_date.year
            st.session_state[f"{state_key}_month"] = initial_date.month
            st.session_state[f"{state_key}_day"] = initial_date.day

    _initialize_date_state(start_state_key, default_start_date)
    _initialize_date_state(end_state_key, default_end_date)

    # 以前のバージョンで保存された親stateがDB範囲外の場合だけ補正する。
    # ただしユーザーが操作中の年・月・日は絶対に毎回上書きしない。
    def _repair_out_of_range_date_once(state_key, fallback_date, lower_date, upper_date):
        value = st.session_state.get(state_key)
        try:
            if isinstance(value, pd.Timestamp):
                value = value.date()
            elif isinstance(value, str):
                parsed = pd.to_datetime(value, errors="coerce")
                value = parsed.date() if not pd.isna(parsed) else None
        except Exception:
            value = None

        if not isinstance(value, date) or value < lower_date or value > upper_date:
            st.session_state[state_key] = fallback_date
            # 子stateがまだ存在しない場合だけ初期化する。
            if f"{state_key}_year" not in st.session_state:
                st.session_state[f"{state_key}_year"] = fallback_date.year
            if f"{state_key}_month" not in st.session_state:
                st.session_state[f"{state_key}_month"] = fallback_date.month
            if f"{state_key}_day" not in st.session_state:
                st.session_state[f"{state_key}_day"] = fallback_date.day

    if len(valid_dates) > 0:
        _repair_out_of_range_date_once(
            start_state_key,
            default_start_date,
            default_start_date,
            default_end_date,
        )
        _repair_out_of_range_date_once(
            end_state_key,
            default_end_date,
            default_start_date,
            default_end_date,
        )

    start_date = japanese_calendar(
        "開始日",
        start_state_key,
        default_date=default_start_date,
    )

    end_date = japanese_calendar(
        "終了日",
        end_state_key,
        default_date=default_end_date,
    )

    # ==========================================
    # 2段目：機種選択
    # ==========================================

    if not df_filter.empty:

        models = (
            df_filter["機種名"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        models = models[models != ""]

        models = sorted(
            models.unique().tolist()
        )

    else:

        models = []

    model_options = ["全て"] + models

    # ==========================================
    # 機種選択を日付変更後も確実に保持する
    # ==========================================
    #
    # Streamlitではカレンダーのボタン操作によって画面全体が
    # 再実行されます。その際、selectbox自身の状態だけに依存すると、
    # 環境によって「全て」に戻った値を拾ってしまうことがあります。
    #
    # そこで、ユーザーが最後に明示的に選択した機種を
    # 「selected_machine_filter」に別保存します。
    # 日付変更によるrerunではこの値を変更しません。
    #
    # 店舗ごとに機種選択状態も分離する。
    machine_filter_key = f"selected_machine_filter_{store_state_key}"
    machine_widget_key = f"analysis_model_widget_{store_state_key}"

    if machine_filter_key not in st.session_state:
        st.session_state[machine_filter_key] = "全て"

    def _save_machine_filter():
        # ユーザーが機種selectboxを操作した時だけ、この値を更新する。
        st.session_state[machine_filter_key] = (
            st.session_state.get(machine_widget_key, "全て")
        )

    # 保存している機種が現在のDBの選択肢から消えている場合のみ
    # 「全て」に戻す。
    if st.session_state[machine_filter_key] not in model_options:
        st.session_state[machine_filter_key] = "全て"

    # selectbox自身のキーと、実際のフィルタ条件を分離する。
    widget_default = st.session_state[machine_filter_key]

    if machine_widget_key not in st.session_state:
        st.session_state[machine_widget_key] = widget_default

    # widget側が選択肢から外れている場合だけ同期する。
    if st.session_state[machine_widget_key] not in model_options:
        st.session_state[machine_widget_key] = widget_default

    st.markdown(
        "<div class='date-picker-label'>機種</div>",
        unsafe_allow_html=True,
    )

    st.selectbox(
        "機種",
        model_options,
        key=machine_widget_key,
        on_change=_save_machine_filter,
        label_visibility="collapsed",
    )

    # ランキング集計に使う機種は、selectboxの表示値ではなく
    # 「最後にユーザーが明示的に選択した値」を使用する。
    selected_model = st.session_state[machine_filter_key]

    # ==========================================
    # 日付チェック
    # ==========================================

    if start_date is None or end_date is None:

        st.info(
            "開始日と終了日を選択してください。"
        )

        st.stop()

    if start_date > end_date:

        st.warning(
            "開始日は終了日以前の日付を選択してください。"
        )

        st.stop()

    # ==========================================
    # 選択条件の表示
    # ==========================================

    # ==========================================
    # 日付範囲でフィルタリング
    # ==========================================

    if not df_filter.empty:

        filtered_slopachi = df_filter[
            (df_filter["_日付_dt"] >= start_date)
            &
            (df_filter["_日付_dt"] <= end_date)
        ].copy()

    else:

        filtered_slopachi = pd.DataFrame()

    # ==========================================
    # 機種でフィルタリング
    # ==========================================
    #
    # 重要：
    # 日付を変更した際も、現在選択されている機種を必ず
    # 「その日付範囲のデータ」に対して適用する。
    #
    # これにより、
    #   例）機種「炎炎2」を選択
    #       ↓
    #       日付を変更
    #       ↓
    #       変更後の日付範囲に存在する「炎炎2」だけで再集計
    #
    # となる。
    # ==========================================

    if selected_model != "全て":

        if not filtered_slopachi.empty:
            machine_mask = (
                filtered_slopachi["機種名"]
                .astype(str)
                .str.strip()
                .eq(str(selected_model).strip())
            )

            filtered_slopachi = filtered_slopachi.loc[
                machine_mask
            ].copy()

        else:
            # 日付条件に該当するデータがない場合も、
            # 機種条件を維持した空のDataFrameにする。
            filtered_slopachi = filtered_slopachi.copy()

    # ==========================================
    # 台番号ランキング
    # ==========================================
    #
    # filtered_slopachi はここまでに
    #   1. 日付範囲
    #   2. 選択機種（「全て」以外の場合）
    # の両方を適用済み。
    #
    # したがって、ここから作成するランキング_dfと島図の色は
    # 必ず現在の日付＋機種条件に連動する。
    #
    #
    # ここが今回の重要部分です。
    #
    # 「機種名＋台番号」ではなく、
    # 「台番号」だけで回数を数えます。
    #
    # 例：
    #
    # 8/1   炎炎2       2001
    # 8/5   炎炎2       2001
    # 8/10  炎炎2       2001
    #
    # ↓
    #
    # 2001 / 炎炎2 / 3回
    #
    # ==========================================

    if not filtered_slopachi.empty:

        # --------------------------------------
        # 台番号・機種名を文字列として統一
        # --------------------------------------

        filtered_slopachi["台番号"] = (
            filtered_slopachi["台番号"]
            .astype(str)
            .str.strip()
        )

        filtered_slopachi["機種名"] = (
            filtered_slopachi["機種名"]
            .astype(str)
            .str.strip()
        )

        # 空の台番号は除外
        filtered_slopachi = filtered_slopachi[
            filtered_slopachi["台番号"] != ""
        ].copy()

        # --------------------------------------
        # 台番号ごとの出現回数
        # --------------------------------------

        count_df = (
            filtered_slopachi
            .groupby("台番号", as_index=False)
            .size()
            .rename(
                columns={
                    "size": "回数"
                }
            )
        )

        # --------------------------------------
        # 台番号ごとの最新機種名を取得
        #
        # 期間中に機種変更があった場合は、
        # 一番新しい日付の機種名を表示
        # --------------------------------------

        latest_machine_df = (
            filtered_slopachi
            .sort_values(
                by=[
                    "台番号",
                    "_日付_dt"
                ],
                ascending=[
                    True,
                    False
                ]
            )
            .drop_duplicates(
                subset=["台番号"],
                keep="first"
            )
            [
                [
                    "台番号",
                    "機種名"
                ]
            ]
        )

        # --------------------------------------
        # 回数＋機種名を結合
        # --------------------------------------

        ranking_df = count_df.merge(
            latest_machine_df,
            on="台番号",
            how="left"
        )

        # --------------------------------------
        # 台番号を数字順にするための列
        # --------------------------------------

        ranking_df["_台番号_num"] = pd.to_numeric(
            ranking_df["台番号"],
            errors="coerce"
        )

        # --------------------------------------
        # 回数の多い順
        # 同じ回数なら台番号順
        # --------------------------------------

        ranking_df = ranking_df.sort_values(
            by=[
                "回数",
                "_台番号_num",
                "台番号"
            ],
            ascending=[
                False,
                True,
                True
            ],
            na_position="last",
        ).reset_index(drop=True)

        # --------------------------------------
        # 同じ回数は同じ順位
        #
        # 例：
        #
        # 3回 → 1位
        # 3回 → 1位
        # 2回 → 2位
        # 2回 → 2位
        # 1回 → 3位
        #
        # --------------------------------------

        ranking_df["順位"] = (
            ranking_df["回数"]
            .rank(
                method="dense",
                ascending=False
            )
            .astype(int)
        )

        # --------------------------------------
        # 表示する列
        # --------------------------------------

        ranking_df = ranking_df[
            [
                "順位",
                "台番号",
                "機種名",
                "回数"
            ]
        ]

    else:

        ranking_df = pd.DataFrame(
            columns=[
                "順位",
                "台番号",
                "機種名",
                "回数"
            ]
        )

    # ==========================================
    # ランキング表示
    # ==========================================

    st.subheader("台番号ランキング")

    st.caption(
        "選択した日付範囲・機種に一致するDBデータを、"
        "台番号の登場回数が多い順にランキングしています。"
    )

    # ==========================================
    # データがある場合
    # ==========================================

    if not ranking_df.empty:

        display_ranking_df = ranking_df.copy()

        # 順位を「1位」の形式にする
        display_ranking_df["順位"] = (
            display_ranking_df["順位"]
            .astype(str)
            + "位"
        )

        # 列名をユーザー指定の表示にする
        display_ranking_df = display_ranking_df.rename(
            columns={
                "順位": "順位",
                "台番号": "台番号",
                "機種名": "機種名",
                "回数": "回数",
            }
        )

        # --------------------------------------
        # 表のスタイル
        # --------------------------------------

        def style_ranking_table(styler):

            styler.set_properties(
                **{
                    "background-color": "#111522",
                    "color": "#f5f7ff",
                    "border-color": "rgba(255,255,255,.10)",
                    "font-size": "16px",
                }
            )

            styler.set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            (
                                "background-color",
                                "#171d2d"
                            ),
                            (
                                "color",
                                "#aeb8cc"
                            ),
                            (
                                "font-weight",
                                "700"
                            ),
                            (
                                "border-color",
                                "rgba(255,255,255,.12)"
                            ),
                        ],
                    },
                    {
                        "selector": "td",
                        "props": [
                            (
                                "border-color",
                                "rgba(255,255,255,.08)"
                            ),
                        ],
                    },
                    {
                        "selector": "tbody tr:hover td",
                        "props": [
                            (
                                "background-color",
                                "#1a2133"
                            ),
                        ],
                    },
                ]
            )

            return styler

        styled_ranking = style_ranking_table(
            display_ranking_df.style
        )

        st.dataframe(
            styled_ranking,
            use_container_width=True,
            hide_index=True,
        )

        # ==========================================
        # 島図：台番号ランキングと連動して着色
        # ==========================================

        st.subheader("島図")
        st.caption(
            "ランキング順位に応じて、島図上の該当台番号を自動で着色しています。"
        )

        render_island_map(ranking_df, store)

    # ==========================================
    # データがない場合
    # ==========================================

    else:

        if len(valid_dates) > 0:
            st.info(
                "選択した日付範囲・機種に該当するデータがDBにありません。\n\n"
                f"DBで認識できている日付範囲："
                f"{min(valid_dates).strftime('%Y/%m/%d')} 〜 "
                f"{max(valid_dates).strftime('%Y/%m/%d')}"
            )
        else:
            st.info(
                "DBは読み込めていますが、「日付」列を正しい日付として認識できません。"
            )

# ==========================================
# タブ2
# ==========================================

with tab2:
    if store == "メガフェイス1180座間店":
        st.info("メガフェイス1180座間店は現在スロパチ分析データのみ対応しています。")
    else:
        st.subheader("作成中のため、完成をお待ちください。")


# ==========================================
# ダッシュボード最下部：戻る
# ==========================================

st.markdown("---")

back_col = st.columns([4, 1, 4])[1]
with back_col:
    if st.button("戻る", use_container_width=True, key="back_to_store_button"):
        st.session_state["selected_store"] = None
        st.rerun()
