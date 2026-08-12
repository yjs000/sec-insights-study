"""
Stage 1 — 참고 답안. 먼저 starter.py를 직접 채워본 뒤에 비교용으로만 여세요.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"


def build_index_and_count_nodes(documents) -> int:
    index = VectorStoreIndex.from_documents(documents)
    return len(index.docstore.docs)


def main():
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    Settings.embed_model = MockEmbedding(embed_dim=1536)

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()
    print(f"로드된 Document 개수: {len(documents)}\n")

    # Settings.node_parser = ... 가 아니라 Settings.transformations = [...] 를 씁니다.
    # 이유는 README.md의 "함정" 절 참고 (node_parser는 최초 접근 시 캐싱되어
    # 두 번째부터는 재할당해도 from_documents()에 반영되지 않습니다).
    Settings.transformations = [SentenceSplitter(chunk_size=256, chunk_overlap=20)]
    small_chunk_count = build_index_and_count_nodes(documents)
    print(f"chunk_size=256  -> 노드 개수: {small_chunk_count}")

    Settings.transformations = [SentenceSplitter(chunk_size=1024, chunk_overlap=20)]
    large_chunk_count = build_index_and_count_nodes(documents)
    print(f"chunk_size=1024 -> 노드 개수: {large_chunk_count}")

    print(f"\n차이: {small_chunk_count - large_chunk_count}개")


if __name__ == "__main__":
    main()
