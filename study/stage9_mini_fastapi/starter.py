"""
Stage 9 (선택) — 미니 FastAPI SSE 엔드포인트
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
실제 OpenAI API 키/크레딧이 필요합니다.

실행: python starter.py
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
    """Stage 8의 스트리밍 로직을 async 채널로 흘려보내는 버전 (messaging.py의 handle_chat_message와 동일한 구조)"""
    async with send_chan:
        agent = build_agent()
        # TODO 1: await agent.astream_chat(question)으로 스트리밍 응답 얻기
        streaming_response = None  # <- 여기를 채우세요

        response_str = ""
        # TODO 2: async for token in streaming_response.async_response_gen(): 로 순회하며
        #         response_str에 누적하고 send_chan.send(response_str)로 보내기
        pass  # <- 여기를 채우세요


app = FastAPI()


@app.get("/chat")
async def chat(q: str):
    # TODO 3: anyio.create_memory_object_stream(100)으로 send_chan, recv_chan 생성
    send_chan, recv_chan = None, None  # <- 여기를 채우세요

    async def event_publisher():
        async with send_chan:
            task = asyncio.create_task(run_agent(q, send_chan))
            # TODO 4: async for msg in recv_chan: yield msg
            pass  # <- 여기를 채우세요
            await task

    return EventSourceResponse(event_publisher())


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"
    uvicorn.run(app, host="0.0.0.0", port=8010)


if __name__ == "__main__":
    main()
