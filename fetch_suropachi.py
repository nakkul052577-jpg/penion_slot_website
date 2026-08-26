import io
import re
import sqlite3
import time
from bs4 import BeautifulSoup
import easyocr
from PIL import Image, ImageEnhance
import requests

DB_PATH = "p_ark_database.db"
SHOP_ID = "22404"
BASE_POSTS_URL = "https://777.slopachi-station.com/shopposts/?shop_id=" + SHOP_ID

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("⚙️ OCRエンジンを読み込み中...")
reader = easyocr.Reader(['ja', 'en'], gpu=False)


def reset_and_init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS ピーアーク相模大野_スロパチ")
    cursor.execute(
        """
    CREATE TABLE ピーアーク相模大野_スロパチ (
        項番 INTEGER PRIMARY KEY AUTOINCREMENT,
        日付 TEXT,
        機種名 TEXT,
        台番号 TEXT,
        UNIQUE(日付, 台番号, 機種名)
    )
    """
    )
    conn.commit()
    conn.close()
    print("🗑️ 既存DBを削除し、一から再作成（初期化）しました。")


def normalize_date(raw_text, default_year="2026"):
    """日付を YYYY/MM/DD 形式に整形"""
    if not raw_text:
        return ""

    year_m = re.search(r'(20\d{2})', raw_text)
    year = year_m.group(1) if year_m else default_year

    md_m = re.search(r'(\d{1,2})月\s*(\d{1,2})日', raw_text)
    if not md_m:
        md_m = re.search(r'(\d{1,2})[/\-](\d{1,2})', raw_text)

    if md_m:
        month = int(md_m.group(1))
        day = int(md_m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year}/{month:02d}/{day:02d}"
    return ""


def parse_machine_numbers(num_str):
    numbers = []
    parts = re.split(r'[,・]', num_str)
    for part in parts:
        part = part.strip()
        range_match = re.match(r'^(\d+)\s*[〜～\-]\s*(\d+)$', part)
        if range_match:
            start_num = int(range_match.group(1))
            end_num = int(range_match.group(2))
            for n in range(start_num, end_num + 1):
                numbers.append(str(n))
        else:
            num_match = re.search(r'\d+', part)
            if num_match:
                numbers.append(num_match.group())
    return numbers


def preprocess_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('L')
        img = img.resize(
            (img.width * 2, img.height * 2), Image.Resampling.LANCZOS
        )
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception:
        return image_bytes


def is_pachinko_model(model_name):
    pachinko_patterns = [
        r'^[PpeE]\s',
        r'パチンコ',
        r'ユニコーン',
        r'鬼がかり',
        r'4パチ',
        r'玉',
        r'BOX',
        r'ボックス',
        r'総差玉',
        r'取材',
        r'来店',
        r'レポート',
    ]
    for pattern in pachinko_patterns:
        if re.search(pattern, model_name, re.IGNORECASE):
            return True
    return False


def clean_model_name(text):
    text = text.strip()
    if re.search(r'[+＋\-ー−]?\d+.*[枚石Gg玉発]|回転数|差枚|差玉|総計|平均', text):
        return ""
    if re.match(r'^[+\-\d,.\sGg枚石発!]+$', text):
        return ""
    text = re.sub(r'^[+＋\-ー−,\s]+', '', text)

    if is_pachinko_model(text):
        return ""

    return text if len(text) >= 2 else ""


