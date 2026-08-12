"""
Stage 6 — 파이썬 함수를 에이전트 도구로 (FunctionTool)
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
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


# TODO 1: ticker: str을 받아 FAKE_PRICES에서 찾아 문자열로 반환하는 함수 작성
#         없는 티커면 "정보 없음"을 반환
def get_fake_stock_price(ticker: str) -> str:
    ...  # <- 여기를 채우세요


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    llm = OpenAI(model="gpt-4o-mini", temperature=0)

    # TODO 2: FunctionTool.from_defaults(fn=get_fake_stock_price, description="...")로 도구화
    stock_tool = None  # <- 여기를 채우세요

    # TODO 3: 이 도구 하나만 가진 OpenAIAgent.from_tools([stock_tool], llm=llm, verbose=True) 생성
    agent = None  # <- 여기를 채우세요

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
