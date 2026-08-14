"""
Stage 8 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

OpenAIAgent 시절엔 콜백을 BaseCallbackHandler로 잡았지만, FunctionAgent는
Workflow 기반이라 이벤트를 handler.stream_events()로 직접 순회해서 관찰합니다.
스트리밍 토큰과 "중간 상태 관찰"이 같은 스트림 안에서 자연스럽게 합쳐집니다
(sec-insights의 messaging.py가 콜백+스트리밍을 SSE 하나로 합치는 것과 같은 아이디어).
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
    handler = agent.run(user_msg="LYFT 주가 알려줘")

    async for event in handler.stream_events():
        if isinstance(event, ToolCall):
            print(f"\n>>> TOOL CALL   name={event.tool_name} args={event.tool_kwargs}")
        elif isinstance(event, ToolCallResult):
            print(f">>> TOOL RESULT {event.tool_output}")
        elif isinstance(event, AgentStream):
            # LLM이 생성하는 토큰 조각. 여기가 "진짜 스트리밍" 부분.
            print(event.delta, end="", flush=True)

    final_response = await handler
    print("\n\n최종 답변:", final_response)


if __name__ == "__main__":
    asyncio.run(main())
