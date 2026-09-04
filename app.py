import streamlit as st

from config import AUTH_PASSWORD
from styles.theme import apply_global_css
from pages.login import show_login
from pages.menu import show_top_menu, show_store_select
from pages.minigame import show_minigame
from pages.analysis import show_analysis

st.set_page_config(
    page_title="PENION ANALYTICS",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 共通セッション状態
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "app_page" not in st.session_state:
    st.session_state["app_page"] = "menu"
if "selected_store" not in st.session_state:
    st.session_state["selected_store"] = None

apply_global_css()

# 未認証ならログイン画面だけを表示
if not st.session_state["authenticated"]:
    show_login()
    st.stop()

# 認証後の画面ルーティング
page = st.session_state.get("app_page", "menu")

if page == "menu":
    show_top_menu()
    st.stop()

if page == "store_select":
    show_store_select()
    st.stop()

if page == "minigame":
    show_minigame()
    st.stop()

if page == "analysis":
    store = st.session_state.get("selected_store")
    if not store:
        st.session_state["app_page"] = "store_select"
        st.rerun()
    show_analysis(store)
    st.stop()

# 不明なページ状態になった場合
st.session_state["app_page"] = "menu"
st.rerun()
