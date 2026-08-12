"""
Stage 6 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
실제 OpenAI API 키/크레딧이 필요합니다.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI

FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    if price is None:
        return "정보 없음"
    return f"{ticker.upper()} 현재가: ${price}"


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    llm = OpenAI(model="gpt-4o-mini", temperature=0)

    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )

    agent = OpenAIAgent.from_tools([stock_tool], llm=llm, verbose=True)

    print("=" * 20, "관련 질문", "=" * 20)
    response1 = agent.chat("UBER 주가 얼마야?")
    print("\n답변:", response1)

    print("\n" + "=" * 20, "없는 티커", "=" * 20)
    response2 = agent.chat("TSLA 주가는?")
    print("\n답변:", response2)

    print("\n" + "=" * 20, "무관한 질문", "=" * 20)
    response3 = agent.chat("오늘 기분 어때?")
    print("\n답변:", response3)


if __name__ == "__main__":
    main()
