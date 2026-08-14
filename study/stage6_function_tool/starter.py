"""
Stage 6 — 파이썬 함수를 에이전트 도구로 (FunctionTool)
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.
"""
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent

from llm_provider import get_llm

FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


# TODO 1: ticker: str을 받아 FAKE_PRICES에서 찾아 문자열로 반환하는 함수 작성
#         없는 티커면 "정보 없음"을 반환
def get_fake_stock_price(ticker: str) -> str:
    ...  # <- 여기를 채우세요


async def main():
    llm = get_llm()

    # TODO 2: FunctionTool.from_defaults(fn=get_fake_stock_price, description="...")로 도구화
    stock_tool = None  # <- 여기를 채우세요

    # TODO 3: 이 도구 하나만 가진 FunctionAgent(tools=[stock_tool], llm=llm, verbose=True) 생성
    agent = None  # <- 여기를 채우세요

    print("=" * 20, "관련 질문", "=" * 20)
    # TODO 4: await agent.run(user_msg="UBER 주가 얼마야?")로 실행 (OpenAIAgent와 달리 .chat()이 아니라 .run()을 씀)
    response1 = None  # <- 여기를 채우세요
    print("\n답변:", response1)

    print("\n" + "=" * 20, "없는 티커", "=" * 20)
    response2 = await agent.run(user_msg="TSLA 주가는?")
    print("\n답변:", response2)

    print("\n" + "=" * 20, "무관한 질문", "=" * 20)
    response3 = await agent.run(user_msg="오늘 기분 어때?")
    print("\n답변:", response3)


if __name__ == "__main__":
    asyncio.run(main())
