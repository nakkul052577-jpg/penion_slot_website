import streamlit as st
from games.lottery import show_lottery
from games.if_pachinko import show_if_pachinko

def show_minigame():
    st.markdown(
        """
        <div style="padding:20px 0 8px;font-family:Orbitron,sans-serif;color:#9fa8bf;font-size:11px;letter-spacing:2px;">
            PENION ANALYTICS / MINI GAME
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("メニューに戻る", key="back_to_menu_from_minigame"):
        st.session_state["app_page"] = "menu"
        st.rerun()

    st.title("ゲーム選択")
    st.caption("プレイするゲームを選択してください。")

    game_name = st.selectbox(
        "ゲームを選択",
        ["抽選", "IFのパチンコ"],
        key="selected_minigame",
    )

    st.markdown("---")

    if game_name == "抽選":
        show_lottery()
    elif game_name == "IFのパチンコ":
        show_if_pachinko()
