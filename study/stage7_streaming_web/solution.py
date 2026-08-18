"""
Stage 7 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

실행: python solution.py
브라우저: http://localhost:8010
"""
import asyncio
import sys
from pathlib import Path

import anyio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflows import Context
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen.llm_generators import LLMQuestionGenerator
from llama_index.core.agent.workflow import FunctionAgent, AgentStream

from llm_provider import get_llm, get_embed_model, CHUNK_SIZE, CHUNK_OVERLAP, PROVIDER
from index_cache import get_or_build_index

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"
PERSIST_DIR = Path(__file__).resolve().parent / f"storage_{PROVIDER}"
DOC_ID_KEY = "db_document_id"
FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}
HTML_PATH = Path(__file__).resolve().parent / "static" / "chat_solution.html"


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    for doc in docs:
        doc.metadata[DOC_ID_KEY] = doc_id
    return docs


def query_engine_for(index: VectorStoreIndex, doc_id: str):
    filters = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value=doc_id)])
    return index.as_query_engine(similarity_top_k=3, filters=filters)


def get_fake_stock_price(ticker: str) -> str:
    """주어진 티커의 현재 주가를 반환한다. 없는 티커면 '정보 없음'을 반환한다."""
    price = FAKE_PRICES.get(ticker.upper())
    return "정보 없음" if price is None else f"{ticker.upper()} 현재가: ${price}"


def build_document_qa_tool(llm) -> QueryEngineTool:
    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")
    index = get_or_build_index(lyft_docs + uber_docs, str(PERSIST_DIR))

    tools = [
        QueryEngineTool(
            query_engine=query_engine_for(index, "lyft"),
            metadata=ToolMetadata(name="lyft", description="Lyft의 2021년 SEC 10-K 재무보고서"),
        ),
        QueryEngineTool(
            query_engine=query_engine_for(index, "uber"),
            metadata=ToolMetadata(name="uber", description="Uber의 2021년 SEC 10-K 재무보고서"),
        ),
    ]
    question_gen = LLMQuestionGenerator.from_defaults(llm=llm)
    sub_question_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=tools, question_gen=question_gen, verbose=True
    )
    return QueryEngineTool.from_defaults(
        query_engine=sub_question_engine,
        name="document_qa",
        description="Lyft/Uber의 2021년 SEC 재무보고서 내용에 대한 질문(리스크 요인, 매출 등)에 답한다.",
    )


def build_stock_price_tool(llm) -> FunctionTool:
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    stock_agent = FunctionAgent(tools=[stock_tool], llm=llm, verbose=True)

    async def ask_stock_agent(question: str) -> str:
        response = await stock_agent.run(user_msg=question)
        return str(response)

    def sync_placeholder(question: str) -> str:
        raise NotImplementedError("동기 호출은 지원하지 않습니다 (async_fn만 사용)")

    return FunctionTool.from_defaults(
        fn=sync_placeholder,
        async_fn=ask_stock_agent,
        name="stock_price",
        description="주식 티커의 현재가를 조회한다.",
    )


# ---- 비싼 초기화는 모듈 로드(서버 시작) 시점에 한 번만 ----
print("[startup] 에이전트/도구/인덱스를 초기화합니다 (한 번만 실행됨)...")
_llm = get_llm()
Settings.llm = _llm
Settings.embed_model = get_embed_model()
Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

_document_qa_tool = build_document_qa_tool(_llm)
_stock_price_tool = build_stock_price_tool(_llm)
top_agent = FunctionAgent(tools=[_document_qa_tool, _stock_price_tool], llm=_llm, verbose=False)
print("[startup] 초기화 완료.")


async def run_agent(question: str, send_chan: anyio.streams.memory.MemoryObjectSendStream):
    async with send_chan:
        ctx = Context(top_agent)  # 요청마다 새 대화 (세션 유지는 이번 스테이지 범위 밖)
        handler = top_agent.run(user_msg=question, ctx=ctx)

        response_str = ""
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                response_str += event.delta
                await send_chan.send(response_str)

        await handler


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PATH.read_text(encoding="utf-8")


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
