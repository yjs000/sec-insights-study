"""
Stage 3 — 문서 여러 개를 한 인덱스에 넣고 필터링
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.

주의: 메타데이터 키 이름으로 "doc_id"를 쓰지 마세요 — LlamaIndex가 내부적으로
ref_doc UUID를 저장할 때 이미 "doc_id" 키를 예약해서 씁니다. 우리가 넣은 값이
그걸로 덮어써져서 필터가 항상 0건을 반환하게 됩니다 (README "함정" 절 참고).
sec-insights도 이 충돌을 피하려고 "db_document_id"라는 키를 씁니다.
"""
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public"
LYFT_PDF = PUBLIC_DIR / "lyft-2021-10k.pdf"
UBER_PDF = PUBLIC_DIR / "uber-2021-10k.pdf"

DOC_ID_KEY = "db_document_id"  # sec-insights의 DB_DOC_ID_KEY와 동일한 이유로 이 이름을 씁니다


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    # TODO 1: 각 Document의 metadata[DOC_ID_KEY]에 doc_id 값을 채워넣기
    for doc in docs:
        pass  # <- 여기를 채우세요
    return docs


def print_source_doc_ids(label: str, response):
    ids = [n.node.metadata.get(DOC_ID_KEY, "?") for n in response.source_nodes]
    print(f"{label}: {dict(Counter(ids))}")


def main():
    Settings.embed_model = MockEmbedding(embed_dim=1536)
    Settings.llm = MockLLM()
    Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=10)]

    lyft_docs = load_and_tag(LYFT_PDF, "lyft")
    uber_docs = load_and_tag(UBER_PDF, "uber")

    # TODO 2: lyft_docs + uber_docs를 합쳐 하나의 VectorStoreIndex 생성
    index = None  # <- 여기를 채우세요

    question = "What were the total revenues?"

    # ---- 필터 없이 검색 ----
    # TODO 3: index.as_query_engine(similarity_top_k=6)으로 쿼리 엔진 생성 후 질의
    unfiltered_engine = None  # <- 여기를 채우세요
    unfiltered_response = None  # <- unfiltered_engine.query(question)
    print_source_doc_ids("필터 없음", unfiltered_response)

    # ---- uber만 필터링해서 검색 ----
    # TODO 4: MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="uber")]) 생성
    uber_filter = None  # <- 여기를 채우세요

    # TODO 5: filters=uber_filter를 넣어 쿼리 엔진 생성 후 같은 질문 재질의
    filtered_engine = None  # <- 여기를 채우세요
    filtered_response = None  # <- filtered_engine.query(question)
    print_source_doc_ids("uber 필터", filtered_response)


if __name__ == "__main__":
    main()
