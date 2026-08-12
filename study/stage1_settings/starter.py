"""
Stage 1 — 전역 Settings
TODO 표시된 부분만 채우세요. README.md를 먼저 읽으세요.
크레딧 걱정 없도록 MockEmbedding을 씁니다 (이번 스테이지는 청크 개수만 관찰하면 됩니다).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding

PDF_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "lyft-2021-10k.pdf"


def build_index_and_count_nodes(documents) -> int:
    """현재 Settings.node_parser 기준으로 인덱스를 만들고 노드 개수를 반환"""
    index = VectorStoreIndex.from_documents(documents)
    return len(index.docstore.docs)


def main():
    assert PDF_PATH.exists(), f"PDF를 찾을 수 없습니다: {PDF_PATH}"

    # 임베딩은 Mock으로 고정 (이번 스테이지 관심사는 청크 개수뿐)
    Settings.embed_model = MockEmbedding(embed_dim=1536)

    documents = SimpleDirectoryReader(input_files=[str(PDF_PATH)]).load_data()
    print(f"로드된 Document 개수: {len(documents)}\n")

    # TODO 1: Settings.transformations를 [SentenceSplitter(chunk_size=256, chunk_overlap=20)]으로 설정
    # 주의: Settings.node_parser = ... 로는 두 번째 변경이 반영 안 됩니다 (아래 README "함정" 참고)
    Settings.transformations = [SentenceSplitter(chunk_size=256, chunk_overlap=20)]  # <- 여기를 채우세요

    small_chunk_count = build_index_and_count_nodes(documents)
    print(f"chunk_size=256  -> 노드 개수: {small_chunk_count}")

    # TODO 2: Settings.transformations를 [SentenceSplitter(chunk_size=1024, chunk_overlap=20)]으로 재설정
    # Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=10)
    Settings.transformations = [SentenceSplitter(chunk_size=1024, chunk_overlap=20)]  # <- 여기를 채우세요

    large_chunk_count = build_index_and_count_nodes(documents)
    print(f"chunk_size=1024 -> 노드 개수: {large_chunk_count}")

    print(f"\n차이: {small_chunk_count - large_chunk_count}개")


if __name__ == "__main__":
    main()
