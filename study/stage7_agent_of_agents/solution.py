"""
Stage 7 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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

    document_qa_tool = QueryEngineTool.from_defaults(
        query_engine=sub_question_engine,
        name="document_qa",
        description="Lyft/Uber의 2021년 SEC 재무보고서 내용에 대한 질문(리스크 요인, 매출 등)에 답한다.",
    )
    stock_price_tool = QueryEngineTool.from_defaults(
        query_engine=stock_agent,
        name="stock_price",
        description="주식 티커의 현재가를 조회한다.",
    )

    top_agent = OpenAIAgent.from_tools(
        [document_qa_tool, stock_price_tool],
        llm=llm,
        verbose=True,
    )

    print("=" * 20, "문서 질문", "=" * 20)
    print(top_agent.chat("Uber의 2021년 주요 리스크 요인은 뭐야?"))

    print("\n" + "=" * 20, "주가 질문", "=" * 20)
    print(top_agent.chat("UBER 주가 알려줘"))

    print("\n" + "=" * 20, "복합 질문", "=" * 20)
    print(top_agent.chat("Uber 리스크 요인 알려주고 UBER 주가도 알려줘"))


if __name__ == "__main__":
    main()
