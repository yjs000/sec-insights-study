"""
Stage 6 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

OpenAIAgent(구식, llama-index-core<0.13 전용) 대신 FunctionAgent를 씁니다.
FunctionAgent는 provider에 상관없이 "함수 호출을 지원하는 LLM"이면 다 동작하는
범용 에이전트입니다. 동기 .chat() 대신 비동기 .run()만 제공하므로 asyncio로 실행합니다.
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


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    return "정보 없음" if price is None else f"{ticker.upper()} 현재가: ${price}"


async def main():
    llm = get_llm()

    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )

    agent = FunctionAgent(tools=[stock_tool], llm=llm, verbose=True)

    print("=" * 20, "관련 질문", "=" * 20)
    response1 = await agent.run(user_msg="UBER 주가 얼마야?")
    print("\n답변:", response1)

    print("\n" + "=" * 20, "없는 티커", "=" * 20)
    response2 = await agent.run(user_msg="TSLA 주가는?")
    print("\n답변:", response2)

    print("\n" + "=" * 20, "무관한 질문", "=" * 20)
    response3 = await agent.run(user_msg="오늘 기분 어때?")
    print("\n답변:", response3)


if __name__ == "__main__":
    asyncio.run(main())
