"""
Stage 5 — QueryEngineTool + SubQuestionQueryEngine
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
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

from llm_provider import get_llm, get_embed_model, CHUNK_SIZE, CHUNK_OVERLAP, PROVIDER
from index_cache import get_or_build_index

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"
# 프로바이더마다 임베딩 차원/모델이 달라서 캐시 폴더를 분리합니다.
PERSIST_DIR = Path(__file__).resolve().parent / f"storage_{PROVIDER}"

DOC_ID_KEY = "db_document_id"  # Stage 3에서 배운 것: "doc_id"는 LlamaIndex 예약 키라 쓰면 안 됨


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    for doc in docs:
        doc.metadata[DOC_ID_KEY] = doc_id
    return docs


def main():
    llm = get_llm()
    Settings.llm = llm
    Settings.embed_model = get_embed_model()
    Settings.transformations = [SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)]

    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")
    index = get_or_build_index(lyft_docs + uber_docs, str(PERSIST_DIR))

    # TODO 1: doc_id="lyft"인 청크만 검색하는 쿼리 엔진 생성
    #         힌트: filters = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="lyft")])
    #              return index.as_query_engine(similarity_top_k=3, filters=filters)
    lyftFilters = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="lyft")])
    lyft_query_engine = index.as_query_engine(similarity_top_k=3, filters=lyftFilters)  # <- 여기를 채우세요

    # TODO 2: doc_id="uber"인 청크만 검색하는 쿼리 엔진 생성 (위와 동일한 패턴)
    uberFilters = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="uber")])
    uber_query_engine = index.as_query_engine(similarity_top_k=3, filters=uberFilters)    # <- 여기를 채우세요

    # TODO 3: 두 쿼리 엔진을 QueryEngineTool로 래핑 (name="lyft"/"uber", description은 의미있게)
    tools = [
        QueryEngineTool(query_engine=lyft_query_engine, metadata=ToolMetadata(name="lyft", description="문서에 대한 정보")),
        QueryEngineTool(query_engine=uber_query_engine, metadata=ToolMetadata(name="uber", description="문서에 대한 정보")),
    ]

    # TODO 4: LLMQuestionGenerator.from_defaults(llm=llm)로 질문 분해기 생성
    #         (llama-index-question-gen-openai 없이도 동작하는 범용 방식)
    question_gen = LLMQuestionGenerator.from_defaults(llm=llm)  # <- 여기를 채우세요

    # TODO 5: SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, question_gen=question_gen, verbose=True)로 조립
    sub_question_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=tools, question_gen=question_gen, verbose=True)  # <- 여기를 채우세요

    question = "Uber와 Lyft 중 2021년 매출이 더 큰 회사는 어디야?"
    response = sub_question_engine.query(question)

    print("\n" + "=" * 40)
    print("최종 답변:", response)


if __name__ == "__main__":
    main()
