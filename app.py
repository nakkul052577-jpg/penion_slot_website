import os
import time
import sqlite3
import base64
import calendar
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

AUTH_PASSWORD = "pass"
DB_PATH = "p_ark_database.db"

# 日本語カレンダーは外部パッケージを使わず、このファイル内で実装しています。


# ==========================================
# 2. データベース初期化＆ロード処理
# ==========================================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ピーアーク相模大野_スロパチ (
        項番 INTEGER PRIMARY KEY AUTOINCREMENT,
        日付 TEXT,
        台番号 TEXT,
        機種名 TEXT,
        UNIQUE(日付, 台番号, 機種名)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ピーアーク相模大野_まとまる君 (
        項番 INTEGER PRIMARY KEY AUTOINCREMENT,
        日付 TEXT,
        並び人数 TEXT,
        取材 TEXT,
        来店 TEXT,
        機種名 TEXT,
        台番号 TEXT,
        差枚 INTEGER,
        回転G数 INTEGER,
        UNIQUE(日付, 台番号)
    )
    """)

    conn.commit()

    # ------------------------------------------
    # サンプルデータは登録しない
    # ------------------------------------------
    # このアプリは p_ark_datebase.db に保存されている
    # 実データのみを読み込みます。

    conn.close()



init_db()


def load_data():

    conn = sqlite3.connect(DB_PATH)

    df_sp = pd.read_sql_query(
        """
        SELECT *
        FROM ピーアーク相模大野_スロパチ
        ORDER BY 日付 DESC
        """,
        conn,
    )

    df_mt = pd.read_sql_query(
        """
        SELECT *
        FROM ピーアーク相模大野_まとまる君
        ORDER BY 日付 DESC
        """,
        conn,
    )

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

ISLAND_CANVAS_SIZE = (2030, 964)
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


def build_island_positions():
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


ISLAND_POSITIONS = build_island_positions()


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


def render_island_map(ranking_df):
    """画像を使わずSVGで島図を描画し、ランキング変更に完全連動させる。"""
    rank_map = _normalise_ranking_for_map(ranking_df)
    signature = _island_rank_signature(rank_map)

    cells = []
    seen = set()

    for machine_number, positions in ISLAND_POSITIONS.items():
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

    status_text = (
        f"表示中：{len(rank_map)}台 / ランキング連動"
        if rank_map else
        "ランキング対象データなし"
    )

    svg = (
        f'<svg class="island-svg" viewBox="0 0 {ISLAND_CANVAS_SIZE[0]} {ISLAND_CANVAS_SIZE[1]}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="台番号島図">'
        f'<rect x="0" y="0" width="{ISLAND_CANVAS_SIZE[0]}" height="{ISLAND_CANVAS_SIZE[1]}" fill="#fafafa"/>'
        f'{"".join(legend)}'
        f'{"".join(cells)}'
        f'<text x="1020" y="28" text-anchor="middle" font-size="14" font-weight="800" '
        f'font-family="Arial, Noto Sans JP, sans-serif" fill="#555555">島図 / 台番号ランキング</text>'
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
.map-stage {{ position:relative; width:2030px; height:964px; transform-origin:top left; }}
.island-svg {{ display:block; width:2030px; height:964px; user-select:none; }}
.island-machine {{ cursor:default; }}
.island-machine rect {{ transition:filter .12s, stroke-width .12s; }}
.island-machine:hover rect {{ filter:brightness(1.06) drop-shadow(0 1px 2px rgba(0,0,0,.25)); stroke-width:2; }}
.zoom-label {{ min-width:45px; text-align:center; }}
.hint {{ padding:8px 12px; background:#fafafa; color:#777; font-size:11px; text-align:center; border-top:1px solid #ddd; }}
</style>
</head>
<body data-ranking-signature="{signature}">
<div class="map-card">
<div class="toolbar">
<div>島図 <span style="opacity:.65">／ {status_text}</span></div>
<div style="display:flex;align-items:center;gap:5px;">
<button onclick="zoom(-0.1)">−</button><span class="zoom-label" id="zoomLabel">100%</span><button onclick="zoom(0.1)">＋</button><button onclick="resetZoom()">リセット</button>
</div>
</div>
<div class="map-scroll"><div class="map-stage" id="mapStage">{svg}</div></div>
<div class="hint">台番号にマウスを合わせると、順位・回数・機種名を確認できます。スマホでは横にスワイプできます。</div>
</div>
<script>
(function() {{
const stage=document.getElementById('mapStage'); const label=document.getElementById('zoomLabel'); let scale=1;
window.zoom=function(delta) {{ scale=Math.max(.5,Math.min(1.6,scale+delta)); stage.style.transform=`scale(${{scale}})`; stage.style.marginBottom=`${{964*(scale-1)}}px`; label.textContent=Math.round(scale*100)+'%'; }};
window.resetZoom=function() {{ scale=1; stage.style.transform='scale(1)'; stage.style.marginBottom='0px'; label.textContent='100%'; }};
}})();
</script>
</body>
</html>'''

    components.html(html, height=1060, scrolling=False)


# ==========================================
# 日本語カレンダー（外部パッケージ不要）
# ==========================================

JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

def japanese_calendar(label, state_key, default_date=None):
    """
    日付表示そのものをクリックすると、日本語カレンダーが開く日付ピッカー。

    ・日付表示とカレンダーアイコンを同じ1つの枠にまとめる
    ・枠全体をクリック可能にする
    ・カレンダーはダークテーマ
    ・曜日、年月、日付を日本語表示
    """
    if default_date is None:
        default_date = date.today()

    if state_key not in st.session_state:
        st.session_state[state_key] = default_date

    # 保存値を必ず date 型へ統一
    selected_date = st.session_state[state_key]
    if isinstance(selected_date, pd.Timestamp):
        selected_date = selected_date.date()
    elif isinstance(selected_date, str):
        selected_date = pd.to_datetime(selected_date).date()
    st.session_state[state_key] = selected_date

    view_key = f"{state_key}_view_month"
    if view_key not in st.session_state:
        st.session_state[view_key] = selected_date.replace(day=1)

    st.markdown(
        f"<div class='date-picker-label'>{label}</div>",
        unsafe_allow_html=True,
    )

    # 日付＋カレンダーアイコンを「1つの枠」にする。
    # このボタン全体を押すとカレンダーが開く。
    with st.popover(
        f"{selected_date.strftime('%Y/%m/%d')}",
        use_container_width=True,
    ):
        nav_prev, nav_title, nav_next = st.columns([1, 5, 1])

        with nav_prev:
            if st.button(
                "‹",
                key=f"{state_key}_prev_month",
                use_container_width=True,
            ):
                current = st.session_state[view_key]
                previous_month = (
                    current.replace(day=1) - timedelta(days=1)
                ).replace(day=1)
                st.session_state[view_key] = previous_month
                st.rerun()

        with nav_title:
            view_month = st.session_state[view_key]
            st.markdown(
                f"<div class='jp-calendar-title'>{view_month.year}年{view_month.month}月</div>",
                unsafe_allow_html=True,
            )

        with nav_next:
            if st.button(
                "›",
                key=f"{state_key}_next_month",
                use_container_width=True,
            ):
                current = st.session_state[view_key]
                if current.month == 12:
                    next_month = current.replace(
                        year=current.year + 1,
                        month=1,
                        day=1,
                    )
                else:
                    next_month = current.replace(
                        month=current.month + 1,
                        day=1,
                    )
                st.session_state[view_key] = next_month
                st.rerun()

        # 曜日
        weekday_cols = st.columns(7)
        for i, weekday in enumerate(JAPANESE_WEEKDAYS):
            with weekday_cols[i]:
                st.markdown(
                    f"<div class='jp-calendar-weekday'>{weekday}</div>",
                    unsafe_allow_html=True,
                )

        # 日付
        month_days = calendar.monthcalendar(
            view_month.year,
            view_month.month,
        )

        for week_index, week in enumerate(month_days):
            day_cols = st.columns(7)

            for weekday_index, day_number in enumerate(week):
                with day_cols[weekday_index]:
                    if day_number == 0:
                        st.markdown(
                            "<div class='jp-calendar-empty'></div>",
                            unsafe_allow_html=True,
                        )
                        continue

                    day_date = date(
                        view_month.year,
                        view_month.month,
                        day_number,
                    )

                    is_selected = day_date == selected_date
                    button_label = (
                        f"● {day_number}"
                        if is_selected
                        else str(day_number)
                    )

                    if st.button(
                        button_label,
                        key=f"{state_key}_day_{day_date.isoformat()}",
                        use_container_width=True,
                    ):
                        st.session_state[state_key] = day_date
                        st.session_state[view_key] = day_date.replace(day=1)
                        st.rerun()

        st.markdown(
            f"<div class='jp-calendar-selected'>選択日："
            f"{selected_date.year}年{selected_date.month}月{selected_date.day}日"
            f"</div>",
            unsafe_allow_html=True,
        )

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

    /* ダッシュボード上部の操作ボタンをスマホで横にはみ出させない */
    div[data-testid="stHorizontalBlock"] {
        max-width: 100% !important;
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
   スマホ表示時のカレンダー崩れ防止
   Streamlitはスマホ幅で st.columns() を縦並びにするため、
   カレンダーの「前月・年月・次月」や「曜日・日付」が
   1列になっていました。ポップオーバー内だけ横並びに固定します。
   ========================================================= */
@media (max-width: 768px) {
    div[data-testid="stPopoverBody"] {
        width: min(94vw, 520px) !important;
        max-width: 94vw !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* カレンダー内部の全 st.columns をスマホでも横並びにする */
    div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        min-width: 0 !important;
        gap: 3px !important;
    }

    div[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 0 !important;
        width: 0 !important;
        flex: 1 1 0 !important;
    }

    /* 日付・曜日ボタンを各列の幅に収める */
    div[data-testid="stPopoverBody"] div.stButton,
    div[data-testid="stPopoverBody"] div.stButton > button {
        width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    div[data-testid="stPopoverBody"] div.stButton > button {
        padding-left: 2px !important;
        padding-right: 2px !important;
        font-size: 13px !important;
    }

    /* カレンダー内の余白をスマホ向けに少し縮小 */
    div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
        min-width: 0 !important;
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
                パチスロ分析システムへようこそ。<br>
                パスワードを入力してダッシュボードへ進んでください。
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
# 6. 店舗選択画面
# ==========================================

if st.session_state["selected_store"] is None:

    st.markdown(
        """
        <div style="padding: 20px 0 8px; font-family: Orbitron, sans-serif; color: #9fa8bf; font-size: 11px; letter-spacing: 2px;">
            PENION ANALYTICS / STORE SELECT
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title("🏪 店舗選択")
    st.caption("分析対象の店舗を選択してください。")

    store_options = ["店舗を選択して下さい", "ピーアーク相模大野"]

    store_name = st.selectbox(
        "店舗",
        store_options,
        index=0,
        label_visibility="collapsed",
    )

    if st.button("分析を開始  →", use_container_width=False, key="start_analysis_button"):
        if store_name == "店舗を選択して下さい":
            st.warning("店舗を選択して下さい。")
        else:
            st.session_state["selected_store"] = store_name
            st.rerun()

    st.stop()


