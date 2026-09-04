import streamlit as st

def apply_global_css():
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
