# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# [JUN_JALI] Maya_Python/JUN_All/Framework -> vendor/Framework 복사 (재실행 = 갱신)
#
# 스탠드얼론 변환기는 JUN_All 의 공용 위젯(TSL · 로그 · 테마 · 메뉴 바)을 쓴다. JUN_JALI 만 받은 PC 에서도
# 돌아가야 하므로 경로를 참조하지 않고 통째로 복사해 둔다(816KB). 출처 커밋은 vendor/FRAMEWORK_SOURCE.txt.
#
# 사용:
#   .venv\Scripts\python tools\sync_framework.py                    (기본: ..\Maya_Python\JUN_All\Framework)
#   .venv\Scripts\python tools\sync_framework.py <Framework 폴더>

import datetime
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "vendor", "Framework")
DEFAULT_SRC = os.path.join(os.path.dirname(ROOT), "Maya_Python", "JUN_All", "Framework")


def _git(cwd, *args):
    try:
        out = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        return out.stdout.strip() if out.returncode == 0 else ""
    except OSError:
        return ""


def main(src):
    src = os.path.abspath(src)
    if not os.path.isfile(os.path.join(src, "qt", "qt.py")):
        print("[ERROR] Not a Framework folder: {0}".format(src))
        return 1

    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    shutil.copytree(src, DEST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    commit = _git(src, "log", "-1", "--format=%H %ad", "--date=short", "--", ".")
    remote = _git(src, "remote", "get-url", "Dnable_repo") or _git(src, "remote", "get-url", "origin")
    dirty = _git(src, "status", "--porcelain", "--", ".")
    with open(os.path.join(os.path.dirname(DEST), "FRAMEWORK_SOURCE.txt"), "w", encoding="utf-8") as f:
        f.write("source : {0}\n".format(src))
        f.write("remote : {0}\n".format(remote or "-"))
        f.write("commit : {0}\n".format(commit or "-"))
        f.write("dirty  : {0}\n".format("yes (uncommitted changes were copied)" if dirty else "no"))
        f.write("synced : {0}\n".format(datetime.datetime.now().isoformat(timespec="seconds")))
    print("[OK] Framework copied -> {0}".format(DEST))
    print("     commit {0}".format(commit or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC))
