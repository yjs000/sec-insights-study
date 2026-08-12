"""
Stage 5 — QueryEngineTool + SubQuestionQueryEngine
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
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"

DOC_ID_KEY = "db_document_id"  # Stage 3에서 배운 것: "doc_id"는 LlamaIndex 예약 키라 쓰면 안 됨


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    for doc in docs:
        doc.metadata[DOC_ID_KEY] = doc_id
    return docs


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    Settings.embed_model = OpenAIEmbedding()
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")
    index = VectorStoreIndex.from_documents(lyft_docs + uber_docs)

    # TODO 1: doc_id="lyft"인 청크만 검색하는 쿼리 엔진 생성
    #         힌트: filters=MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="lyft")])
    lyft_query_engine = None  # <- 여기를 채우세요

    # TODO 2: doc_id="uber"인 청크만 검색하는 쿼리 엔진 생성
    uber_query_engine = None  # <- 여기를 채우세요

    # TODO 3: 두 쿼리 엔진을 QueryEngineTool로 래핑 (name="lyft"/"uber", description은 의미있게)
    tools = [
        # QueryEngineTool(query_engine=lyft_query_engine, metadata=ToolMetadata(name="lyft", description="...")),
        # QueryEngineTool(query_engine=uber_query_engine, metadata=ToolMetadata(name="uber", description="...")),
    ]

    # TODO 4: SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, verbose=True)로 조립
    sub_question_engine = None  # <- 여기를 채우세요

    question = "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?"
    response = sub_question_engine.query(question)

    print("\n" + "=" * 40)
    print("최종 답변:", response)


if __name__ == "__main__":
    main()
