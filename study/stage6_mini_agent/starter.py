"""
Stage 6 — 미니 에이전트 만들기 (한 번에 다 붙이기)
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
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

    # TODO 1: get_or_build_index(lyft_docs + uber_docs, str(PERSIST_DIR))로 인덱스 생성/로드
    index = get_or_build_index(lyft_docs + uber_docs, str(PERSIST_DIR))  # <- 여기를 채우세요

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

    # TODO 2: LLMQuestionGenerator.from_defaults(llm=llm)로 질문 분해기 생성
    question_gen = LLMQuestionGenerator.from_defaults(llm=llm)  # <- 여기를 채우세요

    # TODO 3: SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, question_gen=question_gen, verbose=True)
    sub_question_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, question_gen=question_gen, verbose=True)  # <- 여기를 채우세요

    # TODO 4: QueryEngineTool.from_defaults(query_engine=sub_question_engine, name="document_qa", description="...")
    return QueryEngineTool.from_defaults(query_engine=sub_question_engine, name="document_qa", description="Lyft/Uber의 2021년 SEC 재무보고서 내용에 대한 질문(리스크 요인, 매출 등)에 답한다.")  # <- 여기를 채우세요


# ---------- 2. 주가 조회 에이전트 (Stage 6/7 재사용) ----------

def build_stock_price_tool(llm) -> FunctionTool:
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    # TODO 5: 이 도구 하나만 가진 FunctionAgent(tools=[stock_tool], llm=llm, verbose=True) 생성
    stock_agent = FunctionAgent(tools=[stock_tool], llm=llm, verbose=True)  # <- 여기를 채우세요

    # TODO 6: question: str을 받아 `await stock_agent.run(user_msg=question)`을 호출하고
    #         str(response)를 반환하는 비동기 함수 작성
    async def ask_stock_agent(question: str) -> str:
        response = await stock_agent.run(user_msg=question)
        return str(response)  # <- 여기를 채우세요 (str()로 감싸야 함: response는 AgentOutput 객체라 그대로 반환하면 상위 에이전트가 파싱하기 애매함)

    def sync_placeholder(question: str) -> str:
        raise NotImplementedError("동기 호출은 지원하지 않습니다 (async_fn만 사용)")

    # TODO 7: FunctionTool.from_defaults(fn=sync_placeholder, async_fn=ask_stock_agent,
    #         name="stock_price", description="...")
    return FunctionTool.from_defaults(fn=sync_placeholder, async_fn=ask_stock_agent,name="stock_price", description="주식 티커의 현재가를 조회한다.")  # <- 여기를 채우세요


async def main():
    llm = get_llm()
    Settings.llm = llm
    Settings.embed_model = get_embed_model()
    Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

    document_qa_tool = build_document_qa_tool(llm)
    stock_price_tool = build_stock_price_tool(llm)

    # TODO 8: 위 두 도구를 가진 최상위 FunctionAgent(tools=[...], llm=llm, verbose=True) 생성
    top_agent = FunctionAgent(tools=[document_qa_tool, stock_price_tool], llm=llm, verbose=True)  # <- 여기를 채우세요

    # TODO 9: Context(top_agent)로 대화 상태를 담을 ctx 하나 생성 (루프 밖에서 한 번만!)
    ctx = Context(top_agent)  # <- 여기를 채우세요

    print("미니 sec-insights 에이전트입니다. 'exit' 입력 시 종료.")
    print("예: 'Uber의 2021년 주요 리스크 요인이 뭐야?' / 'UBER 주가는 얼마야?' / '그럼 LYFT는?'\n")

    while True:
        question = input("질문> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        # TODO 10: await top_agent.run(user_msg=question, ctx=ctx)로 실행하고 결과 출력
        # 무료 NIM 엔드포인트는 스트리밍 도중 가끔 502/Internal server error를 던집니다.
        # 한 턴이 실패해도 REPL 전체가 죽지 않도록 감싸줍니다 (같은 ctx라 다음 질문에서 이어서 시도 가능).
        try:
            response = await top_agent.run(user_msg=question, ctx=ctx)  # <- 여기를 채우세요
            print(f"\n답변> {response}\n")
        except Exception as e:
            print(f"\n[일시적 오류] {type(e).__name__}: {e}\n다시 질문해보세요.\n")


if __name__ == "__main__":
    asyncio.run(main())
