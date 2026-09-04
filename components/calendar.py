import calendar
from datetime import date
import pandas as pd
import streamlit as st

JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

def japanese_calendar(label, state_key, default_date=None):
    """スマホ対応の日付選択。年月日を個別のプルダウンで選択する。"""
    if default_date is None:
        default_date = date.today()

    # 保存値を date 型へ統一
    selected_date = st.session_state.get(state_key, default_date)
    if isinstance(selected_date, pd.Timestamp):
        selected_date = selected_date.date()
    elif isinstance(selected_date, str):
        selected_date = pd.to_datetime(selected_date).date()
    if not isinstance(selected_date, date):
        selected_date = default_date

    # 年の選択範囲。データの年に依存せず、スマホでも十分選べる範囲にする。
    current_year = date.today().year
    min_year = min(2020, selected_date.year - 5)
    max_year = max(2035, selected_date.year + 5)
    years = list(range(min_year, max_year + 1))
    months = list(range(1, 13))

    st.markdown(
        f"<div class='date-picker-label'>{label}</div>",
        unsafe_allow_html=True,
    )

    # 年・月・日を独立したプルダウンにする。
    # st.popover / st.columns(7) を使わないため、スマホで横幅が膨らまない。
    year_key = f"{state_key}_year"
    month_key = f"{state_key}_month"
    day_key = f"{state_key}_day"

    if year_key not in st.session_state:
        st.session_state[year_key] = selected_date.year
    if month_key not in st.session_state:
        st.session_state[month_key] = selected_date.month
    if day_key not in st.session_state:
        st.session_state[day_key] = selected_date.day

    # 既存の値が範囲外になっている場合に補正
    if st.session_state[year_key] not in years:
        st.session_state[year_key] = selected_date.year
    if st.session_state[month_key] not in months:
        st.session_state[month_key] = selected_date.month

    selected_year = st.selectbox(
        "年",
        years,
        format_func=lambda y: f"{y}年",
        key=year_key,
        label_visibility="collapsed",
    )

    selected_month = st.selectbox(
        "月",
        months,
        format_func=lambda m: f"{m}月",
        key=month_key,
        label_visibility="collapsed",
    )

    # 月・年に応じて日数を決定（うるう年にも対応）
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    days = list(range(1, days_in_month + 1))

    # 31日→30日など月を変更した際に存在しない日にならないよう補正
    if st.session_state[day_key] not in days:
        st.session_state[day_key] = days[-1]

    selected_day = st.selectbox(
        "日",
        days,
        format_func=lambda d: f"{d}日",
        key=day_key,
        label_visibility="collapsed",
    )

    selected_date = date(selected_year, selected_month, selected_day)
    st.session_state[state_key] = selected_date

    return selected_date
