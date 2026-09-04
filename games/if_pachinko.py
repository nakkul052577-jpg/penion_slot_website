import random
import streamlit as st

def show_if_pachinko():
    st.markdown(
        """
        <style>
        div[data-testid="stNumberInput"] label,
        div[data-testid="stNumberInput"] p {
            color: #d8dee9 !important;
            font-weight: 600 !important;
        }

        /* 数値入力欄：ゲーム選択と同じ暗い背景・グレー系の枠 */
        div[data-testid="stNumberInput"] {
            background: transparent !important;
        }

        div[data-testid="stNumberInput"] [data-baseweb="input"],
        div[data-testid="stNumberInput"] [data-baseweb="base-input"],
        div[data-testid="stNumberInput"] [data-baseweb="input"] > div {
            background-color: #1d2635 !important;
            border-color: #465267 !important;
            box-shadow: none !important;
        }

        div[data-testid="stNumberInput"] [data-baseweb="input"] {
            border: 1px solid #465267 !important;
            border-radius: 14px !important;
            overflow: hidden !important;
        }

        div[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within {
            background-color: #1d2635 !important;
            border-color: #64748b !important;
            box-shadow: none !important;
        }

        div[data-testid="stNumberInput"] input,
        div[data-testid="stNumberInput"] input[type="number"] {
            color: #e5e7eb !important;
            background-color: #1d2635 !important;
            -webkit-text-fill-color: #e5e7eb !important;
            border: none !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }

        div[data-testid="stNumberInput"] input::placeholder {
            color: #9ca3af !important;
            -webkit-text-fill-color: #9ca3af !important;
        }

        /* number_input標準の－／＋ボタンは非表示 */
        div[data-testid="stNumberInput"] button {
            display: none !important;
        }

        div[data-testid="stCaptionContainer"] {
            color: #aab4c5 !important;
        }

        /* IFのパチンコ内の条件入力枠 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #3f4a5c !important;
            background: #171d29 !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("IFのパチンコ")
    st.caption("入力した条件をもとに、通常時・初当たり・RUSHを完全確率でシミュレーションします。")

    # ==========================================
    # IFのパチンコ：振り分け行数の管理
    # ==========================================
    if "pachinko_distribution_count" not in st.session_state:
        st.session_state["pachinko_distribution_count"] = 2

    if "pachinko_result" not in st.session_state:
        st.session_state["pachinko_result"] = None

    def _pachinko_number(value, digits=0):
        """表示用の数値整形"""
        if digits == 0:
            return f"{int(round(value)):,}"
        return f"{value:,.{digits}f}"


    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(31,41,55,.98), rgba(17,24,39,.98));
            border: 1px solid #3f4a5c;
            border-radius: 14px;
            padding: 18px 20px 8px;
            margin-bottom: 12px;
            color: #e5e7eb;
        ">
            <div style="
                font-size: 24px;
                font-weight: 800;
                color: #f3f4f6;
                letter-spacing: .5px;
            ">条件</div>
            <div style="
                margin-top: 5px;
                color: #aab4c5;
                font-size: 13px;
            ">シミュレーションに使用する条件を入力してください</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        jackpot_probability = st.number_input(
            "1. 大当たり確率（1 / ○○○）",
            min_value=1.0,
            value=float(st.session_state.get("pachinko_jackpot_probability", 319.0)),
            step=1.0,
            key="pachinko_jackpot_probability",
        )

        rush_entry_rate = st.number_input(
            "2. ラッシュ突入確率（%）",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("pachinko_rush_entry_rate", 60.0)),
            step=1.0,
            key="pachinko_rush_entry_rate",
        )

        initial_payout = st.number_input(
            "3. 初当たり時の出球（玉）",
            min_value=0,
            value=int(st.session_state.get("pachinko_initial_payout", 1500)),
            step=100,
            key="pachinko_initial_payout",
        )

        rush_continue_rate = st.number_input(
            "4. ラッシュ継続率（%）",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("pachinko_rush_continue_rate", 81.0)),
            step=1.0,
            key="pachinko_rush_continue_rate",
        )

        st.markdown("**ラッシュの出玉振り分け**")
        st.caption("左に確率（%）、右に出球（玉）を入力してください。")

        distribution = []
        for i in range(st.session_state["pachinko_distribution_count"]):
            left, right = st.columns(2)

            default_rate = 50.0 if i < 2 else 0.0
            default_payout = 1500 if i == 0 else (3000 if i == 1 else 1500)

            with left:
                rate = st.number_input(
                    f"確率 {i + 1}（%）",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(st.session_state.get(f"pachinko_distribution_rate_{i}", default_rate)),
                    step=1.0,
                    key=f"pachinko_distribution_rate_{i}",
                )
            with right:
                payout = st.number_input(
                    f"出球 {i + 1}（玉）",
                    min_value=0,
                    value=int(st.session_state.get(f"pachinko_distribution_payout_{i}", default_payout)),
                    step=100,
                    key=f"pachinko_distribution_payout_{i}",
                )

            distribution.append({
                "rate": float(rate),
                "payout": int(payout),
            })

        # 振り分け入力欄の下に追加・削除ボタンを配置
        add_col, remove_col, _ = st.columns([1, 1, 4])

        with add_col:
            add_distribution_clicked = st.button(
                "追加",
                key="pachinko_add_distribution",
                use_container_width=True,
            )

        with remove_col:
            remove_distribution_clicked = (
                st.session_state["pachinko_distribution_count"] > 1
                and st.button(
                    "削除",
                    key="pachinko_remove_distribution",
                    use_container_width=True,
                )
            )

        if add_distribution_clicked:
            st.session_state["pachinko_distribution_count"] += 1
            st.rerun()

        if remove_distribution_clicked:
            last_index = st.session_state["pachinko_distribution_count"] - 1
            st.session_state["pachinko_distribution_count"] -= 1
            st.session_state.pop(f"pachinko_distribution_rate_{last_index}", None)
            st.session_state.pop(f"pachinko_distribution_payout_{last_index}", None)
            st.rerun()

        rotation_rate = st.number_input(
            "6. 回転率（250玉あたりの回転数）",
            min_value=0.1,
            value=float(st.session_state.get("pachinko_rotation_rate", 18.0)),
            step=0.1,
            key="pachinko_rotation_rate",
        )

        spins_per_hour = st.number_input(
            "7. 1時間あたりの回転数（エヴァ15の場合200回転）",
            min_value=0.1,
            value=float(st.session_state.get("pachinko_spins_per_hour", 200.0)),
            step=1.0,
            key="pachinko_spins_per_hour",
        )
        st.caption(
            f"1回転あたり：約 {3600 / float(spins_per_hour):.2f} 秒"
        )

        operation_hours = st.number_input(
            "8. 稼働時間（時間）",
            min_value=0.01,
            value=float(st.session_state.get("pachinko_operation_hours", 8.0)),
            step=0.5,
            key="pachinko_operation_hours",
        )

    distribution_total = sum(item["rate"] for item in distribution)

    if abs(distribution_total - 100.0) > 0.000001:
        st.warning(
            f"ラッシュ出玉振り分けの合計は現在 {_pachinko_number(distribution_total, 1)}% です。"
            "結果を実行するには100%にしてください。"
        )

    if st.button(
        "結果を見る 🎰",
        use_container_width=True,
        key="run_if_pachinko",
    ):
        if abs(distribution_total - 100.0) > 0.000001:
            st.error("ラッシュの出玉振り分けの確率合計を100%にしてください。")
        elif (
            jackpot_probability <= 0
            or rotation_rate <= 0
            or spins_per_hour <= 0
            or operation_hours <= 0
        ):
            st.error(
                "大当たり確率・回転率・1時間あたりの回転数・稼働時間は0より大きい値を入力してください。"
            )
        else:
            # ------------------------------------------
            # シミュレーション開始
            # ------------------------------------------
            remaining_time = float(operation_hours) * 3600.0
            balance = 0.0
            total_spins = 0
            history = []

            # 1時間あたりの回転数から、1回転あたりの時間を計算
            seconds_per_spin = 3600.0 / float(spins_per_hour)

            # 250玉あたりの回転率から、1回転あたりの消費玉数を計算
            balls_per_spin = 250.0 / float(rotation_rate)


            while remaining_time >= seconds_per_spin:
                spins_since_last_hit = 0
                hit = False

                # ===== 通常時：時間が足りる間だけ回転 =====
                while remaining_time >= seconds_per_spin:
                    remaining_time -= seconds_per_spin
                    balance -= balls_per_spin
                    total_spins += 1
                    spins_since_last_hit += 1

                    # 大当たり抽選
                    if random.random() < (1.0 / float(jackpot_probability)):
                        hit = True
                        break

                # 当たらず時間切れ
                if not hit:
                    # 最後に当たらず終了した回転数も履歴に残す
                    if spins_since_last_hit > 0:
                        history.append({
                            "回転数": spins_since_last_hit,
                            "出玉": 0,
                            "振り分け履歴": "時間切れ",
                            "RUSH突入": "－",
                            "収支": balance,
                        })
                    break

                # ここから大当たり後の処理
                hit_payout = 0
                distribution_counts = {}
                entered_rush = random.random() < (float(rush_entry_rate) / 100.0)

                if entered_rush:
                    # 初当たり時の出球
                    hit_payout += int(initial_payout)
                    balance += int(initial_payout)

                    # RUSH中は、時間が0以下になってもRUSH終了まで継続
                    while random.random() < (float(rush_continue_rate) / 100.0):
                        # 振り分け抽選
                        roll = random.random() * 100.0
                        cumulative = 0.0
                        selected = distribution[-1]

                        for item in distribution:
                            cumulative += item["rate"]
                            if roll < cumulative:
                                selected = item
                                break

                        selected_payout = int(selected["payout"])
                        hit_payout += selected_payout
                        balance += selected_payout
                        distribution_counts[selected_payout] = (
                            distribution_counts.get(selected_payout, 0) + 1
                        )

                        # RUSH1回継続ごとに500秒消費
                        remaining_time -= 500.0

                    if distribution_counts:
                        rush_distribution_text = "、".join(
                            f"RUSH {_pachinko_number(payout)}玉 × {count}回"
                            for payout, count in sorted(distribution_counts.items())
                        )
                        distribution_text = (
                            f"初当たり {_pachinko_number(initial_payout)}玉、"
                            f"{rush_distribution_text}"
                        )
                    else:
                        distribution_text = (
                            f"初当たり {_pachinko_number(initial_payout)}玉、"
                            "RUSH継続なし"
                        )
                else:
                    distribution_text = "RUSHなし"

                # 当たり終了時点、またはRUSH終了時点の累計収支を保存
                history.append({
                    "回転数": spins_since_last_hit,
                    "出玉": hit_payout,
                    "振り分け履歴": distribution_text,
                    "RUSH突入": "突入" if entered_rush else "非突入",
                    "収支": balance,
                })

                # RUSH終了時点で時間が0以下なら即終了
                if remaining_time <= 0:
                    break

                # 通常時へ戻る
                continue

            # 結果をsession_stateに保存
            st.session_state["pachinko_result"] = {
                "balance": balance,
                "total_spins": total_spins,
                "remaining_time": remaining_time,
                "history": history,
                "balls_per_spin": balls_per_spin,
                "operation_seconds": float(operation_hours) * 3600.0,
                "seconds_per_spin": seconds_per_spin,
                "spins_per_hour": float(spins_per_hour),
            }
            st.rerun()

    # ==========================================
    # 結果表示
    # ==========================================
    pachinko_result = st.session_state.get("pachinko_result")

    if pachinko_result is not None:
        balance = pachinko_result["balance"]
        history = pachinko_result["history"]
        sign = "+" if balance >= 0 else "－"

        st.markdown("---")
        st.markdown("### シミュレーション結果")

        st.html(
            f"""
            <div style="
                margin:12px 0 18px;
                padding:26px 18px;
                border-radius:16px;
                border:1px solid rgba(255,255,255,.18);
                background:rgba(255,255,255,.04);
                text-align:center;
            ">
                <div style="
                    color:#9fa8bf;
                    font-size:14px;
                    letter-spacing:1px;
                    margin-bottom:8px;
                ">最終収支</div>
                <div style="
                    color:#ffffff;
                    font-size:48px;
                    font-weight:900;
                    line-height:1.1;
                ">{sign}{_pachinko_number(abs(balance))} 玉</div>
                <div style="
                    color:#9fa8bf;
                    font-size:13px;
                    margin-top:12px;
                ">総回転数：{_pachinko_number(pachinko_result["total_spins"])} 回転</div>
            </div>
            """
        )

        st.subheader("履歴")

        if history:
            history_df = pd.DataFrame(history)

            # 履歴の収支を「＋ / － ○○玉」で表示
            def _format_history_balance(value):
                value = float(value)
                sign = "+" if value >= 0 else "－"
                return f"{sign}{_pachinko_number(abs(value))}玉"

            history_df["収支"] = history_df["収支"].apply(
                _format_history_balance
            )

            history_df.index = range(1, len(history_df) + 1)
            history_df.index.name = "No."
            st.dataframe(
                history_df,
                use_container_width=True,
            )
        else:
            st.info("大当たり履歴はありません。")

        if st.button(
            "結果をリセット",
            use_container_width=True,
            key="reset_if_pachinko_result",
        ):
            st.session_state["pachinko_result"] = None
            st.rerun()
