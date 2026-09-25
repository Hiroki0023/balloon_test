# =============================================================
#  ダイエット応援アプリ v3【学習者用・骨組み】
# -------------------------------------------------------------
#  目標体重と達成期限から「週ごとの体重目標」を作り、その週の目安を
#  達成できたら風船を飛ばすアプリを、みんなで分担して完成させます。
#
#  ▼ 進め方
#     各章の「担当」「やること」「ヒント」を読み、"↓↓↓ ここに書く ↓↓↓" を埋めます。
#     ・「ヒント」はあくまで一例。やることさえ実現できれば書き方は自由です。
#     ・難しい「章2（データベース）」と「風船を出す関数」は最初から完成しています。
#     ・詰まったら：ネット検索 → 生成AIに質問 → app_answer.py（答え）を見る
#
#  ▼ 動かし方（書きかけでも動かして確認できます）
#     cd （このファイルが置いてある場所）
#     streamlit run app.py
#  ▼ ファイル構成： app.py（このファイル）＋ style.css＋ database.csv
# =============================================================

import os
import datetime
import math


# ===== 章1：準備（おまじない）担当：@Hasegawa Y-13/ゆきち/長谷川ゆ =====
# やること：画面を作る道具を読み込み、タイトルを出す。保存ファイル名も決める。
# ヒント：
#   - import streamlit as st / import pandas as pd
#   - st.set_page_config(page_title="ダイエット応援アプリ v3", page_icon="🎈")
#   - st.title("🎈 ダイエット応援アプリ v3") / st.write("...説明...")
#   - 保存ファイル名： DB_FILE = "database.csv"
# ↓↓↓ ここに書く ↓↓↓

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="ダイエット応援アプリ v3",       # ブラウザのタブに表示されるタイトル
    page_icon="🎈",                # タブのファビコン（絵文字やパスを指定可能）
    layout="wide",                 # "centered"（デフォルト）か "wide"（横幅いっぱい）
    initial_sidebar_state="expanded"  # サイドバーの初期状態："auto", "expanded", "collapsed"
)

st.title(
    "🎈 ダイエット応援アプリ v3"
) 

st.write(
    "ダイエット応援アプリへようこそ！"
    "あなたがダイエットに成功するまで伴走します。"
    "今日も楽しんで、ダイエットしましょう！"
)

DB_FILE = "database.csv"


# ↑↑↑ ここまで章1 ↑↑↑

# ===== 章2：データベースの読み書き 担当：@Asada Hiroki-13/だーあさ/朝田 浩暉 =====
# やること：設定（目標・期限など）と日々の記録を、1つの database.csv に読み書きする
#           「みんなが使う道具（関数）」を5つ完成させる。
#  database.csv は次の形（行に種別 type を付けて、設定と記録を1ファイルに同居させる）：
#     type,key,value
#     setting,goal,60.0           ← 設定（key=項目名, value=値）
#     log,2026-06-30,66.0         ← 記録（key=日付, value=体重）
#
#  ★この5つができると、章4〜章8のみんなが load_settings() などを「呼ぶだけ」で使えます。
#  ★pandas（pd）は CSV を「表」として扱う道具。dtype=str は「全部、文字として読む」指定
#    （60.0 が 60 に化けないようにそろえる）。

# 【_load_db】database.csv を丸ごと表として読み込む。無ければ空の表（列だけ）を返す。
# ヒント：
#   - if os.path.exists(DB_FILE):                      # ファイルがあるか確認
#         df = pd.read_csv(DB_FILE, dtype=str)         # 表として読み込む（全部 文字で）
#         for c in ["type", "key", "value"]:           # 万一 列が欠けても落ちない保険
#             if c not in df.columns: df[c] = None
#         return df[["type", "key", "value"]]
#   - 無いときは return pd.DataFrame(columns=["type", "key", "value"])
def _load_db():
    # ↓↓↓ ここに書く（return まで）↓↓↓
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)

        for c in ["type", "key", "value"]:
            if c not in df.columns:
                df[c] = None

        return df[["type", "key", "value"]]
    return pd.DataFrame(columns=["type", "key", "value"])
    # ↑↑↑ ここまで ↑↑↑

