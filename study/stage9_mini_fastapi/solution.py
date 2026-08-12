"""
Stage 9 (선택) — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
실제 OpenAI API 키/크레딧이 필요합니다.

실행: python solution.py
테스트: 다른 터미널에서 curl -N "http://localhost:8010/chat?q=UBER+주가+알려줘"
"""
import asyncio
import os
import sys
from pathlib import Path

import anyio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI

FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    return "정보 없음" if price is None else f"{ticker.upper()} 현재가: ${price}"


def build_agent() -> OpenAIAgent:
    llm = OpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    return OpenAIAgent.from_tools([stock_tool], llm=llm, verbose=False)


async def run_agent(question: str, send_chan: anyio.streams.memory.MemoryObjectSendStream):
    async with send_chan:
        agent = build_agent()
        streaming_response = await agent.astream_chat(question)

        response_str = ""
        async for token in streaming_response.async_response_gen():
            response_str += token
            await send_chan.send(response_str)


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
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"
    uvicorn.run(app, host="0.0.0.0", port=8010)


if __name__ == "__main__":
    main()
