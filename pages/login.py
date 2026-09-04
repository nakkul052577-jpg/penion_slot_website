import os
import base64
import streamlit as st
from config import AUTH_PASSWORD, BASE_DIR

def show_login():
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

        character_path = os.path.join(BASE_DIR, "assets", "penion_character_hd.png")
        if not os.path.exists(character_path):
            character_path = os.path.join(BASE_DIR, "assets", "penion_character.png")

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