# 【load_settings】設定だけを取り出して辞書で返す（例 {"goal":"60.0", "deadline":"2026-08-25", ...}）。
# ヒント：
#   - df = _load_db()
#   - rows = df[df["type"] == "setting"]               # type が setting の行だけ
#   - return {row["key"]: row["value"] for _, row in rows.iterrows()}   # key:value の辞書に
def load_settings():
    # ↓↓↓ ここに書く（return まで）↓↓↓
    df = _load_db()
    rows = df[df["type"] == "setting"]
    return {row["key"]: row["value"] for _, row in rows.iterrows()}
    # ↑↑↑ ここまで ↑↑↑

# 【save_setting】設定を1つ保存する（同じ key があれば上書き）。
# ヒント：
#   - df = _load_db()
#   - keep = ~((df["type"] == "setting") & (df["key"] == str(key)))   # 同じ設定の古い行を外す
#   - df = df[keep]
#   - new_row = pd.DataFrame({"type": ["setting"], "key": [str(key)], "value": [str(value)]})
#   - df = pd.concat([df, new_row], ignore_index=True)                 # 新しい行を足す
#   - df.to_csv(DB_FILE, index=False)                                  # CSVに書き出す
def save_setting(key, value):
    # ↓↓↓ ここに書く ↓↓↓
    df = _load_db()

    keep = ~((df["type"] == "setting") & (df["key"] == str(key)))
    df = df[keep]

    new_row = pd.DataFrame({
        "type": ["setting"],
        "key": [str(key)],
        "value": [str(value)]
    })

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    # ↑↑↑ ここまで ↑↑↑

# 【load_log】日々の記録を date / weight の表で取り出す。無ければ空の表。
# ヒント：
#   - df = _load_db(); rows = df[df["type"] == "log"].copy()           # type が log の行だけ
#   - if rows.empty: return pd.DataFrame(columns=["date", "weight"])
#   - out = pd.DataFrame({"date": rows["key"].astype(str),
#                         "weight": rows["value"].astype(float)})       # 体重は数値に直す
#   - return out.sort_values("date").reset_index(drop=True)            # 日付順に並べる
def load_log():
    # ↓↓↓ ここに書く（return まで）↓↓↓
    df = _load_db()
    rows = df[df["type"] == "log"].copy()

    if rows.empty:
        return pd.DataFrame(columns=["date", "weight"])

    out = pd.DataFrame({
        "date": rows["key"].astype(str),
        "weight": rows["value"].astype(float)
    })

    return out.sort_values("date").reset_index(drop=True)
    # ↑↑↑ ここまで ↑↑↑

# 【save_record】1日分の記録を保存（同じ日付は上書きして1日1行に保つ）。
# ヒント：save_setting とほぼ同じ。違いは type が "log"、key が日付、value が体重。
#   - df = _load_db()
#   - keep = ~((df["type"] == "log") & (df["key"] == str(date_str)))   # 同じ日付の古い行を外す
#   - df = df[keep]
#   - new_row = pd.DataFrame({"type": ["log"], "key": [str(date_str)], "value": [str(weight)]})
#   - df = pd.concat([df, new_row], ignore_index=True); df.to_csv(DB_FILE, index=False)
def save_record(date_str, weight):
    # ↓↓↓ ここに書く ↓↓↓
    df = _load_db()

    keep = ~((df["type"] == "log") & (df["key"] == str(date_str)))
    df = df[keep]

    new_row = pd.DataFrame({
        "type": ["log"],
        "key": [str(date_str)],
        "value": [str(weight)]
    })

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    # ↑↑↑ ここまで ↑↑↑


