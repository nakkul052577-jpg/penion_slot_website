import pandas as pd
import streamlit as st
from datetime import date
from data.db import load_data
from components.calendar import japanese_calendar
from components.island_map import render_island_map
from stores.p_ark import P_ARK_ISLAND_POSITIONS
from stores.megaface_zama import MEGAFACE_ZAMA_ISLAND_POSITIONS

def get_store_positions(store):
    if store == "メガフェイス1180座間店":
        return MEGAFACE_ZAMA_ISLAND_POSITIONS
    return P_ARK_ISLAND_POSITIONS

def show_analysis(store):
    top_col1, top_col2 = st.columns([1, 5])
    with top_col1:
        if st.button("メニュー", key="back_to_main_menu_from_analysis"):
            st.session_state["app_page"] = "menu"
            st.session_state["selected_store"] = None
            st.rerun()

    st.markdown(
        """
        <div class="dashboard-header">
            <div class="dashboard-kicker">PENION ANALYTICS / DASHBOARD</div>
            <div class="dashboard-main-title">分析ダッシュボード</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")


    # ==========================================
    # DBから最新データ取得＆タブ描画
    # ==========================================

    try:
        df_slopachi, df_matomaru = load_data(store)
    except Exception as e:
        st.error("データベースの読み込みに失敗しました。")
        st.code(str(e))
        st.info(
            "相模大野の場合は、このPythonファイルと同じフォルダに "
            "p_ark_database.db があるか確認してください。"
        )
        st.stop()

    # タブの作成
    tab1, tab2 = st.tabs(
        [
            "1. スロパチ分析",
            "2. まとまる君",
        ]
    )

    # ------------------------------------------
    # タブ1：スロパチ分析
    # ------------------------------------------
    with tab1:

        st.subheader("スロパチ分析")

        df_filter = df_slopachi.copy()

        # ==========================================
        # 日付データをdate型に変換
        # ==========================================

        if not df_filter.empty:
            df_filter["_日付_dt"] = pd.to_datetime(
                df_filter["日付"],
                errors="coerce"
            ).dt.date

            valid_dates = df_filter["_日付_dt"].dropna()

        else:
            valid_dates = pd.Series(dtype="object")

        # ==========================================
        # 条件
        # ==========================================

        st.markdown(
            "<div style='font-size: 22px; font-weight: 800; "
            "color: #ffffff; margin-top: 10px; "
            "margin-bottom: 12px; letter-spacing: 1px;'>条件</div>",
            unsafe_allow_html=True,
        )

        # ==========================================
        # 1段目：開始日 ～ 終了日
        # ==========================================

        if len(valid_dates) > 0:
            default_start_date = min(valid_dates)
            default_end_date = max(valid_dates)
        else:
            default_start_date = date.today()
            default_end_date = date.today()

        # 店舗ごとに日付選択状態を分離する。
        # 以前に別の期間を選択した状態が残っていても、現在のDBに存在する
        # 最小日付〜最大日付の外側であれば自動的に補正する。
        # これにより「DBにはデータがあるのに、古い日付選択だけが残って0件」
        # になる問題を防ぐ。
        # これにより、メガフェイスで選択した日付が
        # ピーアーク相模大野にそのまま残る問題を防ぐ。
        # 店舗名をそのままstate keyに使うと、日本語名を記号に置換した際に
        # 別店舗同士で似たキーになる可能性があるため、UTF-8の16進数で完全分離する。
        store_state_key = str(store).encode("utf-8").hex()

        start_state_key = f"analysis_start_date_{store_state_key}"
        end_state_key = f"analysis_end_date_{store_state_key}"

        # 初回だけDBの最小日付・最大日付を設定する。
        # 以前の実装は毎回ここで年月日のselectbox stateまで上書きしていたため、
        # ユーザーが変更しても次の再実行時に初期日付へ戻っていました。
        def _initialize_date_state(state_key, initial_date):
            if state_key not in st.session_state:
                st.session_state[state_key] = initial_date
                st.session_state[f"{state_key}_year"] = initial_date.year
                st.session_state[f"{state_key}_month"] = initial_date.month
                st.session_state[f"{state_key}_day"] = initial_date.day

        _initialize_date_state(start_state_key, default_start_date)
        _initialize_date_state(end_state_key, default_end_date)

        # 以前のバージョンで保存された親stateがDB範囲外の場合だけ補正する。
        # ただしユーザーが操作中の年・月・日は絶対に毎回上書きしない。
        def _repair_out_of_range_date_once(state_key, fallback_date, lower_date, upper_date):
            value = st.session_state.get(state_key)
            try:
                if isinstance(value, pd.Timestamp):
                    value = value.date()
                elif isinstance(value, str):
                    parsed = pd.to_datetime(value, errors="coerce")
                    value = parsed.date() if not pd.isna(parsed) else None
            except Exception:
                value = None

            if not isinstance(value, date) or value < lower_date or value > upper_date:
                st.session_state[state_key] = fallback_date
                # 子stateがまだ存在しない場合だけ初期化する。
                if f"{state_key}_year" not in st.session_state:
                    st.session_state[f"{state_key}_year"] = fallback_date.year
                if f"{state_key}_month" not in st.session_state:
                    st.session_state[f"{state_key}_month"] = fallback_date.month
                if f"{state_key}_day" not in st.session_state:
                    st.session_state[f"{state_key}_day"] = fallback_date.day

        if len(valid_dates) > 0:
            _repair_out_of_range_date_once(
                start_state_key,
                default_start_date,
                default_start_date,
                default_end_date,
            )
            _repair_out_of_range_date_once(
                end_state_key,
                default_end_date,
                default_start_date,
                default_end_date,
            )

        start_date = japanese_calendar(
            "開始日",
            start_state_key,
            default_date=default_start_date,
        )

        end_date = japanese_calendar(
            "終了日",
            end_state_key,
            default_date=default_end_date,
        )

        # ==========================================
        # 2段目：機種選択
        # ==========================================

        if not df_filter.empty:

            models = (
                df_filter["機種名"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            models = models[models != ""]

            models = sorted(
                models.unique().tolist()
            )

        else:

            models = []

        model_options = ["全て"] + models

        # ==========================================
        # 機種選択を日付変更後も確実に保持する
        # ==========================================
        #
        # Streamlitではカレンダーのボタン操作によって画面全体が
        # 再実行されます。その際、selectbox自身の状態だけに依存すると、
        # 環境によって「全て」に戻った値を拾ってしまうことがあります。
        #
        # そこで、ユーザーが最後に明示的に選択した機種を
        # 「selected_machine_filter」に別保存します。
        # 日付変更によるrerunではこの値を変更しません。
        #
        # 店舗ごとに機種選択状態も分離する。
        machine_filter_key = f"selected_machine_filter_{store_state_key}"
        machine_widget_key = f"analysis_model_widget_{store_state_key}"

        if machine_filter_key not in st.session_state:
            st.session_state[machine_filter_key] = "全て"

        def _save_machine_filter():
            # ユーザーが機種selectboxを操作した時だけ、この値を更新する。
            st.session_state[machine_filter_key] = (
                st.session_state.get(machine_widget_key, "全て")
            )

        # 保存している機種が現在のDBの選択肢から消えている場合のみ
        # 「全て」に戻す。
        if st.session_state[machine_filter_key] not in model_options:
            st.session_state[machine_filter_key] = "全て"

        # selectbox自身のキーと、実際のフィルタ条件を分離する。
        widget_default = st.session_state[machine_filter_key]

        if machine_widget_key not in st.session_state:
            st.session_state[machine_widget_key] = widget_default

        # widget側が選択肢から外れている場合だけ同期する。
        if st.session_state[machine_widget_key] not in model_options:
            st.session_state[machine_widget_key] = widget_default

        st.markdown(
            "<div class='date-picker-label'>機種</div>",
            unsafe_allow_html=True,
        )

        st.selectbox(
            "機種",
            model_options,
            key=machine_widget_key,
            on_change=_save_machine_filter,
            label_visibility="collapsed",
        )

        # ランキング集計に使う機種は、selectboxの表示値ではなく
        # 「最後にユーザーが明示的に選択した値」を使用する。
        selected_model = st.session_state[machine_filter_key]

        # ==========================================
        # 日付チェック
        # ==========================================

        if start_date is None or end_date is None:

            st.info(
                "開始日と終了日を選択してください。"
            )

            st.stop()

        if start_date > end_date:

            st.warning(
                "開始日は終了日以前の日付を選択してください。"
            )

            st.stop()

        # ==========================================
        # 選択条件の表示
        # ==========================================

        # ==========================================
        # 日付範囲でフィルタリング
        # ==========================================

        if not df_filter.empty:

            filtered_slopachi = df_filter[
                (df_filter["_日付_dt"] >= start_date)
                &
                (df_filter["_日付_dt"] <= end_date)
            ].copy()

        else:

            filtered_slopachi = pd.DataFrame()

        # ==========================================
        # 機種でフィルタリング
        # ==========================================
        #
        # 重要：
        # 日付を変更した際も、現在選択されている機種を必ず
        # 「その日付範囲のデータ」に対して適用する。
        #
        # これにより、
        #   例）機種「炎炎2」を選択
        #       ↓
        #       日付を変更
        #       ↓
        #       変更後の日付範囲に存在する「炎炎2」だけで再集計
        #
        # となる。
        # ==========================================

        if selected_model != "全て":

            if not filtered_slopachi.empty:
                machine_mask = (
                    filtered_slopachi["機種名"]
                    .astype(str)
                    .str.strip()
                    .eq(str(selected_model).strip())
                )

                filtered_slopachi = filtered_slopachi.loc[
                    machine_mask
                ].copy()

            else:
                # 日付条件に該当するデータがない場合も、
                # 機種条件を維持した空のDataFrameにする。
                filtered_slopachi = filtered_slopachi.copy()

        # ==========================================
        # 台番号ランキング
        # ==========================================
        #
        # filtered_slopachi はここまでに
        #   1. 日付範囲
        #   2. 選択機種（「全て」以外の場合）
        # の両方を適用済み。
        #
        # したがって、ここから作成するランキング_dfと島図の色は
        # 必ず現在の日付＋機種条件に連動する。
        #
        #
        # ここが今回の重要部分です。
        #
        # 「機種名＋台番号」ではなく、
        # 「台番号」だけで回数を数えます。
        #
        # 例：
        #
        # 8/1   炎炎2       2001
        # 8/5   炎炎2       2001
        # 8/10  炎炎2       2001
        #
        # ↓
        #
        # 2001 / 炎炎2 / 3回
        #
        # ==========================================

        if not filtered_slopachi.empty:

            # --------------------------------------
            # 台番号・機種名を文字列として統一
            # --------------------------------------

            filtered_slopachi["台番号"] = (
                filtered_slopachi["台番号"]
                .astype(str)
                .str.strip()
            )

            filtered_slopachi["機種名"] = (
                filtered_slopachi["機種名"]
                .astype(str)
                .str.strip()
            )

            # 空の台番号は除外
            filtered_slopachi = filtered_slopachi[
                filtered_slopachi["台番号"] != ""
            ].copy()

            # --------------------------------------
            # 台番号ごとの出現回数
            # --------------------------------------

            count_df = (
                filtered_slopachi
                .groupby("台番号", as_index=False)
                .size()
                .rename(
                    columns={
                        "size": "回数"
                    }
                )
            )

            # --------------------------------------
            # 台番号ごとの最新機種名を取得
            #
            # 期間中に機種変更があった場合は、
            # 一番新しい日付の機種名を表示
            # --------------------------------------

            latest_machine_df = (
                filtered_slopachi
                .sort_values(
                    by=[
                        "台番号",
                        "_日付_dt"
                    ],
                    ascending=[
                        True,
                        False
                    ]
                )
                .drop_duplicates(
                    subset=["台番号"],
                    keep="first"
                )
                [
                    [
                        "台番号",
                        "機種名"
                    ]
                ]
            )

            # --------------------------------------
            # 回数＋機種名を結合
            # --------------------------------------

            ranking_df = count_df.merge(
                latest_machine_df,
                on="台番号",
                how="left"
            )

            # --------------------------------------
            # 台番号を数字順にするための列
            # --------------------------------------

            ranking_df["_台番号_num"] = pd.to_numeric(
                ranking_df["台番号"],
                errors="coerce"
            )

            # --------------------------------------
            # 回数の多い順
            # 同じ回数なら台番号順
            # --------------------------------------

            ranking_df = ranking_df.sort_values(
                by=[
                    "回数",
                    "_台番号_num",
                    "台番号"
                ],
                ascending=[
                    False,
                    True,
                    True
                ],
                na_position="last",
            ).reset_index(drop=True)

            # --------------------------------------
            # 同じ回数は同じ順位
            #
            # 例：
            #
            # 3回 → 1位
            # 3回 → 1位
            # 2回 → 2位
            # 2回 → 2位
            # 1回 → 3位
            #
            # --------------------------------------

            ranking_df["順位"] = (
                ranking_df["回数"]
                .rank(
                    method="dense",
                    ascending=False
                )
                .astype(int)
            )

            # --------------------------------------
            # 表示する列
            # --------------------------------------

            ranking_df = ranking_df[
                [
                    "順位",
                    "台番号",
                    "機種名",
                    "回数"
                ]
            ]

        else:

            ranking_df = pd.DataFrame(
                columns=[
                    "順位",
                    "台番号",
                    "機種名",
                    "回数"
                ]
            )

        # ==========================================
        # ランキング表示
        # ==========================================

        st.subheader("台番号ランキング")

        st.caption(
            "選択した日付範囲・機種に一致するDBデータを、"
            "台番号の登場回数が多い順にランキングしています。"
        )

        # ==========================================
        # データがある場合
        # ==========================================

        if not ranking_df.empty:

            display_ranking_df = ranking_df.copy()

            # 順位を「1位」の形式にする
            display_ranking_df["順位"] = (
                display_ranking_df["順位"]
                .astype(str)
                + "位"
            )

            # 列名をユーザー指定の表示にする
            display_ranking_df = display_ranking_df.rename(
                columns={
                    "順位": "順位",
                    "台番号": "台番号",
                    "機種名": "機種名",
                    "回数": "回数",
                }
            )

            # --------------------------------------
            # 表のスタイル
            # --------------------------------------

            def style_ranking_table(styler):

                styler.set_properties(
                    **{
                        "background-color": "#111522",
                        "color": "#f5f7ff",
                        "border-color": "rgba(255,255,255,.10)",
                        "font-size": "16px",
                    }
                )

                styler.set_table_styles(
                    [
                        {
                            "selector": "th",
                            "props": [
                                (
                                    "background-color",
                                    "#171d2d"
                                ),
                                (
                                    "color",
                                    "#aeb8cc"
                                ),
                                (
                                    "font-weight",
                                    "700"
                                ),
                                (
                                    "border-color",
                                    "rgba(255,255,255,.12)"
                                ),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [
                                (
                                    "border-color",
                                    "rgba(255,255,255,.08)"
                                ),
                            ],
                        },
                        {
                            "selector": "tbody tr:hover td",
                            "props": [
                                (
                                    "background-color",
                                    "#1a2133"
                                ),
                            ],
                        },
                    ]
                )

                return styler

            styled_ranking = style_ranking_table(
                display_ranking_df.style
            )

            st.dataframe(
                styled_ranking,
                use_container_width=True,
                hide_index=True,
            )

            # ==========================================
            # 島図：台番号ランキングと連動して着色
            # ==========================================

            st.subheader("島図")
            st.caption(
                "ランキング順位に応じて、島図上の該当台番号を自動で着色しています。"
            )

            render_island_map(ranking_df, store, get_store_positions(store))

        # ==========================================
        # データがない場合
        # ==========================================

        else:

            if len(valid_dates) > 0:
                st.info(
                    "選択した日付範囲・機種に該当するデータがDBにありません。\n\n"
                    f"DBで認識できている日付範囲："
                    f"{min(valid_dates).strftime('%Y/%m/%d')} 〜 "
                    f"{max(valid_dates).strftime('%Y/%m/%d')}"
                )
            else:
                st.info(
                    "DBは読み込めていますが、「日付」列を正しい日付として認識できません。"
                )

    # ==========================================
    # タブ2
    # ==========================================

    with tab2:
        if store == "メガフェイス1180座間店":
            st.info("メガフェイス1180座間店は現在スロパチ分析データのみ対応しています。")
        else:
            st.subheader("作成中のため、完成をお待ちください。")


    # ==========================================
    # ダッシュボード最下部：戻る
    # ==========================================

    st.markdown("---")

    back_col = st.columns([4, 1, 4])[1]
    with back_col:
        if st.button("戻る", use_container_width=True, key="back_to_store_button"):
            st.session_state["selected_store"] = None
            st.rerun()
