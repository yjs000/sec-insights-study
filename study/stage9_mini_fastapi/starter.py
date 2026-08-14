"""
Stage 9 (선택) — 미니 FastAPI SSE 엔드포인트
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

실행: python starter.py
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
    async with send_chan:
        agent = build_agent()

        # TODO 1: agent.run(user_msg=question)으로 handler 받기 (await 없이)
        handler = None  # <- 여기를 채우세요

        response_str = ""
        # TODO 2: async for event in handler.stream_events(): 로 순회하며
        #         AgentStream이면 response_str에 event.delta를 누적하고
        #         await send_chan.send(response_str)
        async for event in []:  # <- handler.stream_events() 로 바꾸세요
            pass

        # TODO 3: await handler로 워크플로우 종료까지 대기
        pass  # <- 여기를 채우세요


app = FastAPI()


@app.get("/chat")
async def chat(q: str):
    # TODO 4: anyio.create_memory_object_stream(100)으로 send_chan, recv_chan 생성
    send_chan, recv_chan = None, None  # <- 여기를 채우세요

    async def event_publisher():
        async with send_chan:
            task = asyncio.create_task(run_agent(q, send_chan))
            # TODO 5: async for msg in recv_chan: yield msg
            pass  # <- 여기를 채우세요
            await task

    return EventSourceResponse(event_publisher())


def main():
    uvicorn.run(app, host="0.0.0.0", port=8010)


if __name__ == "__main__":
    main()