# ==========================================
# 7. 分析メイン画面
# ==========================================

store = st.session_state["selected_store"]

col_title, col_btn, col_reset = st.columns([8, 1.5, 1.5])

with col_title:
    st.markdown(
        """
        <div style="font-family:Orbitron,sans-serif; font-size:11px; letter-spacing:2px; color:#8e98b0; margin-bottom:3px;">
            PENION ANALYTICS / DASHBOARD
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="dashboard-main-title">分析ダッシュボード</div>',
        unsafe_allow_html=True,
    )

with col_btn:
    st.write("")
    if st.button("更新", use_container_width=False, key="refresh_data_button"):
        st.cache_data.clear()
        st.success("画面を最新データに更新しました！")
        st.rerun()

with col_reset:
    st.write("")
    if st.button("戻る", key="back_to_store_button"):
        st.session_state["selected_store"] = None
        st.rerun()

st.markdown("---")


# ==========================================
# DBから最新データ取得＆タブ描画
# ==========================================

df_slopachi, df_matomaru = load_data()

# タブの作成
tab1, tab2 = st.tabs(
    [
        "3. スロパチ分析",
        "4. まとまる君",
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

    col_date_start, col_wave, col_date_end = st.columns(
        [1, 0.12, 1],
        gap="small"
    )

    with col_date_start:

        start_date = japanese_calendar(
            "開始日",
            "analysis_start_date",
            default_date=default_start_date,
        )

    with col_wave:

        st.markdown(
            "<div class='date-range-wave'>〜</div>",
            unsafe_allow_html=True,
        )

    with col_date_end:

        end_date = japanese_calendar(
            "終了日",
            "analysis_end_date",
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
    if "selected_machine_filter" not in st.session_state:
        st.session_state["selected_machine_filter"] = "全て"

    def _save_machine_filter():
        # ユーザーが機種selectboxを操作した時だけ、この値を更新する。
        st.session_state["selected_machine_filter"] = (
            st.session_state.get("analysis_model_widget", "全て")
        )

    # 保存している機種が現在のDBの選択肢から消えている場合のみ
    # 「全て」に戻す。
    if st.session_state["selected_machine_filter"] not in model_options:
        st.session_state["selected_machine_filter"] = "全て"

    # selectbox自身のキーと、実際のフィルタ条件を分離する。
    # これが日付変更時に「全て」へ戻ってしまう問題を防ぐ。
    widget_default = st.session_state["selected_machine_filter"]

    if "analysis_model_widget" not in st.session_state:
        st.session_state["analysis_model_widget"] = widget_default

    # widget側が選択肢から外れている場合だけ同期する。
    if st.session_state["analysis_model_widget"] not in model_options:
        st.session_state["analysis_model_widget"] = widget_default

    st.selectbox(
        "機種",
        model_options,
        key="analysis_model_widget",
        on_change=_save_machine_filter,
    )

    # ランキング集計に使う機種は、selectboxの表示値ではなく
    # 「最後にユーザーが明示的に選択した値」を使用する。
    selected_model = st.session_state["selected_machine_filter"]

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

        render_island_map(ranking_df)

    # ==========================================
    # データがない場合
    # ==========================================

    else:

        st.info(
            "選択した日付範囲・機種に該当するデータがDBにありません。"
        )

# ==========================================
# タブ2
# ==========================================

with tab2:

    st.subheader(
        "📈 連続投入分析 (日付 × 台番号)"
    )


    if not df_matomaru.empty:

        pivot_df = df_matomaru.pivot_table(
            index="台番号",
            columns="日付",
            values="差枚",
            aggfunc="first",
        )


        def style_diff(val):

            if pd.isna(val):

                return ""


            elif val > 0:

                return (
                    "background-color:#ffcdd2;"
                    "color:#b71c1c;"
                    "font-weight:bold;"
                )


            elif val < 0:

                return (
                    "background-color:#bbdefb;"
                    "color:#0d47a1;"
                    "font-weight:bold;"
                )


            return ""


        styled_pivot = (
            pivot_df.style
            .map(style_diff)
            .format(
                "{:+.0f}",
                na_rep="-"
            )
        )


        st.dataframe(
            styled_pivot,
            use_container_width=True,
        )


        # --------------------------------------
        # DB全データ
        # --------------------------------------

        with st.expander(
            "📝 まとまる君 DB全データ一覧"
        ):

            st.dataframe(
                df_matomaru[
                    [
                        "日付",
                        "台番号",
                        "機種名",
                        "差枚",
                        "回転G数",
                        "並び人数",
                        "取材",
                        "来店",
                    ]
                ],
                use_container_width=True,
            )


    else:

        st.info(
            "まとまる君テーブルにデータがありません。"
        )