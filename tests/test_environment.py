"""実行環境の不具合を、実際の import で検出する（T-005）。"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# requirements の配布名と import 名が違うものだけ書く
IMPORT_NAMES = {"scikit-learn": "sklearn"}


def required_import_names():
    names = []
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dist = re.split(r"[=<>!~\[; ]", line, maxsplit=1)[0]
        names.append(IMPORT_NAMES.get(dist, dist.replace("-", "_")))
    return names


def test_supabase_is_importable_from_the_project_directory():
    """プロジェクト直下から `from supabase import create_client` が pip 版で成功する。"""
    code = "import supabase; from supabase import create_client; print(supabase.__file__ or '')"
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    hint = (
        "この Python に supabase が入っていないか、同名のローカルディレクトリに隠されています。"
        " `pip install -r requirements.txt` を実行し、`supabase/` という名前のディレクトリを置かないでください。\n"
        + result.stderr[-500:]
    )
    assert result.returncode == 0, hint
    origin = pathlib.Path(result.stdout.strip() or "/")
    assert ROOT not in origin.parents, f"ローカルの {origin} を読み込んでいます。\n{hint}"


def test_no_local_file_or_directory_shadows_a_dependency():
    """依存パッケージと同名のディレクトリ・ファイルをプロジェクト直下に置かない。"""
    clashes = []
    for name in required_import_names():
        for candidate in (ROOT / name, ROOT / f"{name}.py"):
            if candidate.exists():
                clashes.append(candidate.name)
    assert not clashes, f"依存パッケージと同名のものがあります: {clashes}"
