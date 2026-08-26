#!/bin/bash

# ==========================================
# スロパチデータ取得 → GitHub自動push
# ==========================================

cd /Users/karishukunaoki/available2025.08/desk_manager/penion-game/slot_bunseki || exit 1

echo "=========================================="
echo "🚀 自動データ更新を開始"
echo "=========================================="


# ------------------------------------------
# 1. GitHubの最新状態を先に取得
# ------------------------------------------

echo ""
echo "🌐 GitHubの最新状態を確認中..."

git pull --rebase origin main

if [ $? -ne 0 ]; then
    echo "=========================================="
    echo "❌ git pullに失敗しました"
    echo "データ取得を中止します"
    echo "=========================================="
    exit 1
fi


# ------------------------------------------
# 2. データ取得
# ------------------------------------------

echo ""
echo "📥 スロパチデータを取得中..."

/Users/karishukunaoki/available2025.08/desk_manager/penion-game/slot_bunseki/.venv/bin/python3 \
/Users/karishukunaoki/available2025.08/desk_manager/penion-game/slot_bunseki/fetch_suropachi_monthly.py

PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    echo "=========================================="
    echo "❌ Python処理でエラーが発生しました"
    echo "GitHubへのpushは実行しません"
    echo "=========================================="
    exit 1
fi


# ------------------------------------------
# 3. DBをGitに追加
# ------------------------------------------

echo ""
echo "📦 DBの変更を確認中..."

git add p_ark_database.db


# ------------------------------------------
# 4. DBに変更がある場合だけcommit
# ------------------------------------------

if git diff --cached --quiet; then

    echo "📭 DBに変更がないためcommit/pushをスキップします"

else

    echo "💾 Git commitを実行します"

    git commit -m "自動更新: $(date '+%Y-%m-%d %H:%M:%S')"

    if [ $? -ne 0 ]; then
        echo "❌ git commitに失敗しました"
        exit 1
    fi


    # ------------------------------------------
    # 5. GitHubへpush
    # ------------------------------------------

    echo ""
    echo "🚀 GitHubへpush中..."

    git push origin main

    if [ $? -ne 0 ]; then
        echo "=========================================="
        echo "❌ git pushに失敗しました"
        echo "=========================================="
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "🎉 GitHubへの自動更新が完了しました"
    echo "=========================================="

fi

exit 0
