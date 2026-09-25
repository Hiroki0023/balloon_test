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

設定と日々の体重は Supabase（Postgres）の `diet_data` テーブルに保存します。アプリを再起動・再デプロイしても消えません。画面全体は単一のパスワードで保護されます（自分ひとりで使う前提です）。

### 初回セットアップ（本人が行う）

0. `streamlit run` に使う Python に依存パッケージを入れます（`pip install -r requirements.txt`）。入っているかは `python -c "from supabase import create_client; print('ok')"` で確かめられます。
1. Supabase の SQL Editor で `migrations/0001_create_diet_data.sql` を実行します。
2. `.streamlit/secrets.toml.example` をコピーして `.streamlit/secrets.toml` を作り、3 つの値を入れます。
   - `SUPABASE_URL`: Supabase の Project Settings → API にある Project URL
   - `SUPABASE_SERVICE_KEY`: 同じ画面の、サーバ専用の秘密鍵（service_role 相当）
   - `APP_PASSWORD`: 自分で決めたパスワード（16 文字以上のランダムな文字列を推奨）
3. Community Cloud では、アプリの Settings → Secrets に同じ 3 行を貼ります。

秘密鍵とパスワードは `.streamlit/secrets.toml` と Community Cloud の Secrets だけに置き、リポジトリやチャットには載せません。詳しい手順は `02_プロジェクト/ballon/実行手順書.md` を参照してください。

日付は日本時間（JST）で扱います。

## テスト

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

テストは偽のデータベースを使うため、Supabase の鍵は不要です。
