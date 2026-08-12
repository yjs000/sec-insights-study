"""
Stage 5 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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

DOC_ID_KEY = "db_document_id"


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    for doc in docs:
        doc.metadata[DOC_ID_KEY] = doc_id
    return docs


def query_engine_for(index: VectorStoreIndex, doc_id: str):
    filters = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value=doc_id)])
    return index.as_query_engine(similarity_top_k=3, filters=filters)


def main():
    assert os.environ.get("OPENAI_API_KEY"), "study/.env에 OPENAI_API_KEY를 채워주세요"

    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    Settings.embed_model = OpenAIEmbedding()
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")
    index = VectorStoreIndex.from_documents(lyft_docs + uber_docs)

    lyft_query_engine = query_engine_for(index, "lyft")
    uber_query_engine = query_engine_for(index, "uber")

    tools = [
        QueryEngineTool(
            query_engine=lyft_query_engine,
            metadata=ToolMetadata(
                name="lyft",
                description="Lyft의 2021년 SEC 10-K 재무보고서. 매출, 비용, 리스크 요인 등을 담고 있음.",
            ),
        ),
        QueryEngineTool(
            query_engine=uber_query_engine,
            metadata=ToolMetadata(
                name="uber",
                description="Uber의 2021년 SEC 10-K 재무보고서. 매출, 비용, 리스크 요인 등을 담고 있음.",
            ),
        ),
    ]

    sub_question_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=tools,
        verbose=True,
    )

    question = "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?"
    response = sub_question_engine.query(question)

    print("\n" + "=" * 40)
    print("최종 답변:", response)


if __name__ == "__main__":
    main()
