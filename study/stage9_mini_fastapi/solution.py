"""
Stage 9 (선택) — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

실행: python solution.py
테스트: 다른 터미널에서 curl -N "http://localhost:8010/chat?q=UBER+주가+알려줘"
"""
import asyncio
import sys
from pathlib import Path

import anyio
import uvicorn
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent, AgentStream

from llm_provider import get_llm

FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    return "정보 없음" if price is None else f"{ticker.upper()} 현재가: ${price}"


def build_agent() -> FunctionAgent:
    llm = get_llm()
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    return FunctionAgent(tools=[stock_tool], llm=llm, verbose=False)


async def run_agent(question: str, send_chan: anyio.streams.memory.MemoryObjectSendStream):
    """messaging.py의 handle_chat_message와 동일한 구조: 토큰이 생성될 때마다 채널로 흘려보냄"""
    async with send_chan:
        agent = build_agent()
        handler = agent.run(user_msg=question)

        response_str = ""
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                response_str += event.delta
                await send_chan.send(response_str)

        await handler  # 워크플로우가 완전히 끝날 때까지 대기 (예외 전파 포함)


app = FastAPI()


@app.get("/chat")
async def chat(q: str):
    send_chan, recv_chan = anyio.create_memory_object_stream(100)

    async def event_publisher():
        async with send_chan:
            task = asyncio.create_task(run_agent(q, send_chan))
            async for msg in recv_chan:
                yield msg
            await task

    return EventSourceResponse(event_publisher())


def main():
    uvicorn.run(app, host="0.0.0.0", port=8010)


if __name__ == "__main__":
    main()
