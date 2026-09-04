import streamlit as st

def show_top_menu():
    st.markdown(
        """
        <div style="padding: 20px 0 8px; font-family: Orbitron, sans-serif;
                    color: #9fa8bf; font-size: 11px; letter-spacing: 2px;">
            PENION ANALYTICS / MENU
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title("PENION MENU")
    st.caption("利用するコンテンツを選択してください。")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("店舗分析")
            st.caption("店舗ごとのスロパチデータを分析します。")

            if st.button(
                "店舗分析を開く",
                use_container_width=True,
                key="open_store_analysis",
            ):
                st.session_state["app_page"] = "store_select"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("ミニゲーム")
            st.caption("ちょっと遊べるPENIONミニゲーム。")

            if st.button(
                "ミニゲームを開く",
                use_container_width=True,
                key="open_minigame",
            ):
                st.session_state["app_page"] = "minigame"
                st.rerun()


def show_store_select():
    st.markdown(
        """
        <div style="padding: 20px 0 8px; font-family: Orbitron, sans-serif;
                    color: #9fa8bf; font-size: 11px; letter-spacing: 2px;">
            PENION ANALYTICS / STORE SELECT
        </div>
        """,
        unsafe_allow_html=True,
    )

    back_col, _ = st.columns([1, 5])
    with back_col:
        if st.button("メニュー", key="back_to_menu_from_store"):
            st.session_state["app_page"] = "menu"
            st.session_state["selected_store"] = None
            st.rerun()

    st.title("店舗選択")
    st.caption("分析対象の店舗を選択してください。")

    store_options = [
        "店舗を選択して下さい",
        "ピーアーク相模大野",
        "メガフェイス1180座間店",
    ]

    current_store = st.session_state.get("selected_store")
    default_index = (
        store_options.index(current_store)
        if current_store in store_options
        else 0
    )

    store_name = st.selectbox(
        "店舗",
        store_options,
        index=default_index,
        label_visibility="collapsed",
        key="store_select_menu",
    )

    if st.button(
        "分析を開始",
        use_container_width=False,
        key="start_analysis_button",
    ):
        if store_name == "店舗を選択して下さい":
            st.warning("店舗を選択して下さい。")
        else:
            st.session_state["selected_store"] = store_name
            st.session_state["app_page"] = "analysis"
            st.rerun()
