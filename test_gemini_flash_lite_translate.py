#!/usr/bin/env python3
"""
Gemini 2.5 Flash Lite NOTAM 번역 테스트
- .env의 GEMINI_API_KEY 사용
- temp/20260315_225128_067e239f_ImportantFile_19_split.txt에서 NOTAM 몇 개 추출 후 번역
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import google.generativeai as genai


def load_sample_notams(temp_path: Path, max_count: int = 3) -> list[str]:
    """temp 파일에서 NOTAM 블록 몇 개 추출 (날짜줄 + E) 본문)."""
    text = temp_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    notams = []
    i = 0
    while i < len(lines) and len(notams) < max_count:
        line = lines[i]
        stripped = line.strip()
        # NOTAM 헤더: "19SEP25 08:46 - UFN LOWW A2268/25" 형태
        is_header = (
            len(stripped) > 15
            and stripped[0].isdigit()
            and " - " in line
            and (" LOWW " in line or " RKSI " in line or " RKSS " in line)
            and ("/25" in line or "/26" in line)
        )
        if is_header:
            block_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == "============================================================":
                    i += 1
                    break
                block_lines.append(next_line)
                i += 1
            block = "\n".join(block_lines).strip()
            if "E)" in block and len(block) > 30:
                notams.append(block)
        else:
            i += 1
    return notams


def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("오류: .env에 GEMINI_API_KEY 또는 GOOGLE_API_KEY가 없습니다.")
        return 1

    genai.configure(api_key=api_key)
    # 테스트 대상: 2.5 Flash Lite
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    temp_file = PROJECT_ROOT / "temp" / "20260315_225128_067e239f_ImportantFile_19_split.txt"
    if not temp_file.exists():
        print(f"오류: 샘플 파일이 없습니다. {temp_file}")
        return 1

    samples = load_sample_notams(temp_file, max_count=3)
    if not samples:
        # 폴백: 하드코딩 NOTAM 2개
        samples = [
            "19SEP25 08:46 - UFN LOWW A2268/25\nE) RWY11 THR LGT CARRIED OUT IN LED\nRWY29 END LGT CARRIED OUT IN LED",
            "09MAR26 12:00 - 27MAR26 16:00 LOWW A0510/26\nD) DAILY 1200-1600\nE) MOBILE CRANE ERECTED AT OMV REFINERY SCHWECHAT\nPSN: 480824N 0163021E",
        ]
        print("(파일에서 NOTAM 추출 실패 → 기본 2건으로 테스트)\n")
    else:
        print(f"temp 파일에서 NOTAM {len(samples)}건 추출\n")

    prompt_template = """다음 NOTAM을 간단한 한국어로 번역해주세요. 핵심만 요약해도 됩니다.

NOTAM:
{notam}

한국어 번역/요약:"""

    for i, notam in enumerate(samples, 1):
        print(f"--- NOTAM {i} (원문 일부) ---")
        print(notam[:300] + ("..." if len(notam) > 300 else ""))
        print()
        try:
            prompt = prompt_template.format(notam=notam)
            response = model.generate_content(prompt)
            if response and response.text:
                print(f"--- NOTAM {i} 번역 결과 ---")
                print(response.text.strip())
            else:
                print(f"NOTAM {i}: 응답 없음")
        except Exception as e:
            print(f"NOTAM {i} 오류: {e}")
        print()

    print("테스트 완료 (모델: gemini-2.5-flash-lite)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
