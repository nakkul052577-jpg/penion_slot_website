import hashlib
import html as html_lib
import json
import streamlit.components.v1 as components

ISLAND_CANVAS_SIZE = (2050, 850)
ISLAND_CELL_W = 37
ISLAND_CELL_H = 19
ISLAND_RANK_COLORS = {
    1: "#ff1b1b", 2: "#a900d6", 3: "#df4be8", 4: "#13a84a",
    5: "#ffb300", 6: "#ffe000", 7: "#087bb9", 8: "#00a9d8", 9: "#a9a9a9",
}
ISLAND_DEFAULT_COLOR = "#f7f7f7"
ISLAND_BORDER_COLOR = "#7b7b7b"
ISLAND_TEXT_COLOR = "#4a4a4a"

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


def render_island_map(ranking_df, store_name, island_positions):
    """画像を使わずSVGで島図を描画し、ランキング変更に完全連動させる。"""
    rank_map = _normalise_ranking_for_map(ranking_df)
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
.map-stage {{ position:relative; width:2050px; height:850px; transform-origin:top left; }}
.island-svg {{ display:block; width:2050px; height:850px; user-select:none; }}
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
window.zoom=function(delta) {{ scale=Math.max(.5,Math.min(1.6,scale+delta)); stage.style.transform=`scale(${{scale}})`; stage.style.marginBottom=`${{850*(scale-1)}}px`; label.textContent=Math.round(scale*100)+'%'; }};
window.resetZoom=function() {{ scale=1; stage.style.transform='scale(1)'; stage.style.marginBottom='0px'; label.textContent='100%'; }};
}})();
</script>
</body>
</html>'''

    components.html(html, height=940, scrolling=False)
