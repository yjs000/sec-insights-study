"""
Stage 7 — 도구의 계층적 조합 (에이전트를 다시 도구로)
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
실제 OpenAI API 키/크레딧이 필요합니다.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.agent.openai import OpenAIAgent
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"
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
    """Stage 5에서 만든 것과 동일한 문서 검색용 SubQuestionQueryEngine"""
    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")
    index = VectorStoreIndex.from_documents(lyft_docs + uber_docs)

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
    return SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, verbose=True)


def build_stock_agent(llm) -> OpenAIAgent:
    """Stage 6에서 만든 것과 동일한 가짜 주가 조회 에이전트"""
    stock_tool = FunctionTool.from_defaults(
        fn=get_fake_stock_price,
        description="주식 티커(예: UBER, LYFT)를 받아 현재 주가를 반환한다.",
    )
    return OpenAIAgent.from_tools([stock_tool], llm=llm, verbose=True)


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    Settings.llm = llm
    Settings.embed_model = OpenAIEmbedding()
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    sub_question_engine = build_sub_question_engine(llm)
    stock_agent = build_stock_agent(llm)

    # TODO 1: sub_question_engine을 QueryEngineTool.from_defaults(query_engine=..., name="document_qa", description="...")로 감싸기
    document_qa_tool = None  # <- 여기를 채우세요

    # TODO 2: stock_agent를 QueryEngineTool.from_defaults(query_engine=..., name="stock_price", description="...")로 감싸기
    stock_price_tool = None  # <- 여기를 채우세요

    # TODO 3: 위 두 도구를 가진 최상위 OpenAIAgent.from_tools([...], llm=llm, verbose=True) 생성
    top_agent = None  # <- 여기를 채우세요

    print("=" * 20, "문서 질문", "=" * 20)
    print(top_agent.chat("Uber의 2021년 주요 리스크 요인은 뭐야?"))

    print("\n" + "=" * 20, "주가 질문", "=" * 20)
    print(top_agent.chat("UBER 주가 알려줘"))

    print("\n" + "=" * 20, "복합 질문", "=" * 20)
    print(top_agent.chat("Uber 리스크 요인 알려주고 UBER 주가도 알려줘"))


if __name__ == "__main__":
    main()
