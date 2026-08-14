"""
Stage 8 — 스트리밍 응답 + 이벤트 관찰
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.
"""
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import (
    FunctionAgent,
    AgentStream,
    ToolCall,
    ToolCallResult,
)

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
    agent = FunctionAgent(tools=[stock_tool], llm=llm, verbose=False)

    print("=" * 20, "스트리밍 + 이벤트 관찰", "=" * 20)

    # TODO 1: agent.run(user_msg="LYFT 주가 알려줘")를 호출 (await 없이 — handler를 바로 받음)
    handler = None  # <- 여기를 채우세요

    # TODO 2: async for event in handler.stream_events(): 로 순회하며
    #         - ToolCall이면 f"\n>>> TOOL CALL   name={event.tool_name} args={event.tool_kwargs}" 출력
    #         - ToolCallResult이면 f">>> TOOL RESULT {event.tool_output}" 출력
    #         - AgentStream이면 event.delta를 end="", flush=True로 출력 (토큰 스트리밍)
    async for event in []:  # <- handler.stream_events() 로 바꾸세요
        pass

    # TODO 3: await handler로 최종 결과 받기
    final_response = None  # <- 여기를 채우세요
    print("\n\n최종 답변:", final_response)


if __name__ == "__main__":
    asyncio.run(main())
