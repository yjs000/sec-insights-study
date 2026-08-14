"""
Stage 7 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.

이전 버전(OpenAIAgent 기반)과의 핵심 차이:
- SubQuestionQueryEngine은 여전히 BaseQueryEngine이라 QueryEngineTool로 그대로 감쌀 수 있음.
- 하지만 FunctionAgent는 BaseQueryEngine이 아니라서(.query()가 없음) QueryEngineTool로
  감쌀 수 없음. 대신 FunctionTool로 감싸서 "이 함수는 내부적으로 다른 에이전트를 실행한다"는
  형태로 만듭니다 — 결과적으로 같은 "에이전트를 도구로" 아이디어를 다른 메커니즘으로 구현.
"""
import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
# 프로바이더마다 임베딩 차원/모델이 달라서 캐시 폴더를 분리합니다.
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


def build_sub_question_engine(llm) -> SubQuestionQueryEngine:
    """Stage 5에서 만든 것과 동일한 문서 검색용 SubQuestionQueryEngine (여전히 BaseQueryEngine)"""
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
    return SubQuestionQueryEngine.from_defaults(
        query_engine_tools=tools, question_gen=question_gen, verbose=True
    )


def build_stock_agent(llm) -> FunctionAgent:
    """Stage 6에서 만든 것과 동일한 가짜 주가 조회 에이전트"""
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    return FunctionAgent(tools=[stock_tool], llm=llm, verbose=True)


def make_stock_agent_tool(stock_agent: FunctionAgent) -> FunctionTool:
    """FunctionAgent를 다시 도구로 포장. FunctionAgent는 BaseQueryEngine이 아니라서
    QueryEngineTool로는 못 감싸고, FunctionTool의 async_fn 안에서 agent.run()을 호출하는
    방식으로 감쌉니다."""

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

    sub_question_engine = build_sub_question_engine(llm)
    stock_agent = build_stock_agent(llm)

    document_qa_tool = QueryEngineTool.from_defaults(
        query_engine=sub_question_engine,
        name="document_qa",
        description="Lyft/Uber의 2021년 SEC 재무보고서 내용에 대한 질문(리스크 요인, 매출 등)에 답한다.",
    )
    stock_price_tool = make_stock_agent_tool(stock_agent)

    top_agent = FunctionAgent(
        tools=[document_qa_tool, stock_price_tool],
        llm=llm,
        verbose=True,
    )

    print("=" * 20, "문서 질문", "=" * 20)
    print(await top_agent.run(user_msg="Uber의 2021년 주요 리스크 요인은 뭐야?"))

    print("\n" + "=" * 20, "주가 질문", "=" * 20)
    print(await top_agent.run(user_msg="UBER 주가 알려줘"))

    print("\n" + "=" * 20, "복합 질문", "=" * 20)
    print(await top_agent.run(user_msg="Uber 리스크 요인 알려주고 UBER 주가도 알려줘"))


if __name__ == "__main__":
    asyncio.run(main())
