import os
import time
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. ページ基本設定・認証設定
# ==========================================
st.set_page_config(
    page_title="パチスロ分析ダッシュボード",
    page_icon="🎰",
    layout="wide"
)

AUTH_PASSWORD = "pass"
DB_PATH = "p_ark_database.db"

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

    # 初期サンプルデータ（DBが完全空のときのみ生成）
    cursor.execute("SELECT COUNT(*) FROM ピーアーク相模大野_スロパチ")
    if cursor.fetchone()[0] == 0:
        sample_slopachi = [
            ("2026/08/18", "701", "L北斗の拳"),
            ("2026/08/18", "702", "L北斗の拳"),
            ("2026/08/18", "703", "パチスロ ヴァルヴレイヴ"),
            ("2026/08/17", "701", "L北斗の拳"),
            ("2026/08/17", "702", "L北斗の拳"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO ピーアーク相模大野_スロパチ (日付, 台番号, 機種名) VALUES (?, ?, ?)", sample_slopachi)

        sample_matomaru = [
            ("2026/08/18", "563人", "スロパチ取材", "さやかさん", "L北斗の拳", "701", 3200, 8500),
            ("2026/08/18", "563人", "スロパチ取材", "さやかさん", "L北斗の拳", "702", -1500, 6200),
            ("2026/08/18", "563人", "スロパチ取材", "さやかさん", "パチスロ ヴァルヴレイヴ", "703", 5400, 9100),
            ("2026/08/17", "176人", "天草覇道応援団", "クロムさん", "L北斗の拳", "701", 1800, 7800),
            ("2026/08/17", "176人", "天草覇道応援団", "クロムさん", "L北斗の拳", "702", 2100, 8100),
        ]
        cursor.executemany("INSERT OR IGNORE INTO ピーアーク相模大野_まとまる君 (日付, 並び人数, 取材, 来店, 機種名, 台番号, 差枚, 回転G数) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sample_matomaru)
        conn.commit()

    conn.close()

init_db()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df_sp = pd.read_sql_query("SELECT * FROM ピーアーク相模大野_スロパチ ORDER BY 日付 DESC", conn)
    df_mt = pd.read_sql_query("SELECT * FROM ピーアーク相模大野_まとまる君 ORDER BY 日付 DESC", conn)
    conn.close()
    return df_sp, df_mt

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None

# ==========================================
# 画面1: パスワード入力画面
# ==========================================
if not st.session_state["authenticated"]:
    st.title("🔒 パチスロ分析システム ログイン")
    pwd_input = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pwd_input == AUTH_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("パスワードが一致しません。")
    st.stop()

# ==========================================
# 画面2: 店舗選択画面
# ==========================================
if st.session_state["selected_store"] is None:
    st.title("🏪 店舗選択")
    store_name = st.selectbox("分析対象の店舗を選択してください", ["ピーアーク相模大野"])
    if st.button("表示"):
        st.session_state["selected_store"] = store_name
        st.rerun()
    st.stop()

# ==========================================
# ポップアップ(モーダル)によるデータ更新ダイアログ
# ==========================================
@st.dialog("🔄 データ再取得・DB更新中", width="medium")
def show_update_dialog():
    st.write("X (Twitter) から最新の投稿を取得し、AI解析してデータベースを更新します。")
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    time_text = st.empty()
    
    # APIキーの取得（環境変数または Streamlit secrets から）
    api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)

    if not api_key:
        st.error("⚠️ GEMINI_API_KEY が設定されていません。Macのターミナルで export GEMINI_API_KEY='キー' を実行してからお試しください。")
        if st.button("閉じる"):
            st.rerun()
        return

    try:
        from fetch_to_db import run_fetch_process

        def update_progress(step, total, msg, est_sec):
            pct = float(step) / float(total)
            progress_bar.progress(pct)
            status_text.markdown(f"**ステータス**: {msg}")
            if est_sec > 0:
                time_text.caption(f"⏳ 予想残り時間: 約 {est_sec} 秒")
            else:
                time_text.caption("🎉 処理完了！")

        records_count = run_fetch_process(progress_callback=update_progress, api_key=api_key)
        
        st.success(f"🎉 更新が完了しました！新規・更新レコード数: {records_count} 件")
        time.sleep(1.5)
        st.rerun()

    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
        st.info("※ Streamlit Cloud上の場合、Xのブラウザ自動操作が制限されている可能性があります。ローカル環境（Mac上）でお試しください。")
        if st.button("閉じる"):
            st.rerun()

# ==========================================
# 画面3〜5: 分析メイン画面（DB接続）
# ==========================================
store = st.session_state["selected_store"]

col_title, col_btn, col_reset = st.columns([6, 2, 1.5])
with col_title:
    st.title(f"📊 {store} 分析ダッシュボード")

with col_btn:
    st.write("")
    if st.button("🔄 最新データに更新", use_container_width=True):
        st.cache_data.clear() # キャッシュをクリア
        st.success("画面を最新データに更新しました！")
        st.rerun()

with col_reset:
    st.write("")
    if st.button("店舗選択へ戻る"):
        st.session_state["selected_store"] = None
        st.rerun()

st.markdown("---")

# DBから最新データを取得
df_slopachi, df_matomaru = load_data()

tab1, tab2 = st.tabs(["3. スロパチ分析 (位置関係・ランキング)", "4. 連続投入分析 (まとまる君)"])

# ------------------------------------------
# タブ1: スロパチ分析
# ------------------------------------------
with tab1:
    st.subheader("概要 & フィルター条件選択")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dates = sorted(df_slopachi["日付"].unique().tolist(), reverse=True)
        selected_dates = st.multiselect("日付を選択", dates, default=dates[:1] if dates else [])
    
    with col_f2:
        models = sorted(df_slopachi["機種名"].unique().tolist())
        selected_models = st.multiselect("機種名を選択", models, default=models)

    filtered_slopachi = df_slopachi[
        (df_slopachi["日付"].isin(selected_dates)) & 
        (df_slopachi["機種名"].isin(selected_models))
    ]

    st.markdown("---")
    
    col_rank, col_map = st.columns([1, 1])

    with col_rank:
        st.subheader("🏆 対象台ランキング")
        if not filtered_slopachi.empty:
            ranking_df = filtered_slopachi[["日付", "台番号", "機種名"]].reset_index(drop=True)
            ranking_df.index = ranking_df.index + 1
            st.dataframe(ranking_df, use_container_width=True)
        else:
            st.info("該当するデータがDB内にありません。")

    with col_map:
        st.subheader("🗺️ 店舗の台の位置関係")
        st.caption("※選択・ランクインしている台番号に色が付きます")

        active_machines = set(filtered_slopachi["台番号"].unique())
        all_machines = [str(num) for num in range(701, 713)]
        
        cols = st.columns(4)
        for idx, m_no in enumerate(all_machines):
            with cols[idx % 4]:
                if m_no in active_machines:
                    st.markdown(
                        f"""
                        <div style="background-color: #ff4b4b; color: white; padding: 15px; 
                                    text-align: center; border-radius: 8px; font-weight: bold; margin-bottom: 10px;">
                            台番: {m_no}<br>【対象】
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f2f6; color: #333; padding: 15px; 
                                    text-align: center; border-radius: 8px; margin-bottom: 10px;">
                            台番: {m_no}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

# ------------------------------------------
# タブ2: 4. 連続投入分析（まとまる君テーブル）
# ------------------------------------------
with tab2:
    st.subheader("📈 連続投入分析 (日付 × 台番号)")

    if not df_matomaru.empty:
        pivot_df = df_matomaru.pivot_table(
            index="台番号", 
            columns="日付", 
            values="差枚", 
            aggfunc="first"
        )

        def style_diff(val):
            if pd.isna(val):
                return ""
            elif val > 0:
                return "background-color: #ffcdd2; color: #b71c1c; font-weight: bold;"
            elif val < 0:
                return "background-color: #bbdefb; color: #0d47a1; font-weight: bold;"
            return ""

        styled_pivot = pivot_df.style.map(style_diff).format("{:+.0f}", na_rep="-")
        st.dataframe(styled_pivot, use_container_width=True)

        with st.expander("📝 まとまる君 DB全データ一覧"):
            st.dataframe(df_matomaru[["日付", "台番号", "機種名", "差枚", "回転G数", "並び人数", "取材", "来店"]], use_container_width=True)
    else:
        st.info("まとまる君テーブルにデータがありません。")