def extract_data_from_images(soup, date_str):
    extracted = []
    img_tags = soup.find_all('img')

    for img in img_tags:
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if not src:
            continue

        if any(
            k in src
            for k in [
                'logo',
                'header',
                'banner',
                'icon',
                'avatar',
                'btn',
                'pachinko',
            ]
        ):
            continue

        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = 'https://777.slopachi-station.com' + src

        try:
            res = requests.get(src, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                continue

            processed_bytes = preprocess_image(res.content)
            results = reader.readtext(processed_bytes, detail=1)
            if not results:
                continue

            rows = []
            for bbox, text, prob in results:
                top_y = bbox[0][1]
                left_x = bbox[0][0]

                matched_row = None
                for row in rows:
                    if abs(row['y'] - top_y) < 22:
                        matched_row = row
                        break

                if matched_row:
                    matched_row['items'].append(
                        {'x': left_x, 'text': text.strip()}
                    )
                else:
                    rows.append(
                        {'y': top_y, 'items': [{'x': left_x, 'text': text.strip()}]}
                    )

            for row in rows:
                items = sorted(row['items'], key=lambda k: k['x'])
                unit_num, model_name = "", ""

                for item in items:
                    t = item['text']
                    norm_num = (
                        t.replace('I', '1')
                        .replace('l', '1')
                        .replace('q', '9')
                        .replace('O', '0')
                        .replace('o', '0')
                    )
                    num_m = re.search(r'\b(\d{3,4})\b', norm_num)

                    if num_m and not unit_num:
                        unit_num = num_m.group(1)
                        continue

                    cleaned = clean_model_name(t)
                    if cleaned and not model_name:
                        model_name = cleaned

                if unit_num and model_name:
                    extracted.append((date_str, model_name, unit_num))

        except Exception as e:
            print(f"    ⚠️ 画像解析エラー: {e}")

    return extracted


def extract_data_from_tables(soup, date_str):
    extracted = []
    tables = soup.find_all('table')

    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            continue

        header_cols = [
            td.text.strip() for td in rows[0].find_all(['td', 'th'])
        ]
        num_idx, model_idx = -1, -1

        for idx, col in enumerate(header_cols):
            if '台番号' in col or '台番' in col:
                num_idx = idx
            elif '機種' in col or '機種名' in col:
                model_idx = idx

        if num_idx == -1 or model_idx == -1:
            continue

        for row in rows[1:]:
            cols = [td.text.strip() for td in row.find_all(['td', 'th'])]
            if len(cols) > max(num_idx, model_idx):
                unit_num = cols[num_idx]
                model_name = cols[model_idx]

                num_match = re.search(r'\b(\d{3,4})\b', unit_num)
                cleaned_model = clean_model_name(model_name)

                if num_match and cleaned_model:
                    extracted.append(
                        (date_str, cleaned_model, num_match.group(1))
                    )

    return extracted


def is_pachinko_only_article(title_text):
    if 'じゃんじゃんレポート' in title_text or 'パチンコ取材' in title_text:
        return True
    return False


def scrape_article_data(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(res.text, 'html.parser')
    body_text = soup.get_text()
    title_text = soup.find('title').text if soup.find('title') else ""

    if is_pachinko_only_article(title_text):
        print(
            "  ⏭️ [パチンコ限定記事スキップ] タイトルよりパチンコ専門記事と判定"
        )
        return []

    # 1. 記事内から年の特定（無ければ2026年をデフォルト適用）
    year_match = re.search(r'(20\d{2})', title_text + " " + body_text + " " + url)
    detected_year = year_match.group(1) if year_match else "2026"

    # 2. 日付の取得・整形
    formatted_date = ""
    date_match = re.search(
        r'訪問日[:：]\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})', body_text
    )
    if date_match:
        formatted_date = normalize_date(
            date_match.group(1), default_year=detected_year
        )

    if not formatted_date:
        m = re.search(r'(\d{1,2}月\d{1,2}日)', title_text)
        if m:
            formatted_date = normalize_date(
                m.group(1), default_year=detected_year
            )

    if not formatted_date:
        print("  ⏭️ [スキップ] 日付が取得できませんでした")
        return []

    # 3. 日付判定（2026/01/01 以降のみを抽出対象とする）
    if formatted_date < "2026/01/01":
        print(
            f"  ⏭️ [対象外スキップ] {formatted_date} は2026年1月1日以前のデータです"
        )
        return []

    print(f"  📅 処理対象日付: {formatted_date}")

    extracted_data = []

    # A. HTMLテーブルから取得
    table_data = extract_data_from_tables(soup, formatted_date)
    if table_data:
        extracted_data.extend(table_data)

    # B. テキスト要素から取得
    if not extracted_data:
        elements = soup.find_all(
            ['h2', 'h3', 'h4', 'div', 'p', 'strong', 'td', 'a']
        )
        for el in elements:
            text = el.text.strip()
            matches = re.findall(r'【([^】]+)\s+([\d〜～\-・,]+)】', text)
            for model_name, num_range in matches:
                model_clean = model_name.strip()

                if (
                    "列" in model_clean
                    or is_pachinko_model(model_clean)
                    or not re.search(r'\d', num_range)
                ):
                    continue

                for unit_num in parse_machine_numbers(num_range):
                    extracted_data.append(
                        (formatted_date, model_clean, unit_num)
                    )

    # C. 画像(OCR)から取得
    if not extracted_data:
        print("  🖼️ テキスト・テーブルなし。画像(OCR)解析を実行中...")
        ocr_data = extract_data_from_images(soup, formatted_date)
        if ocr_data:
            extracted_data.extend(ocr_data)

    unique_data = list(set(extracted_data))

    # 1件のみ取得（誤検出ノイズ）はスキップ
    if len(unique_data) == 1:
        print(
            f"  ⚠️ [ノイズ除去スキップ] 1件のみ抽出のため誤検出（パチンコ取材等）と判断し除外"
        )
        return []

    if unique_data:
        print(f"  └─ 有効データ {len(unique_data)} 件を抽出完了")

    return unique_data


def fetch_all_article_urls():
    print(f"🌐 記事一覧（ページネーション）を全件収集開始...")
    articles = []
    page = 1

    while True:
        if page == 1:
            page_url = BASE_POSTS_URL
        else:
            page_url = (
                f"https://777.slopachi-station.com/shopposts/page/{page}/?shop_id="
                + SHOP_ID
            )

        print(f"  ├─ 一覧ページ取得中: Page {page}")

        try:
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                break

            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)

            found_in_page = 0
            for a in links:
                href = a['href']
                if "slopachi-station.com" in href and re.search(
                    r'%e3%80%90|%E3%80%91|スロパチ', href
                ):
                    if href not in articles:
                        articles.append(href)
                        found_in_page += 1

            if found_in_page == 0:
                break

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ エラー発生: {e}")
            break

    print(f"✨ 全 {len(articles)} 件の記事URLを取得しました\n")
    return articles


def save_to_db(data_list):
    if not data_list:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    for dt, model, machine_num in data_list:
        cursor.execute(
            """
            INSERT OR IGNORE INTO ピーアーク相模大野_スロパチ (日付, 機種名, 台番号)
            VALUES (?, ?, ?)
        """,
            (dt, model, machine_num),
        )
        if cursor.rowcount > 0:
            saved_count += 1

    conn.commit()
    conn.close()
    return saved_count


def main():
    reset_and_init_db()
    urls_to_process = fetch_all_article_urls()

    total_saved = 0
    for idx, url in enumerate(urls_to_process, 1):
        print(f"[{idx}/{len(urls_to_process)}] 記事処理中: {url}")
        data = scrape_article_data(url)
        saved = save_to_db(data)
        total_saved += saved
        if saved > 0:
            print(f"  └─ 新規保存: {saved} 件\n")
        else:
            print("  └─ 保存データなし\n")
        time.sleep(0.5)

    print("==========================================")
    print("✨ 2026年1月1日以降のスロットデータ保存が完了しました")
    print(f"合計新規登録件数: {total_saved} 件")
    print("==========================================")


if __name__ == "__main__":
    main()