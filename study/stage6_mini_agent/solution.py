"""
Stage 6 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.
"""
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflows import Context
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen.llm_generators import LLMQuestionGenerator
from llama_index.core.agent.workflow import FunctionAgent

from llm_provider import get_llm, get_embed_model, CHUNK_SIZE, CHUNK_OVERLAP, PROVIDER
from index_cache import get_or_build_index

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"
PERSIST_DIR = Path(__file__).resolve().parent / f"storage_{PROVIDER}"
DOC_ID_KEY = "db_document_id"
FAKE_PRICES = {"UBER": 72.5, "LYFT": 11.3}


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


# ---------- 1. 문서 검색 도구 (Stage 5 재사용) ----------

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


# ---------- 2. 주가 조회 에이전트 (Stage 6/7 재사용) ----------

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


async def main():
    llm = get_llm()
    Settings.llm = llm
    Settings.embed_model = get_embed_model()
    Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

    document_qa_tool = build_document_qa_tool(llm)
    stock_price_tool = build_stock_price_tool(llm)

    top_agent = FunctionAgent(
        tools=[document_qa_tool, stock_price_tool],
        llm=llm,
        verbose=True,
    )

    # 이 ctx를 계속 재사용하면 대화가 이어집니다 (REPL 전체에서 하나만 생성)
    ctx = Context(top_agent)

    print("미니 sec-insights 에이전트입니다. 'exit' 입력 시 종료.")
    print("예: 'Uber의 2021년 주요 리스크 요인이 뭐야?' / 'UBER 주가는 얼마야?' / '그럼 LYFT는?'\n")

    while True:
        question = input("질문> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        # 무료 NIM 엔드포인트는 스트리밍 도중 가끔 502/Internal server error를 던집니다.
        # 한 턴이 실패해도 REPL 전체가 죽지 않도록 감싸줍니다 (같은 ctx라 다음 질문에서 이어서 시도 가능).
        try:
            response = await top_agent.run(user_msg=question, ctx=ctx)
            print(f"\n답변> {response}\n")
        except Exception as e:
            print(f"\n[일시적 오류] {type(e).__name__}: {e}\n다시 질문해보세요.\n")


if __name__ == "__main__":
    asyncio.run(main())