# ===== 章2のおまけ：結果を前面に出す関数（文字＋風船）担当：@AsanoMiyo-13/まよりん/浅野深世 =====
# ★風船の演出は v2（app_answer2.py）から流用済みです。中身はさわらなくてOK。
#   浅野さんの本番は「章8で、目安を達成したときに with_balloons=True で呼ぶ」こと（＝飛ばす条件づくり）。
#   message=前面の文字 / with_balloons=Trueなら風船も飛ばす / color=文字の色
def show_result(message, with_balloons=False, color="#d6336c"):
    balloons = ""
    if with_balloons:
        st.balloons()  # 組み込みの風船をひと吹き
        colors = ["#ff5a5f", "#ffb400", "#4ecdc4", "#5a9bff", "#b06bff", "#ff7ac1"]
        for i in range(18):                       # ★風船の数（増やすと派手）
            c = colors[i % len(colors)]
            left = (i * 5 + 3) % 100
            delay = (i % 6) * 0.25
            duration = 4 + (i % 4)
            balloons += (
                f'<div class="balloon" style="left:{left}%;background:{c};'
                f'animation-delay:{delay}s;animation-duration:{duration}s;"></div>'
            )
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    with open(css_path, encoding="utf-8") as f:
        css = " ".join(line.strip() for line in f if line.strip())
    html = (
        f"<style>{css}</style>"
        f'<div class="celebrate">{balloons}</div>'
        f'<div class="result-msg" style="color:{color}">{message}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ===== 章3：週次プランを計算する関数 担当：@TanobeYuya-13/べー/田野邉優也 =====
# やること：「開始体重・目標・開始日・期限」から、週ごとの目安体重を作る2つの関数を完成させる。
#
# 【make_weekly_plan】期限までを1週間ずつに区切り、開始体重→目標へまっすぐ近づく目安を作る。
#   戻り値は (週数, プラン一覧)。プラン一覧は
#     [{"週":1, "開始日":"2026-06-30", "終了日":"2026-07-06", "目安体重":67.0}, ...] の形。
# ヒント：
#   - total_days = (deadline - start_date).days            # 開始日から期限までの日数
#   - weeks = max(1, math.ceil(total_days / 7))            # 何週間か（端数は切り上げ）
#   - for k in range(1, weeks + 1):                         # 第1週〜第weeks週
#       target = start_weight - (start_weight - goal) * k / weeks   # 第k週の目安
#       w_start = start_date + datetime.timedelta(days=(k - 1) * 7) # その週の開始日
#       w_end   = start_date + datetime.timedelta(days=k * 7 - 1)   # その週の終了日
#       if w_end > deadline: w_end = deadline              # 期限を越えたら期限で止める
#       plan.append({"週": k, "開始日": w_start.isoformat(),
#                    "終了日": w_end.isoformat(), "目安体重": round(target, 1)})
#   - 検索例：「python ceil 切り上げ」「datetime timedelta 使い方」
def make_weekly_plan(start_weight, goal, start_date, deadline):
    plan = []
    # ↓↓↓ ここに書く ↓↓↓
    # deadlineとstart_dateの差分から期限までの日数を計算
    total_days = (deadline - start_date).days

    # total_day/7で週単位にしてceilで切り上げ（1.7週みたいな扱いにくい数字にすることを避ける）さらにmax(1, X）にすることでstart_date >= deadlineになった場合に後続の計算が想定外の挙動を行うことを防ぐ)
    weeks = max(1, math.ceil(total_days / 7))

    # 週×目標体重の辞書型データを作成する
    for k in range(1, weeks + 1):

        # 今の体重から目標体重を引いて、何キロ痩せなきゃいけないのかを計算。それを週数で割って1週間当たり何キロ痩せる目標なのかを計算
        target = start_weight - (start_weight - goal) * k / weeks

        # k（経過週数）をベースに該当週の開始日と終了日を取得
        w_start = start_date + datetime.timedelta(days=(k - 1) * 7)  # その週の開始日
        w_end = start_date + datetime.timedelta(days=k * 7 - 1)  # その週の終了日
        if w_end > deadline:
            w_end = deadline  # 期限を越えたら期限で止める

        # 作成しておいたplanの空箱に辞書型で週ごとの目標体重を格納
        plan.append(
            {
                "週": k,
                "開始日": w_start.isoformat(),
                "終了日": w_end.isoformat(),
                "目安体重": round(target, 1),
            }
        )

    # ↑↑↑ ここまで ↑↑↑
    weeks = max(1, len(plan))   # ← 上の for を書いたら、weeks は len(plan) でOK
    return weeks, plan

# 【current_week_index】今日が「第何週」かを返す（1〜weeks の範囲におさめる）。
# ヒント：
#   - elapsed = (today - start_date).days     # 開始日から今日までの経過日数
#   - idx = elapsed // 7 + 1                   # 7日ごとに1週ふえる
#   - return max(1, min(idx, weeks))           # 1未満や weeks 超えは丸める
def current_week_index(start_date, today, weeks):
    # ↓↓↓ ここに書く（return まで） ↓↓↓

    # 開始日からの経過日数を計算

    elapsed = (today - start_date).days
    idx = elapsed // 7 + 1
    return max(
        1, min(idx, weeks)
    )  # 1週目以降の経過週数を計算して今がダイエット開始から何週目にあたるのかを計算

    # ↑↑↑ ここまで ↑↑↑



# ----- サイドバー：データをリセットするボタン（テスト用・任意）担当：朝田 -----
# ヒント：if st.sidebar.button("データをリセット"): os.remove(DB_FILE) で消す → st.rerun()
#         （os.path.exists(DB_FILE) で「あれば消す」にすると安全）
# ↓↓↓ 余裕があれば書く（無くても本体は動きます）↓↓↓
if st.sidebar.button("データをリセット"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.rerun()

# ===== 章4：目標プランを決める（①）=====
# この章は2人で分担します。【入力欄UI】→【保存処理】の順に書くとつながります。
# st.header("① 目標プランを決める")
#
# --- 【入力欄UI】担当：@Hasegawa Y-13/ゆきち/長谷川ゆ ---
# やること：開始体重・目標体重・達成期限の「入力欄」を、横並びで見やすく並べる。
# ヒント：
#   - settings = load_settings()  で保存ずみを読み込み、初期値に使う（無ければ既定値）
#       例： default_goal = float(settings["goal"]) if "goal" in settings else 60.0
#       期限： datetime.date.fromisoformat(settings["deadline"]) / 既定は date.today()+timedelta(days=56)
#   - 横並び： col1, col2, col3 = st.columns(3) → with col1: ... の中に入力欄を置く
#   - 入力欄： st.number_input("開始体重（kg）", min_value=20.0, max_value=200.0, value=既定, step=0.1)
#             st.date_input("達成期限", value=既定の期限)
#   - 入力結果は start_weight_input / goal_input / deadline_input などの変数で受け取る（保存処理で使う）
# ↓↓↓ 長谷川さん：ここに書く ↓↓↓

settings = load_settings()
default_start = float(settings["start_weight"]) if "start_weight" in settings else 60.0
default_goal = float(settings["goal"]) if "goal" in settings else 60.0
default_deadline = (
    datetime.date.fromisoformat(settings["deadline"])
    if "deadline" in settings
    else datetime.date.today() + datetime.timedelta(days=56)
)

st.header("①目標を設定しましょう")

col1, col2, col3 = st.columns(3)

with col1:
    start_weight_input = st.number_input(
        "開始体重（kg）",
        min_value=20.0,
        max_value=200.0,
        value=default_start,
        step=0.1
    )

with col2:
    goal_input = st.number_input(
        "目標体重（kg）",
        min_value=20.0,
        max_value=200.0,
        value=default_goal,
        step=0.1
    )

with col3:
    deadline_input = st.date_input(
        "達成期限",
        value=default_deadline
    )



# --- 【保存処理】担当：@TanobeYuya-13/べー/田野邉優也 ---
# やること：「保存」ボタンが押されたら、上の入力値を save_setting() で4つ保存する。
# ヒント：
#   - if st.button("目標プランを保存"):
#         save_setting("start_weight", start_weight_input)
#         save_setting("goal", goal_input)
#         save_setting("deadline", deadline_input.isoformat())
#         save_setting("start_date", datetime.date.today().isoformat())   ← プランを立てた日
#         st.success("...") の後に st.rerun()
# ↓↓↓ 田野邉さん：ここに書く ↓↓↓

if st.button("目標プランを保存"):
    save_setting(
        "start_weight", start_weight_input
    )  # だーあさパートで作成された変数を受取
    save_setting("goal", goal_input)  # だーあさパートで作成された変数を受取
    save_setting(
        "deadline", deadline_input.isoformat()
    )  # だーあさパートで作成された変数を受取
    save_setting("start_date", datetime.date.today().isoformat())  #  ← プランを立てた日
    st.success("...")
    st.rerun()

# ↑↑↑ ここまで章4 ↑↑↑


# ===== 章5：今週の目安と週次プランを表示（②）=====
# この章も2人で分担します。【計算】で this_week_target と plan を用意 →【表示】で見せる。
# ★this_week_target（今週の目安体重）は、章7のグラフと章8の判定でも使う大事な値です。
st.header("② 今週の目安と週次プラン")
#
# 下の2行は「土台」。消さずに残してください（計算が未完成でもアプリが落ちないように）。
this_week_target = None
settings = load_settings()
#
# --- 【計算】担当：@TanobeYuya-13/べー/田野邉優也 ---
# やること：設定が4つそろっていたら、章3の関数を使って「今週の目安」と plan を計算する。
# ヒント：
#   - needed = ["start_weight", "goal", "deadline", "start_date"]
#     if all(k in settings for k in needed):
#         start_weight = float(settings["start_weight"]); goal = float(settings["goal"])
#         deadline = datetime.date.fromisoformat(settings["deadline"])
#         start_date = datetime.date.fromisoformat(settings["start_date"])
#         today = datetime.date.today()
#         weeks, plan = make_weekly_plan(start_weight, goal, start_date, deadline)
#         week_idx = current_week_index(start_date, today, weeks)
#         this_week_target = plan[week_idx - 1]["目安体重"]    ← この値を必ず入れる
#   ※ 表示は下の長谷川さんパートでやるので、ここは「計算して plan / week_idx / weeks を用意」まででOK。
# ↓↓↓ 田野邉さん：ここに書く ↓↓↓

# 計算に必要な変数が揃っているかチェック
needed = ["start_weight", "goal", "deadline", "start_date"]
if all(k in settings for k in needed):

    # それぞれの変数のデータ型を適切なデータ型に変換
    start_weight = float(settings["start_weight"])
    goal = float(settings["goal"])
    deadline = datetime.date.fromisoformat(settings["deadline"])
    start_date = datetime.date.fromisoformat(settings["start_date"])

    # 「現在が減量開始から何週目にあたるか」の計算のために今日の日付を取得
    today = datetime.date.today()

    # make_weekly_plan関数を利用して目標達成までの週数とそれぞれの目標体重を取得
    weeks, plan = make_weekly_plan(start_weight, goal, start_date, deadline)

    # current_week_indexを利用して今週が減量開始から何週目かの情報を取得
    week_idx = current_week_index(start_date, today, weeks)

    # planの中から今週の週番号に該当する週の目安体重を取得
    this_week_target = plan[week_idx - 1]["目安体重"]

    # 達成期限を過ぎているかどうか
    deadline_passed = today > deadline

# --- 【表示】担当：@Hasegawa Y-13/ゆきち/長谷川ゆ ---
# やること：計算できていれば「今週の目安」を大きく見せ、週次プランの表を出す。できていなければ案内。
# ヒント：
#   - if this_week_target is not None:
#         st.metric("今週の目安体重", f"{this_week_target} kg")          # 大きな数字
#         st.metric などを columns で横並びにすると見やすい（例 week_idx/weeks も）
#         st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)   # 週次プラン表
#     else:
#         st.info("まず①で目標プランを保存してください。")
# ↓↓↓ 長谷川さん：ここに書く ↓↓↓

if this_week_target is not None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("今週の目安体重", f"{this_week_target} kg")

    with col2:
        st.metric("現在の週", f"{week_idx} 週目")

    with col3:
        st.metric("全体の期間", f"{weeks} 週間")

    st.subheader("週次プラン")
    st.dataframe(
        pd.DataFrame(plan),
        use_container_width=True,
        hide_index=True
    )

    if deadline_passed:
        deadline_log = load_log()
        latest_weight = (
            float(deadline_log["weight"].iloc[-1]) if not deadline_log.empty else None
        )

        if latest_weight is not None and latest_weight <= goal:
            st.success(
                f"🎉 達成期限（{deadline.isoformat()}）を迎え、目標体重 {goal}kg を達成しました！"
                "おめでとうございます。①で新しい目標と期限を設定して、次のステップに挑戦しましょう。"
            )
        else:
            st.warning(
                f"⏰ 達成期限（{deadline.isoformat()}）を過ぎました。ここまで続けてきたこと自体が成果です。"
                "①で開始体重・目標・新しい期限を設定し直して、引き続きチャレンジしましょう！"
            )

else:
    st.info("まず①で目標プランを保存してください。")

# ↑↑↑ ここまで章5 ↑↑↑

# ===== 章6：体重を記録する（③）=====
# この章も2人で分担します。【入力＆保存】→【記録ボタンの中身（賞賛と合図）】。
# st.header("③ 体重を記録する")
#
# --- 【入力＆保存】担当：@Asada Hiroki-13/だーあさ/朝田 浩暉 ---
# やること：日付と体重の入力欄を作り、「記録」ボタンが押されたら save_record() で保存する。
# ヒント：
#   - selected_date = st.date_input("記録する日付", key="record_date")
#   - date_str = selected_date.isoformat()       # "2026-06-30" の形（★章8でも使うので必ず作る）
#   - today_weight_input = st.number_input("その日の体重（kg）", min_value=20.0, max_value=200.0, value=66.0, step=0.1)
#   - if st.button("この日の体重を記録"):
#         save_record(date_str, today_weight_input)        # ← ここまでが朝田さん
#         （この if の中に、下の竹村さんパートを続けて書く）
# ↓↓↓ 朝田さん：ここに書く ↓↓↓

st.header("③ 体重を記録する")

selected_date = st.date_input("記録する日付", key="record_date")
date_str = selected_date.isoformat()

if "deadline" in settings and selected_date > datetime.date.fromisoformat(settings["deadline"]):
    st.warning("①で目標を設定してください。")

today_weight_input = st.number_input(
    "その日の体重（kg）",
    min_value=20.0,
    max_value=200.0,
    value=66.0,
    step=0.1
)

if st.button("この日の体重を記録"):
    save_record(date_str, today_weight_input)

# --- 【記録時の賞賛＆演出の合図】担当：@Takemura Nobuhiko-13/たけ/竹村宣彦6️⃣ ---
# やること：上の「記録」ボタンが押されたとき、ねぎらいの言葉を出し、章8の演出を出す合図を立てる。
#           （↑の if st.button(...) の中に、続けて書きます）
# ヒント：
#         st.success(f"{date_str} の体重を記録しました！よくがんばりました👏")
#         st.session_state.show_result_for = date_str   # 押した直後だけ章8の演出を出す合図
#         st.rerun()
# ↓↓↓ 竹村さん：上の if の中に続けて書く ↓↓↓
    st.session_state.flash_message = f"{date_str} の体重を記録しました！よくがんばりました👏"
    st.session_state.show_result_for = date_str
    st.rerun()

if "flash_message" in st.session_state:
    st.success(st.session_state.flash_message)
    del st.session_state.flash_message

# ↑↑↑ ここまで章6 ↑↑↑

# ===== 章7：記録の一覧とグラフ（④）=====
# この章も2人で分担します。【データ取得】で log を用意 →【表とグラフの表示】。
# st.header("④ これまでの記録")
#
# --- 【データ取得】担当：@Asada Hiroki-13/だーあさ/朝田 浩暉 ---
# やること：記録を読み込み、まだ無いときは案内を出す。
# ヒント：
#   - log = load_log()
#   - if log.empty: st.info("まだ記録がありません。③から記録してみましょう。")  → ここで終わり
#   - else: の中に、下の長谷川さんパート（表・グラフ）を書く
# ↓↓↓ 朝田さん：ここに書く ↓↓↓
st.header("④ これまでの記録")

log = load_log()

if log.empty:
    st.info("まだ記録がありません。③から記録してみましょう。")
else:

# --- 【表とグラフの表示】担当：@Hasegawa Y-13/ゆきち/長谷川ゆ ---
# やること：記録を表で見せ、体重の推移を折れ線グラフで出す（目標・今週の目安の線も引けたら◎）。
#           （↑の else: の中に書きます）
# ヒント：
#       st.dataframe(log, use_container_width=True, hide_index=True)   # 表
#       chart_df = log.copy()
#       chart_df["date"] = pd.to_datetime(chart_df["date"]); chart_df = chart_df.set_index("date")
#       chart_df = chart_df.rename(columns={"weight": "体重"})
#       if "goal" in settings: chart_df["最終目標"] = float(settings["goal"])
#       if this_week_target is not None: chart_df["今週の目安"] = this_week_target
#       st.line_chart(chart_df)

# ↓↓↓ 長谷川さん：上の else の中に書く ↓↓↓


    st.subheader("これまでの記録")

    display_log = log.copy()
    display_log["weight"] = display_log["weight"].map(lambda x: f"{x:.1f}kg")

    st.dataframe(display_log, use_container_width=True, hide_index=True)


    st.subheader("体重の推移")
    chart_df = log.copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"])
    chart_df = chart_df.set_index("date")
    chart_df = chart_df.rename(columns={"weight": "体重"})

    if "goal" in settings:
        chart_df["最終目標"] = float(settings["goal"])

    if this_week_target is not None:
        # 各記録日が属する週の目安体重を、章3の関数を使って求める（週が変わると値も変わる階段状の線にする）
        chart_df["今週の目安"] = [
            plan[current_week_index(start_date, d.date(), weeks) - 1]["目安体重"]
            for d in chart_df.index
        ]

    chart_long = chart_df.reset_index().melt("date", var_name="項目", value_name="値")
    y_min = chart_long["値"].min()
    y_max = chart_long["値"].max()
    padding = max((y_max - y_min) * 0.1, 0.5)

    weight_chart = (
        alt.Chart(chart_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="日付"),
            y=alt.Y("値:Q", title="体重（kg）", scale=alt.Scale(domain=[y_min - padding, y_max + padding])),
            color=alt.Color("項目:N", title=""),
        )
    )
    st.altair_chart(weight_chart, width="stretch")

# ↑↑↑ ここまで章7 ↑↑↑


# ===== 章8：コメント＆賞賛＆風船（記録ボタンの直後だけ）=====
# この章も2人で分担します。【判定の下ごしらえ＆コメント文言】→【風船を飛ばす条件】。
#
# --- 【下ごしらえ＆コメント判定】担当：@Takemura Nobuhiko-13/たけ/竹村宣彦6️⃣ ---
# やること：記録した直後だけ、選んだ日の体重を「今週の目安」と比べ、状況を4パターンに仕分けて
#           コメント文言と色を決める（風船を出すかどうかは下の浅野さんが決めます）。
# ヒント：
#   - 記録した直後だけ出す合図：
#       show_for = st.session_state.get("show_result_for")
#       st.session_state.show_result_for = None
#   - log = load_log() を読み直し、 today_rows = log[log["date"] == date_str]
#   - if show_for == date_str and this_week_target is not None and not today_rows.empty:
#         today_weight = float(today_rows["weight"].iloc[0])
#         past = log[log["date"] < date_str]
#         achieved_before = (past["weight"] <= this_week_target).any() if not past.empty else False
#         prev_weight = float(past["weight"].iloc[-1]) if not past.empty else None
#   - 4パターン（この if/else の枝の中で、下の浅野さんパート show_result(...) を呼ぶ）：
#       今日 <= 今週の目安 ＆ achieved_before が False → 🎊 初クリアの特別賞賛 / color="#e8590c"
#       今日 <= 今週の目安 ＆ achieved_before が True  → 🎉 通常の賞賛         / color="#2b8a3e"
#       今日 >  今週の目安 ＆ 前回より減った            → 💪 順調コメント        / color="#1c7ed6"
#       今日 >  今週の目安 ＆ 前回より増えた            → ⚠️ リバウンド警告      / color="#e8590c"
#   - 検索例：「python if elif else」「pandas 条件 抽出 any」
# ↓↓↓ 竹村さん：ここに書く（4パターンの if/else とコメント文言・色）↓↓↓
show_for = st.session_state.get("show_result_for")
st.session_state.show_result_for = None

log = load_log()

if show_for is not None and this_week_target is not None:
    date_str = show_for
    today_rows = log[log["date"] == date_str]

    if not today_rows.empty:
        today_weight = float(today_rows["weight"].iloc[0])
        record_date = datetime.date.fromisoformat(date_str)
        skip_show_result = False

        show_next_goal_toast = False

        if record_date == deadline:
            # 達成期限の最終日は、週の目安ではなく最終目標を達成できたかどうかを伝える
            if today_weight <= goal:
                message = f"🏆 達成期限を迎え、最終目標 {goal}kg を達成しました！お疲れ様でした！"
                color = "#2b8a3e"
                with_balloons = True
            else:
                message = f"⏰ 達成期限を迎えました。最終目標 {goal}kg には届きませんでしたが、ここまでの頑張りは本物です！"
                color = "#e8590c"
                with_balloons = False

            show_next_goal_toast = True

        elif record_date > deadline:
            # 期限を過ぎても新しい目標プランが設定されていない（警告は③の日付入力の下に常設表示）
            skip_show_result = True

        else:
            # 記録した日付が属する週の目安体重を、章3の関数を使って求める（「今週」の目安ではなく、その日付の週の目安と比べる）
            record_week_idx = current_week_index(start_date, record_date, weeks)
            record_target = plan[record_week_idx - 1]["目安体重"]

            past = log[log["date"] < date_str]
            achieved_before = (
                (past["weight"] <= record_target).any()
                if not past.empty
                else False
            )
            prev_weight = (
                float(past["weight"].iloc[-1])
                if not past.empty
                else None
            )

            if today_weight <= record_target and achieved_before == False:
                message = f"🎊 初クリア！今週の目安 {record_target}kg を達成しました！素晴らしいです！"
                color = "#e8590c"
                with_balloons = True

            elif today_weight <= record_target and achieved_before == True:
                message = f"🎉 今週の目安 {record_target}kg をクリア！この調子で続けましょう！"
                color = "#2b8a3e"
                with_balloons = True

            elif today_weight > record_target and prev_weight is not None and today_weight < prev_weight:
                message = f"💪 目安まではあと少し！でも前回より減っています。順調です！"
                color = "#1c7ed6"
                with_balloons = False

            else:
                message = f"⚠️ 今週の目安 {record_target}kg までもう少し。焦らず立て直しましょう！"
                color = "#e8590c"
                with_balloons = False

# --- 【風船を飛ばす条件】担当：@AsanoMiyo-13/まよりん/浅野深世 ---
# やること：上の4パターンそれぞれで show_result(...) を呼び、「今週の目安を達成」した2パターン
#           だけ風船を飛ばす（with_balloons=True）。未達の2パターンは飛ばさない（False）。
# ヒント：
#   - 演出を出す関数は show_result(メッセージ, with_balloons=True/False, color="#色") （章2おまけにある）
#   - 例（達成パターン）：
#       show_result(f"🎊 はじめて今週の目安（{this_week_target}kg）クリア！", with_balloons=True, color="#e8590c")
#       show_result("🎉 今週もクリア！この調子！",                          with_balloons=True, color="#2b8a3e")
#   - 例（未達パターン＝風船なし）：
#       show_result("💪 順調！今週の目安まであと少し！",   with_balloons=False, color="#1c7ed6")
#       show_result("⚠️ リバウンドに注意！立て直そう。",   with_balloons=False, color="#e8590c")
#   ※ 各 show_result(...) は、竹村さんが作った4パターンの if/else の「それぞれの枝の中」に置きます。
# ↓↓↓ 浅野さん：竹村さんの各パターンの中に show_result(...) を入れる ↓↓↓
        if not skip_show_result:
            show_result(message, with_balloons=with_balloons, color=color)

        if show_next_goal_toast:
            # 達成コメントが表示し終わったあとに、次の目標設定の案内を目立つポップアップで出す
            st.toast(
                "**🎯 次の目標を①で設定して、引き続きチャレンジしましょう！**",
                icon="🎯",
                duration="infinite",
            )
# ↑↑↑ ここまで章8 ↑↑↑
