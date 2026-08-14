"""
Stage 7 — 도구의 계층적 조합 (에이전트를 다시 도구로)
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.
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
    """Stage 5와 동일한 문서 검색용 SubQuestionQueryEngine (BaseQueryEngine이라 QueryEngineTool로 바로 감쌀 수 있음)"""
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
    """Stage 6과 동일한 가짜 주가 조회 에이전트"""
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    return FunctionAgent(tools=[stock_tool], llm=llm, verbose=True)


def make_stock_agent_tool(stock_agent: FunctionAgent) -> FunctionTool:
    """FunctionAgent는 BaseQueryEngine이 아니라서(.query()가 없음) QueryEngineTool로
    바로 못 감쌉니다. FunctionTool의 async_fn 안에서 stock_agent.run()을 호출하는
    래퍼 함수를 만들어 그걸 도구화합니다."""

    # TODO 1: question: str을 받아 `await stock_agent.run(user_msg=question)`을 호출하고
    #         str(response)를 반환하는 비동기 함수 작성
    async def ask_stock_agent(question: str) -> str:
        ...  # <- 여기를 채우세요

    def sync_placeholder(question: str) -> str:
        raise NotImplementedError("동기 호출은 지원하지 않습니다 (async_fn만 사용)")

    # TODO 2: FunctionTool.from_defaults(fn=sync_placeholder, async_fn=ask_stock_agent,
    #         name="stock_price", description="...")로 도구화
    return None  # <- 여기를 채우세요


async def main():
    llm = get_llm()
    Settings.llm = llm
    Settings.embed_model = get_embed_model()
    Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

    sub_question_engine = build_sub_question_engine(llm)
    stock_agent = build_stock_agent(llm)

    # TODO 3: sub_question_engine을 QueryEngineTool.from_defaults(query_engine=..., name="document_qa", description="...")로 감싸기
    document_qa_tool = None  # <- 여기를 채우세요

    # TODO 4: make_stock_agent_tool(stock_agent) 호출
    stock_price_tool = None  # <- 여기를 채우세요

    # TODO 5: 위 두 도구를 가진 최상위 FunctionAgent(tools=[...], llm=llm, verbose=True) 생성
    top_agent = None  # <- 여기를 채우세요

    print("=" * 20, "문서 질문", "=" * 20)
    print(await top_agent.run(user_msg="Uber의 2021년 주요 리스크 요인은 뭐야?"))

    print("\n" + "=" * 20, "주가 질문", "=" * 20)
    print(await top_agent.run(user_msg="UBER 주가 알려줘"))

    print("\n" + "=" * 20, "복합 질문", "=" * 20)
    print(await top_agent.run(user_msg="Uber 리스크 요인 알려주고 UBER 주가도 알려줘"))


if __name__ == "__main__":
    asyncio.run(main())
