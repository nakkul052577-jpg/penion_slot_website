import os
import json
import re
import sqlite3
import urllib.request
import urllib.parse
import time

from PIL import Image
from playwright.sync_api import sync_playwright

from google import genai
from google.genai import types


# ==========================================
# 設定
# ==========================================

# 2026年2月1日以降の投稿に限定するクエリ
SEARCH_QUERY = "from:kanagawamatome ピーアーク相模大野 since:2026-02-01"

DB_PATH = "p_ark_database.db"
MODEL_NAME = "gemini-3.6-flash"

# スクロール試行の最大回数
MAX_SCROLL_ATTEMPTS = 50

# APIエラー時の待機時間
RETRY_WAIT = 20


# ==========================================
# DB初期化
# ==========================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
    conn.close()
    print("📁 データベースの準備完了。")


# ==========================================
# Gemini API
# ==========================================

def call_gemini(client, img_obj, prompt):
    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                img_obj,
                prompt
            ],
            config=config
        )

        return res.text

    except Exception as e:
        error_text = str(e)

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            print("\n==========================================")
            print("🚨 Gemini APIのクォータ上限に達しました")
            print("==========================================")
            return None

        raise


# ==========================================
# X検索 & 無限スクロール処理
# ==========================================

def process_x_search(page, client):
    print("🔍 Xの検索を実行中...")

    search_url = (
        "https://x.com/search?q="
        + urllib.parse.quote(SEARCH_QUERY)
        + "&f=live"
    )

    page.goto(search_url)
    print("⏳ 検索結果の読み込みを待っています...")

    try:
        page.wait_for_selector("article", timeout=15000)
    except Exception:
        print("⚠️ 記事の読み込みタイムアウト。")
        return

    processed_urls = set()
    scroll_attempts = 0
    total_processed = 0

    while scroll_attempts < MAX_SCROLL_ATTEMPTS:
        articles = page.query_selector_all("article")
        new_articles_found = False

        for article in articles:
            # 既に処理済みのポスト（URLやID）は重複して処理しない
            time_el = article.query_selector("time")
            if not time_el:
                continue

            link_el = time_el.query_selector("xpath=..")
            post_url = link_el.get_attribute("href") if link_el else None

            if post_url in processed_urls:
                continue

            if post_url:
                processed_urls.add(post_url)

            new_articles_found = True
            total_processed += 1
            temp_path = f"temp_{total_processed}.jpg"

            print("\n------------------------------------------")
            print(f"📌 {total_processed}件目の投稿を処理中")
            print("------------------------------------------")

            try:
                # テキスト取得
                text = article.inner_text()

                # 画像取得
                img_el = article.query_selector("img[src*='media']")
                if not img_el:
                    print("⚠️ 画像が見つからないためスキップします。")
                    continue

                src = img_el.get_attribute("src")
                if not src:
                    print("⚠️ 画像URLが取得できません。")
                    continue

                src = re.sub(r"name=\w+", "name=large", src)
                urllib.request.urlretrieve(src, temp_path)

                img_obj = Image.open(temp_path)
                print("🤖 Geminiで解析中...")

                prompt = f"""
以下のXの投稿テキストと添付画像を読み取り、
情報をJSON形式で抽出してください。

【投稿テキスト】
{text}

【出力要件】
以下のJSONフォーマットのみを正確に出力してください。
余計な文字列は含めないでください。

{{
    "date": "YYYY/MM/DD",
    "lottery_count": "並び人数または人数",
    "coverage": "取材名",
    "visit": "来店演者名",
    "details": [
        {{
            "model_name": "機種名",
            "machine_number": "台番号",
            "diff_medals": 0,
            "game_count": 0
        }}
    ]
}}

数値が画像から読み取れない場合は null にしてください。
"""

                result_text = call_gemini(client, img_obj, prompt)

                if result_text is None:
                    print("🛑 Gemini API上限に達したため処理を一時終了します。")
                    return

                result_text = re.sub(r"```json\s*|\s*```", "", result_text).strip()
                result_json = json.loads(result_text)

                meta_date = result_json.get("date")
                lottery = result_json.get("lottery_count")
                coverage = result_json.get("coverage")
                visit = result_json.get("visit")
                details = result_json.get("details", [])

                if not meta_date:
                    print("❌ 日付が取得できなかったためスキップします。")
                    continue

                # DB保存
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                saved_count = 0

                for d in details:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO ピーアーク相模大野_まとまる君
                        (日付, 並び人数, 取材, 来店, 機種名, 台番号, 差枚, 回転G数)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            meta_date,
                            lottery,
                            coverage,
                            visit,
                            d.get("model_name"),
                            d.get("machine_number"),
                            d.get("diff_medals"),
                            d.get("game_count")
                        )
                    )
                    if cursor.rowcount > 0:
                        saved_count += 1

                conn.commit()
                conn.close()

                print(f"✅ {meta_date} のデータ {saved_count}件を保存しました。")
                time.sleep(3)

            except json.JSONDecodeError as e:
                print(f"❌ GeminiのJSON解析エラー: {e}")
            except Exception as e:
                print(f"❌ エラー発生: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # スクロールして次の件数を読み込む
        print("📜 ページをスクロール中...")
        page.evaluate("window.scrollBy(0, 1000)")
        time.sleep(3)

        if not new_articles_found:
            scroll_attempts += 1
        else:
            scroll_attempts = 0


# ==========================================
# メイン
# ==========================================

def main():
    init_db()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ エラー: GEMINI_API_KEYが設定されていません。")
        return

    client = genai.Client(api_key=api_key)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            storage_state="state.json" if os.path.exists("state.json") else None
        )

        page = context.new_page()
        page.goto("https://x.com/home")

        input("🛑 ブラウザでXにログインしていることを確認し、Enterキーを押してください...")

        context.storage_state(path="state.json")
        process_x_search(page, client)

        browser.close()

    print("\n✨ すべての処理が完了しました。")


if __name__ == "__main__":
    main()