import io
import re
import sqlite3
import time
from datetime import datetime
from urllib.parse import urljoin, unquote, urlparse

import easyocr
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance


# ============================================================
# 初期設定
# ============================================================

DB_PATH = "database.db"

BASE_URL = "https://777.slopachi-station.com/"

# ここ以降のデータを取得
START_DATE = "2026/01/01"

# 日付比較用
START_DATE_OBJ = datetime.strptime(
    START_DATE,
    "%Y/%m/%d"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ============================================================
# OCR 初期化
# ============================================================

print("⚙️ OCRエンジンを読み込み中...")

reader = easyocr.Reader(
    ["ja", "en"],
    gpu=False
)


# ============================================================
# SQLite用
# ============================================================

def quote_identifier(name):
    """
    SQLiteのテーブル名を安全に使用する
    """

    return '"' + name.replace('"', '""') + '"'


def clean_shop_name(shop_name):
    """
    店舗名から不要な装飾を削除する
    """

    shop_name = shop_name.strip()

    # 【スロパチアワード受賞店】などの
    # 先頭の【】装飾を削除
    shop_name = re.sub(
        r"^【[^】]+】",
        "",
        shop_name
    )

    # 空白を整理
    shop_name = re.sub(
        r"\s+",
        " ",
        shop_name
    ).strip()

    return shop_name


def sanitize_table_name(shop_name):
    """
    店舗名をSQLiteのテーブル名として使用可能な形にする
    """

    shop_name = clean_shop_name(
        shop_name
    )

    shop_name = re.sub(
        r'[\x00-\x1f\\/:*?"<>|]',
        "_",
        shop_name
    )

    if not shop_name:
        shop_name = "店舗名不明"

    return f"{shop_name}_スロパチ"


# ============================================================
# 店舗情報取得
# ============================================================

def get_shop_name(shop_id):
    """
    shop_idから店舗情報ページを取得して
    店舗名を取得する
    """

    url = f"{BASE_URL}shop_data/{shop_id}/"

    print("\n🏪 店舗情報を取得中...")

    try:

        res = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        if res.status_code != 200:

            print(
                f"⚠️ 店舗ページ取得失敗 "
                f"(HTTP {res.status_code})"
            )

            return ""

        soup = BeautifulSoup(
            res.text,
            "html.parser"
        )

        # ----------------------------------------------------
        # h1から取得
        # ----------------------------------------------------

        h1 = soup.find("h1")

        if h1:

            shop_name = h1.get_text(
                " ",
                strip=True
            )

            shop_name = clean_shop_name(
                shop_name
            )

            if shop_name:

                return shop_name

        # ----------------------------------------------------
        # titleから取得
        # ----------------------------------------------------

        title_tag = soup.find("title")

        if title_tag:

            title_text = title_tag.get_text(
                " ",
                strip=True
            )

            shop_name = re.split(
                r"[|｜]",
                title_text
            )[0].strip()

            shop_name = clean_shop_name(
                shop_name
            )

            if (
                shop_name
                and shop_name != "店舗情報"
                and shop_name != "shopposts"
                and "スロパチステーション" not in shop_name
            ):

                return shop_name

    except Exception as e:

        print(
            f"⚠️ 店舗情報取得エラー: {e}"
        )

    return ""


# ============================================================
# 店舗テーブル作成
# ============================================================

def init_shop_table(shop_name):

    table_name = sanitize_table_name(
        shop_name
    )

    quoted_table = quote_identifier(
        table_name
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    cursor = conn.cursor()

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {quoted_table} (
            項番 INTEGER PRIMARY KEY AUTOINCREMENT,
            日付 TEXT NOT NULL,
            機種名 TEXT NOT NULL,
            台番号 TEXT NOT NULL,

            UNIQUE(日付, 機種名, 台番号)
        )
        """
    )

    conn.commit()

    conn.close()

    return table_name


# ============================================================
# 日付処理
# ============================================================

def normalize_date(raw_text, default_year="2026"):
    """
    日付を YYYY/MM/DD に統一
    """

    if not raw_text:
        return ""

    # YYYY/MM/DD
    full_date_match = re.search(
        r"(20\d{2})[/\-]"
        r"(\d{1,2})[/\-]"
        r"(\d{1,2})",
        raw_text
    )

    if full_date_match:

        year = int(
            full_date_match.group(1)
        )

        month = int(
            full_date_match.group(2)
        )

        day = int(
            full_date_match.group(3)
        )

        try:

            datetime(
                year,
                month,
                day
            )

            return (
                f"{year:04d}/"
                f"{month:02d}/"
                f"{day:02d}"
            )

        except ValueError:

            return ""

    # 8月18日
    md_match = re.search(
        r"(\d{1,2})月\s*(\d{1,2})日",
        raw_text
    )

    if md_match:

        month = int(
            md_match.group(1)
        )

        day = int(
            md_match.group(2)
        )

        try:

            datetime(
                int(default_year),
                month,
                day
            )

            return (
                f"{default_year}/"
                f"{month:02d}/"
                f"{day:02d}"
            )

        except ValueError:

            return ""

    return ""


# ============================================================
# 記事の日付取得
# ============================================================

def extract_article_date(soup, url):
    """
    記事ページから日付を取得
    """

    body_text = soup.get_text(
        " ",
        strip=True
    )

    title_tag = soup.find(
        "title"
    )

    title_text = ""

    if title_tag:

        title_text = title_tag.get_text(
            " ",
            strip=True
        )

    decoded_url = unquote(
        url
    )

    # --------------------------------------------------------
    # 1. 訪問日
    # --------------------------------------------------------

    date_match = re.search(
        r"訪問日[:：]?\s*"
        r"(20\d{2})[/\-]"
        r"(\d{1,2})[/\-]"
        r"(\d{1,2})",
        body_text
    )

    if date_match:

        return normalize_date(
            date_match.group(0)
        )

    # --------------------------------------------------------
    # 2. タイトル内 YYYY/MM/DD
    # --------------------------------------------------------

    date_match = re.search(
        r"(20\d{2})[/\-]"
        r"(\d{1,2})[/\-]"
        r"(\d{1,2})",
        title_text
    )

    if date_match:

        return normalize_date(
            date_match.group(0)
        )

    # --------------------------------------------------------
    # 3. URL内 YYYY/MM/DD
    # --------------------------------------------------------

    date_match = re.search(
        r"(20\d{2})[/\-]"
        r"(\d{1,2})[/\-]"
        r"(\d{1,2})",
        decoded_url
    )

    if date_match:

        return normalize_date(
            date_match.group(0)
        )

    # --------------------------------------------------------
    # 4. URLの「8月18日」
    # --------------------------------------------------------

    md_match = re.search(
        r"(\d{1,2})月\s*(\d{1,2})日",
        decoded_url
    )

    if md_match:

        return normalize_date(
            md_match.group(0),
            default_year="2026"
        )

    # --------------------------------------------------------
    # 5. タイトルの「8月18日」
    # --------------------------------------------------------

    md_match = re.search(
        r"(\d{1,2})月\s*(\d{1,2})日",
        title_text
    )

    if md_match:

        return normalize_date(
            md_match.group(0),
            default_year="2026"
        )

    # --------------------------------------------------------
    # 6. 本文から YYYY/MM/DD
    # --------------------------------------------------------

    date_match = re.search(
        r"(20\d{2})[/\-]"
        r"(\d{1,2})[/\-]"
        r"(\d{1,2})",
        body_text
    )

    if date_match:

        return normalize_date(
            date_match.group(0)
        )

    return ""


# ============================================================
# 記事URL判定
# ============================================================

def is_article_url(url):
    """
    実際の記事URLか判定する
    """

    parsed = urlparse(
        url
    )

    # ドメイン確認
    if parsed.netloc != "777.slopachi-station.com":

        return False

    # トップページ除外
    if parsed.path in [
        "",
        "/"
    ]:

        return False

    # 一覧・店舗ページ除外
    excluded_paths = [
        "/shopposts",
        "/shop_data",
        "/category",
        "/tag",
        "/author",
        "/page",
        "/wp-",
        "/feed",
    ]

    for excluded in excluded_paths:

        if parsed.path.startswith(
            excluded
        ):

            return False

    # URLを日本語に戻す
    decoded_url = unquote(
        url
    )

    # 記事URLには基本的に
    # 「○月○日」が含まれるため判定
    if re.search(
        r"\d{1,2}月\d{1,2}日",
        decoded_url
    ):

        return True

    # YYYY-MM-DD形式も許可
    if re.search(
        r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}",
        decoded_url
    ):

        return True

    return False


# ============================================================
# 記事URL取得
# ============================================================

def get_article_urls(soup):

    article_urls = []

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a.get(
            "href"
        )

        if not href:
            continue

        url = urljoin(
            BASE_URL,
            href
        )

        # ?以降や#以降を削除
        parsed = urlparse(
            url
        )

        clean_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"{parsed.path}"
        )

        # 実際の記事URLだけ
        if not is_article_url(
            clean_url
        ):

            continue

        if (
            clean_url
            not in article_urls
        ):

            article_urls.append(
                clean_url
            )

    return article_urls


# ============================================================
# 台番号処理
# ============================================================

def parse_machine_numbers(num_str):

    numbers = []

    parts = re.split(
        r"[,、・]",
        num_str
    )

    for part in parts:

        part = part.strip()

        range_match = re.match(
            r"^(\d+)\s*[〜～\-]\s*(\d+)$",
            part
        )

        if range_match:

            start_num = int(
                range_match.group(1)
            )

            end_num = int(
                range_match.group(2)
            )

            if start_num <= end_num:

                for n in range(
                    start_num,
                    end_num + 1
                ):

                    numbers.append(
                        str(n)
                    )

        else:

            num_match = re.search(
                r"\d+",
                part
            )

            if num_match:

                numbers.append(
                    num_match.group()
                )

    return numbers


# ============================================================
# パチンコ判定
# ============================================================

def is_pachinko_model(model_name):

    pachinko_patterns = [

        r"^[PpeE]\s",

        r"パチンコ",

        r"4パチ",

        r"差玉",

        r"総差玉",

    ]

    for pattern in pachinko_patterns:

        if re.search(
            pattern,
            model_name,
            re.IGNORECASE
        ):

            return True

    return False


# ============================================================
# 機種名整形
# ============================================================

def clean_model_name(text):

    text = text.strip()

    if not text:
        return ""

    if re.search(
        r"[+＋\-ー−]?\d+.*"
        r"[枚石Gg玉発]"
        r"|回転数"
        r"|差枚"
        r"|差玉"
        r"|総計"
        r"|平均",
        text
    ):

        return ""

    if re.match(
        r"^[+\-\d,.\sGg枚石発!]+$",
        text
    ):

        return ""

    text = re.sub(
        r"^[+＋\-ー−,\s]+",
        "",
        text
    )

    if is_pachinko_model(
        text
    ):

        return ""

    if len(text) < 2:

        return ""

    return text


# ============================================================
# HTMLテーブルから取得
# ============================================================

def extract_data_from_tables(
    soup,
    date_str
):

    extracted = []

    tables = soup.find_all(
        "table"
    )

    for table in tables:

        rows = table.find_all(
            "tr"
        )

        if not rows:
            continue

        header_cols = [

            td.get_text(
                " ",
                strip=True
            )

            for td in rows[0].find_all(
                ["td", "th"]
            )
        ]

        num_idx = -1
        model_idx = -1

        for idx, col in enumerate(
            header_cols
        ):

            if (
                "台番号" in col
                or "台番" in col
            ):

                num_idx = idx

            if (
                "機種名" in col
                or "機種" in col
            ):

                model_idx = idx

        if (
            num_idx == -1
            or model_idx == -1
        ):

            continue

        for row in rows[1:]:

            cols = [

                td.get_text(
                    " ",
                    strip=True
                )

                for td in row.find_all(
                    ["td", "th"]
                )
            ]

            if (
                len(cols)
                <= max(
                    num_idx,
                    model_idx
                )
            ):

                continue

            unit_num = cols[
                num_idx
            ]

            model_name = cols[
                model_idx
            ]

            num_match = re.search(
                r"\b(\d{3,4})\b",
                unit_num
            )

            cleaned_model = clean_model_name(
                model_name
            )

            if (
                num_match
                and cleaned_model
            ):

                extracted.append(
                    (
                        date_str,
                        cleaned_model,
                        num_match.group(1)
                    )
                )

    return extracted


# ============================================================
# OCR画像前処理
# ============================================================

def preprocess_image(image_bytes):

    try:

        img = Image.open(
            io.BytesIO(
                image_bytes
            )
        ).convert(
            "L"
        )

        img = img.resize(
            (
                img.width * 2,
                img.height * 2
            ),
            Image.Resampling.LANCZOS
        )

        enhancer = ImageEnhance.Contrast(
            img
        )

        img = enhancer.enhance(
            2.0
        )

        buf = io.BytesIO()

        img.save(
            buf,
            format="PNG"
        )

        return buf.getvalue()

    except Exception:

        return image_bytes


# ============================================================
# 画像OCRから取得
# ============================================================

def extract_data_from_images(
    soup,
    date_str
):

    extracted = []

    img_tags = soup.find_all(
        "img"
    )

    for img in img_tags:

        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
        )

        if not src:
            continue

        # ----------------------------------------------------
        # base64などを除外
        # ----------------------------------------------------

        if src.startswith(
            "data:"
        ):

            continue

        # SVGを除外
        if ".svg" in src.lower():

            continue

        # ----------------------------------------------------
        # ロゴ・アイコン類を除外
        # ----------------------------------------------------

        lower_src = src.lower()

        skip_keywords = [

            "logo",
            "header",
            "banner",
            "icon",
            "avatar",
            "btn",
            "arrow",
            "loading",
            "spinner",
            "sns",
            "twitter",
            "instagram",
            "facebook",
        ]

        if any(
            keyword in lower_src
            for keyword in skip_keywords
        ):

            continue

        src = urljoin(
            BASE_URL,
            src
        )

        try:

            res = requests.get(
                src,
                headers=HEADERS,
                timeout=15
            )

            if res.status_code != 200:

                continue

            content_type = res.headers.get(
                "Content-Type",
                ""
            ).lower()

            if "image" not in content_type:

                continue

            if "svg" in content_type:

                continue

            processed_bytes = preprocess_image(
                res.content
            )

            results = reader.readtext(
                processed_bytes,
                detail=1
            )

            if not results:

                continue

            rows = []

            for bbox, text, prob in results:

                if prob < 0.25:

                    continue

                top_y = bbox[0][1]
                left_x = bbox[0][0]

                matched_row = None

                for row in rows:

                    if abs(
                        row["y"] - top_y
                    ) < 22:

                        matched_row = row

                        break

                if matched_row:

                    matched_row["items"].append(
                        {
                            "x": left_x,
                            "text": text.strip()
                        }
                    )

                else:

                    rows.append(
                        {
                            "y": top_y,
                            "items": [
                                {
                                    "x": left_x,
                                    "text": text.strip()
                                }
                            ]
                        }
                    )

            for row in rows:

                items = sorted(
                    row["items"],
                    key=lambda x: x["x"]
                )

                unit_num = ""
                model_name = ""

                for item in items:

                    text = item["text"]

                    normalized_num = (
                        text
                        .replace("I", "1")
                        .replace("l", "1")
                        .replace("O", "0")
                        .replace("o", "0")
                    )

                    num_match = re.search(
                        r"\b(\d{3,4})\b",
                        normalized_num
                    )

                    if (
                        num_match
                        and not unit_num
                    ):

                        unit_num = (
                            num_match.group(1)
                        )

                        continue

                    cleaned = clean_model_name(
                        text
                    )

                    if (
                        cleaned
                        and not model_name
                    ):

                        model_name = cleaned

                if (
                    unit_num
                    and model_name
                ):

                    extracted.append(
                        (
                            date_str,
                            model_name,
                            unit_num
                        )
                    )

        except Exception as e:

            print(
                f"    ⚠️ 画像解析エラー: {e}"
            )

    return extracted


# ============================================================
# パチンコ限定記事判定
# ============================================================

def is_pachinko_only_article(
    title_text
):

    patterns = [
        "じゃんじゃんレポート",
        "パチンコ取材",
    ]

    return any(
        pattern in title_text
        for pattern in patterns
    )


# ============================================================
# 記事データ取得
# ============================================================

def scrape_article_data(
    soup,
    formatted_date
):

    title_tag = soup.find(
        "title"
    )

    title_text = ""

    if title_tag:

        title_text = title_tag.get_text(
            " ",
            strip=True
        )

    # パチンコ限定記事はスキップ
    if is_pachinko_only_article(
        title_text
    ):

        print(
            "  ⏭️ [パチンコ限定記事スキップ]"
        )

        return []

    extracted_data = []

    # --------------------------------------------------------
    # A. HTMLテーブルから取得
    # --------------------------------------------------------

    table_data = extract_data_from_tables(
        soup,
        formatted_date
    )

    extracted_data.extend(
        table_data
    )

    # --------------------------------------------------------
    # B. テキストから取得
    # --------------------------------------------------------

    elements = soup.find_all(
        [
            "h2",
            "h3",
            "h4",
            "p",
            "strong",
            "td",
            "div",
        ]
    )

    for el in elements:

        text = el.get_text(
            " ",
            strip=True
        )

        matches = re.findall(
            r"【([^】]+?)\s+"
            r"([\d〜～\-・,、]+)】",
            text
        )

        for (
            model_name,
            num_range
        ) in matches:

            model_clean = clean_model_name(
                model_name
            )

            if not model_clean:

                continue

            if is_pachinko_model(
                model_clean
            ):

                continue

            for unit_num in parse_machine_numbers(
                num_range
            ):

                extracted_data.append(
                    (
                        formatted_date,
                        model_clean,
                        unit_num
                    )
                )

    # --------------------------------------------------------
    # C. 何も取れなかった場合のみOCR
    # --------------------------------------------------------

    if not extracted_data:

        print(
            "  🖼️ テキスト・テーブルなし。"
            "画像(OCR)解析を実行中..."
        )

        ocr_data = extract_data_from_images(
            soup,
            formatted_date
        )

        extracted_data.extend(
            ocr_data
        )

    # --------------------------------------------------------
    # 重複削除
    # --------------------------------------------------------

    unique_data = list(
        set(extracted_data)
    )

    if unique_data:

        print(
            f"  └─ 有効データ "
            f"{len(unique_data)} 件を抽出完了"
        )

    return unique_data


# ============================================================
# DB保存
# ============================================================

def save_to_db(
    data_list,
    table_name
):

    if not data_list:

        return 0

    quoted_table = quote_identifier(
        table_name
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    cursor = conn.cursor()

    saved_count = 0

    for (
        dt,
        model,
        machine_num
    ) in data_list:

        cursor.execute(
            f"""
            INSERT OR IGNORE INTO
            {quoted_table}
            (
                日付,
                機種名,
                台番号
            )
            VALUES (?, ?, ?)
            """,
            (
                dt,
                model,
                machine_num
            )
        )

        if cursor.rowcount > 0:

            saved_count += 1

    conn.commit()

    conn.close()

    return saved_count


# ============================================================
# 記事一覧取得・処理
# ============================================================

def fetch_and_process_articles(
    shop_id,
    table_name
):

    print(
        "\n🌐 記事一覧を取得開始..."
    )

    total_saved = 0
    total_articles = 0

    page = 1

    stop_processing = False

    processed_urls = set()

    while not stop_processing:

        # ----------------------------------------------------
        # 一覧ページURL
        # ----------------------------------------------------

        if page == 1:

            page_url = (
                f"{BASE_URL}"
                f"shopposts/"
                f"?shop_id={shop_id}"
            )

        else:

            page_url = (
                f"{BASE_URL}"
                f"shopposts/page/{page}/"
                f"?shop_id={shop_id}"
            )

        print(
            f"\n📄 一覧ページ取得中: "
            f"Page {page}"
        )

        try:

            res = requests.get(
                page_url,
                headers=HEADERS,
                timeout=15
            )

            if res.status_code != 200:

                print(
                    "⚠️ 一覧ページ取得失敗"
                )

                break

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            # ------------------------------------------------
            # 実際の記事URLだけ取得
            # ------------------------------------------------

            article_urls = get_article_urls(
                soup
            )

            # 既に処理済みを除外
            article_urls = [

                url
                for url in article_urls
                if url not in processed_urls

            ]

            if not article_urls:

                print(
                    "\n⏹️ 有効な記事が見つからないため終了"
                )

                break

            print(
                f"  📰 記事候補: "
                f"{len(article_urls)} 件"
            )

            # ------------------------------------------------
            # 記事処理
            # ------------------------------------------------

            for article_url in article_urls:

                if article_url in processed_urls:

                    continue

                processed_urls.add(
                    article_url
                )

                total_articles += 1

                print(
                    f"\n[{total_articles}] "
                    f"記事確認中:"
                )

                print(
                    article_url
                )

                try:

                    article_res = requests.get(
                        article_url,
                        headers=HEADERS,
                        timeout=15
                    )

                    if article_res.status_code != 200:

                        print(
                            "  ⚠️ 記事取得失敗"
                        )

                        continue

                    article_soup = BeautifulSoup(
                        article_res.text,
                        "html.parser"
                    )

                    # ----------------------------------------
                    # 最初に日付だけ取得
                    # ----------------------------------------

                    article_date = extract_article_date(
                        article_soup,
                        article_url
                    )

                    if not article_date:

                        print(
                            "  ⏭️ 日付が取得できませんでした"
                        )

                        continue

                    print(
                        f"  📅 記事日付: "
                        f"{article_date}"
                    )

                    # ----------------------------------------
                    # 2026/01/01より前なら終了
                    # ----------------------------------------

                    try:

                        article_date_obj = datetime.strptime(
                            article_date,
                            "%Y/%m/%d"
                        )

                    except ValueError:

                        print(
                            "  ⚠️ 日付形式エラー"
                        )

                        continue

                    if (
                        article_date_obj
                        < START_DATE_OBJ
                    ):

                        print(
                            "\n"
                            "======================================================="
                        )

                        print(
                            "⏹️ 2026/01/01より前の記事が"
                            "出たため取得を終了します"
                        )

                        print(
                            f"取得対象開始日: "
                            f"{START_DATE}"
                        )

                        print(
                            f"検出日付: "
                            f"{article_date}"
                        )

                        print(
                            "======================================================="
                        )

                        stop_processing = True

                        break

                    # ----------------------------------------
                    # 2026/01/01以降のみ解析
                    # ----------------------------------------

                    data = scrape_article_data(
                        article_soup,
                        article_date
                    )

                    saved = save_to_db(
                        data,
                        table_name
                    )

                    total_saved += saved

                    if saved > 0:

                        print(
                            f"  💾 新規保存: "
                            f"{saved} 件"
                        )

                    else:

                        print(
                            "  └─ 保存データなし"
                        )

                except Exception as e:

                    print(
                        f"  ❌ 記事処理エラー: {e}"
                    )

                # サーバー負荷軽減
                time.sleep(0.5)

            if stop_processing:

                break

            page += 1

            time.sleep(0.5)

        except Exception as e:

            print(
                f"❌ 一覧処理エラー: {e}"
            )

            break

    return (
        total_articles,
        total_saved
    )


# ============================================================
# メイン処理
# ============================================================

def main():

    print(
        "=" * 55
    )

    print(
        "       スロパチデータ初期取得システム"
    )

    print(
        "=" * 55
    )

    # --------------------------------------------------------
    # shop_id入力
    # --------------------------------------------------------

    while True:

        shop_id = input(
            "\n取得したい店舗のshop_idを入力してください："
        ).strip()

        if shop_id.isdigit():

            break

        print(
            "⚠️ shop_idは数字で入力してください。"
        )

    # --------------------------------------------------------
    # 店舗名取得
    # --------------------------------------------------------

    shop_name = get_shop_name(
        shop_id
    )

    if not shop_name:

        print(
            "\n⚠️ 店舗名を自動取得できませんでした。"
        )

        while True:

            shop_name = input(
                "店舗名を入力してください："
            ).strip()

            if shop_name:

                shop_name = clean_shop_name(
                    shop_name
                )

                break

    # --------------------------------------------------------
    # テーブル作成
    # --------------------------------------------------------

    table_name = init_shop_table(
        shop_name
    )

    print(
        "\n"
        + "=" * 55
    )

    print(
        f"🏪 店舗名: {shop_name}"
    )

    print(
        f"🆔 shop_id: {shop_id}"
    )

    print(
        f"📅 取得対象: {START_DATE} 以降"
    )

    print(
        f"🗄️ テーブル: {table_name}"
    )

    print(
        f"💾 DB: {DB_PATH}"
    )

    print(
        "=" * 55
    )

    # --------------------------------------------------------
    # 記事取得
    # --------------------------------------------------------

    total_articles, total_saved = (
        fetch_and_process_articles(
            shop_id,
            table_name
        )
    )

    # --------------------------------------------------------
    # 完了
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 55
    )

    print(
        "✨ データ取得完了"
    )

    print(
        f"確認記事数: {total_articles} 件"
    )

    print(
        f"新規保存件数: {total_saved} 件"
    )

    print(
        f"使用テーブル: {table_name}"
    )

    print(
        f"データベース: {DB_PATH}"
    )

    print(
        "=" * 55
    )


# ============================================================
# 実行
# ============================================================

if __name__ == "__main__":

    main()