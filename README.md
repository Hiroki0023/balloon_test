# ダイエット応援アプリ

目標体重と達成期限から週ごとの目安を作成し、体重の記録と推移を確認できるStreamlitアプリです。

## ローカルでの起動

Python 3.11を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloudへのデプロイ

1. Streamlit Community CloudでGitHubアカウントを接続します。
2. `Hiroki0023/balloon_test` リポジトリと `main` ブランチを選択します。
3. Main file pathに `app.py` を指定します。
4. Advanced settingsでPython 3.11を選択し、Deployを実行します。

## データ保存について

入力データは実行環境の `database.csv` に保存されます。Streamlit Community Cloudのファイル保存は永続的ではなく、アプリの再起動・再デプロイなどでデータが消える可能性があります。また、複数ユーザー間で同じファイルを共有します。本番運用では外部データベースへの移行が必要です。
