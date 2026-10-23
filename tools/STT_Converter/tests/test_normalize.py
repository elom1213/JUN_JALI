# -*- coding: utf-8 -*-
# STT Converter - 정규화 시험 (docs/0130 §4 표의 예시 전부). num2words 가 있으면 영어 큰 수까지.
# 사용: .venv_stt\Scripts\python.exe tools\STT_Converter\tests\test_normalize.py
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)

from tools.STT_Converter.app.core.normalize import normalize, korean, japanese, english  # noqa: E402

results = []


def check(name, got, expected):
    ok = got == expected
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "\n     got      {0!r}\n     expected {1!r}".format(got, expected)))


# ---------------------------------------------------------------- 한국어 수사
check("ko sino 1", korean.sino(1), "일")
check("ko sino 10", korean.sino(10), "십")
check("ko sino 11", korean.sino(11), "십일")
check("ko sino 100", korean.sino(100), "백")
check("ko sino 2026", korean.sino(2026), "이천이십육")
check("ko sino 10000", korean.sino(10000), "만")
check("ko sino 12345", korean.sino(12345), "만이천삼백사십오")
check("ko sino 100000000", korean.sino(100000000), "억")
check("ko sino 0", korean.sino(0), "영")
check("ko native 1 counter", korean.native(1), "한")
check("ko native 3 counter", korean.native(3), "세")
check("ko native 20 counter", korean.native(20), "스무")
check("ko native 21 counter", korean.native(21), "스물한")
check("ko native 3 alone", korean.native(3, with_counter=False), "셋")
check("ko native 100", korean.native(100), None)

# ---------------------------------------------------------------- 한국어 문장
r = normalize("제가 파에톤 님 마음속 1등이 될 거예요!", "Korean")
check("ko 1등", r.text, "제가 파에톤 님 마음속 일등이 될 거예요!")
check("ko 1등 replaced", r.replaced[0][:2], ("1등", "일등"))
check("ko 3개", normalize("사과 3개 주세요", "Korean").text, "사과 세개 주세요")
check("ko 10시", normalize("10시에 만나요", "Korean").text, "열시에 만나요")
check("ko 2026년 3월 5일", normalize("2026년 3월 5일", "Korean").text, "이천이십육년 삼월 오일")
check("ko 150개 (sino fallback)", normalize("150개", "Korean").text, "백오십개")
check("ko 3.5", normalize("3.5 배", "Korean").text, "삼 점 오 배")
check("ko 50%", normalize("50% 할인", "Korean").text, "오십퍼센트 할인")
check("ko 1,000원", normalize("1,000원", "Korean").text, "천원")
check("ko 전각 숫자", normalize("１２시", "Korean").text, "열두시")
r = normalize("KWI 노드를 만들어요", "Korean", {"KWI": "케이더블유아이"})
check("ko user dict", r.text, "케이더블유아이 노드를 만들어요")
r = normalize("UE 에디터", "Korean")
check("ko latin unresolved", [u[0] for u in r.unresolved], ["UE"])
check("ko quotes/ellipsis", normalize("\"그리고… 언젠가는\"", "Korean").text, "그리고 언젠가는")
check("ko newlines -> space", normalize("첫 줄\n둘째 줄\r\n셋째", "Korean").text, "첫 줄 둘째 줄 셋째")
check("ko unchanged", normalize("저는 반드시 올라갈 거예요", "Korean").changed, False)

# ---------------------------------------------------------------- 일본어
check("ja kanji 3", japanese.kanji(3), "三")
check("ja kanji 10", japanese.kanji(10), "十")
check("ja kanji 2026", japanese.kanji(2026), "二千二十六")
check("ja kanji 10000", japanese.kanji(10000), "一万")
check("ja kanji 1000", japanese.kanji(1000), "千")
check("ja 3時", normalize("3時に会いましょう", "Japanese").text, "三時に会いましょう")
check("ja 2026年", normalize("2026年", "Japanese").text, "二千二十六年")
check("ja 50%", normalize("50%", "Japanese").text, "五十パーセント")
check("ja 3.5", normalize("3.5倍", "Japanese").text, "三点五倍")
check("ja keeps spaces", normalize("そして、いつか\nパエトーン様", "Japanese").text, "そして、いつか パエトーン様")
check("ja brackets", normalize("「おはよう」と言った", "Japanese").text, "おはよう と言った")
r = normalize("JALI リグ", "Japanese", {"JALI": "ジャリ"})
check("ja user dict", r.text, "ジャリ リグ")
check("ja latin unresolved", [u[0] for u in normalize("UE で作る", "Japanese").unresolved], ["UE"])
r = normalize("今日は", "Japanese", kana=True)
check("ja kana option (pykakasi optional)", r.text in ("きょうは", "今日は"), True)

# ---------------------------------------------------------------- 영어
check("en 2018 year", normalize("in 2018 we met", "English").text, "in twenty eighteen we met")
check("en 2005 year", normalize("in 2005", "English").text, "in two thousand five")
check("en 1900", normalize("in 1900", "English").text, "in nineteen hundred")
check("en 1st", normalize("the 1st time", "English").text, "the first time")
check("en 3rd", normalize("3rd", "English").text, "third")
check("en 50%", normalize("50% off", "English").text, "fifty percent off")
check("en $5", normalize("$5", "English").text, "five dollars")
check("en $1", normalize("$1", "English").text, "one dollar")
check("en $2.50", normalize("$2.50", "English").text, "two dollars fifty cents")
check("en 3:30", normalize("at 3:30", "English").text, "at three thirty")
check("en 3:00", normalize("at 3:00", "English").text, "at three o'clock")
check("en 3:05", normalize("at 3:05", "English").text, "at three oh five")
check("en 3.5", normalize("3.5 times", "English").text, "three point five times")
check("en 1,000", normalize("1,000 people", "English").text, "one thousand people")
check("en 12", normalize("12 joints", "English").text, "twelve joints")
check("en 2,018 (comma, not year)", normalize("2,018", "English").text, "two thousand eighteen")
r = normalize("open UE and KWI", "English")
check("en acronyms W23", [u[0] for u in r.unresolved], ["UE", "KWI"])
r = normalize("open UE", "English", {"UE": "U E"})
check("en user dict", r.text, "open U E")
check("en quotes", normalize("\"No matter how far you go.\"", "English").text, "No matter how far you go.")
check("en unchanged", normalize("One day, I'll climb high enough.", "English").changed, False)

# ---------------------------------------------------------------- 공통
try:
    normalize("x", "Klingon")
    check("unknown language raises", False, True)
except ValueError:
    check("unknown language raises", True, True)

n_fail = results.count(False)
print("\n{0} checks, {1} failed".format(len(results), n_fail))
sys.exit(1 if n_fail else 0)
