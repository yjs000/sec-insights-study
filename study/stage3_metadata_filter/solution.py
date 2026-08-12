"""
Stage 3 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
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

DOC_ID_KEY = "db_document_id"


def load_and_tag(pdf_path: Path, doc_id: str):
    docs = SimpleDirectoryReader(input_files=[str(pdf_path)]).load_data()
    for doc in docs:
        doc.metadata[DOC_ID_KEY] = doc_id
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

    index = VectorStoreIndex.from_documents(lyft_docs + uber_docs)

    question = "What were the total revenues?"

    unfiltered_engine = index.as_query_engine(similarity_top_k=6)
    unfiltered_response = unfiltered_engine.query(question)
    print_source_doc_ids("필터 없음", unfiltered_response)

    uber_filter = MetadataFilters(filters=[ExactMatchFilter(key=DOC_ID_KEY, value="uber")])
    filtered_engine = index.as_query_engine(similarity_top_k=6, filters=uber_filter)
    filtered_response = filtered_engine.query(question)
    print_source_doc_ids("uber 필터", filtered_response)


if __name__ == "__main__":
    main()
