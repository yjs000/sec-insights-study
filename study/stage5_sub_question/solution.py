"""
Stage 5 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
NVIDIA NIM(무료) 또는 OpenAI(유료) 중 study/.env의 LLM_PROVIDER로 선택된 프로바이더를 씁니다.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # study/llm_provider.py 임포트용

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen.llm_generators import LLMQuestionGenerator

from llm_provider import get_llm, get_embed_model, CHUNK_SIZE, CHUNK_OVERLAP

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
    llm = get_llm()
    Settings.llm = llm
    Settings.embed_model = get_embed_model()
    Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

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

    # llama-index-question-gen-openai 없이도 동작하는 범용(LLM 프롬프트 기반) 질문 분해기.
    # (llama-index-core>=0.13에서는 OpenAI 전용 question-gen 패키지가 지원되지 않음)
    question_gen = LLMQuestionGenerator.from_defaults(llm=llm)

    sub_question_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=tools,
        question_gen=question_gen,
        verbose=True,
    )

    question = "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?"
    response = sub_question_engine.query(question)

    print("\n" + "=" * 40)
    print("최종 답변:", response)


if __name__ == "__main__":
    main()
