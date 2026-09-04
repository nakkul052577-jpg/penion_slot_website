import base64
import random
import time
import streamlit as st
import streamlit.components.v1 as components
from config import LOTTERY_RED_IMAGE, LOTTERY_GOLD_IMAGE, LOTTERY_RAINBOW_IMAGE

def show_lottery():
    st.subheader("抽選")
    st.caption("抽選人数を選択し、ランダムで1人を決定します。")

    # 抽選人数欄をゲーム選択欄と同じダーク系にする
    st.markdown(
        """
        <style>
        /* ==========================================
           抽選人数入力欄
           スマホでも「ゲームを選択」と同じ背景に統一
           Streamlit / BaseWeb のDOM差異にも対応
           ========================================== */
        div[data-testid="stNumberInput"] {
            width: 100% !important;
            background: transparent !important;
        }

        div[data-testid="stNumberInput"] > div,
        div[data-testid="stNumberInput"] [data-baseweb="base-input"],
        div[data-testid="stNumberInput"] [data-baseweb="input"],
        div[data-testid="stNumberInput"] [data-baseweb="input"] > div {
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

        /* 内側の不要な二重枠だけ消す */
        div[data-testid="stNumberInput"] [data-baseweb="input"] > div,
        div[data-testid="stNumberInput"] [data-baseweb="base-input"] > div {
            border-color: transparent !important;
            box-shadow: none !important;
        }

        /* iPhone / Androidを含め、実際のinputにも背景色を強制 */
        div[data-testid="stNumberInput"] input,
        div[data-testid="stNumberInput"] input[type="number"] {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            background: #171d2d !important;
            background-color: #171d2d !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            appearance: textfield !important;
            -webkit-appearance: none !important;
            opacity: 1 !important;
        }

        div[data-testid="stNumberInput"] input::-webkit-inner-spin-button,
        div[data-testid="stNumberInput"] input::-webkit-outer-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }

        /* ＋／－ボタンを完全非表示 */
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

        /* タップ時・フォーカス時も白くならないよう固定 */
        div[data-testid="stNumberInput"] [data-baseweb="base-input"]:hover,
        div[data-testid="stNumberInput"] [data-baseweb="base-input"]:focus-within,
        div[data-testid="stNumberInput"] [data-baseweb="input"]:hover,
        div[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
        div[data-testid="stNumberInput"] input:hover,
        div[data-testid="stNumberInput"] input:focus {
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
        "抽選する",
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

