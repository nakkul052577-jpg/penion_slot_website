import hashlib
import html as html_lib
import json

ISLAND_CANVAS_SIZE = (2050, 700)
ISLAND_CELL_W = 37
ISLAND_CELL_H = 19

ISLAND_RANK_COLORS = {
    1: "#ff1b1b", 2: "#a900d6", 3: "#df4be8", 4: "#13a84a",
    5: "#ffb300", 6: "#ffe000", 7: "#087bb9", 8: "#00a9d8", 9: "#a9a9a9",
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
